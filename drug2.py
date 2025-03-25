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

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={
        'temperature': 0.3,
        'max_output_tokens': 1000
    }
)

def enhance_image_quality(img):
    """Improve image quality for better text recognition"""
    try:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        return img
    except Exception:
        return img

def analyze_medicine_image(image):
    """Medicine analysis with essential scientific information"""
    try:
        prompt = """
        لە کوردی سۆرانیدا تەنیا ئەم زانیارییانە بڵێ:
        
        1. ناوی زانستی دەرمان: [ناوی زانستی]
        2. ناوی بازرگانی: [ناوی بازرگانی]
        
        3. بەکارهێنان:
        - [بۆ کامی نەخۆشی/ئازار بەکاردێت]
        
        4. سوودەکان:
        - [سودی سەرەکی]
        
        5. زیانەکان:
        - [کاریگەرییە نەخوازراوە سەرەکییەکان]

        ئەگەر ناتوانیت دەرمانەکە بشناسیتەوە:
        "نەتوانم دەرمانەکە بشناسمەوە. تکایە وێنەیەکی ڕوونتر بنێرە"
        """
        
        enhanced_img = enhance_image_quality(image)
        response = model.generate_content([prompt, enhanced_img])
        return response.text
    
    except Exception as e:
        return f"هەڵەیەک ڕوویدا: {str(e)}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    بەخێربێیت بۆ بۆتی زانیاری دەرمانی 🔬

تکایە وێنەی پاکەتی دەرمانێک بنێرە بۆ بینینی:
- ناوی زانستی و بازرگانی
- بۆ چ بەکاردێت
- سوود و زیانەکانی
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
🔬 زانیاری دەرمان:

{description}

⚠️ ئامۆژگاری: هەمیشە پێش بەکارهێنان ڕاوێژ لە پزیشک بکە.
"""
            bot.reply_to(message, response)
    
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
    print("Starting medicine information bot...")
    run_bot()