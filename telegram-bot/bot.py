import logging
import asyncio
import time
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import TimedOut, NetworkError, RetryAfter

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== ТВОИ ДАННЫЕ =====
TOKEN = "8356262671:AAFpw2GxPp7_DAnFDPX45cn6lr3f3AXUffY"
FILE_ID = "BQACAgEAAxkBAAIgTWmXfWAZu8sh3HQC5vQjnrVp-TK-AAIMCQAC4QfARIqc8d_wUUsFOgQ"
ADMIN_ID = 8426101180  # Замени на свой Telegram ID для получения уведомлений

# Первый канал
CHANNEL1_ID = "-1003318734165"
CHANNEL1_LINK = "https://t.me/br_mason"
CHANNEL1_NAME = "BR MASON"

# Второй канал
CHANNEL2_ID = "-1002371853221"
CHANNEL2_LINK = "https://t.me/HolidollaModz"
CHANNEL2_NAME = "HolidollaModz"

# ===== НАСТРОЙКИ ОПТИМИЗАЦИИ =====
TIMEOUT = 25  # Таймаут для операций (Bothost убивает после 30 секунд)
CACHE_TTL = 60  # Время жизни кэша подписок в секундах
MAX_RETRIES = 3  # Количество попыток при ошибках

# Кэш для результатов проверки подписки
subscription_cache = {}
cache_timestamps = {}

