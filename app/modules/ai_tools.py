from __future__ import annotations

from app.modules.tools import argument_or_reply
from app.services.ai import AIUnavailableError
from app.userbot.registry import command


async def _run(context: object, system: str, text: str, heading: str = "") -> None:
    if not text.strip():
        await context.edit("⚠️ Добавь текст или ответь командой на сообщение.")
        return
    if not context.services.ai.available:
        await context.edit("⚠️ AI не настроен. Добавь AI_API_KEY в переменные сервиса.")
        return
    try:
        result = await context.services.ai.transform(system, text[:8_000])
        await context.services.usage.record_ai(context.user_id, result.prompt_tokens, result.completion_tokens)
        answer = result.text.strip()[:3_700]
        await context.edit(f"{heading}\n\n{answer}" if heading else answer)
    except AIUnavailableError:
        await context.services.usage.record_ai(context.user_id, error=True)
        await context.edit("⚠️ AI сейчас недоступен. Попробуй чуть позже.")


async def _text(context: object) -> str:
    return await argument_or_reply(context)


@command(name="ai", aliases=["ask"], category="AI / полезное", description="Спросить AI о чём угодно.", usage=".ai <вопрос>", requires_ai=True)
async def ask(context: object) -> None:
    await _run(context, "Ответь по-русски как сильный помощник: сначала дай прямой ответ, потом коротко объясни почему и приведи пример, когда это полезно. Если данных не хватает — скажи, что именно нужно уточнить.", await _text(context), "🤖 Ответ")


@command(name="sum", aliases=["summarize"], category="AI / полезное", description="Коротко выжать главное из текста.", usage=".sum <текст> или reply", requires_ai=True)
async def summarize(context: object) -> None:
    await _run(context, "Сделай полезное резюме на русском в трёх блоках: «Суть» (1–2 предложения), «Главное» (3–7 пунктов), «Что делать» (только если это следует из текста). Сохрани важные числа, даты и имена. Не выдумывай фактов.", await _text(context), "📝 Резюме")


@command(name="replyai", aliases=["replytext"], category="AI / полезное", description="Придумать естественный ответ на сообщение.", usage="reply .replyai [тон]", requires_ai=True)
async def reply_ai(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.raw_text:
        await context.edit("⚠️ Ответь этой командой на сообщение.")
        return
    tone = context.raw_args.strip() or "дружелюбно и естественно"
    await _run(context, f"Предложи ТРИ готовых ответа на сообщение в тоне «{tone}»: короткий, обычный и с лёгкой инициативой. Каждый вариант должен быть естественным, по-русски, без пояснений и не выдумывать факты.", reply.raw_text, "💬 Варианты ответа")


@command(name="rewrite", category="AI / полезное", description="Переписать текст в нужном тоне.", usage=".rewrite <тон> | <текст>", requires_ai=True)
async def rewrite(context: object) -> None:
    tone, separator, text = context.raw_args.partition("|")
    if not separator:
        text = await _text(context)
        tone = "ясно и естественно"
    await _run(context, f"Перепиши текст по-русски в тоне «{tone.strip() or 'ясно и естественно'}». Сохрани все факты, имена, ссылки и исходный смысл. Сделай текст готовым к отправке. Верни только итоговый текст.", text)


@command(name="translate", aliases=["tr"], category="AI / полезное", description="Перевести текст с сохранением смысла.", usage=".translate en | <текст>", requires_ai=True)
async def translate(context: object) -> None:
    language, separator, text = context.raw_args.partition("|")
    if not separator:
        parts = context.raw_args.split(maxsplit=1)
        language = parts[0] if parts else ""
        text = parts[1] if len(parts) > 1 else ""
    if not text.strip():
        reply = await context.get_reply()
        text = reply.raw_text if reply and reply.raw_text else ""
    await _run(context, f"Переведи текст на {language.strip() or 'русский'}. Сохрани имена, ссылки, формат чисел, сленг и тон. Если есть неоднозначность — выбери наиболее естественный разговорный вариант. Верни только перевод.", text)


@command(name="explain", aliases=["eli5"], category="AI / полезное", description="Объяснить сложное простыми словами.", usage=".explain <вопрос/текст>", requires_ai=True)
async def explain(context: object) -> None:
    await _run(context, "Объясни тему простым русским языком в структуре: «Что это», «Как работает», «Зачем это нужно», «Пример». Не упрощай до неверного и не лей воду.", await _text(context), "🧩 Объяснение")


@command(name="tasks", aliases=["todoai"], category="AI / полезное", description="Вытащить задачи и сроки из текста.", usage=".tasks <текст> или reply", requires_ai=True)
async def tasks(context: object) -> None:
    await _run(context, "Извлеки из текста конкретные задачи. Верни чек-лист: [ ] задача — приоритет (высокий/средний/низкий) — срок, только если он указан. В конце добавь «Жду уточнения», если в тексте есть неясные поручения. Не придумывай сроки и исполнителей.", await _text(context), "✅ Задачи")


@command(name="planai", aliases=["plan"], category="AI / полезное", description="Собрать реалистичный план достижения цели.", usage=".plan <цель>", requires_ai=True)
async def plan_ai(context: object) -> None:
    await _run(context, "Составь практичный план достижения цели: результат, первый шаг сегодня, шаги 2–6, риски и критерий готовности. У каждого шага должна быть конкретика, а не общие слова. Пиши по-русски и без воды.", await _text(context), "🧭 План")


@command(name="proofread", aliases=["fixtext"], category="AI / полезное", description="Исправить ошибки, не меняя твой стиль.", usage=".proofread <текст> или reply", requires_ai=True)
async def proofread(context: object) -> None:
    await _run(context, "Исправь орфографию, пунктуацию и очевидные опечатки в русском тексте. Не меняй стиль, смысл, сленг, имена и ссылки. Верни только исправленный текст.", await _text(context))


@command(name="ideas", aliases=["brainstorm"], category="AI / полезное", description="Накидать небанальные идеи под задачу.", usage=".ideas <задача>", requires_ai=True)
async def ideas(context: object) -> None:
    await _run(context, "Предложи 8 конкретных, небанальных и реализуемых идей для задачи. Каждая: название — что сделать — зачем это зайдёт. Последней строкой выбери две самые сильные и объясни выбор. Отвечай по-русски.", await _text(context), "💡 Идеи")
