import os
import telebot

# ទាញយក Token និង URL ពី Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! Telegram Bot របស់អ្នកកំពុងដំណើរការហើយ។")

# បើកដំណើរការ Webhook ប្រសិនបើមាន RENDER_URL បើមិនចឹងទេប្រើ Polling
if RENDER_URL:
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    print(f"Webhook set to {RENDER_URL}")
else:
    print("Starting bot with polling...")
    bot.infinity_polling()
