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

# URL សាធារណៈរបស់ Render service (ឧទាហរណ៍ https://telegrambot-33p5.onrender.com)
# ត្រូវកំណត់ជា Environment Variable ឈ្មោះ RENDER_URL នៅក្នុង Render dashboard
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
    """
    ផ្ញើ request ទៅខ្លួនឯងរៀងរាល់ 10 នាទី ដើម្បីកុំឲ្យ Render Free tier
    ដាក់ service ចូល sleep ដោយសារ inactive។ ចាំបាច់ត្រូវកំណត់
    RENDER_URL ជា environment variable ជាមុនសិន។
    """
    if not RENDER_URL:
        print("[WARN] RENDER_URL មិនទាន់កំណត់ - self-ping នឹងមិនដំណើរការ")
        return
    while True:
        try:
            requests.get(RENDER_URL, timeout=10)
            print(f"[PING] ផ្ញើ keep-alive ping ទៅ {RENDER_URL} ជោគជ័យ")
        except Exception as e:
            print(f"[PING] បរាជ័យ: {e}")
        time.sleep(600)  # រង់ចាំ 10 នាទី មុនផ្ញើម្តងទៀត


# ------------------ Bot Handlers ------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! សូមផ្ញើលីង TikTok ឬ YouTube មកខ្ញុំ ខ្ញុំនឹងទាញយកវីដេអូឱ្យ!")


@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if "http" not in url:
        bot.reply_to(message, "សូមផ្ញើលីង TikTok ឬ YouTube ត្រឹមត្រូវមក!")
        return

    sent_msg = bot.reply_to(message, "កំពុងទាញយកវីដេអូ, សូមរង់ចាំបន្តិច...")

    filename = f"video_{uuid.uuid4().hex}.mp4"

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
    print(f"[DEBUG] Looking for cookies at: {cookie_path}")

    if os.path.exists(cookie_path):
        size = os.path.getsize(cookie_path)
        print(f"[DEBUG] cookies.txt found, size = {size} bytes")
        if size > 100:
            ydl_opts['cookiefile'] = cookie_path
        else:
            print("[DEBUG] cookies.txt ទទេ ឬតូចពេក - មិនប្រើ")
    else:
        print("[DEBUG] cookies.txt រកមិនឃើញ! ត្រូវ upload ជា Secret File នៅ Render")

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

    # Thread 1: Flask web server (keep Render port open)
    t_web = Thread(target=run_web)
    t_web.daemon = True
    t_web.start()

    # Thread 2: Self-ping ដើម្បីការពារ Render sleep
    t_ping = Thread(target=self_ping)
    t_ping.daemon = True
    t_ping.start()

    # Main thread: Telegram polling loop (រត់ជានិច្ច ទោះកុំព្យូទ័រអ្នកបិទក៏ដោយ
    # ព្រោះ process នេះស្ថិតនៅលើ Render server មិនមែនលើកុំព្យូទ័រអ្នកទេ)
    bot.infinity_polling(skip_pending=True, timeout=60)
