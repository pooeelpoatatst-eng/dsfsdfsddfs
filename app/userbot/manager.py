from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.database.repositories import UserRepository

logger = logging.getLogger(__name__)


class UserbotManager:
    def __init__(self, factory: Any, crypto: Any, users: UserRepository, services: Any, mode_repository: Any, max_clients: int) -> None:
        self.factory, self.crypto, self.users, self.services, self.mode_repository = factory, crypto, users, services, mode_repository
        self.max_clients = max_clients
        self.clients: dict[int, Any] = {}
        self._lock = asyncio.Lock()

    async def start_all(self) -> None:
        for user in await self.users.connected_users():
            try: await self.start_user(user.control_bot_user_id)
            except Exception: logger.exception("restore_failed owner_id=%s", user.control_bot_user_id)

    async def start_user(self, owner_id: int, preconnected_client: Any | None = None, session: str | None = None, account_id: int | None = None) -> Any:
        async with self._lock:
            if owner_id in self.clients: return self.clients[owner_id]
            if len(self.clients) >= self.max_clients: raise RuntimeError("Active client limit reached")
            user = await self.users.get(owner_id)
            if not user or not user.connected: raise ValueError("No connected account")
            raw_session = session or self.crypto.decrypt(user.encrypted_session or "")
            client = preconnected_client or self.factory.create_from_string_session(raw_session)
            from app.userbot.client import UserClient
            instance = UserClient(owner_id, user.id, account_id or user.telegram_account_id or 0, raw_session, client, self.services, self.mode_repository)
            try: await instance.start()
            except PermissionError:
                await self.users.disconnect(owner_id)
                raise
            self.clients[owner_id] = instance
            return instance

    async def stop_user(self, owner_id: int, logout: bool = False) -> None:
        client = self.clients.pop(owner_id, None)
        if client: await client.stop(logout)

    async def restart_user(self, owner_id: int) -> Any:
        await self.stop_user(owner_id)
        return await self.start_user(owner_id)

    def get_client(self, owner_id: int) -> Any | None: return self.clients.get(owner_id)
    def is_running(self, owner_id: int) -> bool: return owner_id in self.clients
    async def shutdown(self) -> None:
        await asyncio.gather(*(self.stop_user(owner_id) for owner_id in list(self.clients)), return_exceptions=True)
