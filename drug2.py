import os
import time
import threading
import telebot
from PIL import Image
import google.generativeai as genai
from requests.exceptions import ConnectionError, ReadTimeout
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Configure API keys from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7322174132:AAF2xMjQxZ5P90BnTvR7PODP1H02uXQwCP0')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyAf6pEnDG9xuJRyaSjbNzetmG2Qn2q2uYE')

# Initialize Telegram Bot with optimized settings
bot = telebot.TeleBot(
    TELEGRAM_BOT_TOKEN,
    threaded=False,
    num_threads=1,
    skip_pending=True
)

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={
        'temperature': 0.4,
        'max_output_tokens': 2000
    }
)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread"""

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

def start_health_server():
    """Start health check server on port 8000"""
    server = ThreadedHTTPServer(('0.0.0.0', 8000), HealthHandler)
    print("Health check server running on port 8000")
    server.serve_forever()

def analyze_medicine_image(image):
    """Analyze medicine packaging with enhanced error handling"""
    try:
        prompt = """
        Identify this medicine from its packaging in Kurdish Sorani.
        Include:
        1. Medicine name (brand + generic)
        2. Medical uses
        3. Safety info:
           - Pregnancy safety
           - Side effects
           - Warnings
        4. Typical dosage (with doctor consultation reminder)
        
        If unclear, respond:
        "ناتوانم دەرمانەکە ناسایەوە. تکایە وێنەیەکی باشتر و ڕوونتر بنێرە، بە تایبەتی ناوی دەرمانەکە و زانیارییەکانی تر."
        """
        
        response = model.generate_content(
            [prompt, image],
            request_options={'timeout': 10}
        )
        return response.text or "پەڕەیەکی بەتاڵی گەڕانەوە"
    
    except Exception as e:
        return f"هەڵە ڕووی دا لە خوێندنەوەی وێنەکە: {str(e)}\nتکایە دووبارەی بکەرەوە."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    بەخێربێیت بۆ بۆتی ناسینەوەی دەرمان! 👨‍⚕️💊

ئەم بۆتە یارمەتیت دەدات بزانیت:
- ئەو دەرمانە بۆ چی بەکاردەهێنرێت
- ئایا بۆ خانمە دووگیانەکان مەترسی هەیە
- کاریگەرییە لاوەکییەکانی
- زانیارییەکانی تری پەیوەست

تکایە وێنەیەکی ڕوون لە پاکێتی دەرمانەکە بنێرە، بە تایبەتی بەشی ناوی دەرمانەکە.
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_medicine_photo(message):
    temp_image_path = 'medicine_image.jpg'
    try:
        # Get file info
        file_info = bot.get_file(message.photo[-1].file_id)
        
        # Download file (removed timeout parameter)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save and process image
        with open(temp_image_path, 'wb') as f:
            f.write(downloaded_file)
        
        with Image.open(temp_image_path) as img:
            description = analyze_medicine_image(img)
            bot.reply_to(message, f"{description}\n\nهەمیشە ڕاوێژ بە پزیشکی پسپۆڕ بکە")
    
    except Exception as e:
        bot.reply_to(message, f"هەڵە: {str(e)[:200]}\nتکایە دووبارەی بکەرەوە.")
    
    finally:
        if os.path.exists(temp_image_path):
            try: 
                os.remove(temp_image_path)
            except: 
                pass

def run_bot():
    """Run bot with auto-recovery"""
    while True:
        try:
            print("Starting bot polling...")
            bot.polling(
                none_stop=True,
                timeout=30,
                long_polling_timeout=20
            )
        except (ConnectionError, ReadTimeout) as e:
            print(f"Connection error: {e}. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            print(f"Critical error: {e}. Restarting in 30s...")
            time.sleep(30)

if __name__ == '__main__':
    # Start health check server in background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Start the bot
    print("Bot starting with health checks...")
    run_bot()