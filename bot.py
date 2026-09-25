import os
import telebot
import requests
from dotenv import load_dotenv
from flask import Flask
import threading

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))

# Multiple tokens ko comma se split karke ek list bana lenge
tokens_str = os.getenv('APIFY_TOKENS', '')
APIFY_TOKENS = [t.strip() for t in tokens_str.split(',') if t.strip()]

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot 24/7 Zinda Hai with Multiple Tokens!"

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

    if not APIFY_TOKENS:
        bot.reply_to(message, "⚠️ API Tokens set nahi hain!")
        return

    msg = bot.reply_to(message, "⏳ Video nikal raha hoon, thoda wait karo...")
    payload = {"url": url}
    success = False

    # Ek-ek karke sabhi tokens try karenge
    for token in APIFY_TOKENS:
        try:
            api_url = f"https://api.apify.com/v2/acts/igview-owner~terabox-fast-video-downloader/run-sync-get-dataset-items?token={token}"
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
                
                success = True
                break  # Kaam ho gaya, aage ke token check karne ki zaroorat nahi
            
            else:
                # Agar limit khatam hui, to loop chalega aur automatically agla token use hoga
                print(f"Token failed with status {response.status_code}, trying next...")
                continue
                
        except Exception as e:
            print(f"Error: {e}, trying next token...")
            continue 
            
    if not success:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Sabhi API accounts ki limit khatam ho gayi hai ya server down hai.")

if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.start()
    bot.infinity_polling()
