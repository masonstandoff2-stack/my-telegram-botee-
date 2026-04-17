import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8356262671:AAFpw2GxPp7_DAnFDPX45cn6lr3f3AXUffY"
FILE_ID = "BQACAgEAAxkBAAJIkGngzW4twTnNwnYUdMDV7rKFeY5iAAKRBwADAwhHBiAIjp65c3Y7BA"

# ===== КАНАЛЫ ДЛЯ ПОДПИСКИ =====
CHANNELS = [
    {
        "id": "-1003204433403",
        "link": "https://t.me/MansoryHolidolla_br",
        "name": "Mansory Holidolla"
    },
    {
        "id": "-1003758523737",
        "link": "https://t.me/JoonNovember",
        "name": "Резерв"
    }
]

# ===== ПРОВЕРКА ПОДПИСКИ НА ВСЕ КАНАЛЫ =====
async def check_user_subscription(user_id, context):
    """Проверяет подписку пользователя на ВСЕ каналы"""
    results = {}
    
    for channel in CHANNELS:
        channel_id = channel["id"]
        channel_name = channel["name"]
        
        try:
            member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            is_subscribed = member.status in ['member', 'administrator', 'creator']
            results[channel_name] = is_subscribed
            logger.info(f"Канал {channel_name}: статус {member.status} для {user_id}")
        except Exception as e:
            logger.error(f"Ошибка проверки канала {channel_name}: {e}")
            results[channel_name] = False
    
    # Подписан ли на ВСЕ каналы
    all_subscribed = all(results.values())
    return all_subscribed, results

# ===== СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Проверяем подписку на все каналы
    all_subscribed, subscriptions = await check_user_subscription(user_id, context)
    
    if all_subscribed:
        # Подписан на все каналы
        keyboard = [[InlineKeyboardButton("📥 Получить файл", callback_data="get_file")]]
        await update.message.reply_text(
            f"✅ Привет, {first_name}!\nТы подписан на все каналы.\nНажми кнопку для получения файла.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Не подписан на некоторые каналы
        keyboard = []
        
        # Добавляем кнопки для неподписанных каналов
        for channel in CHANNELS:
            if not subscriptions.get(channel["name"], False):
                keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {channel['name']}", url=channel["link"])])
        
        keyboard.append([InlineKeyboardButton("✅ Я подписался на всё", callback_data="check_subs")])
        
        # Список каналов, на которые нужно подписаться
        missing_channels = [ch["name"] for ch in CHANNELS if not subscriptions.get(ch["name"], False)]
        missing_text = "\n".join([f"• {ch}" for ch in missing_channels])
        
        await update.message.reply_text(
            f"❌ Привет, {first_name}!\nПодпишись на эти каналы:\n{missing_text}\n\nПосле подписки нажми кнопку:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== КНОПКИ =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    if query.data == "check_subs":
        # Проверяем подписку на все каналы
        all_subscribed, subscriptions = await check_user_subscription(user_id, context)
        
        if all_subscribed:
            # Всё хорошо
            keyboard = [[InlineKeyboardButton("📥 Получить файл", callback_data="get_file")]]
            await query.edit_message_text(
                f"✅ Отлично, {first_name}! Теперь ты подписан на все каналы.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Всё ещё не подписан на некоторые каналы
            keyboard = []
            
            # Добавляем кнопки для неподписанных каналов
            for channel in CHANNELS:
                if not subscriptions.get(channel["name"], False):
                    keyboard.append([InlineKeyboardButton(f"📢 {channel['name']}", url=channel["link"])])
            
            keyboard.append([InlineKeyboardButton("🔄 Проверить снова", callback_data="check_subs")])
            
            # Список каналов, на которые нужно подписаться
            missing_channels = [ch["name"] for ch in CHANNELS if not subscriptions.get(ch["name"], False)]
            missing_text = "\n".join([f"• {ch}" for ch in missing_channels])
            
            await query.edit_message_text(
                f"❌ {first_name}, ты всё ещё не подписан на эти каналы:\n{missing_text}",
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
    
    for channel in CHANNELS:
        channel_id = channel["id"]
        channel_name = channel["name"]
        
        text += f"📢 Канал: {channel_name}\n"
        
        try:
            chat = await context.bot.get_chat(channel_id)
            text += f"   ✅ Найден: {chat.title}\n"
            
            try:
                bot_in_channel = await context.bot.get_chat_member(channel_id, context.bot.id)
                text += f"   Бот в канале: {bot_in_channel.status}\n"
            except Exception as e:
                text += f"   ❌ Бот не в канале: {e}\n"
                
            try:
                user_in_channel = await context.bot.get_chat_member(channel_id, user_id)
                text += f"   Вы в канале: {user_in_channel.status}\n"
            except Exception as e:
                text += f"   ❌ Ошибка проверки вас: {e}\n"
                
        except Exception as e:
            text += f"   ❌ Канал недоступен: {e}\n"
        
        text += "\n"
    
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
