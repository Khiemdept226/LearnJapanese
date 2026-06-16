import logging

from telegram.ext import ContextTypes

import db
import learning_items
from flashcard_handlers import _settings_filters, format_card_front, front_keyboard

logger = logging.getLogger(__name__)


def should_send_daily_flashcard_message(stats):
    return stats.get("due", 0) > 0 or stats.get("new", 0) > 0


def format_daily_reminder(stats):
    lines = [
        "Ôn tập flashcard hôm nay",
        f"Đến hạn: {stats['due']}",
        f"Từ mới còn lại: {stats['new']}",
        f"Đang học: {stats['learning']}",
    ]
    if stats.get("due_all") is not None:
        lines.append(f"Tổng đến hạn mọi deck: {stats['due_all']}")
    lines.append("Bấm thẻ bên dưới hoặc dùng /flash để học ngay.")
    return "\n".join(lines)


async def send_daily_flashcards(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Starting daily flashcard dispatch...")
    users = db.get_all_users()
    for user in users:
        telegram_user_id = user["telegram_user_id"]
        chat_id = user["chat_id"]
        try:
            settings = learning_items.get_user_settings(telegram_user_id)
            stats = learning_items.get_learning_stats(telegram_user_id, **_settings_filters(settings))
            all_stats = learning_items.get_learning_stats(telegram_user_id, level=None)
            stats["due_all"] = all_stats["due"]
            if not should_send_daily_flashcard_message(stats):
                continue
            await context.bot.send_message(chat_id=chat_id, text=format_daily_reminder(stats))
            card = None
            if stats["due"] > 0 and settings["daily_review_limit"] > 0:
                card = learning_items.pick_due_item(telegram_user_id, **_settings_filters(settings))
            elif (
                stats["new"] > 0
                and settings["daily_new_limit"] > 0
                and learning_items.should_allow_new_cards(settings)
            ):
                card = learning_items.pick_new_item(telegram_user_id, **_settings_filters(settings))
            if card:
                learning_items.set_current_session(telegram_user_id, card["id"], answer_shown=False)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=format_card_front(card),
                    reply_markup=front_keyboard(),
                )
        except Exception as exc:
            logger.error("Failed to send flashcard reminder to %s: %s", telegram_user_id, exc)
