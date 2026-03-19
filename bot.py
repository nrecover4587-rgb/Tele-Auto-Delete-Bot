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
# ADMIN CHECK
# ------------------------
async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

# ------------------------
# FORCE SUB
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
# MAIN MENU
# ------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}"),
            InlineKeyboardButton("💬 Update Group", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ],
        [
            InlineKeyboardButton("❓ Help & Commands", callback_data="help")
        ],
        [
            InlineKeyboardButton("➕ Add me to Your Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")
        ]
    ])

# ------------------------
# HELP MENU
# ------------------------
def help_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Set Text", callback_data="set_text"),
            InlineKeyboardButton("📁 Set Media", callback_data="set_media")
        ],
        [
            InlineKeyboardButton("🧠 Edit ON", callback_data="edit_on"),
            InlineKeyboardButton("❌ Edit OFF", callback_data="edit_off")
        ],
        [
            InlineKeyboardButton("🔗 Bio ON", callback_data="bio_on"),
            InlineKeyboardButton("🚫 Bio OFF", callback_data="bio_off")
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("⚠️ Disable", callback_data="disable")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back")
        ]
    ])

# ------------------------
# START (FIXED)
# ------------------------
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    # ✅ Force sub with button
    if not await check_force_sub(user_id):
        return await message.reply_text(
            "🔒 Please join our channel first to use the bot",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
            ])
        )

    caption = (
        f"🛡 Hello {name}!\n"
        "I'm Auto Delete Bot 🤖\n\n"
        "Keeps your group clean & safe.\n\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ Made by MistuBots\n"
        f"📢 https://t.me/{FORCE_SUB_CHANNEL}"
    )

    await message.reply_photo(
        photo="https://files.catbox.moe/vp4s7x.jpg",
        caption=caption,
        has_spoiler=True,
        reply_markup=main_menu()
    )

# ------------------------
# CALLBACKS
# ------------------------
@bot.on_callback_query()
async def callback(_, query: CallbackQuery):
    data = query.data

    if data == "help":
        await query.message.edit_text(
            "📚 Bot Commands Help\n\nSelect any option below:",
            reply_markup=help_menu()
        )

    elif data == "back":
        await query.message.edit_text(
            "🔙 Main Menu",
            reply_markup=main_menu()
        )

    else:
        texts = {
            "set_text": "📝 /set_text 60\nSet text delete time",
            "set_media": "📁 /set_media 60\nSet media delete time",
            "edit_on": "🧠 /edit_on\nEnable edit protection",
            "edit_off": "❌ /edit_off\nDisable edit protection",
            "bio_on": "🔗 /bio_on\nEnable bio guard",
            "bio_off": "🚫 /bio_off\nDisable bio guard",
            "status": "📊 /status\nCheck settings",
            "disable": "⚠️ /disable\nDisable system"
        }

        if data in texts:
            await query.message.edit_text(
                texts[data],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="help")]
                ])
            )

# ------------------------
# BIO ON/OFF
# ------------------------
@bot.on_message(filters.command("bio_on") & filters.group)
async def bio_on(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()
    await groups.update_one({"group_id": message.chat.id}, {"$set": {"bio_guard": True}}, upsert=True)
    await message.reply("✅ Bio Guard ON")

@bot.on_message(filters.command("bio_off") & filters.group)
async def bio_off(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()
    await groups.update_one({"group_id": message.chat.id}, {"$set": {"bio_guard": False}}, upsert=True)
    await message.reply("❌ Bio Guard OFF")

# ------------------------
# AUTO DELETE + BIO CHECK
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

            if "http" in bio or "t.me" in bio or "@" in bio:
                await message.delete()
                return
    except:
        pass

# ------------------------
# RUN (HEROKU FIX)
# ------------------------
async def main():
    await bot.start()
    print("🔥 Bot Started")

    stop_event = asyncio.Event()

    def shutdown():
        print("🛑 Shutting down...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, shutdown)
    loop.add_signal_handler(signal.SIGINT, shutdown)

    await stop_event.wait()
    await bot.stop()
    print("✅ Bot Stopped")

if __name__ == "__main__":
    asyncio.run(main())
