from __future__ import annotations

import random
import re

from app.constants import AI_DAILY_LIMITS, KAWAII_SYSTEM_PROMPT, SHORT_LOCAL_WORDS
from app.services.ai import AIUnavailableError
from app.userbot.registry import command

EMOJI = ["💖", "💞", "💘", "😻", "🩷", "✨"]
KAOMOJI = ["(｡･ω･｡)ﾉ♡", "(´｡• ω •｡`)", "(✿˘︶˘)♡", "(✧ω✧)", "(≧◡≦)", ":3"]
SUFFIX = [" nya~", " kyaa~", " hehe~", " uwu", " мур~", ""]


def local_kawaii(text: str) -> str:
    if not text.strip(): return text
    words = re.split(r"(\s+)", text)
    candidates = [i for i, word in enumerate(words) if word and not word.isspace() and len(re.sub(r"\W", "", word, flags=re.UNICODE)) >= 2]
    if candidates and random.random() < 0.7:
        index = random.choice(candidates)
        word = words[index]
        match = re.match(r"([^\w]*)(.)(.*)", word, re.UNICODE)
        if match and random.random() < 0.55:
            words[index] = f"{match.group(1)}{match.group(2)}-{match.group(2)}{match.group(3)}"
        elif len(word) > 3:
            words[index] = word + random.choice(["", "", "ик", ""])
    result = "".join(words)
    if len(text) <= 4:
        return result + random.choice(EMOJI + ["~ :3"])
    addon = random.choice([random.choice(EMOJI), random.choice(SUFFIX) + " " + random.choice(KAOMOJI), ""])
    return (result + addon).strip()


async def transform_kawaii(client: object, chat_id: int, text: str) -> str | None:
    config = await client.mode_manager.config(chat_id, "kawaii")
    # Local is the reliable default: it works instantly and does not need AI.
    # AI is an explicit opt-in via `.kawaii ai`.
    mode = config.get("engine", "local")
    if mode == "local" or text.strip().lower() in SHORT_LOCAL_WORDS:
        return local_kawaii(text)
    usage = await client.services.usage.ai_usage(client.user_id)
    # Plans are server-side and must not expose provider credentials to users.
    limit = AI_DAILY_LIMITS.get("free", 100)
    if limit is not None and usage and usage.requests >= limit:
        return local_kawaii(text)
    try:
        await client.rate_limiter.wait("ai")
        result = await client.services.ai.transform(KAWAII_SYSTEM_PROMPT, text[:4000])
        await client.services.usage.record_ai(client.user_id, result.prompt_tokens, result.completion_tokens)
        return result.text[: min(len(text) * 2 + 20, 8000)]
    except AIUnavailableError:
        await client.services.usage.record_ai(client.user_id, error=True)
        return None


@command(name="kawaii", aliases=["nya"], category="AI / режимы", description="Включить kawaii-режим для обычных сообщений.", usage=".kawaii [off|ai|local|global]")
async def kawaii(context: object) -> None:
    args = [arg.lower() for arg in context.args]
    global_scope = bool(args and args[0] == "global")
    if global_scope: args = args[1:]
    chat_id = 0 if global_scope else context.chat_id
    if args and args[0] == "off":
        await context.client.mode_manager.set(chat_id, "kawaii", False)
        await context.edit("╭ Kawaii\n├ Status: OFF\n╰ Scope: " + ("all chats" if global_scope else "this chat")); return
    if args and args[0] in {"ai", "local"}:
        await context.client.mode_manager.set(chat_id, "kawaii", True, {"engine": args[0]})
        await context.edit(f"╭ Kawaii\n├ Status: ON\n├ Mode: {args[0].upper()}\n╰ Scope: {'all chats' if global_scope else 'this chat'}"); return
    enabled = await context.client.mode_manager.toggle(chat_id, "kawaii")
    config = await context.client.mode_manager.config(chat_id, "kawaii")
    await context.edit(f"╭ Kawaii\n├ Status: {'ON' if enabled else 'OFF'}\n├ Mode: {config.get('engine', 'local').upper()}\n╰ Scope: {'all chats' if global_scope else 'this chat'}")
