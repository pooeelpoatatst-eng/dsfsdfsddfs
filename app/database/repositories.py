from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.database.engine import Database
from app.database.models import AIUsage, ChatMode, CommandUsage, LoginAudit, Note, User, UserSetting


class UserRepository:
    def __init__(self, db: Database) -> None: self.db = db

    async def get(self, control_id: int) -> User | None:
        async with self.db.session() as s: return await s.scalar(select(User).where(User.control_bot_user_id == control_id))

    async def ensure(self, control_id: int) -> User:
        user = await self.get(control_id)
        if user: return user
        async with self.db.session() as s:
            user = User(control_bot_user_id=control_id)
            s.add(user)
            await s.flush()
            return user

    async def connected_users(self) -> list[User]:
        async with self.db.session() as s: return list((await s.scalars(select(User).where(User.connected.is_(True)))).all())

    async def connect(self, control_id: int, telegram_id: int, username: str | None, first_name: str | None, encrypted: str) -> User:
        async with self.db.session() as s:
            duplicate = await s.scalar(select(User).where(User.telegram_account_id == telegram_id, User.control_bot_user_id != control_id))
            if duplicate: raise ValueError("telegram_account_already_connected")
            user = await s.scalar(select(User).where(User.control_bot_user_id == control_id))
            if not user:
                user = User(control_bot_user_id=control_id); s.add(user)
            user.telegram_account_id, user.username, user.first_name = telegram_id, username, first_name
            user.encrypted_session, user.connected = encrypted, True
            await s.flush()
            return user

    async def disconnect(self, control_id: int) -> None:
        async with self.db.session() as s:
            user = await s.scalar(select(User).where(User.control_bot_user_id == control_id))
            if user:
                user.connected = False; user.encrypted_session = None; user.telegram_account_id = None

    async def audit(self, control_id: int, event: str) -> None:
        async with self.db.session() as s: s.add(LoginAudit(control_bot_user_id=control_id, event=event))


class SettingsRepository:
    def __init__(self, db: Database) -> None: self.db = db
    async def get(self, user_id: int, key: str, default: Any = None) -> Any:
        async with self.db.session() as s:
            row = await s.scalar(select(UserSetting).where(UserSetting.user_id == user_id, UserSetting.key == key))
            return row.value_json if row else default
    async def set(self, user_id: int, key: str, value: Any) -> None:
        async with self.db.session() as s:
            row = await s.scalar(select(UserSetting).where(UserSetting.user_id == user_id, UserSetting.key == key))
            if row: row.value_json = value
            else: s.add(UserSetting(user_id=user_id, key=key, value_json=value))


class ModeRepository:
    def __init__(self, db: Database) -> None: self.db = db
    async def get(self, user_id: int, chat_id: int, mode: str) -> ChatMode | None:
        async with self.db.session() as s: return await s.scalar(select(ChatMode).where(ChatMode.user_id == user_id, ChatMode.chat_id == chat_id, ChatMode.mode == mode))
    async def set(self, user_id: int, chat_id: int, mode: str, enabled: bool, config: dict[str, Any] | None = None) -> None:
        async with self.db.session() as s:
            row = await s.scalar(select(ChatMode).where(ChatMode.user_id == user_id, ChatMode.chat_id == chat_id, ChatMode.mode == mode))
            if row: row.enabled, row.config_json = enabled, config or row.config_json
            else: s.add(ChatMode(user_id=user_id, chat_id=chat_id, mode=mode, enabled=enabled, config_json=config or {}))
    async def enabled(self, user_id: int, chat_id: int) -> list[ChatMode]:
        async with self.db.session() as s:
            chat = list((await s.scalars(select(ChatMode).where(ChatMode.user_id == user_id, ChatMode.chat_id == chat_id, ChatMode.enabled.is_(True)))).all())
            if chat: return chat
            return list((await s.scalars(select(ChatMode).where(ChatMode.user_id == user_id, ChatMode.chat_id == 0, ChatMode.enabled.is_(True)))).all())


class UsageRepository:
    def __init__(self, db: Database) -> None: self.db = db
    async def ai_usage(self, user_id: int) -> AIUsage | None:
        async with self.db.session() as s: return await s.scalar(select(AIUsage).where(AIUsage.user_id == user_id, AIUsage.date == date.today()))
    async def record_ai(self, user_id: int, prompt_tokens: int = 0, completion_tokens: int = 0, error: bool = False) -> None:
        async with self.db.session() as s:
            row = await s.scalar(select(AIUsage).where(AIUsage.user_id == user_id, AIUsage.date == date.today()))
            if not row: row = AIUsage(user_id=user_id, date=date.today()); s.add(row)
            # Existing rows created before a flush may still contain None instead
            # of Python-side defaults, so normalise all counters before incrementing.
            row.requests = (row.requests or 0) + 1
            row.prompt_tokens = (row.prompt_tokens or 0) + prompt_tokens
            row.completion_tokens = (row.completion_tokens or 0) + completion_tokens
            row.total_tokens = (row.total_tokens or 0) + prompt_tokens + completion_tokens
            row.errors = (row.errors or 0) + int(error)
    async def command(self, user_id: int, name: str) -> None:
        async with self.db.session() as s:
            row = await s.scalar(select(CommandUsage).where(CommandUsage.user_id == user_id, CommandUsage.command == name))
            if row: row.count += 1
            else: s.add(CommandUsage(user_id=user_id, command=name, count=1))


class NotesRepository:
    def __init__(self, db: Database) -> None: self.db = db
    async def add(self, user_id: int, chat_id: int | None, name: str, content: str) -> None:
        async with self.db.session() as s:
            row = await s.scalar(select(Note).where(Note.user_id == user_id, Note.chat_id == chat_id, Note.name == name.lower()))
            if row: row.content = content
            else: s.add(Note(user_id=user_id, chat_id=chat_id, name=name.lower(), content=content))
    async def get(self, user_id: int, chat_id: int, name: str) -> Note | None:
        async with self.db.session() as s:
            return await s.scalar(select(Note).where(Note.user_id == user_id, Note.name == name.lower(), Note.chat_id.in_([chat_id, None])).order_by(Note.chat_id.desc().nullslast()))
    async def list(self, user_id: int, chat_id: int) -> list[Note]:
        async with self.db.session() as s: return list((await s.scalars(select(Note).where(Note.user_id == user_id, Note.chat_id.in_([chat_id, None])))).all())

    async def delete(self, user_id: int, name: str) -> bool:
        async with self.db.session() as s:
            result = await s.execute(delete(Note).where(Note.user_id == user_id, Note.name == name.lower()))
            return bool(result.rowcount)

    async def clear(self, user_id: int) -> int:
        async with self.db.session() as s:
            result = await s.execute(delete(Note).where(Note.user_id == user_id))
            return int(result.rowcount or 0)
