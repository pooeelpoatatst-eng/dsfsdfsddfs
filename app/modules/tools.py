from __future__ import annotations

import asyncio
import random
import time

from app import __version__
from app.constants import TRANSFORM_MODES
from app.userbot.registry import command

EN_TO_RU = str.maketrans("qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>", "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ")
RU_TO_EN = str.maketrans("йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ", "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>")

async def argument_or_reply(context: object) -> str:
    if context.raw_args: return context.raw_args
    reply = await context.get_reply()
    return reply.raw_text if reply and reply.raw_text else ""

@command(name="sw", category="Инструменты", description="Исправить неверную раскладку.", usage=".sw <text> или reply")
async def switch_layout(context: object) -> None:
    text = await argument_or_reply(context)
    if not text: await context.edit("⚠️ Добавь текст или reply."); return
    latin = sum(char.isascii() and char.isalpha() for char in text)
    cyrillic = sum("а" <= char.lower() <= "я" or char.lower() == "ё" for char in text)
    await context.edit(text.translate(EN_TO_RU if latin >= cyrillic else RU_TO_EN))

@command(name="leet", category="Инструменты", description="Мемная leet-трансформация.", usage=".leet <text> или reply")
async def leet(context: object) -> None:
    text = await argument_or_reply(context)
    if not text: await context.edit("⚠️ Добавь текст."); return
    variants = {"а": ["a", "4", "à"], "е": ["e", "3", "è"], "и": ["u", "1", "i"], "о": ["0", "o", "ò"], "с": ["c", "$", "s"], "т": ["t", "7", "T"]}
    await context.edit("".join(random.choice(variants.get(char.lower(), [char])) if char.isalpha() and random.random() < .55 else char for char in text))

@command(name="love", category="Остальное", description="Короткое любовное сообщение.", usage=".love [@username] или reply")
async def love(context: object) -> None:
    target = context.raw_args
    if not target:
        reply = await context.get_reply(); target = getattr(reply, "sender_id", "тебя") if reply else "тебя"
    await context.edit(random.choice([f"{target}, ты невероятный человек 💖", f"Для {target}: немного тепла и любви 💞", f"{target}, ты сегодня особенно классный ✨"]))

@command(name="type", category="Инструменты", description="Эффект печати через редактирование.", usage=".type [0.2] <text>")
async def type_effect(context: object) -> None:
    parts = context.raw_args.split(maxsplit=1)
    delay = 0.2
    if parts and parts[0].replace(".", "", 1).isdigit():
        delay = min(max(float(parts.pop(0)), .15), 1.0)
    text = " ".join(parts)
    if not text: await context.edit("⚠️ Добавь текст."); return
    for end in range(1, len(text) + 1):
        context.client.processed.add(context.chat_id, context.message.id)
        await context.event.edit(text[:end])
        await asyncio.sleep(delay)

@command(name="ping", category="Инструменты", description="Проверить состояние userbot.", usage=".ping")
async def ping(context: object) -> None:
    started = time.perf_counter(); await context.client.client.get_me(); telegram_ms = (time.perf_counter() - started) * 1000
    await context.edit(f"╭ Ping\n├ Telegram: {telegram_ms:.0f}ms\n├ AI: {'configured' if context.services.ai.available else 'disabled'}\n╰ Userbot: online")

@command(name="core", category="Инструменты", description="Версия и состояние ядра.", usage=".core")
async def core(context: object) -> None:
    await context.edit(f"╭ Core\n├ Version: {__version__}\n├ Commands: {len(set(meta.name for meta in __import__('app.userbot.registry', fromlist=['REGISTRY']).REGISTRY.values()))}\n├ AI: {'enabled' if context.services.ai.available else 'disabled'}\n╰ Account: {context.client.telegram_user_id}")

@command(name="switch", category="AI / режимы", description="Показать или переключить transform-режим.", usage=".switch [kawaii|toxic|troll|rp|leet]")
async def switch(context: object) -> None:
    if context.args:
        mode = context.args[0].lower()
        if mode not in TRANSFORM_MODES:
            await context.edit("⚠️ Доступно: kawaii, toxic, troll, rp, leet."); return
        enabled = await context.client.mode_manager.toggle(context.chat_id, mode)
        await context.edit(f"{mode.title()}: {'✅ ON' if enabled else '❌ OFF'}"); return
    active = set(await context.client.mode_manager.active(context.chat_id))
    lines = ["╭ Modes"] + [f"├ {mode.title()}: {'✅' if mode in active else '❌'}" for mode in sorted(TRANSFORM_MODES)] + ["╰ Use .switch <mode>"]
    await context.edit("\n".join(lines))
