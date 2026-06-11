import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")

# Schedule & Timezone
TIMEZONE = os.getenv("TIMEZONE", "Asia/Bangkok")
DAILY_SEND_TIME = os.getenv("DAILY_SEND_TIME", "07:30")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/learningjp.sqlite3")

def validate_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token":
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GOOGLE_SHEET_ID or GOOGLE_SHEET_ID == "your_google_sheet_id":
        missing.append("GOOGLE_SHEET_ID")
        
    if missing:
        raise ValueError(f"Missing or invalid required environment variables: {', '.join(missing)}")

# Flashcards
FLASHCARD_ENABLED = os.getenv("FLASHCARD_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")
FLASHCARD_DAILY_TIME = os.getenv("FLASHCARD_DAILY_TIME", "20:30")
FLASHCARD_DAILY_NEW_LIMIT = int(os.getenv("FLASHCARD_DAILY_NEW_LIMIT", "5"))
FLASHCARD_DAILY_REVIEW_LIMIT = int(os.getenv("FLASHCARD_DAILY_REVIEW_LIMIT", "20"))
FLASHCARD_LEVEL = os.getenv("FLASHCARD_LEVEL", "N4")
FLASHCARD_TIMEZONE = os.getenv("FLASHCARD_TIMEZONE", TIMEZONE)
FLASHCARD_IMPORT_SOURCE = os.getenv("FLASHCARD_IMPORT_SOURCE", "sheet").strip().lower()
FLASHCARD_PDF_PATH = os.getenv("FLASHCARD_PDF_PATH", "docs/20250312140417_Tài liệu flash N4.pdf")
FLASHCARD_PDF_LEVEL = os.getenv("FLASHCARD_PDF_LEVEL", "N4")
FLASHCARD_PDF_SOURCE = os.getenv("FLASHCARD_PDF_SOURCE", "n4_pdf")
FLASHCARD_SHEET_NAME = os.getenv("FLASHCARD_SHEET_NAME", "flashcards")
FLASHCARD_SHEET_LEVEL = os.getenv("FLASHCARD_SHEET_LEVEL", "N4")

