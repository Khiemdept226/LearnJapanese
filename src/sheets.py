# Mock version of sheets.py for testing without Google API
# import gspread
# from google.oauth2.service_account import Credentials
# import os
# from .config import GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE

def get_client():
    # Mocking client, not needed for mock data
    return True

def fetch_ready_lessons():
    """
    Returns mock lessons for testing.
    """
    mock_lessons = [
        {
            'lesson_id': 'N5-001',
            'level': 'N5',
            'title': 'Chào hỏi buổi sáng',
            'dialogue_jp': 'A: おはようございます。\nB: おはようございます。今日は寒いですね。\nA: そうですね。',
            'dialogue_vi': 'A: Chào buổi sáng.\nB: Chào buổi sáng. Hôm nay lạnh nhỉ.\nA: Đúng vậy nhỉ.',
            'vocab': 'おはよう = chào buổi sáng\n今日 (きょう) = hôm nay\n寒い (さむい) = lạnh',
            'grammar': 'は: trợ từ chủ đề\nですね: nhỉ, nhé (tìm kiếm sự đồng tình)',
            'quiz': 'Hôm nay thời tiết thế nào?',
            'quiz_answer': 'Thời tiết lạnh (寒いですね)',
            'shadowing': '今日は寒いですね。',
            'status': 'ready',
            'order': 1
        },
        {
            'lesson_id': 'N5-002',
            'level': 'N5',
            'title': 'Hỏi tên',
            'dialogue_jp': 'A: お名前は何ですか。\nB: 私は山田です。\nA: よろしくお願いします。',
            'dialogue_vi': 'A: Tên của bạn là gì?\nB: Tôi là Yamada.\nA: Rất mong được giúp đỡ.',
            'vocab': '名前 (なまえ) = Tên\n何 (なん) = Cái gì\n私 (わたし) = Tôi',
            'grammar': '何ですか: Là cái gì?\nよろしくお願いします: Rất mong được giúp đỡ.',
            'quiz': 'Người B tên là gì?',
            'quiz_answer': 'Yamada (山田)',
            'shadowing': 'お名前は何ですか。',
            'status': 'ready',
            'order': 2
        }
    ]
    return mock_lessons

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
