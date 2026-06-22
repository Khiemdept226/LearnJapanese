import datetime as dt
import json

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


def continue_keyboard(next_callback="flash:next"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Thẻ tiếp theo", callback_data=next_callback)],
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


def stats_keyboard(next_callback="flash:next"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Danh sách hôm nay", callback_data="flash:today:list")],
        [InlineKeyboardButton("Thẻ tiếp theo", callback_data=next_callback)],
    ])

LANE_LABELS = {
    "vocab": "Từ mới",
    "kanji": "Kanji",
    "grammar": "Ngữ pháp",
}

LANE_GOAL_PRESETS = {
    "vocab": {"light": (5, 25), "steady": (10, 50), "heavy": (15, 80)},
    "kanji": {"light": (1, 15), "steady": (3, 30), "heavy": (5, 50)},
    "grammar": {"light": (1, 10), "steady": (2, 20), "heavy": (4, 40)},
}
LANE_DECK_USAGE = "Usage: /lane_deck neword|kanji|grammar <deck|all>"
LANE_TAGS_USAGE = "Usage: /lane_tags neword|kanji|grammar <tags|all>"
LANE_SETTINGS_LANES = ("vocab", "kanji", "grammar")

def lane_goal_keyboard(item_type):
    lane = learning_items.normalize_lane(item_type)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Nhẹ", callback_data=f"flash:lane_goal:{lane}:light"),
        InlineKeyboardButton("Đều", callback_data=f"flash:lane_goal:{lane}:steady"),
        InlineKeyboardButton("Nặng", callback_data=f"flash:lane_goal:{lane}:heavy"),
    ]])


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
        "/neword - học từ mới\n"
        "/vocab - học từ mới\n"
        "/kanji - học kanji\n"
        "/grammar - học ngữ pháp\n"
        "/mix - học xen kẽ từ mới, kanji, ngữ pháp\n"
        "/flash - học thông minh theo filter hiện tại\n"
        "/stats - thống kê tổng\n"
        "/stats_neword - thống kê từ mới\n"
        "/stats_kanji - thống kê kanji\n"
        "/stats_grammar - thống kê ngữ pháp\n"
        "/goal_neword - chọn goal từ mới\n"
        "/goal_kanji - chọn goal kanji\n"
        "/goal_grammar - chọn goal ngữ pháp\n"
        "/lane_settings - xem filter từng lane\n"
        "/lane_deck <lane> <deck|all> - chọn deck cho lane\n"
        "/lane_tags <lane> <tags|all> - chọn tags cho lane\n"
        "/flash_stats - xem tiến độ filter hiện tại\n"
        "/flash_reset - học lại flashcard từ đầu\n"
        "/show - hiện đáp án\n"
        "/again /hard /good /easy - chấm thẻ"
    )


def item_extra(item):
    raw = item.get("extra_json")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}

