from telegram.ext import ContextTypes
import logging
import db
import sheets

logger = logging.getLogger(__name__)

async def send_daily_lesson(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Starting daily lesson dispatch...")
    users = db.get_all_users()
    
    for user in users:
        telegram_user_id = user['telegram_user_id']
        chat_id = user['chat_id']
        current_order = user['current_lesson_order']
        
        lesson = sheets.get_lesson_by_order(current_order)
        if lesson:
            try:
                text = (
                    f"Bài học mới hôm nay: {lesson['lesson_id']} - {lesson['title']}\n\n"
                    f"{lesson['dialogue_jp']}\n\n"
                    f"Chọn lệnh:\n"
                    f"/dich - bản dịch\n"
                    f"/tuvung - từ vựng\n"
                    f"/nguphap - ngữ pháp\n"
                    f"/quiz - câu hỏi\n"
                    f"/shadowing - luyện nói\n\n"
                    f"Khi học xong, hãy dùng /next để chuyển bài."
                )
                await context.bot.send_message(chat_id=chat_id, text=text)
                db.record_sent_lesson(telegram_user_id, lesson['lesson_id'])
                logger.info(f"Sent lesson {lesson['lesson_id']} to user {telegram_user_id}")
                
            except Exception as e:
                logger.error(f"Failed to send lesson to {telegram_user_id}: {e}")
        else:
            try:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text="Chúc mừng bạn đã học hết các bài hiện có! Hãy dùng /review để ôn tập hoặc chờ thêm bài mới."
                )
            except Exception as e:
                logger.error(f"Failed to send finish msg to {telegram_user_id}: {e}")
