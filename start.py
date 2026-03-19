from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import BOT_USERNAME, FORCE_SUB_CHANNEL, OWNER_ID


# 🔹 Force Subscribe Check
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


# 🔥 START COMMAND
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    # Force Sub
    if not await check_force_sub(client, user_id):
        buttons = [[
            InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]]
        return await message.reply_text(
            "🔒 **Access Denied!**\n\nJoin our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Buttons
    buttons = [
        [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
        [
            InlineKeyboardButton("⚙️ Commands", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ],
        [
            InlineKeyboardButton("👨‍💻 Owner", user_id=OWNER_ID),
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]
    ]

    text = f"""
✨ **Hello {name}!**

🤖 I'm an **Auto Delete Bot**

💣 Features:
• Auto delete text messages  
• Auto delete media files  
• Separate timers  

⚙️ Commands:
• /set_text <sec>
• /set_media <sec>
• /status
• /disable  

🚀 Add me to your group & enjoy clean chats!
"""

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )


# 🔥 CALLBACK HANDLER
@Client.on_callback_query()
async def callback_handler(client, query: CallbackQuery):

    # HELP
    if query.data == "help":
        await query.message.edit_text(
            "⚙️ **Commands Panel**\n\n"
            "📝 /set_text 60 → delete text\n"
            "📁 /set_media 60 → delete media\n"
            "📊 /status → check settings\n"
            "❌ /disable → turn off",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # ABOUT
    elif query.data == "about":
        await query.message.edit_text(
            "ℹ️ **About Bot**\n\n"
            "This bot auto deletes messages (text + media)\n"
            "after a set time.\n\n"
            "Made with ❤️ for clean groups.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # BACK
    elif query.data == "back":
        buttons = [
            [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
            [
                InlineKeyboardButton("⚙️ Commands", callback_data="help"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]
        ]

        await query.message.edit_text(
            "🔙 Back to main menu",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
