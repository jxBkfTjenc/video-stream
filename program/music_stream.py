"""
Video + Music Stream Telegram Bot
Copyright (c) 2022-present levina=lab <https://github.com/levina-lab>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but without any warranty; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/licenses.html>
"""


import re
import asyncio

from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, Message

from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
from pytgcalls.exceptions import NoAudioSourceFound, NoActiveGroupCall, GroupCallNotFound

from program import LOGS
from program.utils.inline import stream_markup
from driver.design.thumbnail import thumb
from driver.design.chatname import CHAT_TITLE
from driver.filters import command, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.core import calls, user, me_user
from driver.utils import bash, remove_if_exists, from_tg_get_msg
from driver.database.dbqueue import add_active_chat, remove_active_chat, music_on
from driver.decorators import require_admin, check_blacklist

from config import BOT_USERNAME, IMG_1, IMG_2, IMG_5
from asyncio.exceptions import TimeoutError
from youtubesearchpython import VideosSearch


def ytsearch(query: str):
    try:
        search = VideosSearch(query, limit=1).result()
        data = search["result"][0]
        songname = data["title"]
        url = data["link"]
        duration = data["duration"]
        thumbnail = data["thumbnails"][0]["url"]
        return [songname, url, duration, thumbnail]
    except Exception as e:
        print(e)
        return 0

async def ytdl(link: str):
    stdout, stderr = await bash(
        f'yt-dlp --geo-bypass -g -f "[height<=?720][width<=?1280]" {link}'
    )
    if stdout:
        return 1, stdout
    return 0, stderr

def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


async def play_tg_file(c: Client, m: Message, replied: Message = None, link: str = None):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if link:
        try:
            replied = await from_tg_get_msg(link)
        except Exception as e:
            LOGS.info(e)
            return await m.reply_text(f"🚫 error:\n\n» {e}")
    if not replied:
        return await m.reply(
            "» balas ke **file audio** atau **berikan sesuatu untuk mencari.**"
        )
    if replied.audio or replied.voice:
        if not link:
            suhu = await replied.reply("📥 download audio...")
        else:
            suhu = await m.reply("📥 download audio...")
        dl = await replied.download()
        link = replied.link
        songname = "music"
        thumbnail = f"{IMG_5}"
        duration = "00:00"
        try:
            if replied.audio:
                if replied.audio.title:
                    songname = replied.audio.title[:80]
                else:
                    songname = replied.audio.file_name[:80]
                if replied.audio.thumbs:
                    if not link:
                        thumbnail = await c.download_media(replied.audio.thumbs[0].file_id)
                    else:
                        thumbnail = await user.download_media(replied.audio.thumbs[0].file_id)
                duration = convert_seconds(replied.audio.duration)
            elif replied.voice:
                songname = "voice note"
                duration = convert_seconds(replied.voice.duration)
        except BaseException:
            pass

        if not thumbnail:
            thumbnail = f"{IMG_5}"

        if chat_id in QUEUE:
            await suhu.edit("🔄 Antrian musik...")
            gcname = m.chat.title
            ctitle = await CHAT_TITLE(gcname)
            title = songname
            userid = m.from_user.id
            image = await thumb(thumbnail, title, userid, ctitle)
            pos = add_to_queue(chat_id, songname, dl, link, "music", 0)
            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
            buttons = stream_markup(user_id)
            await suhu.delete()
            await m.reply_photo(
                photo=image,
                reply_markup=InlineKeyboardMarkup(buttons),
                caption=f"💡 **Musik ditambahkan ke antrean »** `{pos}`\n\n"
                        f"🗂 **Nama:** [{songname}]({link}) | `musik`\n"
                        f"⏱️ **Durasi:** `{duration}`\n"
                        f"🧸 **Request dari:** {requester}",
            )
            remove_if_exists(image)
        else:
            try:
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                title = songname
                userid = m.from_user.id
                image = await thumb(thumbnail, title, userid, ctitle)
                await suhu.edit("🔄 Bergabung dengan Obrolan Suara Grup...")
                await music_on(chat_id)
                await add_active_chat(chat_id)
                await calls.join_group_call(
                    chat_id,
                    AudioPiped(
                        dl,
                        HighQualityAudio(),
                    ),
                    stream_type=StreamType().pulse_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "music", 0)
                await suhu.delete()
                buttons = stream_markup(user_id)
                requester = (
                    f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                )
                await m.reply_photo(
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"🗂 **Nama:** [{songname}]({link}) | `musik`\n"
                            f"⏱️ **Durasi:** `{duration}`\n"
                            f"🧸 **Request dari:** {requester}",
                )
                remove_if_exists(image)
            except (NoActiveGroupCall, GroupCallNotFound):
                await suhu.delete()
                await remove_active_chat(chat_id)
                await m.reply_text("❌ Bot tidak dapat menemukan obrolan suara Grup atau tidak aktif.\n\n» Gunakan perintah /startvc untuk mengaktifkan obrolan suara Grup !")
            except Exception as e:
                LOGS.info(e)
    else:
        await m.reply_text(
            "» balas ke **file audio** atau **berikan sesuatu untuk mencari.**"
        )


