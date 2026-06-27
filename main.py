import os
import telebot
import requests
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time

# --- XOGTAADA CUSUB (StreamHG) ---
# Halkan geli API Key-ga aad StreamHG ka soo qaadatay
API_KEY = "32036t23uujg8e4ikofnf" 
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Ku soo dhawaaw StreamHG Uploader!\n\nIi soo dir Video (ilaa 20MB) ama Direct Link kasta.")

@bot.message_handler(content_types=['video', 'document', 'text'])
def handle_upload(message):
    file_id = None
    if message.content_type == 'video':
        file_id = message.video.file_id
    elif message.content_type == 'document' and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
    elif message.content_type == 'text' and message.text.startswith('http'):
        process_remote_url(message, message.text)
        return
    else:
        bot.reply_to(message, "❌ Fadlan ii soo dir Video ama Direct Link oo keliya.")
        return

    if file_id:
        sent_msg = bot.reply_to(message, "⏳ Muqaalka waa la qabtay, StreamHG ayaan u dirayaa...")
        try:
            file_info = bot.get_file(file_id)
            direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            process_remote_url(message, direct_link, sent_msg)
        except Exception as e:
            bot.edit_message_text(f"❌ Cilad: Telegram Limit (20MB). Isticmaal Link Generator.", message.chat.id, sent_msg.message_id)

def process_remote_url(message, url, sent_msg=None):
    if not sent_msg:
        sent_msg = bot.reply_to(message, "⏳ StreamHG ayaan u dirayaa...")
        
    # API URL-ka StreamHG
    api_url = f"https://streamhg.com/api/upload/url?key={API_KEY}&url={url}"
    
    try:
        response = requests.get(api_url, timeout=30)
        data = response.json()
        if data.get('status') == 200:
            file_code = data.get('result', {}).get('filecode')
            bot.edit_message_text(f"✅ Guul! Muqaalka waa la upload-gareeyey.\n\nLink: https://streamhg.com/{file_code}", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text(f"❌ StreamHG Error: {data.get('msg')}", message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Cilad: Xiriirka StreamHG waa uu go'ay.", message.chat.id, sent_msg.message_id)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Active")

def run_health_server():
    httpd = HTTPServer(('0.0.0.0', 7860), HealthCheckHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception:
            time.sleep(10)