# ===== ДЕКОРАТОР ДЛЯ ОБРАБОТКИ ТАЙМАУТОВ =====
def handle_timeout(func):
    """Декоратор для защиты от таймаутов"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            logger.error(f"⏰ Таймаут в функции {func.__name__}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка в {func.__name__}: {e}")
            return None
    return wrapper

# ===== ОПТИМИЗИРОВАННАЯ ПРОВЕРКА ПОДПИСКИ =====
async def check_subscription(user_id, context):
    """Проверяет подписку на оба канала (с параллельными запросами)"""
    try:
        # Запускаем обе проверки параллельно
        task1 = context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=user_id)
        task2 = context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=user_id)
        
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        
        sub1 = False
        sub2 = False
        
        # Проверяем первый канал
        if not isinstance(results[0], Exception):
            sub1 = results[0].status in ['member', 'administrator', 'creator']
        else:
            logger.warning(f"Ошибка проверки канала 1 для {user_id}: {results[0]}")
        
        # Проверяем второй канал
        if not isinstance(results[1], Exception):
            sub2 = results[1].status in ['member', 'administrator', 'creator']
        else:
            logger.warning(f"Ошибка проверки канала 2 для {user_id}: {results[1]}")
        
        return sub1 and sub2
    except Exception as e:
        logger.error(f"Критическая ошибка проверки подписки: {e}")
        return False

async def check_subscription_cached(user_id, context):
    """Проверка подписки с кэшированием"""
    current_time = time.time()
    
    # Очистка устаревшего кэша (раз в 100 запросов)
    if len(subscription_cache) > 1000:
        cleanup_time = current_time - (CACHE_TTL * 2)
        expired = [uid for uid, ts in cache_timestamps.items() if ts < cleanup_time]
        for uid in expired:
            subscription_cache.pop(uid, None)
            cache_timestamps.pop(uid, None)
    
    # Проверяем кэш
    if user_id in subscription_cache:
        cached_time = cache_timestamps.get(user_id, 0)
        if current_time - cached_time < CACHE_TTL:
            return subscription_cache[user_id]
    
    # Делаем реальную проверку
    result = await check_subscription(user_id, context)
    
    # Сохраняем в кэш
    subscription_cache[user_id] = result
    cache_timestamps[user_id] = current_time
    
    return result

# ===== ИСПРАВЛЕННАЯ ФУНКЦИЯ =====
async def get_unsubscribed_channels(user_id, context):
    """Возвращает список каналов, на которые не подписан пользователь"""
    unsubscribed = []
    
    # Проверяем первый канал
    try:
        member1 = await context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=user_id)
        if member1.status not in ['member', 'administrator', 'creator']:
            unsubscribed.append((CHANNEL1_NAME, CHANNEL1_LINK))
            logger.info(f"Пользователь {user_id} НЕ подписан на {CHANNEL1_NAME}")
    except Exception as e:
        logger.warning(f"Ошибка при проверке канала 1 для {user_id}: {e}")
        # В случае ошибки считаем, что пользователь не подписан
        unsubscribed.append((CHANNEL1_NAME, CHANNEL1_LINK))
        logger.info(f"Добавляем {CHANNEL1_NAME} в список неподписанных из-за ошибки")
    
    # Проверяем второй канал
    try:
        member2 = await context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=user_id)
        if member2.status not in ['member', 'administrator', 'creator']:
            unsubscribed.append((CHANNEL2_NAME, CHANNEL2_LINK))
            logger.info(f"Пользователь {user_id} НЕ подписан на {CHANNEL2_NAME}")
    except Exception as e:
        logger.warning(f"Ошибка при проверке канала 2 для {user_id}: {e}")
        # В случае ошибки считаем, что пользователь не подписан
        unsubscribed.append((CHANNEL2_NAME, CHANNEL2_LINK))
        logger.info(f"Добавляем {CHANNEL2_NAME} в список неподписанных из-за ошибки")
    
    logger.info(f"Для пользователя {user_id} найдено {len(unsubscribed)} неподписанных каналов")
    return unsubscribed

# ===== БЕЗОПАСНАЯ ОТПРАВКА ФАЙЛА =====
async def safe_send_document(context, chat_id, document, max_retries=MAX_RETRIES):
    """Отправка документа с повторными попытками"""
    for attempt in range(max_retries):
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="upload_document")
            await asyncio.sleep(0.5)  # Небольшая задержка перед отправкой
            
            await context.bot.send_document(
                chat_id=chat_id,
                document=document
            )
            logger.info(f"✅ Файл отправлен пользователю {chat_id}")
            return True
            
        except RetryAfter as e:
            wait_time = e.retry_after
            logger.warning(f"⚠️ Telegram просит подождать {wait_time}с")
            await asyncio.sleep(min(wait_time, 5))  # Ждем не больше 5 секунд
            
        except (TimedOut, NetworkError) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"⚠️ Сетевая ошибка, попытка {attempt + 2} через {wait_time}с")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Не удалось отправить файл после {max_retries} попыток")
                return False
                
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке: {e}")
            return False
    
    return False

# ===== ОБРАБОТЧИКИ КОМАНД =====
@handle_timeout
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт - проверяем подписку и показываем кнопку"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Отправляем "печатает..." чтобы пользователь не думал, что бот завис
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    
    is_subscribed = await check_subscription_cached(user_id, context)

    if is_subscribed:
        keyboard = [[
            InlineKeyboardButton("📥 Получить файл", callback_data="get_file")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            f"✨ <b>С возвращением, {first_name}!</b>\n\n"
            f"✅ Вы подписаны на все каналы\n\n"
            f"🎯 Нажми на кнопку ниже, чтобы получить файл"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        unsubscribed = await get_unsubscribed_channels(user_id, context)

        keyboard = []
        for name, link in unsubscribed:
            keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        channels_list = "\n".join([f"• {name}: {link}" for name, link in unsubscribed])

        welcome_text = (
            f"👋 <b>Привет, {first_name}!</b>\n\n"
            f"🔒 <b>Доступ к файлу закрыт</b>\n"
            f"Для получения доступа необходимо подписаться на каналы:\n\n"
            f"{channels_list}\n\n"
            f"<i>✅ После подписки нажми кнопку «Я подписался»</i>"
        )

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

@handle_timeout
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    first_name = query.from_user.first_name

    if query.data == "get_file":
        # Показываем, что бот работает
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        
        is_subscribed = await check_subscription_cached(user_id, context)

        if not is_subscribed:
            unsubscribed = await get_unsubscribed_channels(user_id, context)

            keyboard = []
            for name, link in unsubscribed:
                keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

            keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            channels_list = "\n".join([f"• {name}: {link}" for name, link in unsubscribed])

            await query.edit_message_text(
                f"⚠️ <b>Доступ ограничен</b>\n\n"
                f"{first_name}, для получения файла нужно подписаться на каналы:\n\n"
                f"{channels_list}",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return

        # Отправляем файл
        success = await safe_send_document(context, user_id, FILE_ID)

        if success:
            await query.edit_message_text(
                f"✅ <b>Файл отправлен!</b>\n\n"
                f"Проверь сообщения внизу",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "❌ <b>Ошибка</b>\nНе удалось отправить файл. Попробуй позже.",
                parse_mode='HTML'
            )

    elif query.data == "check_subscription":
        # Показываем, что бот работает
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        
        is_subscribed = await check_subscription_cached(user_id, context)

        if is_subscribed:
            keyboard = [[
                InlineKeyboardButton("📥 Получить файл", callback_data="get_file")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"✅ <b>Отлично, {first_name}!</b>\n\n"
                f"Теперь ты подписан на все каналы\n\n"
                f"Нажми кнопку ниже, чтобы получить файл",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            unsubscribed = await get_unsubscribed_channels(user_id, context)

            keyboard = []
            for name, link in unsubscribed:
                keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

            keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            channels_list = "\n".join([f"• {name}: {link}" for name, link in unsubscribed])

            await query.edit_message_text(
                f"❌ <b>Подписка не найдена</b>\n\n"
                f"{first_name}, ты не подписан на следующие каналы:\n\n"
                f"{channels_list}\n\n"
                f"Пожалуйста, подпишись и нажми кнопку снова",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

@handle_timeout
async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка файла только подписанным"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Отправляем "печатает..."
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    
    is_subscribed = await check_subscription_cached(user_id, context)

    if not is_subscribed:
        unsubscribed = await get_unsubscribed_channels(user_id, context)

        keyboard = []
        for name, link in unsubscribed:
            keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        channels_list = "\n".join([f"• {name}: {link}" for name, link in unsubscribed])

        await update.message.reply_text(
            f"⚠️ <b>Доступ ограничен</b>\n\n"
            f"{first_name}, для получения файла нужно подписаться на каналы:\n\n"
            f"{channels_list}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return

    # Отправляем файл
    await safe_send_document(context, user_id, FILE_ID)

@handle_timeout
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое сообщение = попытка получить файл"""
    await get_file(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    help_text = (
        "📌 <b>Доступные команды:</b>\n\n"
        "/start - проверка подписки на каналы\n"
        "/get - получить файл\n"
        "/help - это сообщение\n\n"
        f"<b>Каналы для подписки:</b>\n"
        f"• {CHANNEL1_NAME}: {CHANNEL1_LINK}\n"
        f"• {CHANNEL2_NAME}: {CHANNEL2_LINK}"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

# ===== ДИАГНОСТИЧЕСКАЯ КОМАНДА =====
async def diagnose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Диагностика проблем с подпиской"""
    user_id = update.effective_user.id
    
    try:
        # Проверяем первый канал
        try:
            member1 = await context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=user_id)
            status1 = f"Статус: {member1.status}"
            is_sub1 = member1.status in ['member', 'administrator', 'creator']
        except Exception as e:
            status1 = f"Ошибка: {type(e).__name__} - {e}"
            is_sub1 = False
        
        # Проверяем второй канал
        try:
            member2 = await context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=user_id)
            status2 = f"Статус: {member2.status}"
            is_sub2 = member2.status in ['member', 'administrator', 'creator']
        except Exception as e:
            status2 = f"Ошибка: {type(e).__name__} - {e}"
            is_sub2 = False
        
        # Проверяем права бота
        try:
            bot_member1 = await context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=context.bot.id)
            bot_status1 = f"Статус бота: {bot_member1.status}"
        except Exception as e:
            bot_status1 = f"Бот не админ или ошибка: {e}"
        
        try:
            bot_member2 = await context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=context.bot.id)
            bot_status2 = f"Статус бота: {bot_member2.status}"
        except Exception as e:
            bot_status2 = f"Бот не админ или ошибка: {e}"
        
        diag_text = f"""
🔍 <b>ДИАГНОСТИКА</b>

👤 <b>Пользователь:</b> {user_id}

📢 <b>Канал 1: {CHANNEL1_NAME}</b>
ID: {CHANNEL1_ID}
{bot_status1}
Ваш статус: {status1}
Подписан: {'✅' if is_sub1 else '❌'}

📢 <b>Канал 2: {CHANNEL2_NAME}</b>
ID: {CHANNEL2_ID}
{bot_status2}
Ваш статус: {status2}
Подписан: {'✅' if is_sub2 else '❌'}

<b>Общий доступ:</b> {'✅ Разрешен' if (is_sub1 and is_sub2) else '❌ Запрещен'}
"""
        
        await update.message.reply_text(diag_text, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка диагностики: {e}")

# ===== ОБРАБОТЧИК ОШИБОК =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"❌ Произошла ошибка: {context.error}")
    
    # Уведомляем админа о критических ошибках
    if ADMIN_ID:
        try:
            error_msg = f"❌ Ошибка бота: {context.error}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=error_msg[:200])
        except:
            pass

# ===== ЗАПУСК БОТА =====
def main():
    """Запуск бота с оптимизациями для Bothost"""
    print("╔════════════════════════════════╗")
    print("║     🚀 БОТ ЗАПУСКАЕТСЯ...      ║")
    print("╠════════════════════════════════╣")
    print(f"║ 📢 Канал 1: {CHANNEL1_NAME[:15]}...  ║")
    print(f"║ 📢 Канал 2: {CHANNEL2_NAME[:15]}...  ║")
    print("╠════════════════════════════════╣")
    print("║ ⚡ Режим: Оптимизированный      ║")
    print("║ 🔒 Таймаут: 25 сек              ║")
    print("║ 💾 Кэш: 60 сек                  ║")
    print("╚════════════════════════════════╝")

    # Создаем приложение с настройками для Bothost
    app = Application.builder()\
        .token(TOKEN)\
        .connect_timeout(20)\
        .read_timeout(20)\
        .write_timeout(20)\
        .build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_file))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("diag", diagnose))  # Новая диагностическая команда
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Добавляем глобальный обработчик ошибок
    app.add_error_handler(error_handler)

    print("\n✅ Бот готов к работе!")
    print("📡 Запуск polling...\n")

    try:
        app.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True,  # Пропускаем старые обновления
            close_loop=True  # Закрываем цикл при выходе
        )
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == '__main__':
    main()
