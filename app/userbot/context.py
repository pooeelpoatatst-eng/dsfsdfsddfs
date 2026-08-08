from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from telethon.tl.custom import Message


@dataclass
class CommandContext:
    owner_id: int
    user_id: int
    client: Any
    event: Any
    message: Message
    chat_id: int
    args: list[str]
    raw_args: str
    services: Any

    async def edit(self, text: str) -> Message:
        self.client.processed.add(self.chat_id, self.message.id)
        await self.client.rate_limiter.wait("message_edit")
        return await self.event.edit(text)

    async def edit_html(self, text: str) -> Message:
        """Edit with Telegram HTML formatting for menus and structured output."""
        self.client.processed.add(self.chat_id, self.message.id)
        await self.client.rate_limiter.wait("message_edit")
        return await self.event.edit(text, parse_mode="html")

    async def reply(self, text: str) -> Message:
        await self.client.rate_limiter.wait("message_send")
        result = await self.event.reply(text)
        self.client.mark_internal(result)
        return result

    async def reply_html(self, text: str) -> Message:
        await self.client.rate_limiter.wait("message_send")
        result = await self.event.reply(text, parse_mode="html")
        self.client.mark_internal(result)
        return result

    async def delete(self) -> None:
        self.client.processed.add(self.chat_id, self.message.id)
        await self.event.delete()

    async def get_reply(self) -> Message | None:
        return await self.event.get_reply_message()
