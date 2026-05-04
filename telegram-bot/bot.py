import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8356262671:AAFpw2GxPp7_DAnFDPX45cn6lr3f3AXUffY"
FILE_ID = "BQACAgEAAxkBAAJNeGnzuNkvB8tWf8kKXcIAAcYXE9Gd6wACbwYAAph-oUfzL5FFEmDfbDsE"
OWNER_ID = 8733257796  # ЗАМЕНИТЕ НА ВАШ TELEGRAM ID (узнайте у @userinfobot)

# Хранилище последнего пользователя, которому писал владелец
last_user_reply = {}

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
    
    # Создаём клавиатуру с поддержкой
    keyboard_main = [
        [InlineKeyboardButton("📥 Получить файл", callback_data="get_file")],
        [InlineKeyboardButton("💬 Техподдержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    
    if all_subscribed:
        # Подписан на все каналы
        await update.message.reply_text(
            f"✅ Привет, {first_name}!\n"
            f"Ты подписан на все каналы.\n\n"
            f"📥 Нажми кнопку для получения файла\n"
            f"💬 Или напиши в техподдержку если есть вопросы",
            reply_markup=InlineKeyboardMarkup(keyboard_main)
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
            f"❌ Привет, {first_name}!\n"
            f"Подпишись на эти каналы:\n{missing_text}\n\n"
            f"После подписки нажми кнопку:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== ТЕХПОДДЕРЖКА - ОБРАБОТКА СООБЩЕНИЙ =====
async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений в техподдержку"""
    user = update.effective_user
    message = update.message
    
    # Если это владелец - не пересылаем, это ответы
    if user.id == OWNER_ID:
        return
    
    # Пересылаем сообщение владельцу
    await forward_to_owner(update, context)

async def forward_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение от пользователя владельцу"""
    user = update.effective_user
    message = update.message
    
    # Формируем информацию о пользователе
    user_info = (
        f"🆕 <b>НОВОЕ СООБЩЕНИЕ В ПОДДЕРЖКУ!</b>\n"
        f"{'─' * 30}\n"
        f"👤 <b>Пользователь:</b> {user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"📱 <b>Username:</b> @{user.username if user.username else 'нет'}\n"
        f"🔗 <b>Ссылка:</b> tg://user?id={user.id}\n"
        f"{'─' * 30}\n"
        f"💬 <b>Сообщение:</b>\n"
        f"{message.text if message.text else '[Не текстовое сообщение]'}\n"
        f"{'─' * 30}"
    )
    
    # Отправляем владельцу информацию + пересылаем сообщение
    try:
        # Сначала отправляем информацию
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=user_info,
            parse_mode="HTML"
        )
        
        # Пересылаем само сообщение (если это не текст)
        if message.text:
            # Для текста уже отправили выше
            pass
        elif message.photo:
            await message.photo[-1].copy(chat_id=OWNER_ID, caption=f"📸 Фото от {user.full_name}")
        elif message.voice:
            await message.voice.copy(chat_id=OWNER_ID, caption=f"🎤 Голосовое от {user.full_name}")
        elif message.video:
            await message.video.copy(chat_id=OWNER_ID, caption=f"🎥 Видео от {user.full_name}")
        elif message.document:
            await message.document.copy(chat_id=OWNER_ID, caption=f"📄 Документ от {user.full_name}")
        else:
            await context.bot.send_message(chat_id=OWNER_ID, text=f"⚠️ Неподдерживаемый тип сообщения")
        
        # Подсказка для ответа
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"✍️ <b>ЧТОБЫ ОТВЕТИТЬ:</b>\n"
                 f"Просто напишите ответ на это сообщение!\n"
                 f"Бот сам отправит его пользователю {user.id}",
            parse_mode="HTML"
        )
        
        # Сохраняем ID пользователя в контексте для ответа
        # Ключом будет message_id последнего сообщения от владельца
        context.bot_data[f"reply_to_{OWNER_ID}"] = user.id
        
        # Подтверждение пользователю
        await message.reply_text(
            "✅ <b>Сообщение отправлено в техподдержку!</b>\n\n"
            "📬 Мы ответим вам в ближайшее время.\n"
            "💡 Ответ придёт в этот диалог.",
            parse_mode="HTML"
        )
        
        logger.info(f"Сообщение от {user.id} переслано владельцу")
        
    except Exception as e:
        logger.error(f"Ошибка при пересылке: {e}")
        await message.reply_text("❌ Ошибка при отправке сообщения. Попробуйте позже.")

# ===== ОБРАБОТКА ОТВЕТОВ ОТ ВЛАДЕЛЬЦА =====
async def handle_owner_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответы владельца (ПРОСТОЙ ТЕКСТ или ОТВЕТ на сообщение)"""
    user = update.effective_user
    
    # Только владелец может отвечать
    if user.id != OWNER_ID:
        return
    
    message = update.message
    reply_text = message.text
    
    if not reply_text:
        await message.reply_text("❌ Пожалуйста, отправьте текст ответа")
        return
    
    # СПОСОБ 1: Ответ на конкретное сообщение от бота
    if message.reply_to_message:
        # Пытаемся найти ID пользователя из пересланного сообщения
        reply_to_msg = message.reply_to_message
        
        # Проверяем, есть ли в тексте ID пользователя
        import re
        user_id_match = re.search(r'ID:</code> <code>(\d+)</code>', reply_to_msg.text or '')
        if user_id_match:
            target_user_id = int(user_id_match.group(1))
        else:
            # Ищем в bot_data сохранённый ID
            target_user_id = context.bot_data.get(f"reply_to_{OWNER_ID}")
            
        if target_user_id:
            await send_reply_to_user(update, context, target_user_id, reply_text)
            return
    
    # СПОСОБ 2: Просто текст (без ответа) - используем последнего пользователя
    target_user_id = context.bot_data.get(f"reply_to_{OWNER_ID}")
    if target_user_id:
        await send_reply_to_user(update, context, target_user_id, reply_text)
    else:
        await message.reply_text(
            "❌ <b>Не могу определить кому отвечать!</b>\n\n"
            "📝 <b>Как ответить пользователю:</b>\n"
            "1️⃣ <b>Ответьте на сообщение</b> которое пришло от бота (из поддержки)\n"
            "2️⃣ Или сначала получите сообщение от пользователя, а потом напишите ответ\n\n"
            "💡 <b>Пример:</b>\n"
            "Пользователь: Здравствуйте!\n"
            "Бот пересылает вам → вы отвечаете на это сообщение бота",
            parse_mode="HTML"
        )

async def send_reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, reply_text: str):
    """Отправляет ответ пользователю"""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📬 <b>Ответ от поддержки:</b>\n\n{reply_text}\n\n"
                 f"─" * 30 + "\n"
                 f"❓ <i>Остались вопросы? Просто напишите их сюда!</i>",
            parse_mode="HTML"
        )
        
        # Подтверждение владельцу
        await update.message.reply_text(
            f"✅ <b>Ответ успешно отправлен!</b>\n\n"
            f"👤 <b>Пользователь ID:</b> <code>{user_id}</code>\n"
            f"💬 <b>Текст ответа:</b>\n{reply_text}",
            parse_mode="HTML"
        )
        
        logger.info(f"Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка при отправке!</b>\n\n"
            f"Пользователь {user_id} возможно заблокировал бота.\n"
            f"Ошибка: {e}",
            parse_mode="HTML"
        )

# ===== ОБРАБОТЧИК КНОПОК =====
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
            keyboard = [
                [InlineKeyboardButton("📥 Получить файл", callback_data="get_file")],
                [InlineKeyboardButton("💬 Техподдержка", callback_data="support")],
                [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
            ]
            await query.edit_message_text(
                f"✅ Отлично, {first_name}! Теперь ты подписан на все каналы.\n\n"
                f"📥 Нажми кнопку для получения файла\n"
                f"💬 Или напиши в техподдержку если есть вопросы",
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
    
    elif query.data == "support":
        await query.edit_message_text(
            f"💬 <b>Техподдержка</b>\n\n"
            f"Напишите ваш вопрос подробно, и мы ответим вам в ближайшее время.\n\n"
            f"📝 <b>Примеры вопросов:</b>\n"
            f"• Не приходит файл\n"
            f"• Вопросы по боту\n"
            f"• Предложения и пожелания\n\n"
            f"✍️ <b>Просто напишите ваше сообщение ниже:</b>",
            parse_mode="HTML"
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            f"📖 <b>Помощь и инструкция</b>\n\n"
            f"🤖 <b>Как пользоваться ботом:</b>\n"
            f"1️⃣ Подпишитесь на все каналы\n"
            f"2️⃣ Нажмите «Получить файл»\n"
            f"3️⃣ Скачайте файл\n\n"
            f"💬 <b>Техподдержка:</b>\n"
            f"Если у вас возникли проблемы, нажмите кнопку «Техподдержка» и опишите вашу проблему.\n\n"
            f"⏱ <b>Время ответа:</b>\n"
            f"Обычно мы отвечаем в течение 24 часов.\n\n"
            f"❓ <b>Частые вопросы:</b>\n"
            f"• Файл не скачивается? Проверьте интернет и попробуйте снова.\n"
            f"• Не вижу файл? Нажмите «Получить файл» ещё раз.\n"
            f"• Вопрос не в тему? Напишите в техподдержку.\n\n"
            f"📌 <b>Важно:</b> Не спамьте, это может привести к блокировке.",
            parse_mode="HTML"
        )

# ===== ДИАГНОСТИКА =====
async def diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса бота"""
    user_id = update.effective_user.id
    
    text = f"🔍 <b>Диагностика для {user_id}:</b>\n\n"
    
    for channel in CHANNELS:
        channel_id = channel["id"]
        channel_name = channel["name"]
        
        text += f"📢 <b>Канал:</b> {channel_name}\n"
        
        try:
            chat = await context.bot.get_chat(channel_id)
            text += f"   ✅ Найден: {chat.title}\n"
            
            try:
                bot_in_channel = await context.bot.get_chat_member(channel_id, context.bot.id)
                text += f"   🤖 Бот в канале: {bot_in_channel.status}\n"
            except Exception as e:
                text += f"   ❌ Бот не в канале: {e}\n"
                
            try:
                user_in_channel = await context.bot.get_chat_member(channel_id, user_id)
                text += f"   👤 Вы в канале: {user_in_channel.status}\n"
            except Exception as e:
                text += f"   ❌ Ошибка проверки вас: {e}\n"
                
        except Exception as e:
            text += f"   ❌ Канал недоступен: {e}\n"
        
        text += "\n"
    
    # Проверка настройки владельца
    text += f"👑 <b>Владелец ID:</b> <code>{OWNER_ID}</code>\n"
    if update.effective_user.id == OWNER_ID:
        text += "✅ <b>Вы владелец бота</b>"
    
    await update.message.reply_text(text, parse_mode="HTML")

# ===== ОБРАБОТЧИК ОШИБОК =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирование ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_user:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⚠️ <b>Ошибка в боте</b>\n\n"
                 f"👤 Пользователь: {update.effective_user.id}\n"
                 f"❌ Ошибка: {context.error}",
            parse_mode="HTML"
        )

# ===== ЗАПУСК =====
def main():
    print("🚀 Запуск бота...")
    print(f"👑 Владелец ID: {OWNER_ID}")
    print("📨 Все сообщения в техподдержку будут пересылаться владельцу")
    print("✍️ Просто отвечайте на сообщения бота - они уйдут пользователю!\n")
    
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("diag", diag))
    
    # Регистрируем обработчики сообщений
    # Сначала проверяем, не владелец ли это (ответы)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(user_id=OWNER_ID),
        handle_owner_reply
    ))
    
    # Обработка сообщений от обычных пользователей
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.User(user_id=OWNER_ID),
        support_message
    ))
    
    # Регистрируем обработчики кнопок
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Регистрируем обработчик ошибок
    app.add_error_handler(error_handler)
    
    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    main()
