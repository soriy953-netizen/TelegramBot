import os
import uuid
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "Hello, World! Telegram Bot is running."

def run_web():
    app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Please send me a YouTube link to download videos.")

# Handle incoming YouTube links and show quality selection buttons
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        bot.reply_to(message, "Please send a valid YouTube link.")
        return

    # Create inline keyboard for quality selection
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    # We pass URL and quality format code in callback_data
    markup.add(
        InlineKeyboardButton("🎬 Best Quality", callback_data=f"dl|best|{url}"),
        InlineKeyboardButton("📱 Medium (720p/360p)", callback_data=f"dl|medium|{url}")
    )

    bot.reply_to(message, "⏳ Please select the video quality you want:", reply_markup=markup)

# Handle button clicks for quality selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('dl|'))
def callback_query(call):
    data_parts = call.data.split('|')
    quality = data_parts[1]
    url = data_parts[2]

    bot.answer_callback_query(call.id, "Downloading has started...")
    bot.edit_message_text("⏳ Downloading video, please wait...", call.message.chat.id, call.message.message_id)

    unique_filename = f"video_{uuid.uuid4().hex}.mp4"

    # Select yt-dlp format based on user choice
    if quality == 'best':
        ydl_opts = {'format': 'best', 'outtmpl': unique_filename}
    else:
        ydl_opts = {'format': 'best[height<=720]', 'outtmpl': unique_filename}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(unique_filename, 'rb') as video_file:
            bot.send_video(call.message.chat.id, video_file)

        bot.edit_message_text("✅ Download complete successfully!", call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ An error occurred: {e}", call.message.chat.id, call.message.message_id)

    finally:
        if os.path.exists(unique_filename):
            os.remove(unique_filename)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
