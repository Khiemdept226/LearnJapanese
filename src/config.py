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
    # if not GOOGLE_SHEET_ID or GOOGLE_SHEET_ID == "your_google_sheet_id":
    #     missing.append("GOOGLE_SHEET_ID")
        
    if missing:
        raise ValueError(f"Missing or invalid required environment variables: {', '.join(missing)}")
