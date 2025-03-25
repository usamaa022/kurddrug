import os
import time
import telebot
from PIL import Image, ImageEnhance
import google.generativeai as genai
from requests.exceptions import ConnectionError, ReadTimeout

# Configure API keys
TELEGRAM_BOT_TOKEN = '7322174132:AAF2xMjQxZ5P90BnTvR7PODP1H02uXQwCP0'
GOOGLE_API_KEY = 'AIzaSyAf6pEnDG9xuJRyaSjbNzetmG2Qn2q2uYE'

# Initialize Telegram Bot
bot = telebot.TeleBot(
    TELEGRAM_BOT_TOKEN,
    threaded=False,
    num_threads=1,
    skip_pending=True
)

# Configure Google Generative AI with medical knowledge
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    'gemini-1.5-pro',
    generation_config={
        'temperature': 0.4,
        'top_p': 0.95,
        'max_output_tokens': 2000
    },
    system_instruction="You are a pharmaceutical expert with deep knowledge of medicine composition and effects."
)

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
    """Comprehensive drug analysis using packaging and medical knowledge"""
    try:
        prompt = """
        Analyze this medicine packaging and provide detailed scientific information in Kurdish Sorani:

        1. ناوی زانستی: [Scientific name + chemical composition]
           - پێکهاتە: [Active ingredients + inactive components]
           - جۆری دەرمان: [Tablet/Capsule/Injection etc.]

        2. ناوی بازرگانی: [Brand names in Kurdistan region if available]

        3. کاریگەرییە باشەکان:
           - [3-5 main therapeutic effects]
           - [Mechanism of action in simple terms]

        4. کاریگەرییە نەخوازراوەکان:
           - [3-5 common side effects]
           - [Rare but serious risks]

        5. زانیارییە تایبەتەکان:
           - [Half-life and metabolism]
           - [Drug interactions to watch for]

        Provide complete information even if not all details are visible on packaging.
        Use your pharmaceutical knowledge to supplement missing information.
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

من دەتوانم ئەم زانیاریانەت پێبڵێم لەسەر هەر دەرمانێک:
- ناوی زانستی و پێکهاتەکەی
- کاریگەرییە باشەکان
- کاریگەرییە نەخوازراوەکان
- زانیارییە تایبەتەکان

تکایە وێنەی پاکەتەکە بنێرە یان ناوی دەرمانەکە بنووسە.
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
            response = f"""
🧪 زانیاری زانستی دەرمان:

{analysis}

⚠️ ئامۆژگاری: هەمیشە پێش بەکارهێنان ڕاوێژ لە پزیشک یان ئەندازیاری دەرمانسازی بکە.
"""
            bot.reply_to(message, response)
    
    except Exception as e:
        bot.reply_to(message, f"هەڵە: {str(e)[:200]}")
    
    finally:
        if os.path.exists(temp_image_path):
            try: os.remove(temp_image_path)
            except: pass

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        response = model.generate_content(f"""
        Provide detailed scientific information in Kurdish Sorani about: {message.text}

        Include:
        1. Scientific name and composition
        2. Therapeutic effects
        3. Side effects
        4. Special pharmacological properties
        """)
        bot.reply_to(message, f"🔍 زانیاری:\n\n{response.text}")
    except Exception as e:
        bot.reply_to(message, f"هەڵە: نەتوانم زانیاری بدۆزمەوە. تکایە ناوەکە ڕاست بنووسە.")

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
    print("Starting advanced medicine bot...")
    run_bot()