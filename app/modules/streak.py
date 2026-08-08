from __future__ import annotations

from datetime import date, timedelta

from app.userbot.registry import command


KEY = "streaks"


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


async def _data(context: object) -> dict[str, dict[str, object]]:
    value = await context.services.settings.get(context.user_id, KEY, {})
    return value if isinstance(value, dict) else {}


@command(name="streak", category="Огонёк", description="Отметить сегодняшнюю серию общения с человеком.", usage="reply .streak или .streak @username")
async def streak(context: object) -> None:
    identifier, name = await _target(context)
    if not identifier:
        await context.edit("⚠️ Ответь на сообщение человека или укажи @username.")
        return
    values = await _data(context)
    today = date.today()
    current = values.get(identifier, {})
    last = current.get("last")
    if last == today.isoformat():
        await context.edit(f"🔥 {name}: сегодня уже отмечено · серия {current.get('count', 1)}")
        return
    count = int(current.get("count", 0)) + 1 if last == (today - timedelta(days=1)).isoformat() else 1
    values[identifier] = {"name": name, "last": today.isoformat(), "count": count, "started": current.get("started", today.isoformat())}
    await context.services.settings.set(context.user_id, KEY, values)
    await context.edit(f"🔥 {name}\nСерия: {count} {('день' if count == 1 else 'дня' if 2 <= count <= 4 else 'дней')}\nОтмечено: {today.strftime('%d.%m.%Y')}")


@command(name="streaks", category="Огонёк", description="Показать все активные серии.", usage=".streaks")
async def streaks(context: object) -> None:
    values = await _data(context)
    if not values:
        await context.edit("🔥 Серий пока нет. Ответь на сообщение и напиши .streak")
        return
    today = date.today()
    rows = []
    for entry in values.values():
        last = entry.get("last")
        if last in {today.isoformat(), (today - timedelta(days=1)).isoformat()}:
            rows.append(f"🔥 {entry.get('name', 'Пользователь')} — {entry.get('count', 1)}")
    await context.edit("🔥 Серии\n\n" + ("\n".join(rows) if rows else "Активных серий нет."))


@command(name="streakinfo", category="Огонёк", description="Показать данные серии с человеком.", usage="reply .streakinfo или .streakinfo @username")
async def streakinfo(context: object) -> None:
    identifier, name = await _target(context)
    values = await _data(context)
    entry = values.get(identifier or "")
    if not entry:
        await context.edit(f"🔥 У {name or 'этого человека'} пока нет серии.")
        return
    await context.edit(
        f"🔥 {entry.get('name', name)}\n\n"
        f"Серия: {entry.get('count', 1)}\nНачало: {entry.get('started')}\nПоследняя отметка: {entry.get('last')}"
    )
