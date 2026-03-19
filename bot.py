import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME, FORCE_SUB_CHANNEL

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
        return member.status in ["member", "administrator", "creator"]
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
            InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
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
# START
# ------------------------
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if not await check_force_sub(user_id):
        return await message.reply_text(
            "🔒 Please join our channel first",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
            ])
        )

    caption = (
        f"🛡 Hello {name}!\n\n"
        "🤖 Auto Delete Bot\n"
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
async def callback(client, query: CallbackQuery):
    data = query.data

    if data == "help":
        await query.message.edit_text(
            "📚 Bot Commands Help\n\nSelect any option below:",
            reply_markup=help_menu()
        )

    elif data == "back":
        await query.message.edit_text("🔙 Main Menu", reply_markup=main_menu())

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
# COMMANDS
# ------------------------
@bot.on_message(filters.command("set_text") & filters.group)
async def set_text(client, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    if len(message.command) < 2:
        return await message.reply("Usage: /set_text 60")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"text_time": int(message.command[1])}},
        upsert=True
    )
    await message.reply("✅ Text delete set")

@bot.on_message(filters.command("set_media") & filters.group)
async def set_media(client, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    if len(message.command) < 2:
        return await message.reply("Usage: /set_media 60")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"media_time": int(message.command[1])}},
        upsert=True
    )
    await message.reply("✅ Media delete set")

@bot.on_message(filters.command("bio_on") & filters.group)
async def bio_on(client, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    await groups.update_one({"group_id": message.chat.id}, {"$set": {"bio_guard": True}}, upsert=True)
    await message.reply("✅ Bio Guard ON")

@bot.on_message(filters.command("bio_off") & filters.group)
async def bio_off(client, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    await groups.update_one({"group_id": message.chat.id}, {"$set": {"bio_guard": False}}, upsert=True)
    await message.reply("❌ Bio Guard OFF")

# ------------------------
# AUTO DELETE + BIO CHECK
# ------------------------
@bot.on_message(filters.group & ~filters.service)
async def auto_delete(client, message):
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

            if "http" in bio or "@" in bio:
                await message.delete()
                return

        if message.text and group.get("text_time"):
            await asyncio.sleep(group["text_time"])
            await message.delete()

        elif (message.photo or message.video or message.document) and group.get("media_time"):
            await asyncio.sleep(group["media_time"])
            await message.delete()

    except:
        pass

# ------------------------
# RUN
# ------------------------
bot.run()
