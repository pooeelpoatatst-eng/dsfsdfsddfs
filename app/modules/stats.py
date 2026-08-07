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


@command(name="chatstats", aliases=["stats"], category="Чаты", description="Полная статистика сообщений текущего чата.", usage=".chatstats [N]")
async def chatstats(context: object) -> None:
    try: limit = int(context.args[0]) if context.args else None
    except ValueError: await context.edit("⚠️ .chatstats или .chatstats 500"); return
    if limit is not None and limit < 1:
        await context.edit("⚠️ Число должно быть больше нуля."); return
    await context.edit("📊 считаю всю историю чата...")
    total = 0
    counts: Counter[int] = Counter()
    chars: defaultdict[int, int] = defaultdict(int)
    words: Counter[str] = Counter()
    async for message in context.event.client.iter_messages(context.chat_id, limit=limit):
        if not message.raw_text or not message.sender_id: continue
        total += 1
        counts[message.sender_id] += 1
        chars[message.sender_id] += len(message.raw_text)
        words.update(word.lower() for word in re.findall(r"[\wа-яё]{3,}", message.raw_text, re.IGNORECASE) if word.lower() not in STOP_WORDS)
    if not total:
        await context.edit("⚠️ В последних сообщениях нет текста."); return
    names: dict[int, str] = {}
    leaders = counts.most_common(5)
    for user_id, _ in leaders:
        try: names[user_id] = display_name(await context.event.client.get_entity(user_id), user_id)
        except ValueError: names[user_id] = str(user_id)
    rows = [f"📊 chat stats · {total} сообщений"]
    for user_id, count in leaders:
        average = chars[user_id] // count
        rows.append(f"{names[user_id]} — {count} ({count / total:.0%}), ср {average} симв")
    if words:
        rows.append("слова: " + ", ".join(f"{word} ×{count}" for word, count in words.most_common(7)))
    await context.edit("\n".join(rows)[:4000])