def _format_related_words(value):
    rows = []
    for line in str(value or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|", 2)]
        if len(parts) == 3 and parts[0] and parts[1] and parts[2]:
            rows.append(f"{parts[0]}（{parts[1]}）- {parts[2]}")
        else:
            rows.append(line)
    return rows


def format_item_front(item):
    return (
        "Flashcard\n"
        f"Mặt trước: {_item_front(item)}\n\n"
        "Tự nhớ cách đọc và nghĩa, rồi bấm Hiện đáp án."
    )


def format_item_answer(item):
    extra = item_extra(item)
    item_type = item.get("item_type") or "vocab"
    lines = [f"Mặt trước: {_item_front(item)}"]

    if item_type == "kanji":
        if item.get("hanviet"):
            lines.append(f"Hán Việt: {item['hanviet']}")
        lines.append(f"Nghĩa: {_item_meaning(item)}")
        if extra.get("onyomi"):
            lines.append(f"Onyomi: {extra['onyomi']}")
        if extra.get("kunyomi"):
            lines.append(f"Kunyomi: {extra['kunyomi']}")
        if extra.get("examples"):
            lines.append(f"Ví dụ: {extra['examples']}")
        if extra.get("memo"):
            lines.extend(["", "Cách nhớ:"])
            lines.extend(str(extra["memo"]).splitlines())
        related_words = _format_related_words(extra.get("related_words"))
        if related_words:
            lines.extend(["", "Từ liên quan:"])
            lines.extend(f"{index}. {word}" for index, word in enumerate(related_words, start=1))
    elif item_type == "grammar":
        lines.append(f"Nghĩa: {_item_meaning(item)}")
        if extra.get("usage"):
            lines.append(f"Cách dùng: {extra['usage']}")
        if item.get("example_jp"):
            lines.append(f"Ví dụ: {item['example_jp']}")
        if item.get("example_vi"):
            lines.append(f"Dịch: {item['example_vi']}")
    elif item_type == "kaiwa":
        if extra.get("dialogue_jp"):
            lines.append(f"Hội thoại JP: {extra['dialogue_jp']}")
        if extra.get("dialogue_vi"):
            lines.append(f"Hội thoại VI: {extra['dialogue_vi']}")
        if extra.get("vocab"):
            lines.append(f"Từ vựng: {extra['vocab']}")
        if extra.get("grammar"):
            lines.append(f"Ngữ pháp: {extra['grammar']}")
        if extra.get("shadowing"):
            lines.append(f"Shadowing: {extra['shadowing']}")
        if extra.get("quiz"):
            lines.append(f"Quiz: {extra['quiz']}")
        if extra.get("quiz_answer"):
            lines.append(f"Đáp án: {extra['quiz_answer']}")
    else:
        reading = item.get("reading") or "-"
        lines.append(f"Cách đọc: {reading}")
        if item.get("hanviet"):
            lines.append(f"Hán Việt: {item['hanviet']}")
        lines.append(f"Nghĩa: {_item_meaning(item)}")
        if item.get("example_jp"):
            lines.append(f"Ví dụ: {item['example_jp']}")
        if item.get("example_vi"):
            lines.append(f"Dịch: {item['example_vi']}")

    lines.extend(["", "Bạn nhớ mức nào?"])
    return "\n".join(lines)


def format_card_front(card):
    return format_item_front(card)


def format_card_answer(card):
    return format_item_answer(card)


def format_card_detail(card):
    return format_item_answer(card).replace("\n\nBạn nhớ mức nào?", "")


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

def format_lane_stats(item_type, stats, today_count=None):
    lane = learning_items.normalize_lane(item_type)
    return format_stats(stats, today_count=today_count).replace(
        "Tiến độ flashcard",
        f"Tiến độ {LANE_LABELS[lane]}",
        1,
    )

def _next_callback_for_mode(mode):
    if mode == "mix":
        return "flash:mix_next"
    if mode and mode.startswith("lane:"):
        return f"flash:next_lane:{mode.split(':', 1)[1]}"
    return "flash:next"


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


def format_lane_settings(settings_rows):
    lines = ["Lane settings"]
    for settings in settings_rows:
        lane = learning_items.normalize_lane(settings.get("item_type"))
        lines.extend([
            "",
            LANE_LABELS[lane],
            f"Level: {settings.get('level') or 'N4'}",
            f"Deck: {settings.get('deck_id') or 'all'}",
            f"Tags: {settings.get('tags') or 'all'}",
            f"New/day: {settings.get('daily_new_limit')}",
            f"Review/day: {settings.get('daily_review_limit')}",
        ])
    return "\n".join(lines)


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


async def _send_card_to_message(message, telegram_user_id, card, current_direction="front_to_back"):
    if not card:
        await message.reply_text("Chưa có thẻ flashcard phù hợp. Hãy import dữ liệu Sheet trước.")
        return
    learning_items.set_current_session(telegram_user_id, card["id"], answer_shown=False, current_direction=current_direction)
    await message.reply_text(format_card_front(card), reply_markup=front_keyboard())


async def _edit_card_for_query(query, telegram_user_id, card, current_direction="front_to_back"):
    if not card:
        await query.edit_message_text("Chưa có thẻ phù hợp lúc này.")
        return
    learning_items.set_current_session(telegram_user_id, card["id"], answer_shown=False, current_direction=current_direction)
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


async def _send_lane_card(update: Update, item_type: str):
    user_id = update.effective_user.id
    lane = learning_items.normalize_lane(item_type)
    card = learning_items.pick_next_lane_item(user_id, lane)
    if not card:
        await update.message.reply_text(f"Chưa có thẻ {LANE_LABELS[lane].lower()} phù hợp.")
        return
    await _send_card_to_message(update.message, user_id, card, current_direction=f"lane:{lane}")


async def neword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_card(update, "vocab")


async def vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_card(update, "vocab")


async def kanji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_card(update, "kanji")


async def grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_card(update, "grammar")


async def mix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    card = learning_items.pick_mix_item(user_id)
    await _send_card_to_message(update.message, user_id, card, current_direction="mix")


async def _send_lane_stats(update: Update, item_type: str):
    user_id = update.effective_user.id
    lane = learning_items.normalize_lane(item_type)
    settings = learning_items.get_lane_settings(user_id, lane)
    stats = learning_items.get_lane_stats(user_id, lane)
    start_at, end_at = _today_bounds_utc()
    today_cards = learning_items.get_reviewed_items_between(
        user_id,
        settings.get("level"),
        start_at,
        end_at,
        limit=30,
        item_type=lane,
        deck_id=settings.get("deck_id"),
        tags=settings.get("tags"),
    )
    await update.message.reply_text(
        format_lane_stats(lane, stats, today_count=len(today_cards)),
        reply_markup=stats_keyboard(next_callback=f"flash:next_lane:{lane}"),
    )


async def stats_neword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_stats(update, "vocab")


async def stats_kanji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_stats(update, "kanji")


async def stats_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_lane_stats(update, "grammar")


async def goal_neword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chọn goal từ mới:", reply_markup=lane_goal_keyboard("vocab"))


async def goal_kanji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chọn goal kanji:", reply_markup=lane_goal_keyboard("kanji"))


async def goal_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chọn goal ngữ pháp:", reply_markup=lane_goal_keyboard("grammar"))


async def lane_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [learning_items.get_lane_settings(update.effective_user.id, lane) for lane in LANE_SETTINGS_LANES]
    await update.message.reply_text(format_lane_settings(rows))


def _parse_lane_arg(args, usage):
    if not args:
        return None, usage
    try:
        return learning_items.normalize_lane(args[0]), None
    except ValueError:
        return None, usage


async def lane_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lane, error = _parse_lane_arg(context.args, LANE_DECK_USAGE)
    if error or len(context.args) < 2:
        await update.message.reply_text(LANE_DECK_USAGE)
        return
    deck_id = " ".join(context.args[1:]).strip()
    deck_id = None if deck_id.lower() == "all" else deck_id
    settings = learning_items.set_lane_filter(update.effective_user.id, lane, deck_id=deck_id, tags=learning_items.get_lane_settings(update.effective_user.id, lane).get("tags"))
    await update.message.reply_text(format_lane_settings([settings]))


async def lane_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lane, error = _parse_lane_arg(context.args, LANE_TAGS_USAGE)
    if error or len(context.args) < 2:
        await update.message.reply_text(LANE_TAGS_USAGE)
        return
    tags = " ".join(context.args[1:]).strip()
    tags = None if tags.lower() == "all" else tags
    settings = learning_items.set_lane_filter(update.effective_user.id, lane, deck_id=learning_items.get_lane_settings(update.effective_user.id, lane).get("deck_id"), tags=tags)
    await update.message.reply_text(format_lane_settings([settings]))


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
    session = learning_items.get_current_session(update.effective_user.id)
    next_callback = _next_callback_for_mode(session.get("current_direction") if session else None)
    updated, error = learning_items.grade_current_item(update.effective_user.id, grade)
    if error:
        await update.message.reply_text(grade_error_message(error))
        return
    await update.message.reply_text(format_next_review(updated), reply_markup=continue_keyboard(next_callback))


async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "again")


