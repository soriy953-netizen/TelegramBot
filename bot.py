import os
import uuid
from flask import Flask
from threading import Thread
import telebot
import yt_dlp

# Get Telegram Bot Token from environment variables
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Initialize Flask Web Server to keep the bot alive on Render
app = Flask('')

@app.route('/')
def home():
    return "Hello, World! Telegram Bot is running."

def run_web():
    app.run(host='0.0.0.0', port=8080)

# Handle /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Please send me a YouTube link to download the video.")

# Handle incoming YouTube links
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # Check if the text looks like a URL
    if not url.startswith("http"):
        bot.reply_to(message, "Please send a valid YouTube link.")
        return

    bot.reply_to(message, "Downloading video, please wait...")

    # Generate a unique filename using uuid to prevent file conflict errors
    unique_filename = f"video_{uuid.uuid4().hex}.mp4"

    ydl_opts = {
        'format': 'best',
        'outtmpl': unique_filename,
    }

    try:
        # Download video using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Send the video back to Telegram
        with open(unique_filename, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)

        bot.reply_to(message, "Download complete!")

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

    finally:
        # Clean up and delete the file from server disk after sending
        if os.path.exists(unique_filename):
            os.remove(unique_filename)

if __name__ == "__main__":
    # Start the web server in a separate background thread
    t = Thread(target=run_web)
    t.start()
    
    # Start the Telegram bot polling
    bot.infinity_polling()
