import datetime as dt

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import learning_items
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
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Quên", callback_data="flash:grade:again"),
        InlineKeyboardButton("Khó", callback_data="flash:grade:hard"),
        InlineKeyboardButton("Nhớ", callback_data="flash:grade:good"),
        InlineKeyboardButton("Dễ", callback_data="flash:grade:easy"),
    ]])


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
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Hủy", callback_data="flash:reset:cancel"),
        InlineKeyboardButton("Reset tiến độ", callback_data="flash:reset:confirm"),
    ]])


def stats_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Danh sách hôm nay", callback_data="flash:today:list")],
        [InlineKeyboardButton("Thẻ tiếp theo", callback_data="flash:next")],
    ])


def _item_front(item):
    return item.get("front") or item.get("word") or "-"


def _item_meaning(item):
    return item.get("meaning") or item.get("back") or "-"


def _settings_filters(settings):
    return {
        "level": settings.get("level"),
        "item_type": settings.get("item_type"),
        "deck_id": settings.get("deck_id"),
        "tags": settings.get("tags"),
    }


def _session_item_id(session):
    return session.get("current_learning_item_id") or session.get("current_flashcard_id")


def today_cards_keyboard(cards):
    rows = [[InlineKeyboardButton(_item_front(card), callback_data=f"flash:card:{card['id']}")] for card in cards[:10]]
    rows.append([InlineKeyboardButton("Quay lại thống kê", callback_data="flash:stats")])
    return InlineKeyboardMarkup(rows)


def format_reset_confirm():
    return (
        "Bạn chắc muốn xóa tiến độ flashcard và học lại từ đầu?\n\n"
        "Không xóa dữ liệu thẻ đã import. Chỉ reset tiến độ của riêng bạn."
    )


def format_help():
    return (
        "Danh sách lệnh\n"
        "/start - bắt đầu bot\n"
        "/today - bài hôm nay\n"
        "/flash_start - bật flashcard\n"
        "/flash - học thông minh: ưu tiên thẻ đến hạn, nếu không có thì lấy thẻ mới\n"
        "/flash_new - chỉ lấy thẻ mới chưa học\n"
        "/flash_review - chỉ ôn thẻ đã đến hạn\n"
        "/flash_stats - xem tiến độ\n"
        "/flash_goal - chọn mục tiêu học\n"
        "/flash_reset - học lại flashcard từ đầu\n"
        "/flash_settings - xem bộ lọc hiện tại\n"
        "/flash_level N4 - chọn level\n"
        "/flash_type vocab|kanji|grammar|kaiwa - chọn loại thẻ\n"
        "/flash_deck n4_vocab_core - chọn deck\n"
        "/flash_tags food,verb - lọc theo tag\n"
        "/show - hiện đáp án\n"
        "/again /hard /good /easy - chấm thẻ"
    )


def format_card_front(card):
    return (
        "Flashcard\n"
        f"Mặt trước: {_item_front(card)}\n\n"
        "Tự nhớ cách đọc và nghĩa, rồi bấm Hiện đáp án."
    )


def format_card_answer(card):
    reading = card.get("reading") or "-"
    lines = [
        f"Mặt trước: {_item_front(card)}",
        f"Cách đọc: {reading}",
    ]
    if card.get("hanviet"):
        lines.append(f"Hán Việt: {card['hanviet']}")
    lines.append(f"Nghĩa: {_item_meaning(card)}")
    if card.get("example_jp"):
        lines.append(f"Ví dụ: {card['example_jp']}")
    if card.get("example_vi"):
        lines.append(f"Dịch: {card['example_vi']}")
    lines.extend(["", "Bạn nhớ mức nào?"])
    return "\n".join(lines)


def format_card_detail(card):
    return format_card_answer(card).replace("\n\nBạn nhớ mức nào?", "")


