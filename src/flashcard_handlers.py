import datetime as dt

from telegram import Update
from telegram.ext import ContextTypes

import flashcards
from config import FLASHCARD_LEVEL


def format_card_front(card):
    reading = card.get("reading") or "-"
    return (
        "N4 Flashcard\n"
        f"言葉: {card['word']}\n"
        f"読み方: {reading}\n\n"
        "Tự nhớ nghĩa, rồi dùng /show để xem đáp án."
    )


def format_card_answer(card):
    lines = [
        f"意味: {card['meaning']}",
    ]
    if card.get("example_jp"):
        lines.append(f"例文: {card['example_jp']}")
    if card.get("example_vi"):
        lines.append(f"Dịch: {card['example_vi']}")
    lines.append("")
    lines.append("Bạn nhớ mức nào?")
    lines.append("/again /hard /good /easy")
    return "\n".join(lines)


def format_stats(stats):
    return (
        "Tiến độ flashcard\n"
        f"Tổng thẻ: {stats['total']}\n"
        f"Từ mới: {stats['new']}\n"
        f"Đến hạn: {stats['due']}\n"
        f"Đang học: {stats['learning']}\n"
        f"Đã vào review: {stats['review']}\n"
        f"Số lần quên: {stats['lapses']}"
    )


def grade_error_message(code):
    if code == "no_pending":
        return "Chưa có thẻ nào. Dùng /flash trước."
    if code == "answer_not_shown":
        return "Bạn cần dùng /show để xem đáp án trước khi chấm."
    return "Không chấm được thẻ hiện tại. Dùng /flash để thử lại."


def format_next_review(updated):
    due = dt.datetime.fromisoformat(updated["due_at"])
    return f"Next review: {due.strftime('%Y-%m-%d %H:%M')}"


async def flash_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flashcards.init_flashcard_db()
    await update.message.reply_text(
        "Đã bật học flashcard N4.\n"
        "Dùng /flash để học thẻ đến hạn hoặc từ mới.\n"
        "Flow: /flash -> /show -> /again /hard /good /easy"
    )


async def _send_card(update, telegram_user_id, card):
    if not card:
        await update.message.reply_text("Chưa có thẻ flashcard phù hợp. Hãy import dữ liệu PDF trước.")
        return
    flashcards.ensure_user_review(telegram_user_id, card["id"])
    flashcards.set_current_session(telegram_user_id, card["id"], answer_shown=False)
    await update.message.reply_text(format_card_front(card))


async def flash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    card = flashcards.pick_next_card(user_id, FLASHCARD_LEVEL)
    await _send_card(update, user_id, card)


async def flash_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    card = flashcards.pick_new_card(user_id, FLASHCARD_LEVEL)
    await _send_card(update, user_id, card)


async def flash_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    card = flashcards.pick_due_card(user_id, FLASHCARD_LEVEL)
    if not card:
        await update.message.reply_text("Hiện không có thẻ đến hạn. Dùng /flash_new để học từ mới.")
        return
    await _send_card(update, user_id, card)


async def flash_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = flashcards.get_flashcard_stats(update.effective_user.id, FLASHCARD_LEVEL)
    await update.message.reply_text(format_stats(stats))


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = flashcards.get_current_session(user_id)
    if not session or not session.get("current_flashcard_id"):
        await update.message.reply_text("Chưa có thẻ nào. Dùng /flash trước.")
        return
    card = flashcards.get_flashcard(session["current_flashcard_id"])
    if not card:
        await update.message.reply_text("Không tìm thấy thẻ hiện tại. Dùng /flash để lấy thẻ khác.")
        return
    flashcards.reveal_current_session(user_id)
    await update.message.reply_text(format_card_answer(card))


async def _grade(update, grade):
    updated, error = flashcards.grade_current_card(update.effective_user.id, grade)
    if error:
        await update.message.reply_text(grade_error_message(error))
        return
    await update.message.reply_text(format_next_review(updated))


async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade(update, "again")


async def hard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade(update, "hard")


async def good(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade(update, "good")


async def easy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade(update, "easy")

