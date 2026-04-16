import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8356262671:AAFpw2GxPp7_DAnFDPX45cn6lr3f3AXUffY"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Отправь мне файл, я покажу его ID")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_id = doc.file_id

    info = (
        f"✅ **НОВЫЙ FILE ID:**\n\n"
        f"`{file_id}`\n\n"
        f"📝 Имя: {doc.file_name}\n"
        f"📦 Размер: {doc.file_size / 1024 / 1024:.1f} MB\n\n"
        f"🔹 Скопируй этот ID"
    )

    await update.message.reply_text(info, parse_mode='Markdown')
    print(f"✅ Получен FILE_ID: {file_id}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🚀 Бот для получения ID запущен...")
    print("📤 Отправь свой APK файл этому боту")
    app.run_polling()


if __name__ == '__main__':
    main()