def format_stats(stats, today_count=None):
    lines = [
        "Tiến độ flashcard",
        f"Tổng thẻ: {stats['total']}",
        f"Thẻ mới: {stats['new']}",
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
        lines.append(f"{index}. {_item_front(card)} / {reading} / {_item_meaning(card)}")
    if len(cards) > 10:
        lines.append(f"... còn {len(cards) - 10} thẻ khác")
    return "\n".join(lines)


def format_goal(settings):
    return (
        "Mục tiêu hiện tại\n"
        f"Preset: {settings['preset']}\n"
        f"Thẻ mới/ngày: {settings['daily_new_limit']}\n"
        f"Ôn tối đa/ngày: {settings['daily_review_limit']}\n"
        f"Quên: ôn lại sau {settings['again_delay_minutes']} phút"
    )


def format_settings(settings):
    return (
        "Flash settings\n"
        f"Level: {settings.get('level') or '-'}\n"
        f"Type: {settings.get('item_type') or 'all'}\n"
        f"Deck: {settings.get('deck_id') or 'all'}\n"
        f"Tags: {settings.get('tags') or 'all'}\n"
        f"Preset: {settings.get('preset')}"
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
    return start_local.astimezone(dt.timezone.utc).isoformat(), end_local.astimezone(dt.timezone.utc).isoformat()


def _today_cards(telegram_user_id, settings):
    start_at, end_at = _today_bounds_utc()
    return learning_items.get_reviewed_items_between(
        telegram_user_id,
        settings.get("level"),
        start_at,
        end_at,
        limit=30,
        item_type=settings.get("item_type"),
        deck_id=settings.get("deck_id"),
        tags=settings.get("tags"),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_help())


async def flash_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_reset_confirm(), reply_markup=reset_keyboard())


async def flash_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    learning_items.init_learning_db()
    await update.message.reply_text(
        "Đã bật học flashcard. Dùng /flash để học, hoặc /flash_settings để xem bộ lọc.",
        reply_markup=goal_keyboard(),
    )


async def flash_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chọn mục tiêu học mỗi ngày:", reply_markup=goal_keyboard())


async def _send_card_to_message(message, telegram_user_id, card):
    if not card:
        await message.reply_text("Chưa có thẻ flashcard phù hợp. Hãy import dữ liệu Sheet trước.")
        return
    learning_items.set_current_session(telegram_user_id, card["id"], answer_shown=False)
    await message.reply_text(format_card_front(card), reply_markup=front_keyboard())


async def _edit_card_for_query(query, telegram_user_id, card):
    if not card:
        await query.edit_message_text("Chưa có thẻ phù hợp lúc này.")
        return
    learning_items.set_current_session(telegram_user_id, card["id"], answer_shown=False)
    await query.edit_message_text(format_card_front(card), reply_markup=front_keyboard())


async def flash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = learning_items.get_user_settings(user_id)
    card = learning_items.pick_next_item(user_id, **_settings_filters(settings))
    await _send_card_to_message(update.message, user_id, card)


async def flash_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = learning_items.get_user_settings(user_id)
    card = learning_items.pick_new_item(user_id, **_settings_filters(settings))
    await _send_card_to_message(update.message, user_id, card)


async def flash_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = learning_items.get_user_settings(user_id)
    card = learning_items.pick_due_item(user_id, **_settings_filters(settings))
    if not card:
        await update.message.reply_text("Hiện chưa có thẻ nào đến hạn. Dùng /flash hoặc /flash_new để học tiếp.")
        return
    await _send_card_to_message(update.message, user_id, card)


async def flash_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = learning_items.get_user_settings(user_id)
    stats = learning_items.get_learning_stats(user_id, **_settings_filters(settings))
    today_cards = _today_cards(user_id, settings)
    await update.message.reply_text(format_stats(stats, today_count=len(today_cards)), reply_markup=stats_keyboard())


async def flash_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = learning_items.get_user_settings(update.effective_user.id)
    await update.message.reply_text(format_settings(settings))


async def flash_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /flash_level N4")
        return
    settings = learning_items.set_user_learning_filter(update.effective_user.id, level=context.args[0].upper())
    await update.message.reply_text(format_settings(settings))


async def flash_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] not in {"vocab", "kanji", "grammar", "kaiwa"}:
        await update.message.reply_text("Usage: /flash_type vocab|kanji|grammar|kaiwa")
        return
    settings = learning_items.set_user_learning_filter(update.effective_user.id, item_type=context.args[0])
    await update.message.reply_text(format_settings(settings))


