import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading
import time

# Flask для Render (webhook)
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health_check():
    return "🤖 Metodist-CoT работает! Telegram: @твойбот | Render OK"

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK'

# Telegram bot
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🤖 Методист-CoT готов! Отправь промпт.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text(f'🔄 Обрабатываю: {prompt[:50]}...')
    
    # ТВОЙ КОД YandexGPT здесь!
    response = "✅ Ответ от YandexGPT"  # Замени на реальный вызов API
    
    await update.message.reply_text(response)

# Bot application
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

def run_bot():
    """Запуск Telegram polling"""
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Запуск Flask в фоне
    flask_thread = threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запуск Telegram бота
    print("🚀 Starting Metodist-CoT...")
    run_bot()
