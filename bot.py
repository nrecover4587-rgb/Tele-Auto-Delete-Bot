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
bot = Client(
    "AutoDeleteBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

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
# 🔥 START COMMAND
# ------------------------
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if not await check_force_sub(user_id):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]]
        return await message.reply("🔒 Join channel to use bot", reply_markup=InlineKeyboardMarkup(btn))

    buttons = [
        [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
        [
            InlineKeyboardButton("⚙️ Commands", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ],
        [
            InlineKeyboardButton("👨‍💻 Owner", user_id=OWNER_ID),
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]
    ]

    await message.reply_text(
        f"✨ Hello {name}!\n\n🤖 Auto Delete Bot Ready!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ------------------------
# 🔥 CALLBACKS
# ------------------------
@bot.on_callback_query()
async def callback(_, query: CallbackQuery):

    if query.data == "help":
        await query.message.edit_text(
            "⚙️ Commands:\n\n"
            "/set_text 60\n"
            "/set_media 60\n"
            "/status\n"
            "/disable",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    elif query.data == "about":
        await query.message.edit_text(
            "ℹ️ Auto Delete Bot\n\nClean your group automatically!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    elif query.data == "back":
        await query.message.edit_text("🔙 Back to menu")

# ------------------------
# 🔥 SET TEXT TIME
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
# 🔥 SET MEDIA TIME
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

    await message.reply(f"Text: {group.get('text_time')} | Media: {group.get('media_time')}")

# ------------------------
# 🔥 DISABLE
# ------------------------
@bot.on_message(filters.command("disable") & filters.group)
async def disable(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    await groups.delete_one({"group_id": message.chat.id})
    await message.reply("✅ Disabled")

# ------------------------
# 🔥 AUTO DELETE
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
# 🔥 RUN BOT (HEROKU SAFE)
# ------------------------
async def main():
    await bot.start()
    print("🔥 Bot Started")
    await asyncio.Event().wait()

async def shutdown():
    print("🛑 Stopping Bot...")
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    loop.run_until_complete(main())
