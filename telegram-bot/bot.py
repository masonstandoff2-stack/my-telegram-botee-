import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8356262671:AAFpw2GxPp7_DAnFDPX45cn6lr3f3AXUffY"
FILE_ID = "BQACAgEAAxkBAAIgTWmXfWAZu8sh3HQC5vQjnrVp-TK-AAIMCQAC4QfARIqc8d_wUUsFOgQ"

# Каналы
CHANNEL1_ID = "-1003318734165"
CHANNEL1_LINK = "https://t.me/br_mason"
CHANNEL1_NAME = "BR MASON"

CHANNEL2_ID = "-1002371853221"
CHANNEL2_LINK = "https://t.me/HolidollaModz"
CHANNEL2_NAME = "HolidollaModz"

# ===== ПРОСТАЯ ПРОВЕРКА ПОДПИСКИ =====
async def check_user_subscription(user_id, context):
    """Проверяет подписку пользователя на каналы"""
    try:
        # Проверяем 1 канал
        try:
            member1 = await context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=user_id)
            sub1 = member1.status in ['member', 'administrator', 'creator']
            logger.info(f"Канал 1: статус {member1.status} для {user_id}")
        except Exception as e:
            logger.error(f"Ошибка канала 1: {e}")
            sub1 = False
        
        # Проверяем 2 канал
        try:
            member2 = await context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=user_id)
            sub2 = member2.status in ['member', 'administrator', 'creator']
            logger.info(f"Канал 2: статус {member2.status} для {user_id}")
        except Exception as e:
            logger.error(f"Ошибка канала 2: {e}")
            sub2 = False
        
        return sub1, sub2
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        return False, False

# ===== СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Проверяем подписку
    sub1, sub2 = await check_user_subscription(user_id, context)
    
    if sub1 and sub2:
        # Подписан на всё
        keyboard = [[InlineKeyboardButton("📥 Получить файл", callback_data="get_file")]]
        await update.message.reply_text(
            f"✅ Привет, {first_name}!\nТы подписан на все каналы.\nНажми кнопку для получения файла.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Не подписан
        keyboard = []
        if not sub1:
            keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {CHANNEL1_NAME}", url=CHANNEL1_LINK)])
        if not sub2:
            keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {CHANNEL2_NAME}", url=CHANNEL2_LINK)])
        
        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subs")])
        
        await update.message.reply_text(
            f"❌ Привет, {first_name}!\nПодпишись на каналы и нажми кнопку:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== КНОПКИ =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    if query.data == "check_subs":
        # Проверяем подписку
        sub1, sub2 = await check_user_subscription(user_id, context)
        
        if sub1 and sub2:
            # Всё хорошо
            keyboard = [[InlineKeyboardButton("📥 Получить файл", callback_data="get_file")]]
            await query.edit_message_text(
                f"✅ Отлично, {first_name}! Теперь ты подписан на все каналы.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Всё ещё не подписан
            keyboard = []
            if not sub1:
                keyboard.append([InlineKeyboardButton(f"📢 {CHANNEL1_NAME}", url=CHANNEL1_LINK)])
            if not sub2:
                keyboard.append([InlineKeyboardButton(f"📢 {CHANNEL2_NAME}", url=CHANNEL2_LINK)])
            
            keyboard.append([InlineKeyboardButton("🔄 Проверить снова", callback_data="check_subs")])
            
            await query.edit_message_text(
                f"❌ {first_name}, ты всё ещё не подписан на некоторые каналы!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == "get_file":
        # Отправляем файл
        try:
            await query.edit_message_text("📤 Отправляю файл...")
            await context.bot.send_document(chat_id=user_id, document=FILE_ID)
            await query.edit_message_text("✅ Файл отправлен!")
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {e}")

# ===== ДИАГНОСТИКА =====
async def diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса бота"""
    user_id = update.effective_user.id
    
    text = f"🔍 Диагностика для {user_id}:\n\n"
    
    # Проверяем канал 1
    try:
        chat1 = await context.bot.get_chat(CHANNEL1_ID)
        text += f"✅ Канал 1 найден: {chat1.title}\n"
        
        try:
            bot_in_channel = await context.bot.get_chat_member(CHANNEL1_ID, context.bot.id)
            text += f"   Бот в канале: {bot_in_channel.status}\n"
        except Exception as e:
            text += f"❌ Бот не в канале 1: {e}\n"
            
        try:
            user_in_channel = await context.bot.get_chat_member(CHANNEL1_ID, user_id)
            text += f"   Вы в канале: {user_in_channel.status}\n"
        except Exception as e:
            text += f"❌ Ошибка проверки вас: {e}\n"
            
    except Exception as e:
        text += f"❌ Канал 1 недоступен: {e}\n"
    
    text += "\n"
    
    # Проверяем канал 2
    try:
        chat2 = await context.bot.get_chat(CHANNEL2_ID)
        text += f"✅ Канал 2 найден: {chat2.title}\n"
        
        try:
            bot_in_channel = await context.bot.get_chat_member(CHANNEL2_ID, context.bot.id)
            text += f"   Бот в канале: {bot_in_channel.status}\n"
        except Exception as e:
            text += f"❌ Бот не в канале 2: {e}\n"
            
        try:
            user_in_channel = await context.bot.get_chat_member(CHANNEL2_ID, user_id)
            text += f"   Вы в канале: {user_in_channel.status}\n"
        except Exception as e:
            text += f"❌ Ошибка проверки вас: {e}\n"
            
    except Exception as e:
        text += f"❌ Канал 2 недоступен: {e}\n"
    
    await update.message.reply_text(text)

# ===== ЗАПУСК =====
def main():
    print("🚀 Запуск бота...")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("diag", diag))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    main()
