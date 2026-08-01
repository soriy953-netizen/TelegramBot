import os
import uuid
import telebot
import yt_dlp
from flask import Flask
from threading import Thread

TOKEN = os.environ.get('BOT_TOKEN')  # ដាក់ token ក្នុង Environment Variable, កុំសរសេរដាក់ត្រង់ក្នុងកូដ
bot = telebot.TeleBot(TOKEN)

# Web Server តូចមួយដើម្បីការពារកុំឱ្យ Render ផ្អាកដំណើរការ (Keep-Alive)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running online!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()
    if "http" in url:
        sent_msg = bot.reply_to(message, "កំពុងទាញយកវីដេអូ, សូមរង់ចាំបន្តិច...")

        # ប្រើ filename ដាច់ដោយឡែកសម្រាប់សារនីមួយៗ ដើម្បីកុំឲ្យប៉ះទង្គិចគ្នា
        filename = f"video_{uuid.uuid4().hex}.mp4"

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': filename,
            'quiet': True,
        }

        # ប្រើ cookies.txt តែក្នុងករណីមានវាមែន
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video)

        except Exception as e:
            bot.reply_to(message, f"មានបញ្ហាពេលទាញយក៖ {e}")

        finally:
            if os.path.exists(filename):
                os.remove(filename)
            try:
                bot.delete_message(message.chat.id, sent_msg.message_id)
            except Exception:
                pass
    else:
        bot.reply_to(message, "សូមផ្ញើលីង TikTok ឬ YouTube មក!")

if __name__ == "__main__":
    print("Bot is running...")
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()