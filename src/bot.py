import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
import datetime
import pytz

from config import TELEGRAM_BOT_TOKEN, validate_config, TIMEZONE, DAILY_SEND_TIME, FLASHCARD_ENABLED, FLASHCARD_TIMEZONE, FLASHCARD_DAILY_TIME
from db import init_db
import handlers
import scheduler
import flashcard_handlers
import flashcard_scheduler

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
    application.add_handler(CommandHandler("help", flashcard_handlers.help_command))
    application.add_handler(CommandHandler("today", handlers.today))
    application.add_handler(CommandHandler("dich", handlers.dich))
    application.add_handler(CommandHandler("tuvung", handlers.tuvung))
    application.add_handler(CommandHandler("nguphap", handlers.nguphap))
    application.add_handler(CommandHandler("quiz", handlers.quiz))
    application.add_handler(CommandHandler("dapan", handlers.dapan))
    application.add_handler(CommandHandler("shadowing", handlers.shadowing))
    application.add_handler(CommandHandler("next", handlers.next_lesson))
    application.add_handler(CommandHandler("review", handlers.review))
    application.add_handler(CommandHandler("flash_start", flashcard_handlers.flash_start))
    application.add_handler(CommandHandler("flash", flashcard_handlers.flash))
    application.add_handler(CommandHandler("flash_new", flashcard_handlers.flash_new))
    application.add_handler(CommandHandler("flash_review", flashcard_handlers.flash_review))
    application.add_handler(CommandHandler("flash_stats", flashcard_handlers.flash_stats))
    application.add_handler(CommandHandler("flash_goal", flashcard_handlers.flash_goal))
    application.add_handler(CommandHandler("flash_reset", flashcard_handlers.flash_reset))
    application.add_handler(CommandHandler("flash_settings", flashcard_handlers.flash_settings))
    application.add_handler(CommandHandler("flash_level", flashcard_handlers.flash_level))
    application.add_handler(CommandHandler("flash_type", flashcard_handlers.flash_type))
    application.add_handler(CommandHandler("flash_deck", flashcard_handlers.flash_deck))
    application.add_handler(CommandHandler("flash_tags", flashcard_handlers.flash_tags))
    application.add_handler(CommandHandler("neword", flashcard_handlers.neword))
    application.add_handler(CommandHandler("vocab", flashcard_handlers.vocab))
    application.add_handler(CommandHandler("kanji", flashcard_handlers.kanji))
    application.add_handler(CommandHandler("grammar", flashcard_handlers.grammar))
    application.add_handler(CommandHandler("mix", flashcard_handlers.mix))
    application.add_handler(CommandHandler("stats", flashcard_handlers.flash_stats))
    application.add_handler(CommandHandler("stats_neword", flashcard_handlers.stats_neword))
    application.add_handler(CommandHandler("stats_kanji", flashcard_handlers.stats_kanji))
    application.add_handler(CommandHandler("stats_grammar", flashcard_handlers.stats_grammar))
    application.add_handler(CommandHandler("goal_neword", flashcard_handlers.goal_neword))
    application.add_handler(CommandHandler("goal_kanji", flashcard_handlers.goal_kanji))
    application.add_handler(CommandHandler("goal_grammar", flashcard_handlers.goal_grammar))
    application.add_handler(CommandHandler("show", flashcard_handlers.show))
    application.add_handler(CommandHandler("again", flashcard_handlers.again))
    application.add_handler(CommandHandler("hard", flashcard_handlers.hard))
    application.add_handler(CommandHandler("good", flashcard_handlers.good))
    application.add_handler(CommandHandler("easy", flashcard_handlers.easy))
    application.add_handler(CallbackQueryHandler(flashcard_handlers.handle_flashcard_callback, pattern="^flash:"))

    # Scheduler
    job_queue = application.job_queue
    tz = pytz.timezone(TIMEZONE)
    hour, minute = map(int, DAILY_SEND_TIME.split(':'))
    time_to_run = datetime.time(hour=hour, minute=minute, tzinfo=tz)
    
    job_queue.run_daily(scheduler.send_daily_lesson, time=time_to_run, name="daily_lesson_job")

    if FLASHCARD_ENABLED:
        flash_tz = pytz.timezone(FLASHCARD_TIMEZONE)
        flash_hour, flash_minute = map(int, FLASHCARD_DAILY_TIME.split(':'))
        flash_time_to_run = datetime.time(hour=flash_hour, minute=flash_minute, tzinfo=flash_tz)
        job_queue.run_daily(
            flashcard_scheduler.send_daily_flashcards,
            time=flash_time_to_run,
            name="daily_flashcard_job"
        )
    
    logger.info("Bot started successfully. Waiting for messages...")
    application.run_polling()

if __name__ == '__main__':
    main()






