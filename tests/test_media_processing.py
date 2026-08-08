import asyncio
import shutil

import pytest

from app.services.media_processing import MAX_MEDIA_BYTES, cleanup, ffmpeg_reply, safe_suffix


def test_media_suffix_and_limit_are_bounded() -> None:
    assert safe_suffix("song.MP3", ".bin") == ".mp3"
    assert safe_suffix("../../evil", ".bin") == ".bin"
    assert MAX_MEDIA_BYTES == 50 * 1024 * 1024


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is required")
async def test_ffmpeg_reply_converts_audio(tmp_path) -> None:
    source = tmp_path / "source.wav"
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.1", str(source),
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    assert await process.wait() == 0

    class File:
        name = "source.wav"
        size = source.stat().st_size

    class Reply:
        file = File()

    class Client:
        async def download_media(self, _reply, file):
            shutil.copy(source, file)
            return file

    folder, output = await ffmpeg_reply(
        Client(), Reply(), output_name="result", output_suffix=".mp3", args=["-c:a", "libmp3lame"]
    )
    try:
        assert output.exists() and output.stat().st_size > 0
    finally:
        cleanup(folder)
