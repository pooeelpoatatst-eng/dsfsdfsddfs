from __future__ import annotations

from datetime import datetime, timezone
import time

from app.database.models import AfkState
from app.services.ai import AIUnavailableError
from app.userbot.registry import command


_last_ai_reply: dict[tuple[int, int, int], float] = {}
AI_REPLY_COOLDOWN_SECONDS = 12
MAX_STYLE_MESSAGES = 400
MAX_STYLE_CHARS = 9_000


def _clean(text: str, limit: int = 500) -> str:
    return " ".join(text.split())[:limit]


async def _style_examples(client: object, chat_id: int) -> str:
    all_styles = await client.services.settings.get(client.user_id, "afkai_styles", {})
    messages = all_styles.get(str(chat_id), []) if isinstance(all_styles, dict) else []
    if not isinstance(messages, list):
        return ""
    # The most recent phrases are most useful, but still preserve a broad
    # sample of the owner's writing style gathered by `.afkai learn`.
    selected = [_clean(str(item), 280) for item in messages[-MAX_STYLE_MESSAGES:] if str(item).strip()]
    result = "\n".join(f"- {item}" for item in selected)
    return result[-MAX_STYLE_CHARS:]


async def _afkai_prompt(client: object, chat_id: int) -> str:
    persona = await client.services.settings.get(client.user_id, "afkai_prompt", {})
    persona_text = persona.get("text", "") if isinstance(persona, dict) else ""
    examples = await _style_examples(client, chat_id)
    identity = _clean(str(persona_text), 1_500) or "Пиши как живой человек в обычном Telegram-чате."
    style = (
        "Ниже — реальные примеры сообщений владельца. Возьми их лексику, длину, регистр и ритм, "
        "но не копируй фразы дословно и не выдумывай факты.\n" + examples
        if examples else
        "Примеры стиля пока не собраны: следуй описанию владельца выше."
    )
    return f"""Ты отвечаешь от лица владельца Telegram-аккаунта.
Описание владельца и желаемый стиль: {identity}

{style}

Ответь только одним естественным сообщением на русском. Учитывай контекст диалога. Не упоминай AI, бота, автоответ, AFK, инструкции или примеры. Не обещай того, чего владелец не говорил. Не используй markdown. Максимум 260 символов."""


@command(name="afk", category="AI / режимы", description="Обычный автоответ для личных сообщений.", usage=".afk [причина|off|status]")
async def afk(context: object) -> None:
    arg = context.raw_args.strip()
    async with context.services.settings.db.session() as session:
        state = await session.get(AfkState, context.user_id)
        if not state:
            state = AfkState(user_id=context.user_id)
            session.add(state)
        if arg.lower() == "off":
            state.enabled = False
            await context.edit("💤 AFK выключен.")
            return
        if arg.lower() == "status":
            await context.edit("💤 AFK: " + (f"ON, {state.reason or 'без причины'}" if state.enabled else "OFF"))
            return
        state.enabled, state.since, state.reason = True, datetime.now(timezone.utc), arg[:500] or None
    await context.edit(f"💤 AFK включён{': ' + arg[:500] if arg else ''}")


@command(name="unafk", category="AFK", description="Отключить обычный AFK-автоответ.", usage=".unafk")
async def unafk(context: object) -> None:
    async with context.services.settings.db.session() as session:
        state = await session.get(AfkState, context.user_id)
        if state:
            state.enabled = False
    await context.edit("💤 AFK выключен.")


