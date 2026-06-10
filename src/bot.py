import logging
from telegram.ext import Application, CommandHandler
import datetime
import pytz

from config import TELEGRAM_BOT_TOKEN, validate_config, TIMEZONE, DAILY_SEND_TIME
from db import init_db
import handlers
import scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    try:
        validate_config()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return

    # Initialize Database
    init_db()

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("today", handlers.today))
    application.add_handler(CommandHandler("dich", handlers.dich))
    application.add_handler(CommandHandler("tuvung", handlers.tuvung))
    application.add_handler(CommandHandler("nguphap", handlers.nguphap))
    application.add_handler(CommandHandler("quiz", handlers.quiz))
    application.add_handler(CommandHandler("dapan", handlers.dapan))
    application.add_handler(CommandHandler("shadowing", handlers.shadowing))
    application.add_handler(CommandHandler("next", handlers.next_lesson))
    application.add_handler(CommandHandler("review", handlers.review))

    # Scheduler
    job_queue = application.job_queue
    tz = pytz.timezone(TIMEZONE)
    hour, minute = map(int, DAILY_SEND_TIME.split(':'))
    time_to_run = datetime.time(hour=hour, minute=minute, tzinfo=tz)
    
    job_queue.run_daily(scheduler.send_daily_lesson, time=time_to_run, name="daily_lesson_job")
    
    logger.info("Bot started successfully. Waiting for messages...")
    application.run_polling()

if __name__ == '__main__':
    main()
