import os
import asyncio
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME, FORCE_SUB_CHANNEL, OWNER_ID

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.errors import FloodWait

# MongoDB
client = AsyncIOMotorClient(DATABASE_URL)
db = client['databas']
groups = db['group_id']
users = db['users']

# Bot setup
bot = Client("deletebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Force Sub
async def check_force_sub(client, user_id):
    try:
        member = await client.get_chat_member(f"@{FORCE_SUB_CHANNEL}", user_id)
        return member.status in [
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.MEMBER
        ]
    except:
        return False


# START
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user_id = message.from_user.id

    if not await check_force_sub(bot, user_id):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]]
        return await message.reply("🔒 Join channel to use bot", reply_markup=InlineKeyboardMarkup(btn))

    await users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

    buttons = [
        [InlineKeyboardButton("➕ Add Me", url=f"http://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
    ]
    await message.reply("👋 Auto Delete Bot (Text + Media Separate)", reply_markup=InlineKeyboardMarkup(buttons))


# SET TEXT TIME
@bot.on_message(filters.command("set_text") & filters.group)
async def set_text(_, message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.delete()

    if len(message.command) < 2:
        return await message.reply("Usage: /set_text 60")

    if not message.command[1].isdigit():
        return await message.reply("❌ Invalid time")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"text_time": int(message.command[1])}},
        upsert=True
    )

    msg = await message.reply(f"✅ Text delete: {message.command[1]} sec")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()


# SET MEDIA TIME
@bot.on_message(filters.command("set_media") & filters.group)
async def set_media(_, message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.delete()

    if len(message.command) < 2:
        return await message.reply("Usage: /set_media 60")

    if not message.command[1].isdigit():
        return await message.reply("❌ Invalid time")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"media_time": int(message.command[1])}},
        upsert=True
    )

    msg = await message.reply(f"✅ Media delete: {message.command[1]} sec")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()


# STATUS
@bot.on_message(filters.command("status") & filters.group)
async def status(_, message):
    group = await groups.find_one({"group_id": message.chat.id})
    if not group:
        return await message.reply("❌ Not set")

    text_time = group.get("text_time", "Not set")
    media_time = group.get("media_time", "Not set")

    await message.reply(f"📝 Text: {text_time}\n📁 Media: {media_time}")


# DISABLE
@bot.on_message(filters.command("disable") & filters.group)
async def disable(_, message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.delete()

    await groups.delete_one({"group_id": message.chat.id})
    await message.reply("✅ Disabled")


# AUTO DELETE
@bot.on_message(filters.group & ~filters.service)
async def auto_delete(_, message):
    chat_id = message.chat.id

    if message.from_user and message.from_user.is_bot:
        return

    group = await groups.find_one({"group_id": chat_id})
    if not group:
        return

    try:
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return
    except:
        pass

    try:
        # TEXT
        if message.text and group.get("text_time"):
            await asyncio.sleep(int(group["text_time"]))
            await message.delete()

        # MEDIA
        elif (
            message.photo or message.video or message.document or
            message.audio or message.voice or message.sticker
        ) and group.get("media_time"):
            await asyncio.sleep(int(group["media_time"]))
            await message.delete()

    except Exception as e:
        print(e)


# Flask
app = Flask(__name__)

@app.route('/')
def home():
    return redirect(f"https://t.me/{BOT_USERNAME}")

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
