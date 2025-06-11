import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Состояния
QUESTION = 0
questions = [
    {"id": "q1", "text": "Как часто вы чувствуете стресс из-за учёбы?", "options": ["Почти всегда", "Часто", "Иногда", "Редко", "Никогда"]},
    {"id": "q2", "text": "Как вы справляетесь с эмоциональными трудностями?", "options": ["Очень сложно", "Скорее сложно", "Нейтрально", "Скорее легко", "Очень легко"]},
]

# Главное меню
MAIN_MENU = [
    ["📝 Пройти тест"],
    ["📚 Материалы", "📞 Помощь"]
]


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Я бот поддержки студентов.\nВыберите действие:", reply_markup=reply_markup)


# Обработка кнопки "📝 Пройти тест"
async def begin_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'] = []
    context.user_data['q_index'] = 0
    return await ask_question(update, context)


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data['q_index']
    if q_index >= len(questions):
        return await finish(update, context)

    question = questions[q_index]
    keyboard = [[opt] for opt in question["options"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(question["text"], reply_markup=markup)
    return QUESTION


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'].append(update.message.text)
    context.user_data['q_index'] += 1
    return await ask_question(update, context)


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data['answers']
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("✅ Спасибо за участие!", reply_markup=reply_markup)
    await update.message.reply_text(f"Ваши ответы: {answers}")
    return ConversationHandler.END


# 📚 Материалы
async def resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Полезные материалы:\n\n"
        "• Управление стрессом: https://example.com/stress\n"
        "• Медитации для студентов: https://example.com/meditation\n"
        "• Прокрастинация: https://example.com/procrastination"
    )


# 📞 Помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Если вам нужна помощь:\n\n"
        "• Обратитесь в студенческую службу поддержки\n"
        "• Или позвоните на горячую линию: 8-***-***-**-**\n\n"
        "Вы можете быть анонимны — мы всегда на вашей стороне."
    )


# Команда отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Опрос отменён.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    return ConversationHandler.END


# Запуск бота
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Пройти тест$"), begin_test)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📚 Материалы$"), resources))
    app.add_handler(MessageHandler(filters.Regex("^📞 Помощь$"), help_command))
    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
