import os
import telebot
import yt_dlp
from flask import Flask
from threading import Thread

TOKEN = '8690146461:AAH5jGP3OrwG3obMm9ooYaYDhBYKEYb7t-o'
bot = telebot.TeleBot(TOKEN)

# បង្កើត Web Server តូចមួយដើម្បីការពារកុំឱ្យ Render ផ្អាកដំណើរការ (Keep-Alive)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running online!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    if "http" in url:
        sent_msg = bot.reply_to(message, "កំពុងទាញយកវីដេអូ, សូមរង់ចាំបន្តិច...")
        
        try:
            ydl_opts = {
                'format': 'mp4',
                'outtmpl': 'downloaded_video.mp4',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            with open('downloaded_video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video)
            
            os.remove('downloaded_video.mp4')
            bot.delete_message(message.chat.id, sent_msg.message_id)
            
        except Exception as e:
            bot.reply_to(message, f"មានបញ្ហាពេលទាញយក៖ {e}")
    else:
        bot.reply_to(message, "សូមផ្ញើលីង YouTube មក!")

if __name__ == "__main__":
    print("Bot is running...")
    # ឱ្យ Web Server រត់ក្នុង Background Thread
    t = Thread(target=run_web)
    t.start()
    # ចាប់ផ្តើម Bot
    bot.infinity_polling()