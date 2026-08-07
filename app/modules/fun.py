from __future__ import annotations

import asyncio
import random
import time

from app.modules.tools import argument_or_reply
from app.userbot.registry import command


async def target(context: object) -> str:
    if context.raw_args: return context.raw_args
    reply = await context.get_reply()
    if reply: return f"[{getattr(reply, 'sender_id', 'него')}]"
    return "тебя"

def make_action(name: str, verb: str, emoji: str) -> None:
    @command(name=name, category="Общение", description=f"Ролевая реакция: {verb}.", usage=f".{name} [@user] или reply")
    async def handler(context: object) -> None:
        await context.edit(f"{emoji} {verb.capitalize()} {await target(context)}")

for _name, _verb, _emoji in (
    ("hug", "обнимаю", "🫂"), ("kiss", "целую", "💋"), ("slap", "шлёпаю", "🫲"),
    ("pat", "глажу", "🐾"), ("bite", "кусаю", "🦷"), ("poke", "тыкаю", "👉"),
    ("wave", "машу", "👋"), ("dance", "танцую с", "💃"), ("bonk", "бонькаю", "🔨"),
    ("cry", "плачу из-за", "😭"), ("laugh", "смеюсь над", "🤣"), ("highfive", "даю пять", "🖐️"),
): make_action(_name, _verb, _emoji)

@command(name="rate", category="Общение", description="Случайная оценка.", usage=".rate [text/reply]")
async def rate(context: object) -> None: await context.edit(f"📊 {await target(context)}: {random.randint(0, 100)}%")

@command(name="ship", category="Общение", description="Совместимость двух имён.", usage=".ship Name1 Name2")
async def ship(context: object) -> None:
    names = context.raw_args or "вы двое"
    await context.edit(f"💘 {names}\nСовместимость: {random.randint(1, 100)}%")

@command(name="eightball", aliases=["8ball"], category="Общение", description="Ответ шара предсказаний.", usage=".eightball <question>")
async def eightball(context: object) -> None:
    answers = ["Да.", "Нет.", "Вероятно.", "Спроси позже.", "Это звучит опасно.", "Однозначно да.", "Лучше не надо."]
    await context.edit("🎱 " + random.choice(answers))

@command(name="fact", category="Общение", description="Случайный факт.", usage=".fact")
async def fact(context: object) -> None:
    facts = ["У осьминога три сердца.", "Бананы ботанически относятся к ягодам.", "Молния горячее поверхности Солнца.", "У выдр есть любимый камень.", "Мёд почти не портится."]
    await context.edit("🧠 " + random.choice(facts))

@command(name="choose", category="Инструменты", description="Выбрать один вариант.", usage=".choose one | two | three")
async def choose(context: object) -> None:
    choices = [item.strip() for item in context.raw_args.split("|") if item.strip()]
    await context.edit("🎯 " + (random.choice(choices) if len(choices) >= 2 else "Укажи минимум два варианта через |"))

@command(name="random", aliases=["rand"], category="Инструменты", description="Случайное число.", usage=".random [min] [max]")
async def random_number(context: object) -> None:
    try:
        low, high = (int(context.args[0]), int(context.args[1])) if len(context.args) >= 2 else (1, 100)
        if low > high or high - low > 10_000_000: raise ValueError
    except ValueError: await context.edit("⚠️ .random 1 100"); return
    await context.edit(f"🎲 {random.randint(low, high)}")

@command(name="reverse", category="Инструменты", description="Развернуть текст.", usage=".reverse <text> или reply")
async def reverse(context: object) -> None:
    text = await argument_or_reply(context)
    await context.edit(text[::-1] if text else "⚠️ Добавь текст.")

@command(name="mock", category="Инструменты", description="SpongeBob-регистр текста.", usage=".mock <text> или reply")
async def mock(context: object) -> None:
    text = await argument_or_reply(context)
    await context.edit("".join(char.upper() if index % 2 else char.lower() for index, char in enumerate(text)) if text else "⚠️ Добавь текст.")

