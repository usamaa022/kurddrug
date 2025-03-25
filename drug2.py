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
        'temperature': 0.2,  # More precise responses
        'max_output_tokens': 4000
    }
)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

def start_health_server():
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
    """Comprehensive medicine analysis in Kurdish Sorani"""
    try:
        prompt = """
        تەنیا بە کوردی سۆرانی وەڵام بدەرەوە. زانیارییەکان پێویستە پێڕستی خوارەوە لەخۆبگرێت:

        🏷 ناوی دەرمان: 
        - ناوی بازرگانی: [ناو]
        - ناوی جێگرەوە: [ناو]

        🩺 بۆ چ دەرمانێکە:
        - [لیستی ئەو نەخۆشییانەی بۆی بەکاردێت]
        - [جۆری ئازارەکانی چارەسەر دەکات]

        💊 چۆنیەتی بەکارهێنان:
        - [ئەو پێناسانەی لەسەر پاکەتەکەیە]
        - [کاتی بەکارهێنان (بەیانی/ئێواران)]

        ⚠️ مەترسی و کاریگەرییە نەخوازراوەکان:
        - [کاریگەرییە لاوەکییەکان]
        - [پێشترازیەکان]

        🤰 ئایا بۆ خانمە دووگیانەکان باشە؟
        - [بەڵێ/نەخێر] + [هۆکار]

        👶 ئایا بۆ منداڵان باشە؟
        - [تەمەنی گونجاو] + [ئامۆژگاری تایبەت]

        💰 نرخ: [ئەگەر دیاربوو]

        📅 ماوەی بەکارهێنان: [ماوەی گونجاو]

        🧊 چۆنیەتی پاراستن: [ئەگەر دیاربوو]

        ئەگەر ناتوانیت دەرمانەکە بشناسیتەوە:
        "نەتوانم دەرمانەکە بشناسمەوە. تکایە وێنەیەکی ڕوونتر بنێرە بە تایبەتی بەشی ناو و زانیارییەکانی پاکەتەکە."
        """
        
        enhanced_img = enhance_image_quality(image)
        
        response = model.generate_content(
            [prompt, enhanced_img],
            request_options={'timeout': 20}
        )
        return response.text
    
    except Exception as e:
        return f"هەڵەیەک ڕوویدا لە خوێندنەوەی وێنەکە: {str(e)}\nتکایە دووبارەی بکەرەوە."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    بەخێربێیت بۆ بۆتی زانستگەی دەرمانی 👨‍⚕️💊

ئەم بۆتە یارمەتیت دەدات لە:
- ناسینەوەی دەرمانەکان
- زانینی بەکارهێنان و کاریگەرییەکانی
- زانینی مەترسی و ئامۆژگاری تایبەت

تکایە وێنەیەکی ڕوون لە پاکەتی دەرمانەکە بنێرە، بە تایبەتی بەشی ناو و زانیارییەکانی.
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
            description = analyze_medicine_image(img)
            response = f"""
🔍 زانیاری دەرمانەکە:

{description}

⚠️ ئامۆژگاری: هەمیشە پێش بەکارهێنانی دەرمان، ڕاوێژ لە پزیشک یان ئەندازیاری دەرمانسازی بکە.
"""
            bot.reply_to(message, response)
    
    except Exception as e:
        bot.reply_to(message, f"هەڵە: {str(e)[:200]}\nتکایە دووبارەی بکەرەوە.")
    
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
    print("Bot starting with medical analysis...")
    run_bot()