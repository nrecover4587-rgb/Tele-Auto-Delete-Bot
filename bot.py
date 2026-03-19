import asyncio
import signal
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME, FORCE_SUB_CHANNEL, OWNER_ID

# MongoDB
mongo = AsyncIOMotorClient(DATABASE_URL)
db = mongo["databas"]
groups = db["group_id"]

# Bot
bot = Client("AutoDeleteBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------------
# 🔹 Admin Check
# ------------------------
async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

# ------------------------
# 🔹 Force Sub
# ------------------------
async def check_force_sub(user_id):
    try:
        member = await bot.get_chat_member(f"@{FORCE_SUB_CHANNEL}", user_id)
        return member.status in [
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.MEMBER
        ]
    except:
        return False

# ------------------------
# 🔥 MAIN MENU
# ------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
        [
            InlineKeyboardButton("⚙️ Commands", callback_data="help"),
            InlineKeyboardButton("✨ Features", callback_data="features")
        ],
        [
            InlineKeyboardButton("👨‍💻 Owner", user_id=OWNER_ID),
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]
    ])

# ------------------------
# 🔥 START (IMAGE + SPOILER)
# ------------------------
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if not await check_force_sub(user_id):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]]
        return await message.reply_text(
            "🔒 Join channel to use bot",
            reply_markup=InlineKeyboardMarkup(btn)
        )

    text = (
        f"✨ Hey {name}!\n\n"
        "🤖 Auto Delete Bot\n\n"
        "💣 Deletes text & media automatically\n"
        "🧠 Edit protection available\n\n"
        "🚀 Add me to your group!"
    )

    await message.reply_photo(
        photo="https://files.catbox.moe/vp4s7x.jpg",  # 👈 apni image link daal
        caption=text,
        has_spoiler=True,
        reply_markup=main_menu()
    )

# ------------------------
# 🔥 CALLBACKS
# ------------------------
@bot.on_callback_query()
async def callback(_, query: CallbackQuery):

    if query.data == "help":
        await query.message.edit_text(
            "⚙️ Commands Panel\n\n"
            "/set_text 60\n"
            "/set_media 60\n"
            "/edit_on\n"
            "/edit_off\n"
            "/bio_on\n"
            "/bio_off\n"
            "/status\n"
            "/disable",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    elif query.data == "features":
        await query.message.edit_text(
            "✨ Features\n\n"
            "⚡ Auto delete\n"
            "📁 Media + text support\n"
            "🛡 Admin safe\n"
            "🧠 Edit protection\n"
            "🔗 Bio link guard",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    elif query.data == "back":
        await query.message.edit_text(
            "✨ Main Menu\n\nSelect an option below:",
            reply_markup=main_menu()
        )

# ------------------------
# 🔥 BIO ON
# ------------------------
@bot.on_message(filters.command("bio_on") & filters.group)
async def bio_on(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"bio_guard": True}},
        upsert=True
    )

    msg = await message.reply("✅ Bio link guard enabled")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# 🔥 BIO OFF
# ------------------------
@bot.on_message(filters.command("bio_off") & filters.group)
async def bio_off(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"bio_guard": False}},
        upsert=True
    )

    msg = await message.reply("❌ Bio link guard disabled")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# 🔥 SET TEXT
# ------------------------
@bot.on_message(filters.command("set_text") & filters.group)
async def set_text(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply("Usage: /set_text 60")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"text_time": int(message.command[1])}},
        upsert=True
    )

    msg = await message.reply("✅ Text delete set")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# 🔥 SET MEDIA
# ------------------------
@bot.on_message(filters.command("set_media") & filters.group)
async def set_media(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply("Usage: /set_media 60")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"media_time": int(message.command[1])}},
        upsert=True
    )

    msg = await message.reply("✅ Media delete set")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# 🔥 STATUS
# ------------------------
@bot.on_message(filters.command("status") & filters.group)
async def status(_, message):
    group = await groups.find_one({"group_id": message.chat.id})
    if not group:
        return await message.reply("❌ Not configured")

    await message.reply(
        f"📝 Text: {group.get('text_time')}\n"
        f"📁 Media: {group.get('media_time')}\n"
        f"🧠 Edit: {group.get('edit_guard')}\n"
        f"🔗 Bio Guard: {group.get('bio_guard', False)}"
    )

# ------------------------
# 🔥 AUTO DELETE + BIO CHECK
# ------------------------
@bot.on_message(filters.group & ~filters.service)
async def auto_delete(_, message):
    if message.from_user and message.from_user.is_bot:
        return

    group = await groups.find_one({"group_id": message.chat.id})
    if not group:
        return

    if await is_admin(message.chat.id, message.from_user.id):
        return

    try:
        if group.get("bio_guard"):
            user = await bot.get_chat(message.from_user.id)
            bio = (user.bio or "").lower()

            if "http" in bio or "t.me" in bio or "www" in bio or "@" in bio:
                warn = await message.reply("⚠️ Bio me link/username allowed nahi!")
                await message.delete()
                await asyncio.sleep(5)
                await warn.delete()
                return

        if message.text and group.get("text_time"):
            await asyncio.sleep(group["text_time"])
            await message.delete()

        elif (
            message.photo or message.video or message.document or
            message.audio or message.voice or message.sticker
        ) and group.get("media_time"):
            await asyncio.sleep(group["media_time"])
            await message.delete()

    except:
        pass

# ------------------------
# 🔥 RUN BOT
# ------------------------
async def main():
    await bot.start()
    print("🔥 Bot Started")
    await asyncio.Event().wait()

async def shutdown():
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    loop.run_until_complete(main())