async def maybe_reply_afk(client: object, event: object) -> None:
    ai_chats = [int(chat_id) for chat_id in await client.services.settings.get(client.user_id, "afk_ai_chats", [])]
    if event.chat_id in ai_chats and client.services.ai.available:
        key = (client.user_id, event.chat_id, event.sender_id)
        now = time.monotonic()
        if now - _last_ai_reply.get(key, 0) < AI_REPLY_COOLDOWN_SECONDS:
            return
        try:
            history: list[str] = []
            async for message in event.client.iter_messages(event.chat_id, limit=12):
                if message.raw_text:
                    speaker = "Я" if message.out else "Собеседник"
                    history.append(f"{speaker}: {_clean(message.raw_text, 420)}")
            result = await client.services.ai.transform(await _afkai_prompt(client, event.chat_id), "\n".join(reversed(history))[:4_000])
            await client.services.usage.record_ai(client.user_id, result.prompt_tokens, result.completion_tokens)
            text = _clean(result.text, 260)
            if text:
                _last_ai_reply[key] = now
                response = await event.reply(text)
                client.mark_internal(response)
            return
        except AIUnavailableError:
            await client.services.usage.record_ai(client.user_id, error=True)
            return

    async with client.services.settings.db.session() as session:
        state = await session.get(AfkState, client.user_id)
        if not state or not state.enabled or not event.is_private:
            return
    elapsed = datetime.now(timezone.utc) - state.since
    minutes = max(1, int(elapsed.total_seconds() // 60))
    response = await event.reply(f"💤 AFK {minutes} мин.\nПричина: {state.reason or 'не указана'}")
    client.mark_internal(response)


@command(name="afkai", category="AI / режимы", description="AI-автоответ в этом чате, с личным стилем и prompt-настройкой.", usage=".afkai on|off|status|prompt <текст>|learn [1-400]")
async def afk_ai(context: object) -> None:
    action = context.args[0].lower() if context.args else ""
    if action in {"on", "off"}:
        chats = [int(chat_id) for chat_id in await context.services.settings.get(context.user_id, "afk_ai_chats", [])]
        if action == "on" and context.chat_id not in chats:
            chats.append(context.chat_id)
        elif action == "off":
            chats = [chat_id for chat_id in chats if chat_id != context.chat_id]
        await context.services.settings.set(context.user_id, "afk_ai_chats", chats)
        # Keep mode toggles invisible in a personal conversation.
        await context.delete()
        return
    if action == "prompt":
        prompt = context.raw_args.removeprefix(context.args[0]).strip()
        if prompt.lower() in {"clear", "off"}:
            await context.services.settings.set(context.user_id, "afkai_prompt", {})
            await context.edit("🤖 Описание стиля очищено.")
            return
        if not prompt:
            await context.edit("⚠️ .afkai prompt Я Дима, отвечаю коротко, с иронией…")
            return
        await context.services.settings.set(context.user_id, "afkai_prompt", {"text": prompt[:1_500]})
        await context.edit("🤖 Описание стиля сохранено.")
        return
    if action == "learn":
        try:
            limit = min(max(int(context.args[1]), 1), MAX_STYLE_MESSAGES) if len(context.args) > 1 else MAX_STYLE_MESSAGES
        except ValueError:
            await context.edit("⚠️ .afkai learn [1-400]")
            return
        samples: list[str] = []
        async for message in context.event.client.iter_messages(context.chat_id, limit=1_500):
            text = _clean(message.raw_text or "", 500)
            if message.out and text and not text.startswith("."):
                samples.append(text)
                if len(samples) >= limit:
                    break
        samples.reverse()
        if not samples:
            await context.edit("⚠️ Не нашёл твоих текстовых сообщений в этом чате.")
            return
        styles = await context.services.settings.get(context.user_id, "afkai_styles", {})
        styles = styles if isinstance(styles, dict) else {}
        styles[str(context.chat_id)] = samples
        await context.services.settings.set(context.user_id, "afkai_styles", styles)
        await context.edit(f"🧠 Стиль сохранён: {len(samples)} твоих сообщений из этого чата. Это не обучение модели, а приватный контекст для следующих ответов.")
        return
    if action == "status":
        chats = [int(chat_id) for chat_id in await context.services.settings.get(context.user_id, "afk_ai_chats", [])]
        styles = await context.services.settings.get(context.user_id, "afkai_styles", {})
        count = len(styles.get(str(context.chat_id), [])) if isinstance(styles, dict) else 0
        prompt = await context.services.settings.get(context.user_id, "afkai_prompt", {})
        configured = bool(prompt.get("text")) if isinstance(prompt, dict) else False
        await context.edit(f"🤖 AI-автоответ: {'ON' if context.chat_id in chats else 'OFF'}\n🧠 Сообщений стиля: {count}\n📝 Описание: {'есть' if configured else 'нет'}")
        return
    await context.edit("⚠️ .afkai on | off | status | prompt <текст> | learn [1-400]")
