import datetime as dt

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import flashcards
from config import FLASHCARD_LEVEL


def front_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Hiện đáp án", callback_data="flash:show")],
        [
            InlineKeyboardButton("Học tiếp", callback_data="flash:next"),
            InlineKeyboardButton("Thống kê", callback_data="flash:stats"),
        ],
    ])


def answer_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Quên", callback_data="flash:grade:again"),
            InlineKeyboardButton("Khó", callback_data="flash:grade:hard"),
            InlineKeyboardButton("Nhớ", callback_data="flash:grade:good"),
            InlineKeyboardButton("Dễ", callback_data="flash:grade:easy"),
        ]
    ])


def goal_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Nước rút JLPT", callback_data="flash:goal:jlpt_sprint")],
        [
            InlineKeyboardButton("Nhẹ", callback_data="flash:goal:light"),
            InlineKeyboardButton("Đều đều", callback_data="flash:goal:steady"),
            InlineKeyboardButton("Nặng", callback_data="flash:goal:heavy"),
        ],
    ])


def format_card_front(card):
    reading = card.get("reading") or "-"
    return (
        "N4 Flashcard\n"
        f"言葉: {card['word']}\n"
        f"読み方: {reading}\n\n"
        "Tự nhớ nghĩa, rồi bấm Hiện đáp án."
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


def format_goal(settings):
    return (
        "Mục tiêu hiện tại\n"
        f"Preset: {settings['preset']}\n"
        f"Từ mới/ngày: {settings['daily_new_limit']}\n"
        f"Ôn tối đa/ngày: {settings['daily_review_limit']}\n"
        f"Quên: ôn lại sau {settings['again_delay_minutes']} phút"
    )


def grade_error_message(code):
    if code == "no_pending":
        return "Chưa có thẻ nào. Dùng /flash trước."
    if code == "answer_not_shown":
        return "Bạn cần bấm Hiện đáp án trước khi chấm."
    return "Không chấm được thẻ hiện tại. Dùng /flash để thử lại."


def format_next_review(updated):
    due = dt.datetime.fromisoformat(updated["due_at"])
    return f"Next review: {due.strftime('%Y-%m-%d %H:%M')}"


async def flash_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flashcards.init_flashcard_db()
    await update.message.reply_text(
        "Đã bật học flashcard N4. Dùng /flash để học, hoặc /flash_goal để chọn mục tiêu.",
        reply_markup=goal_keyboard(),
    )


async def flash_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chọn mục tiêu học mỗi ngày:", reply_markup=goal_keyboard())


async def _send_card_to_message(message, telegram_user_id, card):
    if not card:
        await message.reply_text("Chưa có thẻ flashcard phù hợp. Hãy import dữ liệu PDF trước.")
        return
    flashcards.ensure_user_review(telegram_user_id, card["id"])
    flashcards.set_current_session(telegram_user_id, card["id"], answer_shown=False)
    await message.reply_text(format_card_front(card), reply_markup=front_keyboard())


async def _edit_card_for_query(query, telegram_user_id, card):
    if not card:
        await query.edit_message_text("Chưa có thẻ phù hợp lúc này.")
        return
    flashcards.ensure_user_review(telegram_user_id, card["id"])
    flashcards.set_current_session(telegram_user_id, card["id"], answer_shown=False)
    await query.edit_message_text(format_card_front(card), reply_markup=front_keyboard())


async def flash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = flashcards.get_user_settings(user_id)
    card = flashcards.pick_next_card(user_id, settings["level"])
    await _send_card_to_message(update.message, user_id, card)


async def flash_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = flashcards.get_user_settings(user_id)
    card = flashcards.pick_new_card(user_id, settings["level"])
    await _send_card_to_message(update.message, user_id, card)


async def flash_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = flashcards.get_user_settings(user_id)
    card = flashcards.pick_due_card(user_id, settings["level"])
    if not card:
        await update.message.reply_text("Hiện không có thẻ đến hạn. Dùng /flash_new để học từ mới.")
        return
    await _send_card_to_message(update.message, user_id, card)


async def flash_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = flashcards.get_user_settings(user_id)
    stats = flashcards.get_flashcard_stats(user_id, settings["level"])
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
    await update.message.reply_text(format_card_answer(card), reply_markup=answer_keyboard())


async def _grade_message(update, grade):
    updated, error = flashcards.grade_current_card(update.effective_user.id, grade)
    if error:
        await update.message.reply_text(grade_error_message(error))
        return
    await update.message.reply_text(format_next_review(updated), reply_markup=front_keyboard())


async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "again")


async def hard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "hard")


async def good(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "good")


async def easy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "easy")


async def handle_flashcard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "flash:show":
        session = flashcards.get_current_session(user_id)
        if not session or not session.get("current_flashcard_id"):
            await query.edit_message_text("Chưa có thẻ nào. Dùng /flash trước.")
            return
        card = flashcards.get_flashcard(session["current_flashcard_id"])
        if not card:
            await query.edit_message_text("Không tìm thấy thẻ hiện tại. Dùng /flash để lấy thẻ khác.")
            return
        flashcards.reveal_current_session(user_id)
        await query.edit_message_text(format_card_answer(card), reply_markup=answer_keyboard())
        return

    if data.startswith("flash:grade:"):
        grade = data.split(":")[-1]
        updated, error = flashcards.grade_current_card(user_id, grade)
        if error:
            await query.edit_message_text(grade_error_message(error))
            return
        await query.edit_message_text(format_next_review(updated), reply_markup=front_keyboard())
        return

    if data.startswith("flash:goal:"):
        preset = data.split(":")[-1]
        settings = flashcards.set_user_goal_preset(user_id, preset)
        await query.edit_message_text(format_goal(settings))
        return

    settings = flashcards.get_user_settings(user_id)
    if data == "flash:next":
        card = flashcards.pick_next_card(user_id, settings["level"])
        await _edit_card_for_query(query, user_id, card)
        return
    if data == "flash:stats":
        stats = flashcards.get_flashcard_stats(user_id, settings["level"])
        await query.edit_message_text(format_stats(stats), reply_markup=front_keyboard())
