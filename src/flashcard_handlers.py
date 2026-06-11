import datetime as dt

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import flashcards
from config import FLASHCARD_TIMEZONE


def front_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Hiện đáp án", callback_data="flash:show")],
        [InlineKeyboardButton("Thống kê", callback_data="flash:stats")],
    ])


def continue_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Thẻ tiếp theo", callback_data="flash:next")],
        [InlineKeyboardButton("Thống kê", callback_data="flash:stats")],
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


def reset_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Huỷ", callback_data="flash:reset:cancel"),
            InlineKeyboardButton("Reset tiến độ", callback_data="flash:reset:confirm"),
        ]
    ])


def stats_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Danh sách hôm nay", callback_data="flash:today:list")],
        [InlineKeyboardButton("Thẻ tiếp theo", callback_data="flash:next")],
    ])


def today_cards_keyboard(cards):
    rows = []
    for card in cards[:10]:
        rows.append([InlineKeyboardButton(card["word"], callback_data=f"flash:card:{card['id']}")])
    rows.append([InlineKeyboardButton("Quay lại thống kê", callback_data="flash:stats")])
    return InlineKeyboardMarkup(rows)


def format_reset_confirm():
    return (
        "Bạn chắc muốn xoá tiến độ flashcard và học lại từ đầu?\n\n"
        "Không xoá dữ liệu thẻ đã import. Chỉ reset tiến độ của riêng bạn."
    )


def format_help():
    return (
        "Danh sách lệnh\n"
        "/start - bắt đầu bot\n"
        "/today - bài hôm nay\n"
        "/flash_start - bật flashcard\n"
        "/flash - học thông minh: ưu tiên thẻ đến hạn, nếu không có thì lấy từ mới\n"
        "/flash_new - chỉ lấy từ mới chưa học\n"
        "/flash_review - chỉ ôn thẻ đã đến hạn\n"
        "/flash_stats - xem tiến độ\n"
        "/flash_goal - chọn mục tiêu học\n"
        "/flash_reset - học lại flashcard từ đầu\n"
        "/show - hiện đáp án\n"
        "/again /hard /good /easy - chấm thẻ\n\n"
        "Flow học flashcard\n"
        "1. Dùng /flash để nhận từ.\n"
        "2. Tự nhớ cách đọc + nghĩa.\n"
        "3. Bấm Hiện đáp án.\n"
        "4. Chọn Quên / Khó / Nhớ / Dễ để lên lịch ôn."
    )


def format_card_front(card):
    return (
        "N4 Flashcard\n"
        f"言葉: {card['word']}\n\n"
        "Tự nhớ cách đọc + nghĩa, rồi bấm Hiện đáp án."
    )


def format_card_answer(card):
    reading = card.get("reading") or "-"
    lines = [
        f"言葉: {card['word']}",
        f"読み方: {reading}",
        f"意味: {card['meaning']}",
    ]
    if card.get("example_jp"):
        lines.append(f"例文: {card['example_jp']}")
    if card.get("example_vi"):
        lines.append(f"Dịch: {card['example_vi']}")
    lines.append("")
    lines.append("Bạn nhớ mức nào?")
    return "\n".join(lines)


def format_card_detail(card):
    reading = card.get("reading") or "-"
    lines = [
        f"言葉: {card['word']}",
        f"読み方: {reading}",
        f"意味: {card['meaning']}",
    ]
    if card.get("example_jp"):
        lines.append(f"例文: {card['example_jp']}")
    if card.get("example_vi"):
        lines.append(f"Dịch: {card['example_vi']}")
    return "\n".join(lines)


def format_stats(stats, today_count=None):
    lines = [
        "Tiến độ flashcard",
        f"Tổng thẻ: {stats['total']}",
        f"Từ mới: {stats['new']}",
        f"Đến hạn: {stats['due']}",
        f"Đang học: {stats['learning']}",
        f"Đã vào review: {stats['review']}",
        f"Số lần quên: {stats['lapses']}",
    ]
    if today_count is not None:
        lines.extend(["", "Hôm nay", f"Đã chấm: {today_count}"])
    return "\n".join(lines)


