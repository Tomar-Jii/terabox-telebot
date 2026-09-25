import os
import telebot
import requests
from dotenv import load_dotenv
from flask import Flask
import threading

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
APIFY_TOKEN = os.getenv('APIFY_TOKEN')

# Render ke liye ek chhota sa web server
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot 24/7 Zinda Hai!"

def run_server():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Mujhe koi bhi Terabox link bhejo, main uski direct video download link de dunga. 🚀")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "terabox" not in url.lower():
        bot.reply_to(message, "Bhai, ye Terabox ka link nahi lag raha. Sahi link bhejo.")
        return

    msg = bot.reply_to(message, "⏳ Video nikal raha hoon, thoda wait karo...")
    
    try:
        api_url = f"https://api.apify.com/v2/acts/igview-owner~terabox-fast-video-downloader/run-sync-get-dataset-items?token={APIFY_TOKEN}"
        payload = {"url": url}
        
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code in [200, 201]:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                res = data[0]
                video = res.get('downloadLink') or res.get('url') or res.get('video_url')
                if video:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"✅ Video mil gaya!\n\nDirect Download Link:\n{video}")
                else:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Download link nahi nikal paya.")
            else:
                bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Video private ho sakti hai ya exist nahi karti.")
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"❌ Apify API Error: {response.status_code}")
            
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="⚠️ Server error. Thodi der baad try karo.")

if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.start()
    bot.infinity_polling()
