import os
import threading
import uuid
import yt_dlp
import telebot
from flask import Flask
from waitress import serve

# ------------------- Bot Token -------------------
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(BOT_TOKEN)

# ------------------- Flask (Keep-Alive Web Server) -------------------
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!', 200

def run_web():
    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ------------------- Telegram Handlers -------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "សួស្តី! ផ្ញើ TikTok link មកខ្ញុំ ខ្ញុំនឹងទាញយកវីដេអូឲ្យ។")

@bot.message_handler(func=lambda m: m.text and ('tiktok.com' in m.text))
def handle_tiktok_link(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "កំពុងទាញយកវីដេអូ សូមរង់ចាំ... ⏳")

    filename = f"{uuid.uuid4()}.mp4"
    ydl_opts = {
        'outtmpl': filename,
        'format': 'mp4/best',
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ ទាញយកបានជោគជ័យ!")

    except Exception as e:
        bot.reply_to(message, f"❌ ទាញយកមិនបានទេ សូមព្យាយាមម្តងទៀត។\nError: {e}")

    finally:
        bot.delete_message(message.chat.id, status_msg.message_id)
        if os.path.exists(filename):
            os.remove(filename)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "សូមផ្ញើ TikTok link ត្រឹមត្រូវ (ឧ. https://vt.tiktok.com/...)")

def run_bot():
    bot.infinity_polling(skip_pending=True, timeout=60)

# ------------------- Main -------------------
if __name__ == '__main__':
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    run_bot()