def format_today_card_list(cards):
    if not cards:
        return "Hôm nay chưa có thẻ nào được chấm."
    lines = ["Các thẻ đã chấm hôm nay"]
    for index, card in enumerate(cards[:10], start=1):
        reading = card.get("reading") or "-"
        lines.append(f"{index}. {card['word']} / {reading} / {card['meaning']}")
    if len(cards) > 10:
        lines.append(f"... còn {len(cards) - 10} thẻ khác")
    return "\n".join(lines)


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
    if due.tzinfo is None:
        due = due.replace(tzinfo=dt.timezone.utc)
    local_due = due.astimezone(pytz.timezone(FLASHCARD_TIMEZONE))
    return f"Next review: {local_due.strftime('%Y-%m-%d %H:%M')} ({FLASHCARD_TIMEZONE})"


def _today_bounds_utc(now=None):
    tz = pytz.timezone(FLASHCARD_TIMEZONE)
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    local_now = current.astimezone(tz)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + dt.timedelta(days=1)
    return (
        start_local.astimezone(dt.timezone.utc).isoformat(),
        end_local.astimezone(dt.timezone.utc).isoformat(),
    )


def _today_cards(telegram_user_id, level):
    start_at, end_at = _today_bounds_utc()
    return flashcards.get_reviewed_cards_between(telegram_user_id, level, start_at, end_at, limit=30)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_help())


async def flash_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_reset_confirm(), reply_markup=reset_keyboard())


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
        await message.reply_text("Chưa có thẻ flashcard phù hợp. Hãy import dữ liệu Sheet trước.")
        return
    flashcards.set_current_session(telegram_user_id, card["id"], answer_shown=False)
    await message.reply_text(format_card_front(card), reply_markup=front_keyboard())


async def _edit_card_for_query(query, telegram_user_id, card):
    if not card:
        await query.edit_message_text("Chưa có thẻ phù hợp lúc này.")
        return
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
        await update.message.reply_text("Hiện chưa có thẻ nào đến hạn.\nDùng /flash để học tiếp hoặc /flash_new để học từ mới.")
        return
    await _send_card_to_message(update.message, user_id, card)


async def flash_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = flashcards.get_user_settings(user_id)
    stats = flashcards.get_flashcard_stats(user_id, settings["level"])
    today_cards = _today_cards(user_id, settings["level"])
    await update.message.reply_text(format_stats(stats, today_count=len(today_cards)), reply_markup=stats_keyboard())


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
    await update.message.reply_text(format_next_review(updated), reply_markup=continue_keyboard())


async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "again")


async def hard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "hard")


async def good(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "good")


async def easy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "easy")


async def _edit_stats(query, user_id):
    settings = flashcards.get_user_settings(user_id)
    stats = flashcards.get_flashcard_stats(user_id, settings["level"])
    today_cards = _today_cards(user_id, settings["level"])
    await query.edit_message_text(format_stats(stats, today_count=len(today_cards)), reply_markup=stats_keyboard())


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
        await query.edit_message_text(format_next_review(updated), reply_markup=continue_keyboard())
        return

    if data == "flash:reset:cancel":
        await query.edit_message_text("Đã huỷ reset tiến độ.")
        return

    if data == "flash:reset:confirm":
        flashcards.reset_user_flashcard_progress(user_id)
        await query.edit_message_text("Đã reset tiến độ flashcard. Dùng /flash để học lại từ đầu.")
        return

    if data.startswith("flash:goal:"):
        preset = data.split(":")[-1]
        settings = flashcards.set_user_goal_preset(user_id, preset)
        await query.edit_message_text(format_goal(settings))
        return

    if data == "flash:today:list":
        settings = flashcards.get_user_settings(user_id)
        cards = _today_cards(user_id, settings["level"])
        await query.edit_message_text(format_today_card_list(cards), reply_markup=today_cards_keyboard(cards))
        return

    if data.startswith("flash:card:"):
        card_id = int(data.split(":")[-1])
        card = flashcards.get_flashcard(card_id)
        if not card:
            await query.edit_message_text("Không tìm thấy thẻ này.")
            return
        await query.edit_message_text(format_card_detail(card), reply_markup=stats_keyboard())
        return

    settings = flashcards.get_user_settings(user_id)
    if data == "flash:next":
        card = flashcards.pick_next_card(user_id, settings["level"])
        await _edit_card_for_query(query, user_id, card)
        return
    if data == "flash:stats":
        await _edit_stats(query, user_id)







