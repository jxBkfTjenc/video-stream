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


from driver.core import me_bot, me_user
from driver.queues import QUEUE
from driver.decorators import check_blacklist
from program.utils.inline import menu_markup, stream_markup

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    BOT_USERNAME,
    GROUP_SUPPORT,
    OWNER_USERNAME,
    UPDATES_CHANNEL,
    SUDO_USERS,
    OWNER_ID,
)


@Client.on_callback_query(filters.regex("home_start"))
@check_blacklist()
async def start_set(_, query: CallbackQuery):
    await query.answer("home start")
    await query.edit_message_text(
        f"""Hai [{query.message.chat.first_name}](tg://user?id={query.message.chat.id}) 👋🏻\n
💭 [{me_bot.first_name}](https://t.me/{me_bot.username}) adalah bot untuk memutar musik dan video dalam grup, melalui obrolan video Telegram.
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕ Tambahkan saya ke Grup ➕", url=f"https://t.me/{me_bot.username}?startgroup=true")
                ],[
                    InlineKeyboardButton("📚 CMD", callback_data="command_list"),
                    InlineKeyboardButton("❓ Panduan", callback_data="user_guide")
                ],[
                    InlineKeyboardButton("👥 Group", url=f"https://t.me/{GROUP_SUPPORT}"),
                    InlineKeyboardButton("📣 Channel", url=f"https://t.me/{UPDATES_CHANNEL}")
                ],
            ]
        ),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex("quick_use"))
@check_blacklist()
async def quick_set(_, query: CallbackQuery):
    await query.answer("quick bot usage")
    await query.edit_message_text(
        f"""ℹ️ Panduan penggunaan bot, harap baca sepenuhnya !

👩🏻‍💼 » /play - Ketik ini dengan memberikan judul lagu atau tautan youtube atau file audio untuk memutar Musik. (Ingat untuk tidak memutar live streaming YouTube dengan menggunakan perintah ini!, karena akan menyebabkan ERROR yang tidak terduga.)

👩🏻‍💼 » /vplay - Ketik ini dengan memberikan judul lagu atau link youtube atau file video untuk memutar Video. (Ingat untuk tidak memutar video langsung YouTube dengan menggunakan perintah ini!, karena akan menyebabkan ERROR yang tidak terduga.)

👩🏻‍💼 » /vstream - Ketik ini dengan memberikan tautan video streaming langsung YouTube atau tautan m3u8 untuk memutar Video langsung. (Ingat untuk tidak memutar file audio/video lokal atau video YouTube non-live dengan menggunakan perintah ini!, karena akan menyebabkan ERROR yang tidak terduga.)

❓ Ada pertanyaan? Hubungi kami di [Support Group](https://t.me/{GROUP_SUPPORT}).""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Kembali", callback_data="user_guide")]]
        ),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex("user_guide"))
@check_blacklist()
async def guide_set(_, query: CallbackQuery):
    await query.answer("user guide")
    await query.edit_message_text(
        f"""❓ Bagaimana cara menggunakan Bot ini?, baca Panduan di bawah ini !

1.) Pertama, tambahkan bot ini ke Grup Anda.
2.) Kemudian, jadikan bot ini sebagai administrator di Grup juga berikan semua izin kecuali admin Anonim.
3.) Setelah bot ini dijadikan admin, ketik /reload di Grup untuk memperbarui data admin.
3.) Undang @{me_user.username} ke grup Anda atau ketik /userbotjoin untuk mengundangnya, tetapi dengan mengetik `/play (judul lagu)` atau `/vplay (judul lagu)` assistant biasanya juga otomatis bergabung dengan sendirinya.
4.) Nyalakan /Mulai obrolan video terlebih dahulu sebelum memulai memutar video/musik.

📌 Jika assistant bot tidak bergabung ke obrolan video, pastikan obrolan video sudah diaktifkan dan assistant bot ada di obrolan.

💡 Jika Anda memiliki pertanyaan lanjutan tentang bot ini, Anda dapat menceritakannya di obrolan dukungan saya di sini: @{GROUP_SUPPORT}.""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("» Panduan penggunaan cepat «", callback_data="quick_use")
                ],[
                    InlineKeyboardButton("🔙 Kembali", callback_data="home_start")
                ],
            ]
        ),
    )


@Client.on_callback_query(filters.regex("command_list"))
@check_blacklist()
async def commands_set(_, query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer("commands menu")
    await query.edit_message_text(
        f"""✨ **Hallo [{query.message.chat.first_name}](tg://user?id={query.message.chat.id}) !**

» Lihat menu di bawah ini untuk membaca informasi modul & melihat daftar Perintah yang tersedia !

Semua perintah dapat digunakan dengan (`! / .`) """,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👮🏻‍♀️ Admins", callback_data="admin_command"),
                ],[
                    InlineKeyboardButton("👩🏻‍💼 semua pengguna", callback_data="user_command"),
                ],[
                    InlineKeyboardButton("Sudo", callback_data="sudo_command"),
                    InlineKeyboardButton("Owner", callback_data="owner_command"),
                ],[
                    InlineKeyboardButton("🔙 Kembali", callback_data="home_start")
                ],
            ]
        ),
    )


@Client.on_callback_query(filters.regex("user_command"))
@check_blacklist()
async def user_set(_, query: CallbackQuery):
    await query.answer("Perintah Untuk Semua Pengguna")
    await query.edit_message_text(
        f"""✏️ Daftar perintah untuk semua pengguna.

» /play (nama lagu/link youtube) - memutar musik dari youtube
» /stream (m3u8/youtube link live stream) - putar musik streaming langsung youtube/m3u8
» /vplay (nama video/link youtube) - memutar video dari youtube
» /vstream (m3u8/youtube link live stream) - putar video streaming langsung youtube/m3u8
» /playlist - melihat daftar antrian lagu dan lagu yang sedang diputar
» /lyric (nama lagu) - mencari lirik lagu berdasarkan nama lagu
» /video (nama lagu / judul video) - unduh video dari youtube
» /song (nama lagu) - download lagu dari youtube
» /search (query) - cari link video youtube
» /ping - tampilkan status bot ping
» /uptime - tampilkan status uptime bot
» /alive - tampilkan info bot hidup (hanya di Grup)""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Kembali", callback_data="command_list")]]
        ),
    )


