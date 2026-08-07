from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.userbot.registry import command


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"):
        try: return ImageFont.truetype(path, size)
        except OSError: continue
    return ImageFont.load_default()


@command(name="demot", aliases=["demotivator"], category="Медиа", description="Демотиватор из reply-фото и двух строк.", usage=".demot TITLE | subtitle (reply photo)", requires_reply=True)
async def demot(context: object) -> None:
    reply = await context.get_reply()
    if not reply or not reply.photo:
        await context.edit("⚠️ Ответь на фотографию."); return
    raw = await context.event.client.download_media(reply, file=bytes)
    if not raw: await context.edit("⚠️ Не удалось скачать фото."); return
    title, _, subtitle = context.raw_args.partition("|")
    if not title.strip(): await context.edit("⚠️ .demot TITLE | subtitle"); return
    source = Image.open(BytesIO(raw)).convert("RGB")
    source.thumbnail((900, 700))
    width, height = source.width + 80, source.height + 230
    canvas = Image.new("RGB", (width, height), "#090909")
    canvas.paste(source, ((width - source.width) // 2, 35))
    draw = ImageDraw.Draw(canvas)
    x0, y0 = (width - source.width) // 2 - 4, 31
    draw.rectangle((x0, y0, x0 + source.width + 8, y0 + source.height + 8), outline="white", width=3)
    title_font, sub_font = font(42), font(23)
    title_box = draw.textbbox((0, 0), title.strip()[:80], font=title_font)
    draw.text(((width - (title_box[2] - title_box[0])) // 2, source.height + 70), title.strip()[:80], fill="white", font=title_font)
    subtitle_box = draw.textbbox((0, 0), subtitle.strip()[:120], font=sub_font)
    draw.text(((width - (subtitle_box[2] - subtitle_box[0])) // 2, source.height + 130), subtitle.strip()[:120], fill="#d0d0d0", font=sub_font)
    result = BytesIO(); canvas.save(result, "JPEG", quality=92)
    await context.delete()
    message = await context.event.client.send_file(context.chat_id, result.getvalue(), reply_to=reply.id)
    context.client.mark_internal(message)
