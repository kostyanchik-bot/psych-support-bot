from dotenv import load_dotenv
load_dotenv()

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)
import os
from survey import survey_questions
from analysis import analyze_responses
from recommendations import get_recommendations

# Шаги опроса
SECTION, QUESTION = range(2)

# Главное меню
MAIN_MENU = [
    ["📝 Пройти тест"],
    ["📚 Материалы", "📞 Помощь"],
    ["📋 Чек-листы привычек"],
    ["🔙 Назад"]
]

# Чек-листы
HABITS_MENU = [
    ["🧘 Утренние практики"],
    ["💧 Водный баланс"],
    ["📵 Цифровой детокс"],
    ["🔙 Назад"]
]

habit_checklists = {
    "🧘 Утренние практики": [
        "☑️ Проснулся без прокрастинации",
        "☑️ Сделал зарядку или растяжку",
        "☑️ Медитировал хотя бы 3 минуты"
    ],
    "💧 Водный баланс": [
        "☑️ Выпил стакан воды утром",
        "☑️ Следил за уровнем гидратации в течение дня"
    ],
    "📵 Цифровой детокс": [
        "☑️ 1 час без телефона после пробуждения",
        "☑️ Без соцсетей за 2 часа до сна"
    ]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}! Это психологический бот поддержки студентов.\n\n"
        f"Выберите, что хотите сделать:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📝 Пройти тест":
        context.user_data['section_idx'] = 0
        context.user_data['question_idx'] = 0
        context.user_data['responses'] = {}
        return await ask_question(update, context)

    elif text == "📚 Материалы":
        await update.message.reply_text(
            "📚 Полезные материалы:\n\n"
            "• Управление стрессом: https://example.com/stress\n"
            "• Медитации: https://example.com/meditation\n"
            "• Прокрастинация: https://example.com/procrastination",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ConversationHandler.END

    elif text == "📞 Помощь":
        await update.message.reply_text(
            "📞 Горячая линия: 8-***-***-**-**\n"
            "✉ Вы можете также обратиться в службу поддержки вуза.\n"
            "💬 Мы здесь, чтобы помочь!",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ConversationHandler.END

    elif text == "📋 Чек-листы привычек":
        await update.message.reply_text(
            "📋 Выберите категорию привычек:",
            reply_markup=ReplyKeyboardMarkup(HABITS_MENU, resize_keyboard=True)
        )
        return ConversationHandler.END

    elif text in habit_checklists:
        checklist = habit_checklists[text]
        await update.message.reply_text(
            f"{text}:\n\n" + "\n".join(checklist),
            reply_markup=ReplyKeyboardMarkup(HABITS_MENU, resize_keyboard=True)
        )
        return ConversationHandler.END

    elif text == "🔙 Назад":
        return await start(update, context)

    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
        return ConversationHandler.END


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    section_idx = context.user_data['section_idx']
    question_idx = context.user_data['question_idx']
    section = survey_questions[section_idx]
    questions = section['questions']
    question = questions[question_idx]

    context.user_data['current_qid'] = question['id']
    context.user_data['current_multi'] = question.get("multi", False)

    keyboard = [[opt] for opt in question["options"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(f"{question['text']}", reply_markup=markup)
    return QUESTION


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    qid = context.user_data.get('current_qid')
    is_multi = context.user_data.get('current_multi', False)

    if is_multi:
        values = [a.strip() for a in answer.split(',') if a.strip()]
        context.user_data['responses'][qid] = values
    else:
        context.user_data['responses'][qid] = answer

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
    await update.message.reply_text("✅ Спасибо за ваши ответы! Проводим анализ...", reply_markup=ReplyKeyboardRemove())

    result = analyze_responses(context.user_data['responses'])
    recs = get_recommendations(result)

    await update.message.reply_text(f"📊 Уровень тревожности: *{result['level']}*", parse_mode="Markdown")
    await update.message.reply_text("📌 Рекомендации:")
    for r in recs:
        await update.message.reply_text(f"✅ {r}")

    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("🔁 Вы можете пройти опрос снова или выбрать другой пункт:", reply_markup=reply_markup)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Опрос отменён. Вы можете начать заново с /start", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    return ConversationHandler.END


def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)
        ],
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
