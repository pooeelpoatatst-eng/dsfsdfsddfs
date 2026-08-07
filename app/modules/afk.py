from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.database.models import AfkState
from app.userbot.registry import command


@command(name="afk", category="AI / режимы", description="Автоответ при AFK.", usage=".afk [reason|off|status]")
async def afk(context: object) -> None:
    arg = context.raw_args.strip()
    async with context.services.settings.db.session() as session:
        state = await session.get(AfkState, context.user_id)
        if not state: state = AfkState(user_id=context.user_id); session.add(state)
        if arg.lower() == "off":
            state.enabled = False; await context.edit("💤 AFK выключен."); return
        if arg.lower() == "status":
            await context.edit("💤 AFK: " + (f"ON, {state.reason or 'без причины'}" if state.enabled else "OFF")); return
        state.enabled, state.since, state.reason = True, datetime.now(timezone.utc), arg[:500] or None
    await context.edit(f"💤 AFK включён{': ' + arg[:500] if arg else ''}")


async def maybe_reply_afk(client: object, event: object) -> None:
    async with client.services.settings.db.session() as session:
        state = await session.get(AfkState, client.user_id)
        if not state or not state.enabled or not event.is_private: return
    elapsed = datetime.now(timezone.utc) - state.since
    minutes = max(1, int(elapsed.total_seconds() // 60))
    await event.reply(f"💤 AFK {minutes} мин.\nПричина: {state.reason or 'не указана'}")
