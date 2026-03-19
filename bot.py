import asyncio
import signal
from pyrogram import Client, filters, enums
from motor.motor_asyncio import AsyncIOMotorClient

from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL
from start import *  # start.py imported for start command

# ------------------------
# MongoDB Setup
# ------------------------
mongo = AsyncIOMotorClient(DATABASE_URL)
db = mongo["databas"]
groups = db["group_id"]

# ------------------------
# Pyrogram Bot Setup
# ------------------------
bot = Client(
    "AutoDeleteBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ------------------------
# Admin Check
# ------------------------
async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

# ------------------------
# Set Text Delete Timer
# ------------------------
@bot.on_message(filters.command("set_text") & filters.group)
async def set_text(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()
    if len(message.command) < 2 or not message.command[1].isdigit():
        msg = await message.reply("Usage: /set_text 60")
        await asyncio.sleep(5)
        return await msg.delete()
    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"text_time": int(message.command[1])}},
        upsert=True
    )
    msg = await message.reply(f"✅ Text delete: {message.command[1]} sec")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# Set Media Delete Timer
# ------------------------
@bot.on_message(filters.command("set_media") & filters.group)
async def set_media(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()
    if len(message.command) < 2 or not message.command[1].isdigit():
        msg = await message.reply("Usage: /set_media 60")
        await asyncio.sleep(5)
        return await msg.delete()
    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"media_time": int(message.command[1])}},
        upsert=True
    )
    msg = await message.reply(f"✅ Media delete: {message.command[1]} sec")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# Status Command
# ------------------------
@bot.on_message(filters.command("status") & filters.group)
async def status(_, message):
    group = await groups.find_one({"group_id": message.chat.id})
    if not group:
        msg = await message.reply("❌ Not configured")
        await asyncio.sleep(5)
        return await msg.delete()
    text = group.get("text_time", "Off")
    media = group.get("media_time", "Off")
    msg = await message.reply(f"⚙️ Settings:\n📝 Text: {text}\n📁 Media: {media}")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# Disable Command
# ------------------------
@bot.on_message(filters.command("disable") & filters.group)
async def disable(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()
    await groups.delete_one({"group_id": message.chat.id})
    msg = await message.reply("✅ Auto-delete disabled")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()

# ------------------------
# Auto Delete Engine
# ------------------------
@bot.on_message(filters.group & ~filters.service)
async def auto_delete(_, message):
    chat_id = message.chat.id
    if message.from_user and message.from_user.is_bot:
        return
    group = await groups.find_one({"group_id": chat_id})
    if not group:
        return
    if await is_admin(chat_id, message.from_user.id):
        return
    try:
        # Text
        if message.text and group.get("text_time"):
            await asyncio.sleep(group["text_time"])
            await message.delete()
        # Media
        elif (
            message.photo or message.video or message.document or
            message.audio or message.voice or message.sticker
        ) and group.get("media_time"):
            await asyncio.sleep(group["media_time"])
            await message.delete()
    except Exception as e:
        print(f"Delete error: {e}")

# ------------------------
# Run Bot Gracefully (Heroku Safe)
# ------------------------
async def main():
    await bot.start()
    print("🔥 Bot Started Successfully")
    await asyncio.Event().wait()  # keep running

async def shutdown():
    print("🛑 Shutting down bot...")
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        print("❌ Bot Stopped")
