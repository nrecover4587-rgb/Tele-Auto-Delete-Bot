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


# ➤ Force Subscribe checker
async def check_force_sub(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(f"@{FORCE_SUB_CHANNEL}", user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
            return False
    except:
        return False
    return True


@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user_id = message.from_user.id

    if not await check_force_sub(bot, message.chat.id, user_id):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]]
        await message.reply("**🔒 You must join our channel to use this bot!**", reply_markup=InlineKeyboardMarkup(btn))
        return

    await users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

    buttons = [
        [InlineKeyboardButton("➕ Add Your Group ➕", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")],
        [InlineKeyboardButton("❓ Help", callback_data="help"), InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    await message.reply_text(
        "**👋 Welcome to Auto Deleter Bot!**\n\nI can auto-delete all messages (text + media) after a set time.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@bot.on_callback_query()
async def callback_handler(_, query: CallbackQuery):
    if query.data == "help":
        await query.message.edit_text(
            "**🛠 Help Menu**\n\n"
            "/set_time <sec> – Set auto delete timer.\n"
            "/disable – Disable auto-delete.\n"
            "/status – Show current delete timer.\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "about":
        await query.message.edit_text(
            "**ℹ️ About**\n\nAuto Deleter Bot\nDeletes text + media automatically.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "back":
        await query.message.edit_text(
            "**👋 Welcome Back!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Your Group ➕", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages")],
                [InlineKeyboardButton("❓ Help", callback_data="help"), InlineKeyboardButton("ℹ️ About", callback_data="about")]
            ])
        )


@bot.on_message(filters.command("set_time") & filters.group)
async def set_delete_time(_, message):
    user_id = message.from_user.id

    member = await bot.get_chat_member(message.chat.id, user_id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.delete()

    if len(message.command) < 2:
        return await message.reply("Usage: /set_time 60")

    time = message.command[1]
    if not time.isdigit():
        return await message.reply("❌ Invalid time")

    await groups.update_one(
        {"group_id": message.chat.id},
        {"$set": {"delete_time": int(time)}},
        upsert=True
    )

    msg = await message.reply(f"✅ Delete time set to {time} sec")
    await asyncio.sleep(5)
    await msg.delete()
    await message.delete()


@bot.on_message(filters.command("status") & filters.group)
async def status(_, message):
    group = await groups.find_one({"group_id": message.chat.id})
    if group:
        await message.reply(f"🕒 Delete time: {group['delete_time']} sec")
    else:
        await message.reply("❌ Not set")


@bot.on_message(filters.command("disable") & filters.group)
async def disable(_, message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.delete()

    await groups.delete_one({"group_id": message.chat.id})
    await message.reply("✅ Disabled")


# 🔥 AUTO DELETE (TEXT + MEDIA)
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
        await asyncio.sleep(int(group["delete_time"]))
        await message.delete()
    except Exception as e:
        print(e)


# Flask keep alive
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(f"https://t.me/{BOT_USERNAME}", code=302)

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
