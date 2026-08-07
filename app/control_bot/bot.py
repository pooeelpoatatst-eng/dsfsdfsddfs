from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


@dataclass
class AppContainer:
    settings: Any
    users: Any
    crypto: Any
    factory: Any
    manager: Any
    db: Any
    temp_auth: dict[int, Any]


def create_bot(container: AppContainer) -> tuple[Bot, Dispatcher]:
    bot = Bot(container.settings.control_bot_token.get_secret_value())
    dp = Dispatcher(storage=MemoryStorage())
    from app.control_bot.router import create_router
    dp.include_router(create_router(container))
    return bot, dp
