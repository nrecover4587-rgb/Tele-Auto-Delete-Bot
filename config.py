import os

API_ID = os.environ.get("API_ID","9301087")
API_HASH = os.environ.get("API_HASH","cbabdb3f23de6326352ef3ac26338d9c")
BOT_TOKEN = os.environ.get("BOT_TOKEN","7879064100:AAFRr4wHNLZaN-LN4E5JYeTi-Qtgc0q1HSc")
DATABASE_URL = os.environ.get("DATABASE_URL","mongodb+srv://bob:bobfiles1@bob.sp1vv.mongodb.net/?retryWrites=true&w=majority&appName=bob")
BOT_USERNAME = os.environ.get("BOT_USERNAME","Meeraxmusicbot") # Without @
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "codexempire")  # without @
PORT = int(os.environ.get("PORT", 8080))  # for Flask binding (Koyeb)
OWNER_ID = int(os.environ.get("OWNER_ID", "8364016757"))  # your Telegram user ID
