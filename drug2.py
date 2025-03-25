import os
import time
import telebot
from PIL import Image
import google.generativeai as genai
from requests.exceptions import ConnectionError, ReadTimeout
from telebot.apihelper import ApiException

# Configure API keys from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7322174132:AAF2xMjQxZ5P90BnTvR7PODP1H02uXQwCP0')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyAf6pEnDG9xuJRyaSjbNzetmG2Qn2q2uYE')

# Initialize Telegram Bot with better timeout settings
bot = telebot.TeleBot(
    TELEGRAM_BOT_TOKEN,
    threaded=False,  # Reduces connection issues
    num_threads=1,  # Better for serverless environments
    skip_pending=True  # Skip old messages on restart
)

# Configure Google Generative AI with retry logic
genai.configure(
    api_key=GOOGLE_API_KEY,
    transport='rest',  # More stable than default
    client_options={
        'api_endpoint': 'https://generativelanguage.googleapis.com/v1beta'
    }
)

# Initialize the generative model with safety settings
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={
        'temperature': 0.4,
        'max_output_tokens': 2000
    },
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
)

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
        
        # Generate response with timeout
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
        # Download with timeout
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path, timeout=15)
        
        # Save and process
        with open(temp_image_path, 'wb') as f:
            f.write(downloaded_file)
        
        with Image.open(temp_image_path) as img:
            description = analyze_medicine_image(img)
            bot.reply_to(message, f"{description}\n\nهەمیشە ڕاوێژ بە پزیشکی پسپۆڕ بکە")
    
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
                long_polling_timeout=20,
                restart_on_change=True
            )
        except (ConnectionError, ReadTimeout, ApiException) as e:
            print(f"Connection error: {e}. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            print(f"Critical error: {e}. Restarting in 30s...")
            time.sleep(30)

if __name__ == '__main__':
    print("Bot starting with auto-recovery...")
    run_bot()