from telegram import Update
from telegram.ext import ContextTypes
import db
import sheets

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user exists
    existing_user = db.get_user(user.id)
    if not existing_user:
        initial_order = sheets.get_first_ready_order()
        db.create_or_update_user(user.id, chat_id, user.username, initial_order)
        await update.message.reply_text(
            f"Chào mừng bạn đến với bot học tiếng Nhật!\n"
            f"Mỗi ngày tôi sẽ gửi cho bạn 1 bài học mới.\n"
            f"Hãy dùng lệnh /today để xem bài học hôm nay."
        )
    else:
        db.create_or_update_user(user.id, chat_id, user.username, existing_user['current_lesson_order'])
        await update.message.reply_text("Chào mừng bạn quay trở lại! Dùng /today để xem bài học hiện tại.")

async def send_lesson_info(update: Update, context: ContextTypes.DEFAULT_TYPE, lesson):
    if not lesson:
        await update.message.reply_text("Hiện tại không đọc được bài học hoặc bạn đã học hết bài. Thử lại sau.")
        return
        
    text = (
        f"Bài hôm nay: {lesson['lesson_id']} - {lesson['title']}\n\n"
        f"{lesson['dialogue_jp']}\n\n"
        f"Chọn lệnh:\n"
        f"/dich - bản dịch\n"
        f"/tuvung - từ vựng\n"
        f"/nguphap - ngữ pháp\n"
        f"/quiz - câu hỏi\n"
        f"/shadowing - luyện nói"
    )
    await update.message.reply_text(text)

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        await start(update, context)
        user = db.get_user(update.effective_user.id)
        
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    await send_lesson_info(update, context, lesson)

async def dich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    if lesson:
        await update.message.reply_text(f"Bản dịch:\n{lesson['dialogue_vi']}")

async def tuvung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    if lesson:
        await update.message.reply_text(f"Từ vựng:\n{lesson['vocab']}")

async def nguphap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    if lesson:
        await update.message.reply_text(f"Ngữ pháp:\n{lesson['grammar']}")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    if lesson:
        await update.message.reply_text(f"Câu hỏi luyển tập:\n{lesson['quiz']}\n\n(Dùng /dapan để xem đáp án)")

async def dapan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    if lesson:
        await update.message.reply_text(f"Đáp án:\n{lesson['quiz_answer']}")

async def shadowing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
    lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
    if lesson:
        shadow = lesson.get('shadowing')
        if shadow:
            await update.message.reply_text(f"Luyện nói (Shadowing):\n{shadow}")
        else:
            await update.message.reply_text("Bài này không có phần luyện nói riêng.")

async def next_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        return
        
    current_order = user['current_lesson_order']
    next_order = current_order + 1
    
    lesson = sheets.get_lesson_by_order(next_order)
    if lesson:
        db.update_user_lesson_order(user['telegram_user_id'], next_order)
        await update.message.reply_text("Đã chuyển sang bài tiếp theo!")
        await send_lesson_info(update, context, lesson)
    else:
        await update.message.reply_text("Bạn đã học đến bài cuối cùng hiện có. Hãy chờ thêm bài mới nhé!")

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    latest_sent_lesson_id = db.get_latest_sent_lesson(update.effective_user.id)
    if not latest_sent_lesson_id:
        await update.message.reply_text("Bạn chưa học bài nào để ôn lại.")
        return
        
    lesson = sheets.get_lesson_by_id(latest_sent_lesson_id)
    if lesson:
        await update.message.reply_text("Đây là bài cũ gần nhất bạn đã học:")
        await send_lesson_info(update, context, lesson)
    else:
        await update.message.reply_text("Không tìm thấy thông tin bài cũ.")