async def flash_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /flash_deck n4_vocab_core")
        return
    settings = learning_items.set_user_learning_filter(update.effective_user.id, deck_id=context.args[0])
    await update.message.reply_text(format_settings(settings))


async def flash_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tags = " ".join(context.args).strip() if context.args else ""
    settings = learning_items.set_user_learning_filter(update.effective_user.id, tags=tags or None)
    await update.message.reply_text(format_settings(settings))


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = learning_items.get_current_session(user_id)
    if not session or not _session_item_id(session):
        await update.message.reply_text("Chưa có thẻ nào. Dùng /flash trước.")
        return
    card = learning_items.get_learning_item(_session_item_id(session))
    if not card:
        await update.message.reply_text("Không tìm thấy thẻ hiện tại. Dùng /flash để lấy thẻ khác.")
        return
    learning_items.reveal_current_session(user_id)
    await update.message.reply_text(format_card_answer(card), reply_markup=answer_keyboard())


async def _grade_message(update, grade):
    updated, error = learning_items.grade_current_item(update.effective_user.id, grade)
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
    settings = learning_items.get_user_settings(user_id)
    stats = learning_items.get_learning_stats(user_id, **_settings_filters(settings))
    today_cards = _today_cards(user_id, settings)
    await query.edit_message_text(format_stats(stats, today_count=len(today_cards)), reply_markup=stats_keyboard())


async def handle_flashcard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "flash:show":
        session = learning_items.get_current_session(user_id)
        if not session or not _session_item_id(session):
            await query.edit_message_text("Chưa có thẻ nào. Dùng /flash trước.")
            return
        card = learning_items.get_learning_item(_session_item_id(session))
        if not card:
            await query.edit_message_text("Không tìm thấy thẻ hiện tại. Dùng /flash để lấy thẻ khác.")
            return
        learning_items.reveal_current_session(user_id)
        await query.edit_message_text(format_card_answer(card), reply_markup=answer_keyboard())
        return

    if data.startswith("flash:grade:"):
        grade = data.split(":")[-1]
        updated, error = learning_items.grade_current_item(user_id, grade)
        if error:
            await query.edit_message_text(grade_error_message(error))
            return
        await query.edit_message_text(format_next_review(updated), reply_markup=continue_keyboard())
        return

    if data == "flash:reset:cancel":
        await query.edit_message_text("Đã hủy reset tiến độ.")
        return

    if data == "flash:reset:confirm":
        learning_items.reset_user_learning_progress(user_id)
        await query.edit_message_text("Đã reset tiến độ flashcard. Dùng /flash để học lại từ đầu.")
        return

    if data.startswith("flash:goal:"):
        preset = data.split(":")[-1]
        settings = learning_items.set_user_goal_preset(user_id, preset)
        await query.edit_message_text(format_goal(settings))
        return

    if data == "flash:today:list":
        settings = learning_items.get_user_settings(user_id)
        cards = _today_cards(user_id, settings)
        await query.edit_message_text(format_today_card_list(cards), reply_markup=today_cards_keyboard(cards))
        return

    if data.startswith("flash:card:"):
        card_id = int(data.split(":")[-1])
        card = learning_items.get_learning_item(card_id)
        if not card:
            await query.edit_message_text("Không tìm thấy thẻ này.")
            return
        await query.edit_message_text(format_card_detail(card), reply_markup=stats_keyboard())
        return

    settings = learning_items.get_user_settings(user_id)
    if data == "flash:next":
        card = learning_items.pick_next_item(user_id, **_settings_filters(settings))
        await _edit_card_for_query(query, user_id, card)
        return
    if data == "flash:stats":
        await _edit_stats(query, user_id)
