from __future__ import annotations

import asyncio
import math
import random
import time
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from app.modules.tools import argument_or_reply
from app.userbot.registry import command


def _animation_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in ("C:/Windows/Fonts/seguisb.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _send_gif(context: object, frames: list[Image.Image], name: str, caption: str = "") -> object:
    result = BytesIO()
    result.name = name
    frames[0].save(result, format="GIF", save_all=True, append_images=frames[1:], duration=85, loop=0, disposal=2)
    result.seek(0)
    return result


async def _post_animation(context: object, frames: list[Image.Image], name: str, caption: str = "") -> None:
    file = _send_gif(context, frames, name, caption)
    await context.delete()
    message = await context.event.client.send_file(context.chat_id, file, caption=caption or None, force_document=False, supports_streaming=True)
    context.client.mark_internal(message)


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

@command(name="heart", category="Анимации", description="Анимированное сердце с подписью.", usage=".heart [текст]")
async def heart(context: object) -> None:
    caption = context.raw_args.strip()[:100]
    frames: list[Image.Image] = []
    for index in range(34):
        image = Image.new("RGB", (640, 480), "#100914")
        draw = ImageDraw.Draw(image)
        pulse = 1 + 0.13 * math.sin(index / 34 * math.tau * 2)
        scale = 11.5 * pulse
        points = []
        for step in range(180):
            t = math.tau * step / 180
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            points.append((320 + x * scale, 218 - y * scale))
        glow = (255, 60 + int(35 * pulse), 145)
        draw.polygon(points, fill=glow)
        draw.text((320, 400), caption or "люблю", font=_animation_font(34), anchor="mm", fill="#ffe7f1")
        frames.append(image)
    await _post_animation(context, frames, "heart.gif", caption)

@command(name="boom", category="Анимации", description="Мини-взрыв.", usage=".boom")
async def boom(context: object) -> None:
    for frame in ("        ·\n       · ·\n        ·", "      ✦  ·  ✦\n        · ✦ ·\n      ✦  ·  ✦", "  💥  ✨  💥\n✨  💥  💥  ✨\n  💥  ✨  💥", "✨ ✨ ✨ ✨ ✨\n  ✨  boom  ✨\n✨ ✨ ✨ ✨ ✨", "     ✨\n   ✨   ✨\n✨   💫   ✨\n   ✨   ✨\n     ✨"):
        await context.edit(frame)
        await asyncio.sleep(2)

@command(name="rainbow", category="Анимации", description="Длинная радужная GIF-анимация текста.", usage=".rainbow <text>")
async def rainbow(context: object) -> None:
    text = context.raw_args.strip()[:40] or "РАДУГА"
    font = _animation_font(max(34, min(76, 720 // max(1, len(text)))))
    colours = ((255, 67, 111), (255, 154, 56), (255, 224, 80), (74, 220, 136), (70, 158, 255), (160, 104, 255))
    frames: list[Image.Image] = []
    for frame in range(42):
        image = Image.new("RGB", (720, 360), "#101019")
        draw = ImageDraw.Draw(image)
        widths = [draw.textlength(char, font=font) for char in text]
        x = (720 - sum(widths)) / 2
        for index, char in enumerate(text):
            y = 170 + int(20 * math.sin((frame * .36) + index * .72))
            color = colours[(index + frame // 3) % len(colours)]
            draw.text((x, y), char, font=font, fill=color, anchor="lm", stroke_width=1, stroke_fill="#ffffff")
            x += widths[index]
        frames.append(image)
    await _post_animation(context, frames, "rainbow.gif")
