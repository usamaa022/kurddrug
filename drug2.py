import os
import time
import threading
import telebot
from PIL import Image
import google.generativeai as genai
from requests.exceptions import ConnectionError, ReadTimeout
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Configure API keys
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_telegram_token')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'your_google_ai_key')

# Initialize Telegram Bot
bot = telebot.TeleBot(
    TELEGRAM_BOT_TOKEN,
    threaded=False,
    num_threads=1,
    skip_pending=True
)

# Configure Google Generative AI with enhanced settings
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    'gemini-1.5-pro',
    generation_config={
        'temperature': 0.3,  # More focused responses
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 3000
    },
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
)

# Health Check Server (same as before)
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

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
        # Convert to RGB if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Enhance contrast and sharpness
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        return img
    except Exception:
        return img  # Return original if enhancement fails

def analyze_medicine_image(image):
    """Advanced medicine analysis with structured output"""
    try:
        # Enhanced prompt with strict formatting
        prompt = """
        You are a pharmaceutical expert analyzing medicine packaging. Provide detailed information in Kurdish Sorani following this EXACT format:

        🏷 ناوی دەرمان: [Brand Name] / [Generic Name]
        🏥 بەکارهێنان: [Primary uses - list 3-5 main uses]
        ⚠️ ئاگاداریەکان: 
        - [Warning 1]
        - [Warning 2]
        - [Warning 3]
        🤰 مەترسی بۆ دووگیان: [Safe/Unsafe] - [Explanation]
        💊 دەرمانەکە: [Pill color/shape description]
        📅 ماوەی بەکارهێنان: [Duration if applicable]
        💰 نرخی نزیک: [Approximate price if visible]
        🩺 پێشنیاری تایبەت: [Any special instructions]

        If the medicine cannot be clearly identified:
        "نەتوانم دەرمانەکە دیاری بکەم. تکایە وێنەیەکی ڕوونتر بنێرە بە تایبەتی بەشی ناوی دەرمانەکە و زانیارییەکانی تر."

        Important notes:
        1. Be extremely accurate with drug names
        2. Highlight dangerous interactions
        3. Mention if prescription is required
        4. Include dosage form (tablet, capsule, etc.)
        5. Specify storage conditions if visible
        """
        
        # Enhance image quality before processing
        enhanced_img = enhance_image_quality(image)
        
        # Generate response with retry logic
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
        return f"هەڵەیەک ڕوویدا لە خوێندنەوەی وێنەکە: {str(e)}\nتکایە دووبارەی بکەرەوە بە وێنەیەکی ڕوونتر."

# (Keep the same handle_medicine_photo, run_bot, and main code as before)
# ... [Rest of your existing code remains unchanged]

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
            response = f"🔍 نەتیجەی پشکنین:\n\n{description}\n\n⚠️ هەمیشە ڕاوێژ لە پزیشک یان ئەندازیاری دەرمانسازی بکە پێش بەکارهێنان."
            bot.reply_to(message, response)
    
    except Exception as e:
        bot.reply_to(message, f"هەڵە: {str(e)[:200]}\nتکایە وێنەیەکی ڕوونتر بنێرە.")
    
    finally:
        if os.path.exists(temp_image_path):
            try: 
                os.remove(temp_image_path)
            except: 
                pass

if __name__ == '__main__':
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("Bot starting with enhanced drug recognition...")
    run_bot()