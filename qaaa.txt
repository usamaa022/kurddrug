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
    Analyze the medicine packaging image and generate a description
    """
    try:
        # Prompt for medicine identification and description
        prompt = """
        Identify the medicine from this packaging. 
        Provide the following details in Kurdish Sorani:
        1. Name of the medicine
        2. Primary medical use
        3. Brief description of what condition it treats
        
        Respond only in Kurdish Sorani language.
        If you cannot identify the medicine, say: 
        "ناتوانم دەرمانەکە ناسایەوە. تکایە وێنەیەکی باشتر و ڕوونتر بنێرە."
        """
        
        # Generate response
        response = model.generate_content([prompt, image])
        return response.text
    
    except Exception as e:
        return f"هەڵە ڕووی دا: {str(e)}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    بەخێربێیت! 👋
    
    تکایە وێنەی پاکێتی دەرمانێک بنێرە، 
    منیش پێت دەڵێم بۆ چی بەکاردەهێنرێت.
    
    Please send me an image of a medicine packaging,
    and I'll tell you what it's used for in Kurdish Sorani.
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
            
            # Reply with the description
            bot.reply_to(message, description)
    
    except Exception as e:
        bot.reply_to(message, f"هەڵەیەک ڕووی دا: {str(e)}")
    
    finally:
        # Clean up the temporary file if it exists
        if os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except:
                pass  # Skip if file is already removed or locked

# Start the bot
print("Bot is running...")
bot.polling()