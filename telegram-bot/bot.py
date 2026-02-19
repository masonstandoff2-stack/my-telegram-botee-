import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ===== ТВОИ ДАННЫЕ =====
TOKEN = "8356262671:AAEKOnJH3xI8s0FTccF0DbJjYKiCuzOnc7g"
FILE_ID = "BQACAgEAAxkBAAIgTWmXfWAZu8sh3HQC5vQjnrVp-TK-AAIMCQAC4QfARIqc8d_wUUsFOgQ"

# Первый канал
CHANNEL1_ID = "-1003318734165"  # ID первого канала
CHANNEL1_LINK = "https://t.me/br_mason"  # Ссылка на первый канал
CHANNEL1_NAME = "BR MASON"  # Название первого канала

# Второй канал
CHANNEL2_ID = "-1002371853221"  # ID второго канала
CHANNEL2_LINK = "https://t.me/HolidollaModz"  # Ссылка на второй канал
CHANNEL2_NAME = "HolidollaModz"  # Название второго канала


# =======================

async def check_subscription(user_id, context):
    """Проверяет, подписан ли пользователь на оба канала"""
    try:
        # Проверка первого канала
        member1 = await context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=user_id)
        sub1 = member1.status in ['member', 'administrator', 'creator']

        # Проверка второго канала
        member2 = await context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=user_id)
        sub2 = member2.status in ['member', 'administrator', 'creator']

        # Пользователь должен быть подписан на оба канала
        return sub1 and sub2
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False


async def get_unsubscribed_channels(user_id, context):
    """Возвращает список каналов, на которые не подписан пользователь"""
    unsubscribed = []

    try:
        # Проверка первого канала
        member1 = await context.bot.get_chat_member(chat_id=CHANNEL1_ID, user_id=user_id)
        if member1.status not in ['member', 'administrator', 'creator']:
            unsubscribed.append((CHANNEL1_NAME, CHANNEL1_LINK))
    except:
        unsubscribed.append((CHANNEL1_NAME, CHANNEL1_LINK))

    try:
        # Проверка второго канала
        member2 = await context.bot.get_chat_member(chat_id=CHANNEL2_ID, user_id=user_id)
        if member2.status not in ['member', 'administrator', 'creator']:
            unsubscribed.append((CHANNEL2_NAME, CHANNEL2_LINK))
    except:
        unsubscribed.append((CHANNEL2_NAME, CHANNEL2_LINK))

    return unsubscribed


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт - проверяем подписку и показываем кнопку"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        # Кнопка для получения файла
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
        # Получаем список каналов для подписки
        unsubscribed = await get_unsubscribed_channels(user_id, context)

        # Создаем кнопки для каждого канала
        keyboard = []
        for name, link in unsubscribed:
            keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

        # Добавляем кнопку проверки
        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Формируем список каналов для подписки
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


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    first_name = query.from_user.first_name

    if query.data == "get_file":
        is_subscribed = await check_subscription(user_id, context)

        if not is_subscribed:
            # Получаем список каналов для подписки
            unsubscribed = await get_unsubscribed_channels(user_id, context)

            # Создаем кнопки для каждого канала
            keyboard = []
            for name, link in unsubscribed:
                keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

            keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Формируем список каналов для подписки
            channels_list = "\n".join([f"• {name}: {link}" for name, link in unsubscribed])

            await query.edit_message_text(
                f"⚠️ <b>Доступ ограничен</b>\n\n"
                f"{first_name}, для получения файла нужно подписаться на каналы:\n\n"
                f"{channels_list}",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return

        # Отправляем "печатает..." для лучшего UX
        await context.bot.send_chat_action(chat_id=user_id, action="upload_document")

        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=FILE_ID
            )
            logging.info(f"✅ Файл отправлен пользователю {user_id}")

            # Показываем сообщение об успехе
            await query.edit_message_text(
                f"✅ <b>Файл отправлен!</b>\n\n"
                f"Проверь сообщения внизу",
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"❌ Ошибка отправки: {e}")
            await query.edit_message_text(
                "❌ <b>Ошибка</b>\nНе удалось отправить файл. Попробуй позже.",
                parse_mode='HTML'
            )

    elif query.data == "check_subscription":
        # Проверяем подписку после нажатия кнопки
        is_subscribed = await check_subscription(user_id, context)

        if is_subscribed:
            # Если подписан - показываем кнопку получения файла
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
            # Если не подписан - показываем какие каналы остались
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


async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка файла только подписанным"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        # Получаем список каналов для подписки
        unsubscribed = await get_unsubscribed_channels(user_id, context)

        # Создаем кнопки для каждого канала
        keyboard = []
        for name, link in unsubscribed:
            keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {name}", url=link)])

        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Формируем список каналов для подписки
        channels_list = "\n".join([f"• {name}: {link}" for name, link in unsubscribed])

        await update.message.reply_text(
            f"⚠️ <b>Доступ ограничен</b>\n\n"
            f"{first_name}, для получения файла нужно подписаться на каналы:\n\n"
            f"{channels_list}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return

    # Отправляем "печатает..." для лучшего UX
    await context.bot.send_chat_action(chat_id=update.effective_user.id, action="upload_document")

    try:
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=FILE_ID
        )
        logging.info(f"✅ Файл отправлен пользователю {user_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки: {e}")
        await update.message.reply_text(
            "❌ <b>Ошибка</b>\nНе удалось отправить файл. Попробуй позже.",
            parse_mode='HTML'
        )


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


def main():
    """Запуск"""
    print("╔════════════════════════════════╗")
    print("║     🚀 БОТ ЗАПУСКАЕТСЯ...      ║")
    print("╠════════════════════════════════╣")
    print(f"║ 📢 Канал 1: {CHANNEL1_NAME[:15]}...  ║")
    print(f"║ 📢 Канал 2: {CHANNEL2_NAME[:15]}...  ║")
    print("╚════════════════════════════════╝")

    app = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_file))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("\n✅ Бот готов к работе!")
    app.run_polling()


if __name__ == '__main__':
    main()