@Client.on_message(command(["play", f"play@{BOT_USERNAME}"]) & other_filters)
@check_blacklist()
@require_admin(permissions=["can_manage_voice_chats", "can_delete_messages", "can_invite_users"], self=True)
async def audio_stream(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text(
            "Anda adalah pengguna __Anonymous__ !\n\n» kembali ke akun pengguna asli Anda untuk menggunakan bot ini."
        )
    try:
        ubot = me_user.id
        b = await c.get_chat_member(chat_id, ubot)
        if b.status == "banned":
            try:
                await m.reply_text("❌ Assistant bot di banned dalam grup ini, unban Assistant bot terlebih dahulu untuk dapat memutar musik !")
                await remove_active_chat(chat_id)
            except BaseException:
                pass
            invitelink = (await c.get_chat(chat_id)).invite_link
            if not invitelink:
                await c.export_chat_invite_link(chat_id)
                invitelink = (await c.get_chat(chat_id)).invite_link
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
            await remove_active_chat(chat_id)
    except UserNotParticipant:
        try:
            invitelink = (await c.get_chat(chat_id)).invite_link
            if not invitelink:
                await c.export_chat_invite_link(chat_id)
                invitelink = (await c.get_chat(chat_id)).invite_link
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
            await remove_active_chat(chat_id)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            LOGS.info(e)
            return await m.reply_text(
                f"❌ **Assistant bot gagal bergabung**\n\n**reason**: `{e}`"
            )
    if replied:
        if replied.audio or replied.voice:
            await play_tg_file(c, m, replied)
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» balas ke **file audio** atau **berikan sesuatu untuk mencari.**"
                )
            else:
                suhu = await c.send_message(chat_id, "🔍 **Loading...**")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                if search == 0:
                    await suhu.edit("❌ **Tidak ada hasil yang ditemukan**")
                else:
                    songname = search[0]
                    title = search[0]
                    url = search[1]
                    duration = search[2]
                    thumbnail = search[3]
                    userid = m.from_user.id
                    gcname = m.chat.title
                    ctitle = await CHAT_TITLE(gcname)
                    image = await thumb(thumbnail, title, userid, ctitle)
                    out, ytlink = await ytdl(url)
                    if out == 0:
                        await suhu.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            await suhu.edit("🔄 Antrian Musik...")
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "music", 0
                            )
                            await suhu.delete()
                            buttons = stream_markup(user_id)
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=image,
                                reply_markup=InlineKeyboardMarkup(buttons),
                                caption=f"💡 **Musik ditambahkan ke antrean »** `{pos}`\n\n🗂 **Nama:** [{songname}]({url}) | `musik`\n**⏱ Durasi:** `{duration}`\n🧸 **Request dari:** {requester}",
                            )
                            remove_if_exists(image)
                        else:
                            try:
                                await suhu.edit("🔄 Bergabung dengan Obrolan Suara Grup...")
                                await music_on(chat_id)
                                await add_active_chat(chat_id)
                                await calls.join_group_call(
                                    chat_id,
                                    AudioPiped(
                                        ytlink,
                                        HighQualityAudio(),
                                    ),
                                    stream_type=StreamType().local_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "music", 0)
                                await suhu.delete()
                                buttons = stream_markup(user_id)
                                requester = (
                                    f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                )
                                await m.reply_photo(
                                    photo=image,
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    caption=f"🗂 **Nama:** [{songname}]({url}) | `musik`\n**⏱ Durasi:** `{duration}`\n🧸 **Request dari:** {requester}",
                                )
                                remove_if_exists(image)
                            except (NoActiveGroupCall, GroupCallNotFound):
                                await suhu.delete()
                                await remove_active_chat(chat_id)
                                await m.reply_text("❌ Bot tidak dapat menemukan Obrolan Suara Grup atau tidak aktif.\n\n» Gunakan perintah /startvc untuk mengaktifkan Obrolan Suara Grup !")
                            except NoAudioSourceFound:
                                await suhu.delete()
                                await remove_active_chat(chat_id)
                                await m.reply_text("❌ Konten yang Anda sediakan untuk diputar tidak memiliki sumber audio")
    else:
        if len(m.command) < 2:
            await m.reply(
                "» balas ke **file audio** atau **berikan sesuatu untuk mencari.**"
            )
        elif "t.me" in m.command[1]:
            for i in m.command[1:]:
                if "t.me" in i:
                    await play_tg_file(c, m, link=i)
                continue
        else:
            suhu = await c.send_message(chat_id, "🔍 **Loading...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            if search == 0:
                await suhu.edit("❌ **Tidak ada hasil yang ditemukan**")
            else:
                songname = search[0]
                title = search[0]
                url = search[1]
                duration = search[2]
                thumbnail = search[3]
                userid = m.from_user.id
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                image = await thumb(thumbnail, title, userid, ctitle)
                veez, ytlink = await ytdl(url)
                if veez == 0:
                    await suhu.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        await suhu.edit("🔄 Antrian Musik...")
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Music", 0)
                        await suhu.delete()
                        requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        buttons = stream_markup(user_id)
                        await m.reply_photo(
                            photo=image,
                            reply_markup=InlineKeyboardMarkup(buttons),
                            caption=f"💡 **Musik ditambahkan ke antrean »** `{pos}`\n\n🗂 **Nama:** [{songname}]({url}) | `musik`\n**⏱ Durasi:** `{duration}`\n🧸 **Request dari:** {requester}",
                        )
                        remove_if_exists(image)
                    else:
                        try:
                            await suhu.edit("🔄 Bergabung dengan Obrolan Suara Grup...")
                            await music_on(chat_id)
                            await add_active_chat(chat_id)
                            await calls.join_group_call(
                                chat_id,
                                AudioPiped(
                                    ytlink,
                                    HighQualityAudio(),
                                ),
                                stream_type=StreamType().local_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "music", 0)
                            await suhu.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            buttons = stream_markup(user_id)
                            await m.reply_photo(
                                photo=image,
                                reply_markup=InlineKeyboardMarkup(buttons),
                                caption=f"🗂 **Nama:** [{songname}]({url}) | `musik`\n**⏱ Duration:** `{duration}`\n🧸 **Request dari:** {requester}",
                            )
                            remove_if_exists(image)
                        except (NoActiveGroupCall, GroupCallNotFound):
                            await suhu.delete()
                            await remove_active_chat(chat_id)
                            await m.reply_text("❌ Bot tidak dapat menemukan Obrolan Suara Grup atau tidak aktif.\n\n» Gunakan perintah /startvc untuk mengaktifkan Obrolan Suara Grup !")
                        except NoAudioSourceFound:
                            await suhu.delete()
                            await remove_active_chat(chat_id)
                            await m.reply_text("❌ Konten yang Anda sediakan untuk diputar tidak memiliki sumber audio.\n\n» Coba putar lagu lain atau coba lagi nanti !")


@Client.on_message(command(["stream", f"stream@{BOT_USERNAME}"]) & other_filters)
@check_blacklist()
@require_admin(permissions=["can_manage_voice_chats", "can_delete_messages", "can_invite_users"], self=True)
async def live_music_stream(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text(
            "Anda adalah pengguna __Anonymous__ !\n\n» kembali ke akun pengguna asli Anda untuk menggunakan bot ini."
        )
    try:
        ubot = me_user.id
        b = await c.get_chat_member(chat_id, ubot)
        if b.status == "banned":
            try:
                await m.reply_text("❌ Assistant bot di banned dalam grup ini, unban Assistant bot terlebih dahulu untuk dapat memutar musik !")
                await remove_active_chat(chat_id)
            except BaseException:
                pass
            invitelink = (await c.get_chat(chat_id)).invite_link
            if not invitelink:
                await c.export_chat_invite_link(chat_id)
                invitelink = (await c.get_chat(chat_id)).invite_link
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
            await remove_active_chat(chat_id)
    except UserNotParticipant:
        try:
            invitelink = (await c.get_chat(chat_id)).invite_link
            if not invitelink:
                await c.export_chat_invite_link(chat_id)
                invitelink = (await c.get_chat(chat_id)).invite_link
            if invitelink.startswith("https://t.me/+"):
                invitelink = invitelink.replace(
                    "https://t.me/+", "https://t.me/joinchat/"
                )
            await user.join_chat(invitelink)
            await remove_active_chat(chat_id)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            LOGS.info(e)
            return await m.reply_text(
                f"❌ **Assistant bot gagal bergabung**\n\n**reason**: `{e}`"
            )
    if len(m.command) < 2:
        await m.reply_text("» Beri saya url langsung youtube/url m3u8 untuk streaming.")
    else:
        url = m.text.split(None, 1)[1]
        msg = await m.reply_text("🔍 **Loading...**")
        regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
        match = re.match(regex, url)
        if match:
            coda, data = await ytdl(url)
        else:
            data = url
            coda = 1
        if coda == 0:
            await msg.edit_text(f"❌ yt-dl issues detected\n\n» `{data}`")
        else:
            if "m3u8" in url:
                if chat_id in QUEUE:
                    await msg.edit_text("🔄 Antrian Musik...")
                    pos = add_to_queue(chat_id, "m3u8 audio", data, url, "music", 0)
                    await msg.delete()
                    requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=f"{IMG_1}",
                        reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"💡 **Musik ditambahkan ke antrean »** `{pos}`\n\n🗂 **Nama:** [m3u8 audio stream]({url}) | `live`\n🧸 **Request dari:** {requester}",
                    )
                else:
                    try:
                        await msg.edit_text("🔄 Bergabung dengan Obrolan Suara Grup...")
                        await music_on(chat_id)
                        await add_active_chat(chat_id)
                        await calls.join_group_call(
                            chat_id,
                            AudioPiped(
                                data,
                                HighQualityAudio(),
                            ),
                            stream_type=StreamType().live_stream,
                        )
                        add_to_queue(chat_id, "m3u8 audio", data, url, "music", 0)
                        await msg.delete()
                        requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        buttons = stream_markup(user_id)
                        await m.reply_photo(
                            photo=f"{IMG_2}",
                            reply_markup=InlineKeyboardMarkup(buttons),
                            caption=f"🗂 **Nama:** [m3u8 audio stream]({url}) | `live`\n🧸 **Request dari:** {requester}",
                        )
                    except (NoActiveGroupCall, GroupCallNotFound):
                        await msg.delete()
                        await remove_active_chat(chat_id)
                        await m.reply_text("❌ Bot tidak dapat menemukan Obrolan Suara Grup atau tidak aktif.\n\n» Gunakan perintah /startvc untuk mengaktifkan Obrolan Suara Grup !")
                    except NoAudioSourceFound:
                        await msg.delete()
                        await remove_active_chat(chat_id)
                        await m.reply_text("❌ Konten yang Anda sediakan untuk diputar tidak memiliki sumber audio")
            else:
                search = ytsearch(url)
                title = search[0]
                songname = search[0]
                thumbnail = search[3]
                userid = m.from_user.id
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                image = await thumb(thumbnail, title, userid, ctitle)
                if chat_id in QUEUE:
                    await msg.edit_text("🔄 Antrian Musik...")
                    pos = add_to_queue(chat_id, songname, data, url, "music", 0)
                    await msg.delete()
                    requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=image,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"💡 **Musik ditambahkan ke antrean »** `{pos}`\n\n🗂 **Nama:** [{songname}]({url}) | `live`\n🧸 **Request dari:** {requester}",
                    )
                    remove_if_exists(image)
                else:
                    try:
                        await msg.edit_text("🔄 Bergabung dengan Obrolan Suara Grup...")
                        await music_on(chat_id)
                        await add_active_chat(chat_id)
                        await calls.join_group_call(
                            chat_id,
                            AudioPiped(
                                data,
                                HighQualityAudio(),
                            ),
                            stream_type=StreamType().live_stream,
                        )
                        add_to_queue(chat_id, songname, data, url, "music", 0)
                        await msg.delete()
                        requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        buttons = stream_markup(user_id)
                        await m.reply_photo(
                            photo=image,
                            reply_markup=InlineKeyboardMarkup(buttons),
                            caption=f"🗂 **Nama:** [{songname}]({url}) | `live`\n🧸 **Request dari:** {requester}",
                        )
                        remove_if_exists(image)
                    except (NoActiveGroupCall, GroupCallNotFound):
                        await msg.delete()
                        await remove_active_chat(chat_id)
                        await m.reply_text("❌ Bot tidak dapat menemukan Obrolan Suara Grup atau tidak aktif.\n\n» Gunakan perintah /startvc untuk mengaktifkan Obrolan Suara Grup !")
                    except NoAudioSourceFound:
                        await msg.delete()
                        await remove_active_chat(chat_id)
                        await m.reply_text("❌ Konten yang Anda sediakan untuk diputar tidak memiliki sumber audio")
                    except TimeoutError:
                        await msg.delete()
                        await remove_active_chat(chat_id)
                        await m.reply_text("Proses dibatalkan, silakan coba lagi nanti atau gunakan perintah `/vstream` untuk streaming dalam audio saja.")
