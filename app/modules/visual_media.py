from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps
from telethon import types

from app.services.media_processing import MediaProcessingError, cleanup, ffmpeg_reply
from app.userbot.registry import command


async def _photo(context: object) -> Image.Image | None:
    reply = await context.get_reply()
    if not reply or not reply.photo:
        await context.edit("⚠️ Ответь на фотографию.")
        return None
    raw = await context.event.client.download_media(reply, bytes)
    if not raw:
        await context.edit("⚠️ Не удалось скачать фотографию.")
        return None
    return Image.open(BytesIO(raw)).convert("RGB")


async def _send_image(context: object, image: Image.Image, name: str) -> None:
    image.thumbnail((2_000, 2_000))
    result = BytesIO()
    result.name = name
    image.save(result, "JPEG", quality=92)
    result.seek(0)
    await context.delete()
    sent = await context.event.client.send_file(context.chat_id, result, force_document=False)
    context.client.mark_internal(sent)


def _flip_command(name: str, description: str, operation) -> None:
    @command(name=name, category="MirrorFlip", description=description, usage=f"reply .{name}")
    async def handler(context: object) -> None:
        image = await _photo(context)
        if image:
            await _send_image(context, image.transpose(operation), f"{name}.jpg")


_flip_command("ll", "Отразить фото по горизонтали.", Image.Transpose.FLIP_LEFT_RIGHT)
_flip_command("rr", "Отразить фото по горизонтали.", Image.Transpose.FLIP_LEFT_RIGHT)
_flip_command("uu", "Отразить фото по вертикали.", Image.Transpose.FLIP_TOP_BOTTOM)
_flip_command("dd", "Отразить фото по вертикали.", Image.Transpose.FLIP_TOP_BOTTOM)


@command(name="distort", category="Distort", description="Добавить волнообразное искажение reply-фото.", usage="reply .distort")
async def distort(context: object) -> None:
    image = await _photo(context)
    if not image:
        return
    width, height = image.size
    image = image.transform(
        image.size, Image.Transform.QUAD,
        (0, height * .06, width * .94, 0, width, height * .94, width * .06, height),
        Image.Resampling.BICUBIC,
    )
    await _send_image(context, image, "distort.jpg")


@command(name="tostick", category="ToStick", description="Конвертировать reply-фото в статичный стикер.", usage="reply .tostick")
async def to_sticker(context: object) -> None:
    image = await _photo(context)
    if not image:
        return
    image.thumbnail((512, 512))
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.alpha_composite(image.convert("RGBA"), ((512 - image.width) // 2, (512 - image.height) // 2))
    result = BytesIO()
    result.name = "sticker.webp"
    canvas.save(result, "WEBP", lossless=True, method=6)
    result.seek(0)
    await context.delete()
    sent = await context.event.client.send_file(
        context.chat_id, result, force_document=False,
        attributes=[types.DocumentAttributeSticker(alt="🙂", stickerset=types.InputStickerSetEmpty())],
    )
    context.client.mark_internal(sent)


@command(name="round", category="Circles", description="Сделать из reply-видео круглое видео, до 60 секунд.", usage="reply .round")
async def round_video(context: object) -> None:
    reply = await context.get_reply()
    try:
        folder, path = await ffmpeg_reply(
            context.event.client, reply, output_name="round", output_suffix=".mp4",
            args=[
                "-t", "60", "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=480:480",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-c:a", "aac",
            ],
        )
    except MediaProcessingError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    try:
        await context.delete()
        sent = await context.event.client.send_file(context.chat_id, str(path), video_note=True, force_document=False)
        context.client.mark_internal(sent)
    finally:
        cleanup(folder)
