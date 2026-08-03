import os
import threading
from flask import Flask
from waitress import serve
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ------------------- Bot Token -------------------
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ------------------- Flask (Keep-Alive Web Server) -------------------
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!', 200

def run_web():
    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ------------------- Telegram Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("សួស្តី! Bot កំពុងដំណើរការ។")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()

# ------------------- Main -------------------
if __name__ == '__main__':
    # រត់ Flask web server ក្នុង thread ដាច់ដោយឡែក ដើម្បីកុំឱ្យវា block bot
    web_thread = threading.Thread(target=run_web)
    web_thread.start()

    # រត់ Telegram bot (polling) នៅ main thread
    run_bot()
