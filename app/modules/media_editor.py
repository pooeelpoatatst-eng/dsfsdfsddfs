from __future__ import annotations

from app.services.media_processing import MediaProcessingError, cleanup, ffmpeg_reply
from app.userbot.registry import command


async def _audio(context: object, args: list[str], output: str = "audio.mp3", voice: bool = False) -> None:
    reply = await context.get_reply()
    try:
        folder, path = await ffmpeg_reply(
            context.event.client, reply, output_name=output.rsplit(".", 1)[0], output_suffix=".ogg" if voice else ".mp3",
            args=args + (["-c:a", "libopus", "-b:a", "64k"] if voice else ["-c:a", "libmp3lame", "-q:a", "3"]),
        )
    except MediaProcessingError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    try:
        await context.delete()
        sent = await context.event.client.send_file(context.chat_id, str(path), voice_note=voice, force_document=False)
        context.client.mark_internal(sent)
    finally:
        cleanup(folder)


def _audio_command(name: str, description: str, args: list[str]) -> None:
    @command(name=name, category="AudioEditor", description=description, usage=f"reply .{name}")
    async def handler(context: object) -> None:
        await _audio(context, args, name + ".mp3")


for _name, _description, _args in (
    ("bass", "Добавить бас.", ["-af", "bass=g=8:f=110:w=0.6"]),
    ("fv", "Добавить эффект объёма.", ["-af", "aecho=0.8:0.88:60:0.35"]),
    ("echos", "Добавить эхо.", ["-af", "aecho=0.8:0.9:700:0.35"]),
    ("volup", "Увеличить громкость.", ["-af", "volume=1.5"]),
    ("voldw", "Уменьшить громкость.", ["-af", "volume=0.65"]),
    ("revs", "Развернуть аудио задом наперёд.", ["-af", "areverse"]),
    ("reps", "Повторить аудио дважды.", ["-af", "aloop=loop=1:size=2147483647"]),
    ("slows", "Замедлить аудио.", ["-af", "atempo=0.80"]),
    ("fasts", "Ускорить аудио.", ["-af", "atempo=1.25"]),
    ("rights", "Оставить правый аудиоканал.", ["-af", "pan=mono|c0=c1"]),
    ("lefts", "Оставить левый аудиоканал.", ["-af", "pan=mono|c0=c0"]),
    ("norms", "Нормализовать громкость.", ["-af", "loudnorm"]),
    ("convs", "Конвертировать в MP3.", []),
):
    _audio_command(_name, _description, _args)


@command(name="tovs", category="AudioEditor", description="Конвертировать reply-аудио в голосовое сообщение.", usage="reply .tovs")
async def to_voice(context: object) -> None:
    await _audio(context, [], "voice.ogg", voice=True)


@command(name="cuts", category="AudioEditor", description="Обрезать аудио с начала до указанного числа секунд.", usage="reply .cuts <секунды>")
async def cut_audio(context: object) -> None:
    try:
        seconds = int(context.args[0])
        if not 1 <= seconds <= 600:
            raise ValueError
    except (IndexError, ValueError):
        await context.edit("⚠️ Использование: reply .cuts <1–600 секунд>")
        return
    await _audio(context, ["-t", str(seconds)], "cut.mp3")


async def _video(context: object, args: list[str], output: str = "video.mp4") -> None:
    reply = await context.get_reply()
    try:
        folder, path = await ffmpeg_reply(
            context.event.client, reply, output_name=output.rsplit(".", 1)[0], output_suffix=".mp4",
            args=args + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart"],
        )
    except MediaProcessingError as exc:
        await context.edit(f"⚠️ {exc}")
        return
    try:
        await context.delete()
        sent = await context.event.client.send_file(context.chat_id, str(path), force_document=False, supports_streaming=True)
        context.client.mark_internal(sent)
    finally:
        cleanup(folder)


def _video_command(name: str, description: str, args: list[str]) -> None:
    @command(name=name, category="VideoEditor", description=description, usage=f"reply .{name}")
    async def handler(context: object) -> None:
        await _video(context, args, name + ".mp4")


for _name, _description, _args in (
    ("xflipv", "Отразить видео по горизонтали.", ["-vf", "hflip"]),
    ("yflipv", "Отразить видео по вертикали.", ["-vf", "vflip"]),
    ("bwv", "Сделать видео чёрно-белым.", ["-vf", "hue=s=0"]),
    ("revv", "Развернуть видео и аудио.", ["-vf", "reverse", "-af", "areverse"]),
    ("paintv", "Добавить контурный эффект.", ["-vf", "edgedetect=low=0.1:high=0.4"]),
    ("invertv", "Инвертировать цвета.", ["-vf", "negate"]),
    ("rmsv", "Повернуть видео на 90 градусов.", ["-vf", "transpose=1"]),
    ("audv", "Убрать аудиодорожку.", ["-an"]),
    ("fpsv", "Сделать частоту кадров 30 FPS.", ["-vf", "fps=30"]),
    ("marginv", "Добавить чёрные поля.", ["-vf", "pad=iw+80:ih+80:40:40:black"]),
    ("speedv", "Ускорить видео на 25%.", ["-vf", "setpts=0.8*PTS", "-af", "atempo=1.25"]),
    ("contrastv", "Усилить контраст.", ["-vf", "eq=contrast=1.35"]),
    ("lumv", "Увеличить яркость.", ["-vf", "eq=brightness=0.08"]),
):
    _video_command(_name, _description, _args)


@command(name="cutv", category="VideoEditor", description="Обрезать видео с начала до указанного числа секунд.", usage="reply .cutv <секунды>")
async def cut_video(context: object) -> None:
    try:
        seconds = int(context.args[0])
        if not 1 <= seconds <= 600:
            raise ValueError
    except (IndexError, ValueError):
        await context.edit("⚠️ Использование: reply .cutv <1–600 секунд>")
        return
    await _video(context, ["-t", str(seconds)], "cut.mp4")


@command(name="scalev", category="VideoEditor", description="Изменить ширину видео с сохранением пропорций.", usage="reply .scalev <ширина>")
async def scale_video(context: object) -> None:
    try:
        width = int(context.args[0])
        if not 160 <= width <= 1920 or width % 2:
            raise ValueError
    except (IndexError, ValueError):
        await context.edit("⚠️ Использование: reply .scalev <чётная ширина 160–1920>")
        return
    await _video(context, ["-vf", f"scale={width}:-2"], "scaled.mp4")
