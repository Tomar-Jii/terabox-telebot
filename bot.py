import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from dotenv import load_dotenv
from flask import Flask
import threading

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))

tokens_str = os.getenv('APIFY_TOKENS', '')
APIFY_TOKENS = [t.strip() for t in tokens_str.split(',') if t.strip()]

CHANNEL_ID = os.getenv('CHANNEL_ID') 
CHANNEL_LINK = "https://t.me/+p5Yu1iglyfUxZThh"

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot 24/7 Zinda Hai!"

def run_server():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

def is_subscribed(chat_id, user_id):
    if not chat_id:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['member', 'creator', 'administrator', 'restricted']:
            return True
        return False
    except telebot.apihelper.ApiTelegramException:
        return False
    except Exception:
        return True

def ask_to_join(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Join Channel 🚀", url=CHANNEL_LINK))
    markup.add(InlineKeyboardButton("Joined ✅ (Check)", callback_data="check_join"))
    bot.reply_to(message, "⚠️ **Pehle Hamara Channel Join Karo!**\n\nBot use karne ke liye aapko hamara channel join karna hoga.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_subscribed(CHANNEL_ID, call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verification Successful! Ab aap link bhej sakte hain.", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak join nahi kiya hai!", show_alert=True)

@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == 'private')
def send_welcome(message):
    if CHANNEL_ID and not is_subscribed(CHANNEL_ID, message.from_user.id):
        ask_to_join(message)
        return
    bot.reply_to(message, "Mujhe koi bhi Terabox video ka link bhejo, main uski direct download link de dunga. 🚀\n*(Note: Folder/Filelist link kaam nahi karega, direct video link bhejein)*")

@bot.message_handler(func=lambda message: message.chat.type == 'private')
def handle_message(message):
    if CHANNEL_ID and not is_subscribed(CHANNEL_ID, message.from_user.id):
        ask_to_join(message)
        return

    url = message.text.lower()
    valid_domains = ["terabox", "1024tera", "terafileshare", "freeterabox", "teraboxapp", "4funbox"]
    if not any(domain in url for domain in valid_domains):
        bot.reply_to(message, "Bhai, ye Terabox ka link nahi lag raha. Sahi link bhejo.")
        return

    if not APIFY_TOKENS:
        bot.reply_to(message, "⚠️ API Tokens set nahi hain!")
        return

    msg = bot.reply_to(message, "⏳ Video nikal raha hoon, thoda wait karo...")
    payload = {"url": message.text}
    success = False

    for token in APIFY_TOKENS:
        try:
            api_url = f"https://api.apify.com/v2/acts/igview-owner~terabox-fast-video-downloader/run-sync-get-dataset-items?token={token}"
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code in [200, 201]:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    res = data[0]
                    
                    # Naya Code: Agar API properly fail ho jaye
                    if res.get('success') is False:
                        err_msg = res.get('error', 'File nahi mili.')
                        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, 
                                              text=f"❌ **API Error:** {err_msg}\n\n⚠️ **Tip:** Aapne shayad Folder/Filelist ka link bheja hai. Kripya us folder ko open karke kisi ek video ka direct link bhejein.", parse_mode="Markdown")
                        success = True # Error handle ho gaya, loop tod do
                        break

                    video = res.get('downloadLink') or res.get('url') or res.get('video_url') or res.get('link') or res.get('direct_link')
                    
                    if video:
                        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"✅ Video mil gaya!\n\nDirect Download Link:\n{video}")
                    else:
                        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Download link nahi mila. File private ho sakti hai.")
                else:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Video exist nahi karti ya dataset khali aaya.")
                
                success = True
                break 
            else:
                continue
        except Exception as e:
            continue 
            
    if not success:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Sabhi API accounts ki limit khatam ho gayi hai ya server down hai.")

if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.start()
    bot.infinity_polling()
