import logging

from telegram.ext import ContextTypes

import db
import flashcards
from flashcard_handlers import format_card_front, front_keyboard

logger = logging.getLogger(__name__)


def should_send_daily_flashcard_message(stats):
    return stats.get("due", 0) > 0 or stats.get("new", 0) > 0


def format_daily_reminder(stats):
    return (
        "Ôn tập flashcard hôm nay\n"
        f"Đến hạn: {stats['due']}\n"
        f"Từ mới còn lại: {stats['new']}\n"
        f"Đang học: {stats['learning']}\n"
        "Bấm thẻ bên dưới hoặc dùng /flash để học ngay."
    )


async def send_daily_flashcards(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Starting daily flashcard dispatch...")
    users = db.get_all_users()
    for user in users:
        telegram_user_id = user["telegram_user_id"]
        chat_id = user["chat_id"]
        try:
            settings = flashcards.get_user_settings(telegram_user_id)
            stats = flashcards.get_flashcard_stats(telegram_user_id, settings["level"])
            if not should_send_daily_flashcard_message(stats):
                continue
            await context.bot.send_message(chat_id=chat_id, text=format_daily_reminder(stats))
            card = None
            if stats["due"] > 0 and settings["daily_review_limit"] > 0:
                card = flashcards.pick_due_card(telegram_user_id, settings["level"])
            elif (
                stats["new"] > 0
                and settings["daily_new_limit"] > 0
                and flashcards.should_allow_new_cards(settings)
            ):
                card = flashcards.pick_new_card(telegram_user_id, settings["level"])
            if card:
                flashcards.ensure_user_review(telegram_user_id, card["id"])
                flashcards.set_current_session(telegram_user_id, card["id"], answer_shown=False)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=format_card_front(card),
                    reply_markup=front_keyboard(),
                )
        except Exception as exc:
            logger.error("Failed to send flashcard reminder to %s: %s", telegram_user_id, exc)
