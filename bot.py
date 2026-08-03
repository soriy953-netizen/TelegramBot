import os
import uuid
import time
import traceback
import requests
import telebot
import yt_dlp
from flask import Flask
from threading import Thread

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("សូមកំណត់ BOT_TOKEN ជា Environment Variable នៅក្នុង Render")

RENDER_URL = os.environ.get('RENDER_URL')

bot = telebot.TeleBot(TOKEN)

# ------------------ Web Server (Keep-Alive) ------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is running online!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))


def self_ping():
    if not RENDER_URL:
        print("[WARN] RENDER_URL មិនទាន់កំណត់ - self-ping នឹងមិនដំណើរការ")
        return
    while True:
        try:
            requests.get(RENDER_URL, timeout=10)
            print(f"[PING] ជោគជ័យ")
        except Exception as e:
            print(f"[PING] បរាជ័យ: {e}")
        time.sleep(600)


# ------------------ Bot Handlers ------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! សូមផ្ញើលីង TikTok មកខ្ញុំ ខ្ញុំនឹងទាញយកវីដេអូឱ្យ!")


@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if "http" not in url:
        bot.reply_to(message, "សូមផ្ញើលីង TikTok ត្រឹមត្រូវមក!")
        return

    is_tiktok = "tiktok.com" in url

    sent_msg = bot.reply_to(message, "កំពុងទាញយកវីដេអូ, សូមរង់ចាំបន្តិច...")

    filename = f"video_{uuid.uuid4().hex}.mp4"

    if is_tiktok:
        # TikTok៖ format simplified, តែងតែមាន video+audio ភ្ជាប់រួចរាល់
        # ដូច្នេះមិនចាំបាច់ merge audio/video ដាច់ដោយឡែកទេ
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': filename,
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'nocheckcertificate': True,
        }
    else:
        # YouTube ឬវេបសាយផ្សេង៖ ត្រូវការ format ស្មុគស្មាញជាង
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': filename,
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'nocheckcertificate': True,
        }

        cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
        if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 100:
            ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_size = os.path.getsize(filename)
        max_size = 50 * 1024 * 1024  # 50MB (Telegram Bot API limit)

        if file_size > max_size:
            bot.reply_to(message, "វីដេអូនេះធំពេក (លើស 50MB) មិនអាចផ្ញើតាម Telegram Bot បានទេ។")
        else:
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, timeout=120)

    except Exception as e:
        print("[ERROR] Download failed:")
        print(traceback.format_exc())
        bot.reply_to(message, f"មានបញ្ហាពេលទាញយក៖ {e}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)
        try:
            bot.delete_message(message.chat.id, sent_msg.message_id)
        except Exception:
            pass


# ------------------ Main ------------------
if __name__ == "__main__":
    print("Bot is running...")

    t_web = Thread(target=run_web)
    t_web.daemon = True
    t_web.start()

    t_ping = Thread(target=self_ping)
    t_ping.daemon = True
    t_ping.start()

    bot.infinity_polling(skip_pending=True, timeout=60)
