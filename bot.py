import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from faq import FAQ_DATA, find_faq
from gemini_client import get_gemini_response

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "✂️ *Barber Dos-қа қош келдіңіз!*\n\n"
    "Мен сіздің сұрақтарыңызға жауап беруге дайынмын.\n\n"
    "Сұрақ қойыңыз немесе /faq командасын жіберіңіз — жиі сұралатын сұрақтар тізімін көресіз.\n\n"
    "📍 Абай к-сі 15, Алматы\n"
    "📱 +7 (777) 000-00-00\n"
    "💬 @barberdos"
)

HELP_TEXT = (
    "ℹ️ *Не сұрауға болады:*\n\n"
    "• Қызметтер мен бағалар\n"
    "• Жұмыс уақыты\n"
    "• Мекен-жай\n"
    "• Байланыс ақпараты\n"
    "• Жазылу / бронь\n"
    "• Шеберлер туралы\n\n"
    "Жай хабарлама жіберіңіз — жауап береміз! 💬\n\n"
    "/faq — жиі сұрақтар тізімі"
)


def _build_faq_text() -> str:
    lines = ["📋 *Жиі қойылатын сұрақтар:*\n"]
    icons = {
        "services": "💈",
        "price": "💰",
        "haircut": "✂️",
        "beard": "🪒",
        "children": "👦",
        "hours": "🕐",
        "address": "📍",
        "contact": "📞",
        "booking": "📝",
        "masters": "👨‍💈",
        "combo": "✂️🪒",
        "about": "🏪",
    }
    labels = {
        "services": "Қызметтер тізімі",
        "price": "Бағалар",
        "haircut": "Шаш кесу",
        "beard": "Сақал кесу",
        "children": "Балалар стрижкасы",
        "hours": "Жұмыс уақыты",
        "address": "Мекен-жай",
        "contact": "Байланыс",
        "booking": "Жазылу / Бронь",
        "masters": "Шеберлер",
        "combo": "Комбо пакет",
        "about": "Barber Dos туралы",
    }
    for key, label in labels.items():
        icon = icons.get(key, "•")
        hint = FAQ_DATA[key]["keywords"][0]
        lines.append(f'{icon} *{label}* — «{hint}» деп жазыңыз')
    lines.append("\nНемесе кез келген сұрағыңызды жіберіңіз! 💬")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_build_faq_text(), parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text or ""
    logger.info("Message from %s: %s", update.effective_user.id, user_text)

    faq_answer = find_faq(user_text)
    if faq_answer:
        await update.message.reply_text(faq_answer, parse_mode="Markdown")
        return

    await update.message.chat.send_action("typing")
    ai_answer = await get_gemini_response(user_text)
    await update.message.reply_text(ai_answer)


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is not set")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting polling")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
