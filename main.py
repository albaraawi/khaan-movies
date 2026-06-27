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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Ii soo dir Video ama Document si aan EarnVids ugu upload-gareeyo.")

# Qaybta qabanaysa Video-ga, Document-ga ama Link-ga
@bot.message_handler(content_types=['video', 'document', 'text'])
def handle_upload(message):
    file_id = None
    
    # 1. Haddii uu yahay Video
    if message.content_type == 'video':
        file_id = message.video.file_id
    # 2. Haddii uu yahay Document (mararka qaar muqaalku doc ahaan ayuu u yimaadaa)
    elif message.content_type == 'document' and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
    # 3. Haddii uu yahay Link (Text)
    elif message.content_type == 'text' and message.text.startswith('http'):
        process_remote_url(message, message.text)
        return
    else:
        bot.reply_to(message, "❌ Fadlan ii soo dir Video ama Direct Link oo keliya.")
        return

    # Haddii file la helay, u beddel Link ka dibna upload garee
    if file_id:
        sent_msg = bot.reply_to(message, "⏳ Muqaalka waa la qabtay, hadda ayaan EarnVids u dirayaa...")
        try:
            # Hel link-ga rasmiga ah ee file-ka ka soo baxaya Telegram
            file_info = bot.get_file(file_id)
            direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            
            # U gudbi EarnVids API
            process_remote_url(message, direct_link, sent_msg)
        except Exception as e:
            bot.edit_message_text(f"❌ Cilad: Ma awoodo inaan file-ka ka soo saaro Telegram (Limit 20MB).", message.chat.id, sent_msg.message_id)

def process_remote_url(message, url, sent_msg=None):
    if not sent_msg:
        sent_msg = bot.reply_to(message, "⏳ EarnVids ayaan u dirayaa...")
        
    api_url = f"https://earnvids.com/api/upload/url?key={API_KEY}&url={url}"
    
    try:
        response = requests.get(api_url, timeout=30)
        data = response.json()
        if data.get('status') == 200:
            file_code = data.get('result', {}).get('filecode')
            bot.edit_message_text(f"✅ Guul! Muqaalka waa la upload-gareeyey.\n\nLink: https://earnvids.com/{file_code}", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text(f"❌ EarnVids Error: {data.get('msg')}", message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Cilad: Xiriirka EarnVids API waa uu go'ay.", message.chat.id, sent_msg.message_id)

# Health Check Server
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
