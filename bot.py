# bot.py
from dotenv import load_dotenv
load_dotenv()
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
)

from survey import survey_questions
from analysis import analyze_responses
from recommendations import get_recommendations

import os

# Шаги опроса
SECTION, QUESTION = range(2)

# Хранилище для пользователей
user_data_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['section_idx'] = 0
    context.user_data['question_idx'] = 0
    context.user_data['responses'] = {}

    await update.message.reply_text(
        f"Привет, {user.first_name}! Это психологический бот поддержки студентов.\n\n"
        f"Мы начнем с простого опроса. Отвечай на вопросы честно.",
    )
    return await ask_question(update, context)


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    section_idx = context.user_data['section_idx']
    question_idx = context.user_data['question_idx']
    section = survey_questions[section_idx]
    questions = section['questions']
    question = questions[question_idx]

    # Сохраняем текущий ID для ответа
    context.user_data['current_qid'] = question['id']
    context.user_data['current_multi'] = question.get("multi", False)

    # Клавиатура
    keyboard = [[opt] for opt in question["options"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(f"{question['text']}", reply_markup=markup)
    return QUESTION


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    qid = context.user_data.get('current_qid')
    is_multi = context.user_data.get('current_multi', False)

    if is_multi:
        # Допустим, пользователь перечисляет через запятую
        values = [a.strip() for a in answer.split(',') if a.strip()]
        context.user_data['responses'][qid] = values
    else:
        context.user_data['responses'][qid] = answer

    # Переход к следующему вопросу
    context.user_data['question_idx'] += 1
    section_idx = context.user_data['section_idx']
    question_idx = context.user_data['question_idx']

    if question_idx >= len(survey_questions[section_idx]['questions']):
        context.user_data['section_idx'] += 1
        context.user_data['question_idx'] = 0

    if context.user_data['section_idx'] >= len(survey_questions):
        return await finish(update, context)
    else:
        return await ask_question(update, context)


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо за ваши ответы! Проводим анализ...", reply_markup=ReplyKeyboardRemove())

    result = analyze_responses(context.user_data['responses'])
    recs = get_recommendations(result)

    await update.message.reply_text(f"📊 Уровень тревожности: *{result['level']}*", parse_mode="Markdown")
    await update.message.reply_text("📌 Рекомендации:")
    for r in recs:
        await update.message.reply_text(f"✅ {r}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опрос отменён. Вы можете начать заново с /start.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")  # Задайте переменную среды TELEGRAM_TOKEN или вставьте прямо сюда
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
