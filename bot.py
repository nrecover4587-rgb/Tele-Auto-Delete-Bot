import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME

# MongoDB
mongo = AsyncIOMotorClient(DATABASE_URL)
db = mongo["databas"]
groups = db["group_id"]

# Bot
bot = Client("AutoDeleteBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------------
# OWNER CONFIG
# ------------------------
OWNER_ID = 7113972959  # 👉 apna Telegram ID daal

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
# MAIN MENU
# ------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Help & Commands", callback_data="help")],
        [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
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
            InlineKeyboardButton("🧠 Edit Guard", callback_data="edit"),
            InlineKeyboardButton("🔗 Bio Guard", callback_data="bio")
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
    name = message.from_user.first_name

    caption = (
        f"🛡 Hello {name}!\n\n"
        "🤖 Auto Delete Bot\n"
        "Keeps your group clean & safe.\n\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ Made by MistuBots"
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

    elif data == "set_text":
        text = "📝 /set_text 60\nSet text delete time"

    elif data == "set_media":
        text = "📁 /set_media 60\nSet media delete time"

    elif data == "edit":
        text = "🧠 /edit\nToggle edit protection ON/OFF"

    elif data == "bio":
        text = "🔗 /bio_on /bio_off\nEnable or disable bio guard"

    else:
        return

    if data not in ["help", "back"]:
        await query.message.edit_text(
            text,
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

# 🔥 EDIT TOGGLE
@bot.on_message(filters.command("edit") & filters.group)
async def edit_toggle(client, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    group = await groups.find_one({"group_id": message.chat.id})
    current = group.get("edit_guard", False) if group else False
    new = not current

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"edit_guard": new}},
        upsert=True
    )

    await message.reply(f"🧠 Edit Guard {'ON ✅' if new else 'OFF ❌'}")

# 🔥 BIO GUARD
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
# AUTO SAVE GROUP
# ------------------------
@bot.on_message(filters.group)
async def save_group(client, message):
    try:
        await groups.update_one(
            {"group_id": message.chat.id},
            {"$set": {"group_id": message.chat.id}},
            upsert=True
        )
    except:
        pass

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
        # BIO GUARD
        if group.get("bio_guard"):
            user = await bot.get_chat(message.from_user.id)
            bio = (user.bio or "").lower()

            if "http" in bio or "@" in bio:
                await message.delete()
                return

        # TEXT DELETE
        if message.text and group.get("text_time"):
            await asyncio.sleep(group["text_time"])
            await message.delete()

        # MEDIA DELETE
        elif (message.photo or message.video or message.document or message.sticker) and group.get("media_time"):
            await asyncio.sleep(group["media_time"])
            await message.delete()

    except:
        pass

# ------------------------
# EDIT DETECT
# ------------------------
@bot.on_edited_message(filters.group)
async def edit_detect(client, message):
    group = await groups.find_one({"group_id": message.chat.id})

    if not group or not group.get("edit_guard"):
        return

    if await is_admin(message.chat.id, message.from_user.id):
        return

    try:
        warn = await message.reply(
            f"⚠️ {message.from_user.mention} edited message!\n🗑 Deleted."
        )
        await message.delete()
        await asyncio.sleep(5)
        await warn.delete()
    except:
        pass

# ------------------------
# BROADCAST
# ------------------------
@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ You are not allowed")

    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast")

    msg = message.reply_to_message
    all_groups = groups.find()

    sent = 0
    failed = 0

    await message.reply("🚀 Broadcasting started...")

    async for group in all_groups:
        try:
            await msg.copy(group["group_id"])
            sent += 1
            await asyncio.sleep(0.5)

        except:
            failed += 1

    await message.reply(f"✅ Done!\n\nSent: {sent}\nFailed: {failed}")

# ------------------------
# RUN
# ------------------------
bot.run()
