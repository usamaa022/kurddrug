import os
import time
import threading
import telebot
from PIL import Image, ImageEnhance
import google.generativeai as genai
from requests.exceptions import ConnectionError, ReadTimeout
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Configure API keys
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7322174132:AAF2xMjQxZ5P90BnTvR7PODP1H02uXQwCP0')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyAf6pEnDG9xuJRyaSjbNzetmG2Qn2q2uYE')

# Initialize Telegram Bot
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

class HealthCheckServer(ThreadingMixIn, HTTPServer):
    """HTTP Server for health checks"""
    daemon_threads = True

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def start_health_server():
    """Start health check server in background"""
    server = HealthCheckServer(('0.0.0.0', 8000), HealthHandler)
    server.serve_forever()

def enhance_image_quality(img):
    """Improve image quality for drug name recognition"""
    try:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.8)
        return img
    except Exception:
        return img

def analyze_medicine(image):
    """Comprehensive drug analysis"""
    try:
        prompt = """
        Provide detailed drug information in Kurdish Sorani including:
        1. Scientific name and composition
        2. Therapeutic effects
        3. Side effects
        4. Mechanism of action
        
        If packaging is unclear, use your pharmaceutical knowledge.
        """
        
        enhanced_img = enhance_image_quality(image)
        response = model.generate_content([prompt, enhanced_img])
        return response.text
    
    except Exception as e:
        return f"هەڵە: نەتوانم زانیاری بدۆزمەوە. تکایە دووبارەی بکەرەوە.\nError: {str(e)}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    بەخێربێیت بۆ بۆتی زانستی دەرمانی 🔬💊

من دەتوانم زانیاری زانستیت پێبڵێم لەسەر دەرمانەکان.
تکایە وێنەی پاکەتەکە بنێرە.
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_medicine_photo(message):
    temp_image_path = 'medicine_image.jpg'
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(temp_image_path, 'wb') as f:
            f.write(downloaded_file)
        
        with Image.open(temp_image_path) as img:
            analysis = analyze_medicine(img)
            bot.reply_to(message, f"🧪 زانیاری:\n\n{analysis}")
    
    except Exception as e:
        bot.reply_to(message, f"هەڵە: {str(e)[:200]}")
    
    finally:
        if os.path.exists(temp_image_path):
            try: os.remove(temp_image_path)
            except: pass

def run_bot():
    """Run bot with auto-recovery"""
    while True:
        try:
            print("Bot is running...")
            bot.polling(none_stop=True, timeout=30)
        except (ConnectionError, ReadTimeout) as e:
            print(f"Connection error: {e}. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}. Restarting in 30s...")
            time.sleep(30)

if __name__ == '__main__':
    # Start health check server in background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    print("Starting medicine bot with health checks...")
    run_bot()