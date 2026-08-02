# YOJANA MITHRA - Telegram Bot Integration
# Text-only bot that connects to Django chatbot API
# SAFE: Does not modify any existing logic

import os
import json
import logging
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DJANGO_API_URL = 'http://127.0.0.1:8000/api/chat/text/'

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in .env file!")

# User language preferences (chat_id -> language code)
USER_LANG = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a welcome message when the /start command is issued.
    """
    welcome_message = (
        "🙏 Welcome to YOJANA MITHRA!\n\n"
        "I'm your AI assistant for Government Schemes in India.\n\n"
        "✨ Ask me anything about:\n"
        "• Central & State Government Schemes\n"
        "• Eligibility criteria\n"
        "• Benefits & application process\n"
        "• Agriculture, education, health schemes\n\n"
        "💬 Just type your question and I'll help you!\n\n"
        "Example:\n"
        "- What is PM Kisan scheme?\n"
        "- Schemes for farmers\n"
        "- Education scholarships"
    )
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {update.effective_user.id} started the bot")


async def language_selector(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show language selection inline keyboard.
    """
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi"),
        ],
        [
            InlineKeyboardButton("ಕನ್ನಡ 🇮🇳", callback_data="lang_kn"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 Select your preferred language:\n"
        "चुनें अपनी भाषा | ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        reply_markup=reply_markup
    )
    logger.info(f"User {update.effective_user.id} requested language selection")


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle language selection from inline keyboard.
    """
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang_code = query.data.replace("lang_", "")  # Extract 'en', 'hi', or 'kn'
    
    # Save user preference
    USER_LANG[chat_id] = lang_code
    
    # Language names for confirmation
    lang_names = {
        "en": "English",
        "hi": "हिन्दी (Hindi)",
        "kn": "ಕನ್ನಡ (Kannada)"
    }
    
    lang_name = lang_names.get(lang_code, "English")
    
    await query.edit_message_text(
        f"✅ Language set to {lang_name}\n\n"
        f"Now ask me anything about government schemes!"
    )
    logger.info(f"User {chat_id} selected language: {lang_code}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle all incoming text messages and send them to Django API.
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    
    logger.info(f"User {user_id}: {user_message}")
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    try:
        # Send to Django API with proper payload
        import httpx
        
        # Get user's selected language (default to English)
        user_language = USER_LANG.get(chat_id, "en")
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            payload = {
                "query": user_message,
                "language": user_language  # Use selected language
            }
            
            response = await client.post(
                DJANGO_API_URL,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                # Try multiple possible response field names
                bot_reply = data.get('answer') or data.get('response') or 'Sorry, I could not process your request.'
                
                # Send response back to user
                await update.message.reply_text(bot_reply)
                logger.info(f"Bot replied to user {user_id}")
                
            else:
                error_message = f"⚠️ Backend error {response.status_code}: {response.text}"
                await update.message.reply_text(error_message)
                logger.error(f"API returned status {response.status_code}: {response.text}")
                
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Error connecting to backend: {str(e)}\n"
            "Please make sure the Django server is running."
        )
        logger.error(f"Error handling message for user {user_id}: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log errors caused by updates.
    """
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """
    Start the Telegram bot.
    """
    logger.info("🚀 Starting YOJANA MITHRA Telegram Bot...")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", language_selector))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start polling
    logger.info("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
