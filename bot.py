import os
import asyncio
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME, FORCE_SUB_CHANNEL, OWNER_ID

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB
client = AsyncIOMotorClient(DATABASE_URL)
db = client['databas']
groups = db['group_id']

# Bot
bot = Client("deletebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# 🔹 Helper: Admin Check
async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False


# 🔹 SET TEXT TIME
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


# 🔹 SET MEDIA TIME
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


# 🔹 STATUS
@bot.on_message(filters.command("status") & filters.group)
async def status(_, message):
    group = await groups.find_one({"group_id": message.chat.id})
    if not group:
        return await message.reply("❌ Not configured")

    text = group.get("text_time", "Off")
    media = group.get("media_time", "Off")

    msg = await message.reply(f"⚙️ Settings:\n📝 Text: {text}\n📁 Media: {media}")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()


# 🔹 DISABLE
@bot.on_message(filters.command("disable") & filters.group)
async def disable(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.delete()

    await groups.delete_one({"group_id": message.chat.id})

    msg = await message.reply("✅ Auto-delete disabled")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()


# 🔥 AUTO DELETE ENGINE (PRO)
@bot.on_message(filters.group & ~filters.service)
async def auto_delete(_, message):
    chat_id = message.chat.id

    # ignore bots
    if message.from_user and message.from_user.is_bot:
        return

    group = await groups.find_one({"group_id": chat_id})
    if not group:
        return

    # ignore admins
    if await is_admin(chat_id, message.from_user.id):
        return

    try:
        # TEXT
        if message.text and group.get("text_time"):
            await asyncio.sleep(group["text_time"])
            await message.delete()

        # MEDIA
        elif (
            message.photo or message.video or message.document or
            message.audio or message.voice or message.sticker
        ) and group.get("media_time"):
            await asyncio.sleep(group["media_time"])
            await message.delete()

    except Exception as e:
        print(f"Delete error: {e}")


# 🌐 Flask Keep Alive
app = Flask(__name__)

@app.route('/')
def home():
    return redirect(f"https://t.me/{BOT_USERNAME}")

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
