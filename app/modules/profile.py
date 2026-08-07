from __future__ import annotations

import base64
from io import BytesIO

from telethon.tl import functions, types
from PIL import Image

from app.userbot.registry import command

MAX_AVATAR_BYTES = 5 * 1024 * 1024


async def target_entity(context: object) -> object | None:
    reply = await context.get_reply()
    if reply:
        return await context.event.client.get_entity(reply.sender_id)
    if context.raw_args:
        try: return await context.event.client.get_entity(context.raw_args)
        except (ValueError, TypeError): return None
    return None


async def set_avatar(client: object, raw: bytes | None) -> None:
    photos = await client(functions.photos.GetUserPhotosRequest(user_id="me", offset=0, max_id=0, limit=100))
    if raw:
        # Telegram rejects byte uploads without an image extension. Re-encode
        # every source format as JPEG and name the upload explicitly.
        image = Image.open(BytesIO(raw)).convert("RGB")
        image.thumbnail((1280, 1280))
        jpeg = BytesIO(); image.save(jpeg, "JPEG", quality=92)
        uploaded = await client.upload_file(jpeg.getvalue(), file_name="profile.jpg")
        await client(functions.photos.UploadProfilePhotoRequest(file=uploaded))
    if photos.photos:
        await client(functions.photos.DeletePhotosRequest(id=[types.InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference) for p in photos.photos]))


@command(name="clone", category="Профиль", description="Скопировать имя, bio и аватар reply-пользователя.", usage=".clone [@username] или reply")
async def clone(context: object) -> None:
    target = await target_entity(context)
    if not target:
        await context.edit("⚠️ Ответь на пользователя или укажи @username."); return
    me = await context.event.client.get_me()
    settings = context.services.settings
    old = await settings.get(context.user_id, "profile_backup")
    if not old:
        own_full = await context.event.client(functions.users.GetFullUserRequest("me"))
        photo = await context.event.client.download_profile_photo("me", file=bytes)
        old = {"first_name": me.first_name or "", "last_name": me.last_name or "", "about": own_full.full_user.about or "", "photo": base64.b64encode(photo).decode() if photo and len(photo) <= MAX_AVATAR_BYTES else None}
        await settings.set(context.user_id, "profile_backup", old)
    full = await context.event.client(functions.users.GetFullUserRequest(target))
    # `target` can be a locally renamed contact. FullUser contains Telegram's
    # actual account name instead of the name saved in the owner's contacts.
    actual = full.users[0]
    about = (full.full_user.about or "")[:70]
    await context.event.client(functions.account.UpdateProfileRequest(first_name=(actual.first_name or "")[:64], last_name=(actual.last_name or "")[:64], about=about))
    photo = await context.event.client.download_profile_photo(target, file=bytes)
    if photo and len(photo) <= MAX_AVATAR_BYTES:
        await set_avatar(context.event.client, photo)
    await context.delete()


@command(name="unclone", aliases=["cloneoff"], category="Профиль", description="Вернуть профиль до .clone.", usage=".unclone")
async def unclone(context: object) -> None:
    backup = await context.services.settings.get(context.user_id, "profile_backup")
    if not backup:
        await context.edit("⚠️ Нет сохранённого профиля."); return
    await context.event.client(functions.account.UpdateProfileRequest(first_name=backup["first_name"], last_name=backup["last_name"], about=backup["about"]))
    raw = base64.b64decode(backup["photo"]) if backup.get("photo") else None
    await set_avatar(context.event.client, raw)
    await context.services.settings.set(context.user_id, "profile_backup", {})
    await context.delete()

@command(name="name", category="Профиль", description="Изменить своё имя.", usage=".name First [Last]")
async def name(context: object) -> None:
    if not context.args: await context.edit("⚠️ Укажи имя."); return
    await context.event.client(functions.account.UpdateProfileRequest(first_name=context.args[0][:64], last_name=" ".join(context.args[1:])[:64]))
    await context.delete()

@command(name="bio", category="Профиль", description="Изменить описание профиля.", usage=".bio <text>")
async def bio(context: object) -> None:
    text = context.raw_args.strip()
    if not text:
        await context.edit("⚠️ .bio текст"); return
    await context.event.client(functions.account.UpdateProfileRequest(about=text[:70]))
    await context.edit("✅ bio обновлено")
