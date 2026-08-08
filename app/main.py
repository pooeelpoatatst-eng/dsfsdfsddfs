from __future__ import annotations

import asyncio
import logging
import signal

from app.config import get_settings
from app.control_bot.bot import AppContainer, create_bot
from app.database.engine import Database
from app.database.repositories import ModeRepository, SettingsRepository, UsageRepository, UserRepository
from app.logging import configure_logging
from app.services.ai import AIService, OpenAICompatibleProvider
from app.services.crypto import SessionCrypto
from app.games.service import GameService
from app.userbot.client import RuntimeServices
from app.userbot.factory import TelegramClientFactory
from app.userbot.manager import UserbotManager
from app.userbot.module_loader import ModuleLoader

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    db = Database(settings.database_url)
    crypto = SessionCrypto(settings.session_encryption_key.get_secret_value())
    users, modes = UserRepository(db), ModeRepository(db)
    provider = None
    if settings.ai_api_key:
        provider = OpenAICompatibleProvider(settings.ai_api_key.get_secret_value(), settings.ai_base_url, settings.ai_model, settings.ai_max_concurrent)
    ai = AIService(provider)
    runtime = RuntimeServices(ai=ai, settings=SettingsRepository(db), usage=UsageRepository(db), modules={})
    runtime.modules.update(__import__("app.constants", fromlist=["DEFAULT_MODULES"]).DEFAULT_MODULES)
    factory = TelegramClientFactory(settings.telegram_api_id, settings.telegram_api_hash.get_secret_value())
    manager = UserbotManager(factory, crypto, users, runtime, modes, settings.max_active_clients)
    container = AppContainer(settings, users, crypto, factory, manager, db, {})
    bot, dispatcher = create_bot(container)
    games = GameService(bot)
    container.games = games
    runtime.games = games
    ModuleLoader().load_all()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig, stop.set)
        except NotImplementedError: pass  # Windows event loop
    try:
        await manager.start_all()
        polling = asyncio.create_task(dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types()))
        stopper = asyncio.create_task(stop.wait())
        done, pending = await asyncio.wait({polling, stopper}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if task is polling and not task.cancelled(): task.result()
    finally:
        await dispatcher.stop_polling()
        await manager.shutdown()
        await ai.close()
        await db.dispose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
