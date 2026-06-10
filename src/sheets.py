import gspread
from google.oauth2.service_account import Credentials
import os
from .config import GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

def get_client():
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        print(f"Warning: Service account file {GOOGLE_SERVICE_ACCOUNT_FILE} not found. Sheet fetch will fail.")
        return None
        
    credentials = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client

def fetch_ready_lessons():
    """
    Fetches all lessons from the sheet.
    Returns a list of dictionaries.
    """
    client = get_client()
    if not client:
        return []
        
    try:
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1 # 'lessons' sheet should be the first one
        records = sheet.get_all_records()
        
        # Filter ready lessons and convert order to int
        ready_lessons = []
        for row in records:
            if str(row.get('status', '')).strip().lower() == 'ready':
                # Convert order to int for reliable comparison
                try:
                    row['order'] = int(row.get('order', 0))
                    ready_lessons.append(row)
                except ValueError:
                    pass
        
        # Sort by order
        ready_lessons.sort(key=lambda x: x['order'])
        return ready_lessons
        
    except Exception as e:
        print(f"Error fetching sheet: {e}")
        return []

def get_lesson_by_order(order):
    lessons = fetch_ready_lessons()
    for lesson in lessons:
        if lesson['order'] == order:
            return lesson
    return None
    
def get_lesson_by_id(lesson_id):
    lessons = fetch_ready_lessons()
    for lesson in lessons:
        if str(lesson['lesson_id']) == str(lesson_id):
            return lesson
    return None

def get_first_ready_order():
    lessons = fetch_ready_lessons()
    if lessons:
        return lessons[0]['order']
    return 1
