from __future__ import annotations

from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.userbot.registry import command


async def _json(url: str) -> dict:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "SaveModUserBot/1.0"})
        response.raise_for_status()
        return response.json()


def _file_name(value: str, fallback: str) -> str:
    clean = "".join(char if char.isalnum() or char in "._- " else "_" for char in value).strip(" .")
    return clean[:80] or fallback


@command(name="kurs", category="Kurs", description="Показать курс валюты к рублю.", usage=".kurs [USD|EUR|CNY]")
async def kurs(context: object) -> None:
    currency = (context.args[0].upper() if context.args else "USD")
    if len(currency) != 3 or not currency.isalpha():
        await context.edit("⚠️ Укажи трёхбуквенный код валюты: .kurs USD")
        return
    try:
        data = await _json(f"https://open.er-api.com/v6/latest/{currency}")
        value = float(data["rates"]["RUB"])
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        await context.edit("⚠️ Не удалось получить курс. Попробуй позже.")
        return
    await context.edit(f"💱 1 {currency} = {value:.2f} RUB\nИсточник: ExchangeRate-API")


@command(name="crypto", category="Kurs", description="Показать цену криптовалюты в USD и RUB.", usage=".crypto [BTC|ETH|SOL]")
async def crypto(context: object) -> None:
    symbol = (context.args[0].lower() if context.args else "btc")
    ids = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "ton": "the-open-network", "usdt": "tether"}
    coin_id = ids.get(symbol, symbol)
    try:
        data = await _json(
            f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,rub&include_24hr_change=true"
        )
        quote = data[coin_id]
        usd, rub = float(quote["usd"]), float(quote["rub"])
        change = float(quote.get("usd_24h_change", 0))
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        await context.edit("⚠️ Не удалось получить цену. Поддерживаются BTC, ETH, SOL, TON, USDT.")
        return
    await context.edit(f"🪙 {symbol.upper()}\n\nUSD: {usd:,.2f}\nRUB: {rub:,.2f}\n24ч: {change:+.2f}%\nИсточник: CoinGecko")


@command(name="mtf", category="MessageToFile", description="Отправить текст из reply как .txt-файл.", usage="reply .mtf [имя]")
async def message_to_file(context: object) -> None:
    reply = await context.get_reply()
    text = reply.raw_text if reply else context.raw_args
    if not text:
        await context.edit("⚠️ Ответь на текстовое сообщение или передай текст после .mtf")
        return
    filename = _file_name(context.args[0] if context.args else "message", "message") + ".txt"
    data = BytesIO(text.encode("utf-8"))
    data.name = filename
    await context.delete()
    sent = await context.event.client.send_file(context.chat_id, data, caption=f"📄 {filename}")
    context.client.mark_internal(sent)


@command(name="ftm", category="MessageToFile", description="Прочитать текстовый файл из reply.", usage="reply .ftm")
async def file_to_message(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.file:
        await context.edit("⚠️ Ответь на текстовый файл.")
        return
    if reply.file.size and reply.file.size > 1_000_000:
        await context.edit("⚠️ Файл больше 1 МБ — не буду засорять чат.")
        return
    raw = await context.event.client.download_media(reply, bytes)
    if not isinstance(raw, bytes):
        await context.edit("⚠️ Не удалось скачать файл.")
        return
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        await context.edit("⚠️ В файле нет текста.")
        return
    await context.edit(text[:4_000])


@command(name="sendmod", category="SendMod", description="Переслать reply-сообщение в указанный чат.", usage="reply .sendmod <@username|ссылка|id>")
async def sendmod(context: object) -> None:
    reply = await context.get_reply()
    target = context.raw_args.strip()
    if not reply or not target:
        await context.edit("⚠️ Ответь на сообщение: .sendmod <куда>")
        return
    try:
        entity = await context.event.client.get_entity(target)
        sent = await context.event.client.forward_messages(entity, reply)
    except Exception:
        await context.edit("⚠️ Не удалось найти чат или переслать сообщение.")
        return
    for item in sent if isinstance(sent, list) else [sent]:
        context.client.mark_internal(item)
    await context.edit("✅ Сообщение переслано.")


@command(name="weather", category="Weather", description="Показать текущую погоду в городе.", usage=".weather <город>")
async def weather(context: object) -> None:
    place = context.raw_args.strip()
    if not place:
        await context.edit("⚠️ Использование: .weather Новосибирск")
        return
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(f"https://wttr.in/{place}", params={"format": "j1", "lang": "ru"})
            response.raise_for_status()
            data = response.json()["current_condition"][0]
        temp = data["temp_C"]
        feel = data["FeelsLikeC"]
        description = data["lang_ru"][0]["value"] if data.get("lang_ru") else data["weatherDesc"][0]["value"]
        wind = data["windspeedKmph"]
        humidity = data["humidity"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        await context.edit("⚠️ Не удалось получить погоду. Проверь название города.")
        return
    await context.edit(f"🌤 {place}\n\n{description}\nТемпература: {temp}°C (ощущается как {feel}°C)\nВетер: {wind} км/ч · Влажность: {humidity}%")


@command(name="time", category="Время", description="Показать время в часовом поясе IANA.", usage=".time [Asia/Novosibirsk]")
async def time_command(context: object) -> None:
    timezone = context.raw_args.strip() or "Asia/Novosibirsk"
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        await context.edit("⚠️ Неизвестный пояс. Пример: .time Europe/Moscow или .time Asia/Tokyo")
        return
    await context.edit(f"🕒 {timezone}\n{now.strftime('%d.%m.%Y %H:%M:%S')} ({now.tzname()})")
