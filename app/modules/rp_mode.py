from __future__ import annotations

from typing import Any

from app.userbot.registry import command


KEY = "rp_rules"


def _rule(raw: str) -> tuple[str, str] | None:
    trigger, marker, reply = raw.partition("|")
    trigger, reply = trigger.strip().casefold(), reply.strip()
    if not marker or not trigger or not reply or len(trigger) > 80 or len(reply) > 1_000:
        return None
    return trigger, reply


async def _rules(context: object) -> dict[str, dict[str, str]]:
    value = await context.services.settings.get(context.user_id, KEY, {})
    return value if isinstance(value, dict) else {}


@command(name="addrp", category="RPMode", description="Добавить RP-ответ на фразу в текущем чате.", usage=".addrp <триггер> | <ответ>")
async def add_rp(context: object) -> None:
    rule = _rule(context.raw_args)
    if not rule:
        await context.edit("⚠️ Использование: .addrp <триггер> | <ответ>")
        return
    trigger, reply = rule
    saved = await _rules(context)
    saved.setdefault(str(context.chat_id), {})[trigger] = reply
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit(f"✅ RP-ответ на «{trigger}» сохранён.")


@command(name="delrp", category="RPMode", description="Удалить RP-ответ по триггеру.", usage=".delrp <триггер>")
async def delete_rp(context: object) -> None:
    trigger = context.raw_args.strip().casefold()
    saved = await _rules(context)
    chat = saved.get(str(context.chat_id), {})
    if trigger not in chat:
        await context.edit("⚠️ RP-триггер не найден.")
        return
    chat.pop(trigger)
    if not chat:
        saved.pop(str(context.chat_id), None)
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit("✅ RP-ответ удалён.")


@command(name="resetrp", category="RPMode", description="Удалить все RP-ответы текущего чата.", usage=".resetrp")
async def reset_rp(context: object) -> None:
    saved = await _rules(context)
    count = len(saved.pop(str(context.chat_id), {}))
    await context.services.settings.set(context.user_id, KEY, saved)
    await context.edit(f"✅ Удалено RP-ответов: {count}.")


async def maybe_rp_reply(client: Any, event: Any) -> None:
    saved = await client.services.settings.get(client.user_id, KEY, {})
    rules = saved.get(str(event.chat_id), {}) if isinstance(saved, dict) else {}
    text = (event.raw_text or "").casefold()
    if not text or not isinstance(rules, dict):
        return
    for trigger, reply in rules.items():
        if trigger in text and isinstance(reply, str):
            sent = await event.reply(reply)
            client.mark_internal(sent)
            return
