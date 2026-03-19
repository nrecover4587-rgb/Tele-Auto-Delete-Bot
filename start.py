from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto

from config import BOT_USERNAME, FORCE_SUB_CHANNEL, OWNER_ID, START_IMG


# 🔹 Force Subscribe
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
async def start(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    # Force Sub
    if not await check_force_sub(client, user_id):
        buttons = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]]
        return await message.reply_photo(
            photo=START_IMG,
            caption="🔒 **Access Denied!**\n\nJoin our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Buttons
    buttons = [
        [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
        [
            InlineKeyboardButton("⚙️ Commands", callback_data="help"),
            InlineKeyboardButton("✨ Features", callback_data="features")
        ],
        [
            InlineKeyboardButton("👨‍💻 Owner", user_id=OWNER_ID),
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]
    ]

    caption = f"""
✨ **Hey {name}!**

🤖 I'm your **Advanced Auto Delete Bot**

💣 I can automatically clean your group by deleting:
• 📝 Text Messages  
• 📁 Media Files (Photo, Video, Docs)  

⚙️ Control everything with simple commands  
⚡ Fast • Smart • Reliable  

━━━━━━━━━━━━━━━
🚀 **Add me & make your group clean like PRO!**
"""

    await message.reply_photo(
        photo=START_IMG,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )


# 🔥 CALLBACK SYSTEM
@Client.on_callback_query()
async def callbacks(client, query: CallbackQuery):

    # HELP MENU
    if query.data == "help":
        text = """
⚙️ **Commands Panel**

📝 /set_text 60  
→ Auto delete text  

📁 /set_media 60  
→ Auto delete media  

📊 /status  
→ Check current settings  

❌ /disable  
→ Turn off auto delete  
"""

        await query.message.edit_media(
            InputMediaPhoto(
                media=START_IMG,
                caption=text
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # FEATURES MENU
    elif query.data == "features":
        text = """
✨ **Bot Features**

⚡ Fast Auto Delete  
📝 Text & Media Separate Timer  
🛡 Admin Protection  
🚫 No Spam / Clean Chat  
🎯 Simple Commands  

💯 Fully Automatic System
"""

        await query.message.edit_media(
            InputMediaPhoto(
                media=START_IMG,
                caption=text
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # BACK BUTTON
    elif query.data == "back":
        buttons = [
            [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=delete_messages")],
            [
                InlineKeyboardButton("⚙️ Commands", callback_data="help"),
                InlineKeyboardButton("✨ Features", callback_data="features")
            ],
            [
                InlineKeyboardButton("👨‍💻 Owner", user_id=OWNER_ID),
                InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
            ]
        ]

        caption = "🔙 Back to main menu"

        await query.message.edit_media(
            InputMediaPhoto(
                media=START_IMG,
                caption=caption
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
