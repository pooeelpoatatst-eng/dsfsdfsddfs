from __future__ import annotations

from telethon import TelegramClient
from telethon.sessions import StringSession


class TelegramClientFactory:
    def __init__(self, api_id: int, api_hash: str) -> None:
        self.api_id, self.api_hash = api_id, api_hash

    def create_from_string_session(self, session: str) -> TelegramClient:
        return TelegramClient(StringSession(session), self.api_id, self.api_hash, auto_reconnect=True, connection_retries=5, retry_delay=2)

    def create_temporary_login_client(self) -> TelegramClient:
        return TelegramClient(StringSession(), self.api_id, self.api_hash, auto_reconnect=True, connection_retries=3)
