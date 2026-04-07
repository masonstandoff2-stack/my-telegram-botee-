import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8356262671:AAFpw2GxPp7_DAnFDPX45cn6lr3f3AXUffY"
FILE_ID = "BQACAgEAAxkBAAJEBWnVX0AQEGb69MvQdXdMffK8TJcyAAK5BAACxMapRpsTtfWl18ACOwQ"

# Только один канал
CHANNEL_ID = "-1003204433403"
CHANNEL_LINK = "https://t.me/MansoryHolidolla_br"
CHANNEL_NAME = "MansoryHolidolla"

# ===== ПРОСТАЯ ПРОВЕРКА ПОДПИСКИ =====
async def check_user_subscription(user_id, context):
    """Проверяет подписку пользователя на канал"""
    try:
        # Проверяем канал
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            is_subscribed = member.status in ['member', 'administrator', 'creator']
            logger.info(f"Канал: статус {member.status} для {user_id}")
            return is_subscribed
        except Exception as e:
            logger.error(f"Ошибка проверки канала: {e}")
            return False
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        return False

# ===== СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Проверяем подписку
    is_subscribed = await check_user_subscription(user_id, context)
    
    if is_subscribed:
        # Подписан на канал
        keyboard = [[InlineKeyboardButton("📥 Получить файл", callback_data="get_file")]]
        await update.message.reply_text(
            f"✅ Привет, {first_name}!\nТы подписан на канал.\nНажми кнопку для получения файла.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Не подписан
        keyboard = [
            [InlineKeyboardButton(f"📢 Подписаться на {CHANNEL_NAME}", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Я подписался", callback_data="check_subs")]
        ]
        
        await update.message.reply_text(
            f"❌ Привет, {first_name}!\nПодпишись на канал и нажми кнопку:",
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
        is_subscribed = await check_user_subscription(user_id, context)
        
        if is_subscribed:
            # Всё хорошо
            keyboard = [[InlineKeyboardButton("📥 Получить файл", callback_data="get_file")]]
            await query.edit_message_text(
                f"✅ Отлично, {first_name}! Теперь ты подписан на канал.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Всё ещё не подписан
            keyboard = [
                [InlineKeyboardButton(f"📢 {CHANNEL_NAME}", url=CHANNEL_LINK)],
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_subs")]
            ]
            
            await query.edit_message_text(
                f"❌ {first_name}, ты всё ещё не подписан на канал!",
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
    
    # Проверяем канал
    try:
        chat = await context.bot.get_chat(CHANNEL_ID)
        text += f"✅ Канал найден: {chat.title}\n"
        
        try:
            bot_in_channel = await context.bot.get_chat_member(CHANNEL_ID, context.bot.id)
            text += f"   Бот в канале: {bot_in_channel.status}\n"
        except Exception as e:
            text += f"❌ Бот не в канале: {e}\n"
            
        try:
            user_in_channel = await context.bot.get_chat_member(CHANNEL_ID, user_id)
            text += f"   Вы в канале: {user_in_channel.status}\n"
        except Exception as e:
            text += f"❌ Ошибка проверки вас: {e}\n"
            
    except Exception as e:
        text += f"❌ Канал недоступен: {e}\n"
    
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
