from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from telethon.errors import (PhoneCodeExpiredError, PhoneCodeInvalidError, PhoneNumberInvalidError,
                             SessionPasswordNeededError, PasswordHashInvalidError)
from telethon.sessions import StringSession

from app.constants import DEFAULT_MODULES
from app.control_bot.keyboards import cancel_keyboard, disconnect_keyboard, home_keyboard
from app.control_bot.states import LoginState
from app.database.repositories import ModeRepository, SettingsRepository, UsageRepository

logger = logging.getLogger(__name__)
PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


@dataclass
class PendingLogin:
    client: object
    phone: str
    phone_code_hash: str
    attempts: int = 0


def create_router(container: object) -> Router:
    router = Router()

    async def menu_text(control_id: int) -> tuple[str, bool]:
        user = await container.users.ensure(control_id)
        online = container.manager.is_running(control_id)
        if not user.connected:
            return "╭ USERBOT\n├ Status: 🔴 disconnected\n╰ Connect Telegram to activate commands", False
        username = f"@{user.username}" if user.username else (user.first_name or "Telegram account")
        return f"╭ USERBOT\n├ {username}\n├ {'🟢 Online' if online else '🟡 reconnecting'}\n├ 🤖 AI: {'ON' if container.settings.ai_api_key else 'OFF'}\n╰ ⚡ Commands ready", True

    async def show_menu(message: Message, control_id: int) -> None:
        text, connected = await menu_text(control_id)
        await message.answer(text, reply_markup=home_keyboard(connected))

    async def cleanup_auth(control_id: int, state: FSMContext) -> None:
        pending = container.temp_auth.pop(control_id, None)
        if pending:
            try: await pending.client.disconnect()
            except Exception: pass
        await state.clear()

    async def delete_secret(message: Message) -> None:
        try: await message.delete()
        except TelegramBadRequest: pass

    @router.message(Command("start", "account"))
    async def start(message: Message) -> None:
        await show_menu(message, message.from_user.id)

    @router.message(Command("cancel"))
    async def cancel(message: Message, state: FSMContext) -> None:
        await cleanup_auth(message.from_user.id, state)
        await message.answer("Авторизация отменена.")

    @router.callback_query(F.data == "home:main")
    async def home(callback: CallbackQuery) -> None:
        text, connected = await menu_text(callback.from_user.id)
        await callback.message.edit_text(text, reply_markup=home_keyboard(connected)); await callback.answer()

    @router.callback_query(F.data == "auth:start")
    async def auth_start(callback: CallbackQuery, state: FSMContext) -> None:
        user = await container.users.ensure(callback.from_user.id)
        if user.connected:
            await callback.answer("Сначала отключи текущий аккаунт.", show_alert=True); return
        await state.set_state(LoginState.phone)
        await callback.message.edit_text("📱 Отправь номер телефона в международном формате.\nПример: +79991234567", reply_markup=cancel_keyboard())
        await callback.answer()

    @router.callback_query(F.data == "auth:cancel")
    async def auth_cancel(callback: CallbackQuery, state: FSMContext) -> None:
        await cleanup_auth(callback.from_user.id, state)
        text, connected = await menu_text(callback.from_user.id)
        await callback.message.edit_text(text, reply_markup=home_keyboard(connected)); await callback.answer()

    @router.message(LoginState.phone)
    async def receive_phone(message: Message, state: FSMContext) -> None:
        phone = (message.text or "").replace(" ", "").replace("-", "")
        if not PHONE_RE.fullmatch(phone):
            await message.answer("❌ Некорректный номер. Используй формат +79991234567.", reply_markup=cancel_keyboard()); return
        await delete_secret(message)
        await cleanup_auth(message.from_user.id, state)
        client = container.factory.create_temporary_login_client()
        try:
            await client.connect()
            sent = await client.send_code_request(phone)
        except PhoneNumberInvalidError:
            await client.disconnect(); await state.set_state(LoginState.phone); await message.answer("❌ Telegram не принял номер.", reply_markup=cancel_keyboard()); return
        except Exception:
            logger.exception("authorization_code_request_failed user=%s", message.from_user.id)
            await client.disconnect(); await state.set_state(LoginState.phone); await message.answer("⚠️ Не удалось отправить код. Повтори позже.", reply_markup=cancel_keyboard()); return
        container.temp_auth[message.from_user.id] = PendingLogin(client, phone, sent.phone_code_hash)
        await container.users.audit(message.from_user.id, "authorization_started")
        await state.set_state(LoginState.code)
        await message.answer("🔐 Telegram отправил код входа. Отправь код.", reply_markup=cancel_keyboard())

    async def complete_login(message: Message, state: FSMContext, pending: PendingLogin) -> None:
        me = await pending.client.get_me()
        session = StringSession.save(pending.client.session)
        try:
            await container.users.connect(message.from_user.id, me.id, me.username, me.first_name, container.crypto.encrypt(session))
            await container.manager.start_user(message.from_user.id, preconnected_client=pending.client, session=session, account_id=me.id)
        except ValueError:
            await pending.client.disconnect(); await cleanup_auth(message.from_user.id, state)
            await message.answer("⚠️ Этот Telegram аккаунт уже подключён."); return
        await container.users.audit(message.from_user.id, "authorization_successful")
        container.temp_auth.pop(message.from_user.id, None)
        await state.clear()
        await message.answer("✅ Telegram аккаунт подключён. Userbot уже online.")
        await show_menu(message, message.from_user.id)

    @router.message(LoginState.code)
    async def receive_code(message: Message, state: FSMContext) -> None:
        pending = container.temp_auth.get(message.from_user.id)
        code = (message.text or "").replace(" ", "")
        await delete_secret(message)
        if not pending or not code.isdigit() or len(code) < 4:
            await message.answer("❌ Некорректный код.", reply_markup=cancel_keyboard()); return
        try:
            await pending.client.sign_in(phone=pending.phone, code=code, phone_code_hash=pending.phone_code_hash)
        except SessionPasswordNeededError:
            await state.set_state(LoginState.password); await message.answer("🔐 На аккаунте включена 2FA. Отправь пароль.", reply_markup=cancel_keyboard()); return
        except (PhoneCodeInvalidError, PhoneCodeExpiredError):
            await message.answer("❌ Код неверный или истёк. Нажми отмену и запроси новый.", reply_markup=cancel_keyboard()); return
        await complete_login(message, state, pending)

    @router.message(LoginState.password)
    async def receive_password(message: Message, state: FSMContext) -> None:
        pending = container.temp_auth.get(message.from_user.id)
        password = message.text or ""
        await delete_secret(message)
        if not pending: await cleanup_auth(message.from_user.id, state); return
        try:
            await pending.client.sign_in(password=password)
        except PasswordHashInvalidError:
            pending.attempts += 1
            if pending.attempts >= 5:
                await cleanup_auth(message.from_user.id, state); await message.answer("❌ Слишком много попыток. Авторизация отменена.")
            else: await message.answer("❌ Неверный пароль. Попробуй ещё раз.", reply_markup=cancel_keyboard())
            return
        password = ""
        await complete_login(message, state, pending)

    @router.callback_query(F.data == "logout:ask")
    async def ask_logout(callback: CallbackQuery) -> None:
        user = await container.users.get(callback.from_user.id)
        name = f"@{user.username}" if user and user.username else "аккаунт"
        await callback.message.edit_text(f"Отключить {name}?", reply_markup=disconnect_keyboard()); await callback.answer()

    @router.callback_query(F.data.in_({"logout:forget", "logout:terminate"}))
    async def logout(callback: CallbackQuery) -> None:
        terminate = callback.data == "logout:terminate"
        await container.manager.stop_user(callback.from_user.id, logout=terminate)
        await container.users.disconnect(callback.from_user.id)
        await callback.answer("Отключено")
        text, connected = await menu_text(callback.from_user.id)
        await callback.message.edit_text(text, reply_markup=home_keyboard(connected))

    @router.callback_query(F.data == "home:commands")
    async def commands(callback: CallbackQuery) -> None:
        await callback.message.edit_text("📚 Возможности\n\nПосле подключения команды работают с вашего аккаунта.\n\n.help - все команды\n.kawaii - режим трансформации\n.bold, .sw, .afk, .note, .ttt и другие.", reply_markup=home_keyboard((await container.users.ensure(callback.from_user.id)).connected)); await callback.answer()

    @router.callback_query(F.data == "home:modules")
    async def modules(callback: CallbackQuery) -> None:
        user = await container.users.ensure(callback.from_user.id)
        settings = SettingsRepository(container.db)
        values = await settings.get(user.id, "modules", DEFAULT_MODULES)
        lines = ["📦 Modules"] + [f"{'✅' if enabled else '❌'} {name}" for name, enabled in values.items()]
        await callback.message.edit_text("\n".join(lines), reply_markup=home_keyboard(True)); await callback.answer()

    @router.callback_query(F.data == "home:settings")
    async def settings(callback: CallbackQuery) -> None:
        await callback.message.edit_text("⚙️ Settings\n\nLanguage: Russian\nDefault send mode: edit\nPrivacy: message history is not stored\n\nAI and modules are managed from their panels.", reply_markup=home_keyboard(True)); await callback.answer()

    @router.callback_query(F.data == "home:ai")
    async def ai(callback: CallbackQuery) -> None:
        user = await container.users.ensure(callback.from_user.id)
        usage = await UsageRepository(container.db).ai_usage(user.id)
        await callback.message.edit_text(f"🤖 AI\n\nModel: {container.settings.ai_model}\nMode: {'enabled' if container.settings.ai_api_key else 'disabled'}\nToday: {usage.requests if usage else 0} requests\nLimit: 100", reply_markup=home_keyboard(True)); await callback.answer()

    @router.callback_query(F.data == "home:stats")
    async def stats(callback: CallbackQuery) -> None:
        user = await container.users.ensure(callback.from_user.id); usage = await UsageRepository(container.db).ai_usage(user.id)
        await callback.message.edit_text(f"📊 Statistics\n\nAI requests today: {usage.requests if usage else 0}\nAI errors: {usage.errors if usage else 0}\nAccount: {'connected' if user.connected else 'disconnected'}", reply_markup=home_keyboard(user.connected)); await callback.answer()

    return router