@Client.on_callback_query(filters.regex("admin_command"))
@check_blacklist()
async def admin_set(_, query: CallbackQuery):
    await query.answer("Perintah Untuk Admin")
    await query.edit_message_text(
        f"""✏️ Daftar perintah untuk admin grup.

» /pause - menjeda trek yang sedang diputar
» /resume - mainkan trek yang sebelumnya dijeda
» /skip - pergi ke trek berikutnya
» /stop - hentikan pemutaran trek dan bersihkan antrian
» /vmute - bisukan assistant bot streamer pada panggilan grup
» /vunmute - mengaktifkan suara assistant bot streamer pada panggilan grup
» /volume `1-200` - mengatur volume musik (assistant bot harus admin)
» /reload - reload bot dan refresh data admin
» /userbotjoin - undang assistant bot untuk bergabung dengan grup
» /userbotleave - perintahkan assistant bot keluar dari grup
» /startvc - memulai/memulai ulang panggilan grup
» /stopvc - hentikan/buang panggilan grup""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Kembali", callback_data="command_list")]]
        ),
    )


@Client.on_callback_query(filters.regex("sudo_command"))
@check_blacklist()
async def sudo_set(_, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in SUDO_USERS:
        await query.answer("⚠️ Anda tidak memiliki izin untuk mengklik tombol ini\n\n» Tombol ini disediakan untuk anggota sudo bot ini.", show_alert=True)
        return
    await query.answer("sudo commands")
    await query.edit_message_text(
        f"""✏️ Daftar perintah untuk pengguna sudo.

» /stats - dapatkan statistik bot saat ini
» /calls - menampilkan daftar semua panggilan grup yang aktif di database
» /block (`chat_id`) - gunakan ini untuk memasukan daftar block grup mana pun agar tidak menggunakan bot Anda
» /unblock (`chat_id`) - gunakan ini untuk menghapus grup dari daftar block agar bisa menggunakan bot Anda
» /blocklist - menampilkan daftar semua grup yang masuk daftar block
» /speedtest - jalankan speedtest server bot
» /sysinfo - tampilkan informasi sistem
» /logs - buat log bot saat ini
» /eval - menjalankan kode
» /sh - menjalankan kode""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Kembali", callback_data="command_list")]]
        ),
    )


@Client.on_callback_query(filters.regex("owner_command"))
@check_blacklist()
async def owner_set(_, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in OWNER_ID:
        await query.answer("⚠️ Anda tidak memiliki izin untuk mengklik tombol ini\n\n» Tombol ini disediakan untuk pemilik bot ini.", show_alert=True)
        return
    await query.answer("owner commands")
    await query.edit_message_text(
        f"""✏️ Daftar perintah untuk pemilik bot.

» /gban (`username` atau `user_id`) - untuk orang yang diblokir secara global, hanya dapat digunakan dalam grup
» /ungban (`username` atau `user_id`) - untuk orang yang dilarang secara global, hanya dapat digunakan dalam grup
» /update - perbarui bot Anda ke versi terbaru
» /restart - restart server bot Anda
» /leaveall - perintahkan assistant bot keluar dari semua grup
» /leavebot (`chat id`) - perintahkan bot untuk keluar dari grup yang Anda tentukan
» /broadcast (`pesan`) - mengirim pesan broadcast ke semua grup di database bot
» /broadcast_pin (`pesan`) - mengirim pesan siaran ke semua grup di database bot dengan pin obrolan""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Kembali", callback_data="command_list")]]
        ),
    )


@Client.on_callback_query(filters.regex("stream_menu_panel"))
@check_blacklist()
async def at_set_markup_menu(_, query: CallbackQuery):
    user_id = query.from_user.id
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Hanya admin dengan izin mengelola obrolan video yang dapat mengetuk tombol ini !", show_alert=True)
    chat_id = query.message.chat.id
    user_id = query.message.from_user.id
    buttons = menu_markup(user_id)
    if chat_id in QUEUE:
        await query.answer("control panel opened")
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.answer("❌ tidak ada yang sedang streaming", show_alert=True)


@Client.on_callback_query(filters.regex("stream_home_panel"))
@check_blacklist()
async def is_set_home_menu(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Hanya admin dengan izin mengelola obrolan video yang dapat mengetuk tombol ini !", show_alert=True)
    await query.answer("control panel closed")
    user_id = query.message.from_user.id
    buttons = stream_markup(user_id)
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("set_close"))
@check_blacklist()
async def on_close_menu(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Hanya admin dengan izin mengelola obrolan video yang dapat mengetuk tombol ini !", show_alert=True)
    await query.message.delete()


@Client.on_callback_query(filters.regex("close_panel"))
@check_blacklist()
async def in_close_panel(_, query: CallbackQuery):
    await query.message.delete()
