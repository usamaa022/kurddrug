import os
import telebot
from PIL import Image
import google.generativeai as genai

# Configure your API keys
TELEGRAM_BOT_TOKEN = '7322174132:AAF2xMjQxZ5P90BnTvR7PODP1H02uXQwCP0'
GOOGLE_API_KEY = 'AIzaSyAf6pEnDG9xuJRyaSjbNzetmG2Qn2q2uYE'

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the generative model (using current recommended model)
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_medicine_image(image):
    """
    Analyze the medicine packaging image and generate a detailed description
    """
    try:
        # Detailed prompt for medicine identification
        prompt = """
        Identify this medicine from its packaging and provide detailed information in Kurdish Sorani.
        Include:
        1. Exact name of the medicine (brand and generic if available)
        2. Primary medical use and what conditions it treats
        3. Important safety information including:
           - If it's safe for pregnant women (highlight if dangerous)
           - Common side effects
           - Any important warnings
        4. Typical dosage (but remind to consult doctor)
        
        If you cannot clearly identify the medicine, respond:
        "ناتوانم دەرمانەکە ناسایەوە. تکایە وێنەیەکی باشتر و ڕوونتر بنێرە، بە تایبەتی ناوی دەرمانەکە و زانیارییەکانی تر."
        
        Format your response clearly in Kurdish Sorani with appropriate warnings.
        """
        
        # Generate response
        response = model.generate_content([prompt, image])
        return response.text
    
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
        # Download the photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save the file temporarily
        with open(temp_image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Open and process the image
        with Image.open(temp_image_path) as img:
            # Analyze the image
            description = analyze_medicine_image(img)
            
            # Add disclaimer
            disclaimer = "\n\n هەمیشە ڕاوێژ بە پزیشکی پسپۆڕ بکە"
            full_response = description + disclaimer
            
            # Reply with the description
            bot.reply_to(message, full_response)
    
    except Exception as e:
        bot.reply_to(message, f"هەڵەیەک ڕووی دا: {str(e)}\nتکایە دووبارەی بکەرەوە.")
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except:
                pass

# Start the bot
print("Bot is running...")
bot.polling()