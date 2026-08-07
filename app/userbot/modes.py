from __future__ import annotations

from app.constants import TRANSFORM_MODES
from app.database.repositories import ModeRepository


class ModeManager:
    def __init__(self, user_id: int, repository: ModeRepository) -> None:
        self.user_id, self.repository = user_id, repository

    async def set(self, chat_id: int, mode: str, enabled: bool, config: dict | None = None) -> None:
        if enabled and mode in TRANSFORM_MODES:
            for other in TRANSFORM_MODES - {mode}:
                await self.repository.set(self.user_id, chat_id, other, False)
        await self.repository.set(self.user_id, chat_id, mode, enabled, config)

    async def toggle(self, chat_id: int, mode: str) -> bool:
        current = await self.repository.get(self.user_id, chat_id, mode)
        enabled = not (current.enabled if current else False)
        await self.set(chat_id, mode, enabled, current.config_json if current else None)
        return enabled

    async def active(self, chat_id: int) -> list[str]:
        return [row.mode for row in await self.repository.enabled(self.user_id, chat_id)]

    async def config(self, chat_id: int, mode: str) -> dict:
        row = await self.repository.get(self.user_id, chat_id, mode)
        if row: return row.config_json
        global_row = await self.repository.get(self.user_id, 0, mode)
        return global_row.config_json if global_row else {}
