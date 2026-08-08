from __future__ import annotations

from typing import Any

from app.userbot.registry import command


LOCAL_KEY = "filters_local"
GLOBAL_KEY = "filters_global"


def _split_rule(raw: str) -> tuple[str, str] | None:
    trigger, separator, response = raw.partition("|")
    trigger, response = trigger.strip().lower(), response.strip()
    if not separator or not trigger or not response or len(trigger) > 80 or len(response) > 3_500:
        return None
    return trigger, response


async def _local(context: object) -> dict[str, dict[str, str]]:
    value = await context.services.settings.get(context.user_id, LOCAL_KEY, {})
    return value if isinstance(value, dict) else {}


async def _save_local(context: object, value: dict[str, dict[str, str]]) -> None:
    await context.services.settings.set(context.user_id, LOCAL_KEY, value)


async def _set_filter(context: object, global_scope: bool) -> None:
    rule = _split_rule(context.raw_args)
    if not rule:
        await context.edit("⚠️ Использование: .filter <слово> | <ответ>")
        return
    trigger, response = rule
    if global_scope:
        filters = await context.services.settings.get(context.user_id, GLOBAL_KEY, {})
        filters = filters if isinstance(filters, dict) else {}
        filters[trigger] = response
        await context.services.settings.set(context.user_id, GLOBAL_KEY, filters)
    else:
        saved = await _local(context)
        chat = saved.setdefault(str(context.chat_id), {})
        chat[trigger] = response
        await _save_local(context, saved)
    await context.edit(f"✅ Фильтр «{trigger}» сохранён{' глобально' if global_scope else ' для этого чата'}.")


async def _remove_filter(context: object, global_scope: bool) -> None:
    trigger = context.raw_args.strip().lower()
    if not trigger:
        await context.edit("⚠️ Укажи триггер фильтра.")
        return
    if global_scope:
        filters = await context.services.settings.get(context.user_id, GLOBAL_KEY, {})
        filters = filters if isinstance(filters, dict) else {}
        removed = filters.pop(trigger, None)
        await context.services.settings.set(context.user_id, GLOBAL_KEY, filters)
    else:
        saved = await _local(context)
        chat = saved.get(str(context.chat_id), {})
        removed = chat.pop(trigger, None)
        if not chat:
            saved.pop(str(context.chat_id), None)
        await _save_local(context, saved)
    await context.edit("✅ Фильтр удалён." if removed is not None else "⚠️ Такого фильтра нет.")


async def _list_filters(context: object, global_scope: bool) -> None:
    if global_scope:
        filters = await context.services.settings.get(context.user_id, GLOBAL_KEY, {})
        filters = filters if isinstance(filters, dict) else {}
        title = "🌐 Глобальные фильтры"
    else:
        filters = (await _local(context)).get(str(context.chat_id), {})
        title = "💬 Фильтры этого чата"
    if not filters:
        await context.edit(f"{title}\n\nПока пусто.")
        return
    lines = "\n".join(f"• {trigger} → {response[:80]}" for trigger, response in sorted(filters.items()))
    await context.edit(f"{title}\n\n{lines}"[:4_000])


@command(name="filter", category="Filters", description="Добавить автоответ для текущего чата.", usage=".filter <слово> | <ответ>")
async def add_filter(context: object) -> None:
    await _set_filter(context, False)


@command(name="stop", category="Filters", description="Удалить фильтр текущего чата.", usage=".stop <слово>")
async def stop_filter(context: object) -> None:
    await _remove_filter(context, False)


@command(name="stopall", category="Filters", description="Удалить все фильтры текущего чата.", usage=".stopall")
async def stop_all_filters(context: object) -> None:
    saved = await _local(context)
    removed = len(saved.pop(str(context.chat_id), {}))
    await _save_local(context, saved)
    await context.edit(f"✅ Удалено фильтров: {removed}.")


@command(name="filters", category="Filters", description="Показать фильтры текущего чата.", usage=".filters")
async def list_filters(context: object) -> None:
    await _list_filters(context, False)


@command(name="gfilter", category="Filters", description="Добавить глобальный автоответ во всех чатах.", usage=".gfilter <слово> | <ответ>")
async def add_global_filter(context: object) -> None:
    await _set_filter(context, True)


@command(name="gstop", category="Filters", description="Удалить глобальный фильтр.", usage=".gstop <слово>")
async def stop_global_filter(context: object) -> None:
    await _remove_filter(context, True)


@command(name="gstopall", category="Filters", description="Удалить все глобальные фильтры.", usage=".gstopall")
async def stop_all_global_filters(context: object) -> None:
    filters = await context.services.settings.get(context.user_id, GLOBAL_KEY, {})
    count = len(filters) if isinstance(filters, dict) else 0
    await context.services.settings.set(context.user_id, GLOBAL_KEY, {})
    await context.edit(f"✅ Удалено глобальных фильтров: {count}.")


@command(name="gfilters", category="Filters", description="Показать глобальные фильтры.", usage=".gfilters")
async def list_global_filters(context: object) -> None:
    await _list_filters(context, True)


@command(name="allfilters", category="Filters", description="Показать число локальных и глобальных фильтров.", usage=".allfilters")
async def all_filters(context: object) -> None:
    local = await _local(context)
    global_filters = await context.services.settings.get(context.user_id, GLOBAL_KEY, {})
    local_count = sum(len(item) for item in local.values() if isinstance(item, dict))
    global_count = len(global_filters) if isinstance(global_filters, dict) else 0
    await context.edit(f"🧩 Все фильтры\n\nЛокальные: {local_count}\nГлобальные: {global_count}")


async def maybe_reply_filter(client: Any, event: Any) -> None:
    text = (event.raw_text or "").lower()
    if not text:
        return
    global_filters = await client.services.settings.get(client.user_id, GLOBAL_KEY, {})
    local_filters = await client.services.settings.get(client.user_id, LOCAL_KEY, {})
    local = local_filters.get(str(event.chat_id), {}) if isinstance(local_filters, dict) else {}
    merged = (global_filters if isinstance(global_filters, dict) else {}) | (local if isinstance(local, dict) else {})
    for trigger, response in merged.items():
        if trigger and trigger in text and isinstance(response, str):
            sent = await event.reply(response)
            client.mark_internal(sent)
            return
