import os
import telebot
import requests
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time

# --- XOGTAADA ---
API_KEY = "45754dmqhtj0jftyenlyw"
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kici Bot-ka (Telebot)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Bot-ka EarnVids waa diyaar! Ii soo dir Link-ga muqaalka.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    url = message.text
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Fadlan soo dir Link sax ah.")
        return
    
    sent_msg = bot.reply_to(message, "⏳ EarnVids ayaan u dirayaa...")
    
    api_url = f"https://earnvids.com/api/upload/url?key={API_KEY}&url={url}"
    
    try:
        response = requests.get(api_url, timeout=20)
        data = response.json()
        if data.get('status') == 200:
            file_code = data.get('result', {}).get('filecode')
            bot.edit_message_text(f"✅ Guul!\n\nLink: https://earnvids.com/{file_code}", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text(f"❌ Khalad: {data.get('msg')}", message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Cilad: EarnVids API ma ka jawaabin.", message.chat.id, sent_msg.message_id)

# Health Check Server (Si Hugging Face uusan u damin Space-ka)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_health_server():
    httpd = HTTPServer(('0.0.0.0', 7860), HealthCheckHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    # Ku bilow health server-ka background-ka
    threading.Thread(target=run_health_server, daemon=True).start()
    
    logger.info("Bot-ka waa la kicinayaa...")
    
    # Isku day inuu bot-ka kiciyo, haddii uu dhaco dib u bilow
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, interval=0)
        except Exception as e:
            logger.error(f"Cilad ayaa dhacday: {e}")
            time.sleep(10) # Sug 10 ilbiriqsi ka dibna dib u bilow
