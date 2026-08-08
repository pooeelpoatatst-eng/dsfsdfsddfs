from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.userbot.registry import command


KEY = "streaks"


def _days_label(count: int) -> str:
    last_two = count % 100
    if 11 <= last_two <= 14:
        return "дней"
    return {1: "день", 2: "дня", 3: "дня", 4: "дня"}.get(count % 10, "дней")


def _day(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value or "")
    except ValueError:
        return None


def apply_message(entry: dict[str, object], today: date, direction: str) -> tuple[dict[str, object], bool]:
    """Record one side of today's private chat and count a completed day once."""
    days = entry.get("days", {})
    days = days if isinstance(days, dict) else {}
    key = today.isoformat()
    state = days.get(key, {})
    state = state if isinstance(state, dict) else {}
    if state.get(direction):
        return entry, False
    state[direction] = True
    days[key] = state
    entry["days"] = {
        stamp: item for stamp, item in days.items()
        if _day(stamp) and _day(stamp) >= today - timedelta(days=3)
    }
    if not (state.get("in") and state.get("out")) or entry.get("counted_day") == key:
        return entry, False
    previous = _day(str(entry.get("last") or ""))
    entry["count"] = int(entry.get("count", 0)) + 1 if previous == today - timedelta(days=1) else 1
    entry["last"] = key
    entry["counted_day"] = key
    entry.setdefault("started", key)
    return entry, True


def is_active(entry: dict[str, object], today: date) -> bool:
    last = _day(str(entry.get("last") or ""))
    return last in {today, today - timedelta(days=1)}


async def _data(context: object) -> dict[str, dict[str, object]]:
    value = await context.services.settings.get(context.user_id, KEY, {})
    return value if isinstance(value, dict) else {}


async def _target(context: object) -> tuple[str, str] | tuple[None, None]:
    reply = await context.get_reply()
    if reply:
        sender = await reply.get_sender()
        identifier = str(reply.sender_id)
        name = getattr(sender, "first_name", None) or getattr(sender, "title", None) or identifier
        return identifier, name
    if context.raw_args.strip():
        value = context.raw_args.strip().removeprefix("@")
        return value.lower(), "@" + value
    return None, None


@command(name="streak", category="Огонёк", description="Показать статус автоматической серии с человеком.", usage="reply .streak или .streak @username")
async def streak(context: object) -> None:
    identifier, name = await _target(context)
    entry = (await _data(context)).get(identifier or "")
    if not entry:
        await context.edit(f"🔥 С {name or 'этим человеком'} серии пока нет. Нужны сообщения с обеих сторон за день.")
        return
    state = "горит" if is_active(entry, date.today()) else "погас"
    count = int(entry.get("count", 0))
    await context.edit(f"🔥 {entry.get('name', name)}: {count} {_days_label(count)} · {state}")


@command(name="streaks", category="Огонёк", description="Показать все текущие и погасшие серии.", usage=".streaks")
async def streaks(context: object) -> None:
    values = await _data(context)
    if not values:
        await context.edit("🔥 Серий пока нет. В личке нужно по сообщению от каждого за день.")
        return
    today = date.today()
    rows = [
        f"{'🔥' if is_active(entry, today) else '💨'} {entry.get('name', identifier)} — {entry.get('count', 0)}"
        for identifier, entry in values.items()
    ]
    await context.edit("🔥 Серии\n\n" + "\n".join(rows[:100]))


@command(name="streakinfo", category="Огонёк", description="Показать подробности серии с человеком.", usage="reply .streakinfo или .streakinfo @username")
async def streakinfo(context: object) -> None:
    identifier, name = await _target(context)
    entry = (await _data(context)).get(identifier or "")
    if not entry:
        await context.edit(f"🔥 У {name or 'этого человека'} пока нет серии.")
        return
    today_state = entry.get("days", {}).get(date.today().isoformat(), {}) if isinstance(entry.get("days"), dict) else {}
    mine = "есть" if isinstance(today_state, dict) and today_state.get("out") else "нет"
    theirs = "есть" if isinstance(today_state, dict) and today_state.get("in") else "нет"
    await context.edit(
        f"🔥 {entry.get('name', name)}\n\n"
        f"Серия: {entry.get('count', 0)} дней\nСтатус: {'горит' if is_active(entry, date.today()) else 'погас'}\n"
        f"Сегодня: твоё сообщение — {mine}, его сообщение — {theirs}"
    )


async def record_message(client: Any, event: Any, direction: str) -> None:
    if not getattr(event, "is_private", False) or event.chat_id == client.telegram_user_id:
        return
    identifier = str(event.chat_id)
    try:
        peer = await event.get_chat()
        name = getattr(peer, "first_name", None) or getattr(peer, "title", None) or identifier
    except Exception:
        name = identifier
    values = await client.services.settings.get(client.user_id, KEY, {})
    values = values if isinstance(values, dict) else {}
    entry = values.get(identifier, {})
    entry = entry if isinstance(entry, dict) else {}
    had_streak_before = bool(entry.get("started"))
    was_active = is_active(entry, date.today())
    entry["name"] = name
    entry, completed = apply_message(entry, date.today(), direction)
    values[identifier] = entry
    await client.services.settings.set(client.user_id, KEY, values)
    if completed:
        try:
            count = int(entry["count"])
            if had_streak_before and not was_active:
                text = f"🔥 Серия снова горит: {count} {_days_label(count)}"
            elif count == 1:
                text = "🔥 Серия началась: 1 день"
            else:
                text = f"🔥 Серия: {count} {_days_label(count)}"
            sent = await event.client.send_message(event.chat_id, text)
            client.mark_internal(sent)
        except Exception:
            pass
