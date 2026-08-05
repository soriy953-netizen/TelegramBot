import os
import uuid
import time
import traceback
import requests
import telebot
import yt-dlp
from flask import Flask
from threading import Thread
from waitress import serve

# ------------------ Token Setup ------------------
TOKEN = os.environ.get('BOT_TOKEN', '').strip()
if not TOKEN:
    raise ValueError("សូមកំណត់ BOT_TOKEN ជា Environment Variable នៅក្នុង Render")

if len(TOKEN) > 12:
    print(f"[DEBUG] BOT_TOKEN loaded: {TOKEN[:6]}...{TOKEN[-4:]} (length={len(TOKEN)})")
else:
    print(f"[DEBUG] BOT_TOKEN looks too short! length={len(TOKEN)}")

RENDER_URL = os.environ.get('RENDER_URL')

bot = telebot.TeleBot(TOKEN)

# ------------------ Web Server (Keep-Alive) ------------------
app = Flask('')

@app.route('/')
def home():
    return "TikTok Downloader Bot is running online!"

def run_web():
    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def self_ping():
    """
    ផ្ញើ request ទៅខ្លួនឯងរៀងរាល់ 10 នាទី ដើម្បីកុំឲ្យ Render Free tier ដាក់ service ចូល sleep។
    """
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
    bot.reply_to(message, "សួស្តី! សូមផ្ញើលីង TikTok មកខ្ញុំ ខ្ញុំនឹងទាញយកវីដេអូឱ្យដោយគ្មាន watermark!")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if "tiktok.com" not in url and "douyin.com" not in url:
        bot.reply_to(message, "សូមផ្ញើតែលីង TikTok ប៉ុណ្ណោះ (ឧទាហរណ៍: https://vt.tiktok.com/...)")
        return

    sent_msg = bot.reply_to(message, "កំពុងទាញយកវីដេអូ, សូមរង់ចាំបន្តិច...")

    file_id = uuid.uuid4().hex
    filename = f"video_{file_id}.mp4"

    # កែសម្រួល yt_dlp options ឱ្យកាន់តែមានស្ថេរភាពក្នុងការទាញយក TikTok
    ydl_opts = {
        'format': 'best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(filename):
            raise Exception("មិនអាចទាញយកឯកសារវីដេអូបានទេ។")

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
        bot.reply_to(message, f"មានបញ្ហាពេលទាញយកវីដេអូនេះ សូមព្យាយាមម្តងទៀត! ({e})")

    finally:
        # លុបចោលឯកសារក្នុង Server ដើម្បីកុំឱ្យពេញ Storage
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
        try:
            bot.delete_message(message.chat.id, sent_msg.message_id)
        except Exception:
            pass

# ------------------ Main ------------------
if __name__ == "__main__":
    print("TikTok Downloader Bot is running...")

    t_web = Thread(target=run_web)
    t_web.daemon = True
    t_web.start()

    t_ping = Thread(target=self_ping)
    t_ping.daemon = True
    t_ping.start()

    bot.infinity_polling(skip_pending=True, timeout=60)
