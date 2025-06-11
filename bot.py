from dotenv import load_dotenv
load_dotenv()

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, CallbackQueryHandler, filters
)
from survey import survey_questions
from analysis import analyze_responses
from recommendations import get_recommendations

import os
import datetime
from collections import defaultdict
import random

# Шаги опроса
SECTION, QUESTION = range(2)

# Главное меню
MAIN_MENU = [
    ["📝 Пройти тест"],
    ["📚 Материалы", "📞 Помощь"],
    ["🎯 Эмоции", "🧩 Антистресс"],
    ["📋 Привычки", "📅 Советы"],
    ["📊 Статистика"]
]

# Простейшее хранилище статистики
user_stats = defaultdict(lambda: {"tests": 0, "last_result": None})

# Простой список привычек
habits = ["💧 Выпил воду", "😴 Лег спать вовремя", "🚶 Прогулялся", "🍎 Поел полезное"]

# Советы на каждый день
daily_tips = [
    "Сделай 5 глубоких вдохов — это мгновенно снизит тревожность.",
    "Постарайся лечь спать на 30 минут раньше обычного.",
    "Прогулка 15 минут на свежем воздухе улучшит настроение.",
    "Попробуй записать 3 хорошие вещи, которые случились сегодня."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}! Это психологический бот поддержки студентов.\n\n"
        f"Выберите, что хотите сделать:",
        reply_markup=reply_markup
    )


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
            "• Прокрастинация: https://example.com/procrastination"
        )

    elif text == "📞 Помощь":
        await update.message.reply_text(
            "📞 Горячая линия: 8-***-***-**-**\n"
            "✉ Вы можете также обратиться в службу поддержки вуза.\n"
            "💬 Мы здесь, чтобы помочь!"
        )

    elif text == "🎯 Эмоции":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("😊", callback_data="happy"),
             InlineKeyboardButton("😐", callback_data="neutral"),
             InlineKeyboardButton("😟", callback_data="anxious")]
        ])
        await update.message.reply_text("Как вы себя чувствуете сегодня?", reply_markup=keyboard)

    elif text == "🧩 Антистресс":
        tips = ["Закрой глаза и сосчитай до 10.", "Встань, потянись, улыбнись.", "Сделай 10 глубоких вдохов.", "Попробуй вспомнить что-то хорошее сегодня."]
        await update.message.reply_text("🧘 Упражнение: " + random.choice(tips))

    elif text == "📋 Привычки":
        markup = ReplyKeyboardMarkup([[h] for h in habits] + [["⬅ Назад"]], resize_keyboard=True)
        await update.message.reply_text("Отметь, что ты сегодня выполнил:", reply_markup=markup)

    elif text == "📅 Советы":
        await update.message.reply_text("📅 Совет дня: " + random.choice(daily_tips))

    elif text == "📊 Статистика":
        user_id = update.effective_user.id
        stats = user_stats[user_id]
        msg = f"📊 Кол-во тестов: {stats['tests']}\n"
        if stats['last_result']:
            msg += f"📈 Последний результат: {stats['last_result']['level']}"
        await update.message.reply_text(msg)

    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.")

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

    user_id = update.effective_user.id
    user_stats[user_id]['tests'] += 1
    user_stats[user_id]['last_result'] = result

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


async def emotion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    emoji = query.data
    messages = {
        "happy": "😊 Здорово! Поделись этим настроением с другом!",
        "neutral": "😐 Нормально. Может, попробовать что-то новенькое сегодня?",
        "anxious": "😟 Это нормально. Попробуй дыхательные упражнения или обратись за поддержкой."
    }
    await query.edit_message_text(messages.get(emoji, "Спасибо за отклик!"))


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
    app.add_handler(CallbackQueryHandler(emotion_callback))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
