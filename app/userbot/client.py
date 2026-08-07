from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from telethon import events
from telethon.errors import FloodWaitError

from app.constants import DEFAULT_MODULES
from app.database.repositories import ModeRepository, SettingsRepository, UsageRepository
from app.userbot.commands import parse_command
from app.userbot.context import CommandContext
from app.userbot.modes import ModeManager
from app.userbot.processed_cache import ProcessedMessageCache
from app.userbot.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class RuntimeServices:
    ai: Any
    settings: SettingsRepository
    usage: UsageRepository
    modules: dict[str, bool]


class UserClient:
    def __init__(self, owner_id: int, user_id: int, telegram_user_id: int, session: str, client: Any, services: RuntimeServices, modes: ModeRepository) -> None:
        self.owner_id, self.user_id, self.telegram_user_id, self.session = owner_id, user_id, telegram_user_id, session
        self.client, self.services = client, services
        self.mode_manager = ModeManager(user_id, modes)
        self.rate_limiter, self.processed = RateLimiter(), ProcessedMessageCache()
        self._locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._started = False

    async def start(self) -> None:
        if self._started: return
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.disconnect()
            raise PermissionError("Telegram session is not authorized")
        self.register_handlers()
        self._started = True

    async def stop(self, logout: bool = False) -> None:
        if logout and self.client.is_connected():
            await self.client.log_out()
        await self.client.disconnect()
        self._started = False

    def register_handlers(self) -> None:
        self.client.add_event_handler(self._on_outgoing, events.NewMessage(outgoing=True))
        self.client.add_event_handler(self._on_incoming, events.NewMessage(incoming=True))

    async def health_check(self) -> bool:
        try:
            if not self.client.is_connected(): await self.client.connect()
            return await self.client.is_user_authorized()
        except Exception:
            return False

    def mark_internal(self, message: Any) -> None:
        if message: self.processed.add(message.chat_id, message.id)

    async def _on_outgoing(self, event: Any) -> None:
        if event.sender_id != self.telegram_user_id or self.processed.contains(event.chat_id, event.id): return
        text = event.raw_text or ""
        if not text: return
        async with self._locks[event.chat_id]:
            if text.startswith("//"):
                self.processed.add(event.chat_id, event.id)
                await event.edit(text[2:])
                return
            parsed = parse_command(text)
            if parsed:
                await self._execute(event, parsed)
                return
            await self._transform(event, text)

    async def _execute(self, event: Any, parsed: Any) -> None:
        if not parsed.meta:
            return
        if not self.services.modules.get(parsed.meta.module, True):
            await event.edit(f"⚠️ Модуль {parsed.meta.module} выключен. Включи его через control bot.")
            return
        context = CommandContext(self.owner_id, self.user_id, self, event, event.message, event.chat_id, parsed.args, parsed.raw_args, self.services)
        try:
            await self.services.usage.command(self.user_id, parsed.meta.name)
            await parsed.meta.handler(context)
        except FloodWaitError as exc:
            await asyncio.sleep(min(exc.seconds, 30))
            await context.edit("⚠️ Telegram попросил подождать. Попробуй позже.")
        except Exception:
            error_id = f"{event.id:X}{self.owner_id:X}"[-10:]
            logger.exception("command_failed owner_id=%s command=%s error_id=%s", self.owner_id, parsed.name, error_id)
            try:
                await context.edit(f"⚠️ Ошибка команды `.{parsed.name}`. ID: {error_id}")
            except Exception:
                # Commands which delete their source message cannot edit an
                # error into it; retain the original exception in logs only.
                logger.exception("command_error_message_failed error_id=%s", error_id)

    async def _transform(self, event: Any, text: str) -> None:
        active = await self.mode_manager.active(event.chat_id)
        if "kawaii" not in active: return
        from app.modules.kawaii import transform_kawaii
        result = await transform_kawaii(self, event.chat_id, text)
        if result and result != text:
            self.processed.add(event.chat_id, event.id)
            await self.rate_limiter.wait("message_edit")
            await event.edit(result)

    async def _on_incoming(self, event: Any) -> None:
        # Incoming automation is intentionally isolated from outgoing transforms.
        if event.sender_id == self.telegram_user_id or not event.raw_text: return
        from app.modules.afk import maybe_reply_afk
        await maybe_reply_afk(self, event)
        from app.modules.games import handle_opponent_move
        await handle_opponent_move(self, event)
