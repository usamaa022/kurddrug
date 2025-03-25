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
    'gemini-1.5-pro',
    generation_config={
        'temperature': 0.3,
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 3000
    }
)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate thread"""
    daemon_threads = True

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

def enhance_image_quality(img):
    """Improve image quality for better recognition"""
    try:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        return img
    except Exception:
        return img

def analyze_medicine_image(image):
    """Advanced medicine analysis with structured output"""
    try:
        prompt = """..."""  # Your existing prompt here
        enhanced_img = enhance_image_quality(image)
        
        for attempt in range(3):
            try:
                response = model.generate_content(
                    [prompt, enhanced_img],
                    request_options={'timeout': 15}
                )
                return response.text
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
                
    except Exception as e:
        return f"هەڵەیەک ڕوویدا: {str(e)}\nتکایە دووبارەی بکەرەوە."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """..."""  # Your existing welcome message
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
            description = analyze_medicine_image(img)
            response = f"🔍 نەتیجەی پشکنین:\n\n{description}\n\n⚠️ هەمیشە ڕاوێژ لە پزیشک بکە."
            bot.reply_to(message, response)
    
    except Exception as e:
        bot.reply_to(message, f"هەڵە: {str(e)[:200]}\nتکایە وێنەیەکی ڕوونتر بنێرە.")
    
    finally:
        if os.path.exists(temp_image_path):
            try: os.remove(temp_image_path)
            except: pass

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
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("Bot starting with enhanced drug recognition...")
    run_bot()