async def hard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "hard")


async def good(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "good")


async def easy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _grade_message(update, "easy")


async def _edit_stats(query, user_id):
    session = learning_items.get_current_session(user_id)
    mode = session.get("current_direction") if session else None
    next_callback = _next_callback_for_mode(mode)
    if mode and mode.startswith("lane:"):
        lane = mode.split(":", 1)[1]
        settings = learning_items.get_lane_settings(user_id, lane)
        stats = learning_items.get_lane_stats(user_id, lane)
        start_at, end_at = _today_bounds_utc()
        today_cards = learning_items.get_reviewed_items_between(
            user_id,
            settings.get("level"),
            start_at,
            end_at,
            limit=30,
            item_type=lane,
            deck_id=settings.get("deck_id"),
            tags=settings.get("tags"),
        )
        await query.edit_message_text(
            format_lane_stats(lane, stats, today_count=len(today_cards)),
            reply_markup=stats_keyboard(next_callback=next_callback),
        )
        return
    settings = learning_items.get_user_settings(user_id)
    stats = learning_items.get_learning_stats(user_id, **_settings_filters(settings))
    today_cards = _today_cards(user_id, settings)
    await query.edit_message_text(
        format_stats(stats, today_count=len(today_cards)),
        reply_markup=stats_keyboard(next_callback=next_callback),
    )


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
        session = learning_items.get_current_session(user_id)
        next_callback = _next_callback_for_mode(session.get("current_direction") if session else None)
        updated, error = learning_items.grade_current_item(user_id, grade)
        if error:
            await query.edit_message_text(grade_error_message(error))
            return
        await query.edit_message_text(format_next_review(updated), reply_markup=continue_keyboard(next_callback))
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

    if data.startswith("flash:lane_goal:"):
        _, _, lane, preset = data.split(":")
        daily_new, daily_review = LANE_GOAL_PRESETS[lane][preset]
        settings = learning_items.set_lane_goal(
            user_id,
            lane,
            daily_new_limit=daily_new,
            daily_review_limit=daily_review,
        )
        await query.edit_message_text(
            f"Đã cập nhật goal {LANE_LABELS[lane]}: {settings['daily_new_limit']} thẻ mới/ngày, {settings['daily_review_limit']} ôn/ngày."
        )
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
    if data.startswith("flash:next_lane:"):
        lane = data.split(":")[-1]
        card = learning_items.pick_next_lane_item(user_id, lane)
        await _edit_card_for_query(query, user_id, card, current_direction=f"lane:{lane}")
        return
    if data == "flash:mix_next":
        card = learning_items.pick_mix_item(user_id)
        await _edit_card_for_query(query, user_id, card, current_direction="mix")
        return
    if data == "flash:stats":
        await _edit_stats(query, user_id)

