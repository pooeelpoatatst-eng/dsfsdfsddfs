from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.userbot.registry import command

STOP_WORDS = {
    "а", "и", "в", "во", "не", "на", "я", "ты", "он", "она", "мы", "вы", "это", "что", "как", "да", "нет", "ну", "но", "за", "с", "со", "по", "к", "у", "от", "для", "то", "же", "бы", "так", "мне", "тебе", "его", "ее", "их", "the", "and", "to", "of", "in", "is", "it",
}


def display_name(sender: object, fallback: int) -> str:
    if not sender: return str(fallback)
    return (getattr(sender, "first_name", None) or getattr(sender, "title", None) or str(fallback)).replace("\n", " ")[:24]


@command(name="chatstats", aliases=["stats"], category="Чаты", description="Статистика последних сообщений чата.", usage=".chatstats [50-500]")
async def chatstats(context: object) -> None:
    try: limit = min(max(int(context.args[0]), 20), 500) if context.args else 200
    except ValueError: await context.edit("⚠️ .chatstats 200 (от 20 до 500)"); return
    messages = []
    async for message in context.event.client.iter_messages(context.chat_id, limit=limit):
        if message.raw_text and message.sender_id:
            messages.append(message)
    if not messages:
        await context.edit("⚠️ В последних сообщениях нет текста."); return
    counts: Counter[int] = Counter(message.sender_id for message in messages)
    chars: defaultdict[int, int] = defaultdict(int)
    words: Counter[str] = Counter()
    names: dict[int, str] = {}
    for message in messages:
        chars[message.sender_id] += len(message.raw_text)
        names[message.sender_id] = display_name(await message.get_sender(), message.sender_id)
        words.update(word.lower() for word in re.findall(r"[\wа-яё]{3,}", message.raw_text, re.IGNORECASE) if word.lower() not in STOP_WORDS)
    total = len(messages)
    leaders = counts.most_common(5)
    rows = [f"📊 chat stats · {total} сообщений"]
    for user_id, count in leaders:
        average = chars[user_id] // count
        rows.append(f"{names[user_id]} — {count} ({count / total:.0%}), ср {average} симв")
    if words:
        rows.append("слова: " + ", ".join(f"{word} ×{count}" for word, count in words.most_common(7)))
    await context.edit("\n".join(rows)[:4000])
