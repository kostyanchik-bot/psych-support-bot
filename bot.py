from dotenv import load_dotenv
load_dotenv()

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters, JobQueue
)
import os
from survey import survey_questions
from analysis import analyze_responses
from recommendations import get_recommendations
from datetime import time, datetime
import random

# Шаги опроса
SECTION, QUESTION = range(2)

# Главное меню
MAIN_MENU = [
    ["📝 Пройти тест"],
    ["📚 Материалы", "📞 Помощь"],
    ["📋 Чек-листы привычек"],
    ["🔃 Сбросить привычки"]
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
        "☑️ Проснулся бодрым",
        "☑️ Сделал зарядку или растяжку",
        "☑️ Медитировал хотя бы 3 минуты"
    ],
    "💧 Водный баланс": [
        "☑️ Выпил стакан воды утром",
        "☑️ Следил за уровнем водного баланса в течение дня"
    ],
    "📵 Цифровой детокс": [
        "☑️ 1 час без телефона после пробуждения",
        "☑️ Без соцсетей за 2 часа до сна"
    ]
}

motivational_quotes = [
    "Ты молодец! Даже маленькие шаги — это движение вперёд!",
    "Каждое усилие имеет значение. Продолжай в том же духе!",
    "Отмечая привычки, ты приближаешься к лучшей версии себя!",
    "Не сдавайся, прогресс уже виден!",
    "Сила в постоянстве. Отличная работа!"
]

user_habit_progress = {}

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
    user_id = update.effective_user.id

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
            "📞 Горячая линия: *-***-***-**-**\n"
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

    elif text == "🔃 Сбросить привычки":
        user_habit_progress[user_id] = {}
        await update.message.reply_text("🔄 Прогресс привычек сброшен.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
        return ConversationHandler.END

    elif text in habit_checklists:
        checklist = habit_checklists[text]
        user_progress = user_habit_progress.get(user_id, {}).get(text, set())

        formatted = []
        for item in checklist:
            check_symbol = "✅" if item in user_progress else "⬜️"
            formatted.append(f"{check_symbol} {item[2:]}")

        keyboard = [[item] for item in checklist] + [["🔙 Назад"]]
        user_habit_progress.setdefault(user_id, {})["current_category"] = text

        await update.message.reply_text(
            f"{text} (нажмите, чтобы отметить выполненное):\n\n" + "\n".join(formatted),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return ConversationHandler.END

    elif text.startswith("☑️") or text.startswith("✅") or text.startswith("⬜️"):
        category = user_habit_progress.get(user_id, {}).get("current_category")
        if category:
            checklist = habit_checklists[category]
            original_item = None
            for item in checklist:
                if text.endswith(item[2:]):
                    original_item = item
                    break
            if original_item:
                current = user_habit_progress.setdefault(user_id, {}).setdefault(category, set())
                if original_item in current:
                    current.remove(original_item)
                else:
                    current.add(original_item)

                formatted = []
                for item in checklist:
                    check_symbol = "✅" if item in current else "⬜️"
                    formatted.append(f"{check_symbol} {item[2:]}")
                keyboard = [[item] for item in checklist] + [["🔙 Назад"]]

                message = f"{category}:\n\n" + "\n".join(formatted)
                message += f"\n\n💬 {random.choice(motivational_quotes)}"

                if set(checklist) == current:
                    message += "\n\n🎉 Поздравляем! Вы выполнили все привычки в этой категории сегодня!"

                await update.message.reply_text(
                    message,
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
        return ConversationHandler.END

    elif text == "🔙 Назад":
        await update.message.reply_text(
            "↩️ Возврат в главное меню:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ConversationHandler.END

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


async def reset_habit_progress(context: ContextTypes.DEFAULT_TYPE):
    global user_habit_progress
    user_habit_progress = {}
    print(f"[{datetime.now()}] Сброс прогресса привычек выполнен.")


def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(TOKEN).build()

    # Планировщик для сброса прогресса каждый день в 00:00
    job_queue: JobQueue = app.job_queue
    job_queue.run_daily(reset_habit_progress, time=time(hour=0, minute=0))

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