@command(name="clap", category="Инструменты", description="Разделить слова хлопками.", usage=".clap <text> или reply")
async def clap(context: object) -> None:
    text = await argument_or_reply(context)
    await context.edit(" 👏 ".join(text.split()) if text else "⚠️ Добавь текст.")

@command(name="count", category="Инструменты", description="Посчитать слова и символы.", usage=".count <text> или reply")
async def count(context: object) -> None:
    text = await argument_or_reply(context)
    await context.edit(f"📏 Символов: {len(text)}\nСлов: {len(text.split())}")

@command(name="timer", category="Инструменты", description="Таймер с редактированием сообщения.", usage=".timer <seconds>")
async def timer(context: object) -> None:
    try: seconds = min(max(int(context.args[0]), 1), 300)
    except (ValueError, IndexError): await context.edit("⚠️ .timer 30 (до 300 сек)"); return
    for remaining in range(seconds, 0, -1):
        await context.edit(f"⏳ {remaining} сек.")
        await asyncio.sleep(1)
    await context.edit("⏰ Время вышло!")

@command(name="loading", category="Анимации", description="Короткая loading-анимация.", usage=".loading")
async def loading(context: object) -> None:
    frames = ["▱▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱▱", "▰▰▱▱▱▱▱▱▱▱", "▰▰▰▱▱▱▱▱▱▱", "▰▰▰▰▱▱▱▱▱▱", "▰▰▰▰▰▱▱▱▱▱", "▰▰▰▰▰▰▱▱▱▱", "▰▰▰▰▰▰▰▱▱▱", "▰▰▰▰▰▰▰▰▱▱", "▰▰▰▰▰▰▰▰▰▱", "▰▰▰▰▰▰▰▰▰▰"]
    for index, frame in enumerate(frames):
        await context.edit(f"⌛ loading\n\n{frame}\n{index * 10}%")
        await asyncio.sleep(1)

@command(name="heart", category="Анимации", description="Анимация сердца.", usage=".heart")
async def heart(context: object) -> None:
    small = """  🩷🩷   🩷🩷
 🩷🩷🩷 🩷🩷🩷
  🩷🩷🩷🩷🩷
   🩷🩷🩷🩷
    🩷🩷🩷
     🩷🩷
      🩷"""
    large = """   💗💗💗     💗💗💗
 💗💗💗💗💗 💗💗💗💗💗
💗💗💗💗💗💗💗💗💗💗💗💗💗
 💗💗💗💗💗💗💗💗💗💗💗
  💗💗💗💗💗💗💗💗💗
   💗💗💗💗💗💗💗
    💗💗💗💗💗
     💗💗💗
      💗"""
    for frame in (small, large, small, large, small, large, "💖"):
        await context.edit(frame)
        await asyncio.sleep(1.4)

@command(name="boom", category="Анимации", description="Мини-взрыв.", usage=".boom")
async def boom(context: object) -> None:
    for frame in ("        ·\n       · ·\n        ·", "      ✦  ·  ✦\n        · ✦ ·\n      ✦  ·  ✦", "  💥  ✨  💥\n✨  💥  💥  ✨\n  💥  ✨  💥", "✨ ✨ ✨ ✨ ✨\n  ✨  boom  ✨\n✨ ✨ ✨ ✨ ✨", "     ✨\n   ✨   ✨\n✨   💫   ✨\n   ✨   ✨\n     ✨"):
        await context.edit(frame)
        await asyncio.sleep(2)

@command(name="rainbow", category="Анимации", description="Цветная анимация.", usage=".rainbow <text>")
async def rainbow(context: object) -> None:
    text = context.raw_args or "rainbow"
    colors = ("🔴", "🟠", "🟡", "🟢", "🔵", "🟣")
    for offset in range(10):
        line = "".join(colors[(index + offset) % len(colors)] for index in range(13))
        await context.edit(f"{line}\n{text}\n{line}")
        await asyncio.sleep(1)
