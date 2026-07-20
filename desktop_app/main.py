import os
import sys
import threading
import time
import datetime
import pystray
from PIL import Image, ImageDraw
import customtkinter as ctk

# Add src and root to path to reuse existing logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import init_db
from learning_items import init_learning_db, get_learning_stats, get_user_settings
from config import validate_config, FLASHCARD_DAILY_TIME, DAILY_SEND_TIME, FLASHCARD_ENABLED
import sheets
import settings_store

# Import the GUI app
from gui.main_window import AppWindow

class DesktopApp:
    def __init__(self):
        # Initialize databases
        init_db()
        init_learning_db()
        
        self.app_window = None
        self.icon = None
        self.running = True
        
    def create_image(self):
        # Create a simple icon for the system tray
        image = Image.new('RGB', (64, 64), color=(30, 30, 30))
        d = ImageDraw.Draw(image)
        d.text((16, 20), "JLPT", fill=(255, 255, 255))
        return image

    def on_show_window(self, icon, item):
        if self.app_window is None or not self.app_window.winfo_exists():
            # Should not happen as we keep it hidden, but just in case
            pass
        self.app_window.after(0, self.app_window.deiconify)
        self.app_window.after(100, self.app_window.focus_force)

    def hide_window(self):
        if self.app_window:
            self.app_window.withdraw()

    def on_exit(self, icon, item):
        self.running = False
        self.icon.stop()
        if self.app_window:
            self.app_window.quit()

    def show_notification(self, title, message):
        if self.icon:
            try:
                # pystray's notify takes (message, title)
                self.icon.notify(message, title)
            except Exception as e:
                print(f"Failed to send notification: {e}")

    def scheduler_loop(self):
        last_daily_lesson_date = None
        last_daily_flashcard_date = None
        last_review_notification_time = 0
        
        while self.running:
            # Load desktop settings
            config = settings_store.load_settings()
            
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.date()
            
            # 1. Daily Lesson Notification
            if config.get("daily_reminder_enabled", True) and current_time == DAILY_SEND_TIME:
                if last_daily_lesson_date != current_date:
                    import db
                    user = db.get_user(1)
                    if user:
                        lesson = sheets.get_lesson_by_order(user['current_lesson_order'])
                        if lesson:
                            self.show_notification(
                                "Bài học mới hôm nay", 
                                f"Bài {lesson['lesson_id']}: {lesson['title']}. Hãy mở app để học nhé!"
                            )
                    last_daily_lesson_date = current_date
            
            # 2. Daily Flashcards Notification (configured daily time)
            if config.get("daily_reminder_enabled", True) and FLASHCARD_ENABLED and current_time == FLASHCARD_DAILY_TIME:
                if last_daily_flashcard_date != current_date:
                    settings = get_user_settings(1)
                    # Helper dictionary mock for _settings_filters
                    filters = {
                        "level": settings.get("level"),
                        "item_type": settings.get("item_type"),
                        "deck_id": settings.get("deck_id"),
                        "tags": settings.get("tags")
                    }
                    stats = get_learning_stats(1, **filters)
                    if stats.get("due", 0) > 0:
                        self.show_notification(
                            "Đến giờ ôn tập rồi!",
                            f"Bạn đang có {stats['due']} thẻ đến hạn cần ôn tập hôm nay."
                        )
                    last_daily_flashcard_date = current_date

            # 3. Periodic Review Notifications (based on interval)
            if config.get("reminder_enabled", True):
                interval_seconds = config.get("reminder_interval_hours", 2) * 3600
                if time.time() - last_review_notification_time >= interval_seconds:
                    settings = get_user_settings(1)
                    filters = {
                        "level": settings.get("level"),
                        "item_type": settings.get("item_type"),
                        "deck_id": settings.get("deck_id"),
                        "tags": settings.get("tags")
                    }
                    stats = get_learning_stats(1, **filters)
                    due_count = stats.get("due", 0)
                    if due_count > 0:
                        self.show_notification(
                            "Nhắc nhở ôn tập",
                            f"Bạn có {due_count} từ cần ôn tập. Hãy dành chút thời gian học nhé!"
                        )
                        # Set to now so we don't notify again until interval passes
                        last_review_notification_time = time.time()
                    else:
                        # If no cards are due, we check again in 10 minutes rather than waiting the whole interval
                        last_review_notification_time = time.time() - interval_seconds + 600

            time.sleep(30)

    def run(self):
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        scheduler_thread.start()
        
        # Setup tray icon
        menu = pystray.Menu(
            pystray.MenuItem("Open App", self.on_show_window, default=True),
            pystray.MenuItem("Quit", self.on_exit)
        )
        self.icon = pystray.Icon("LearnJapanese", self.create_image(), "Learn Japanese App", menu)
        
        # Run pystray in a separate thread because tkinter needs main thread
        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()
        
        # Main GUI Loop
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.app_window = AppWindow()
        self.app_window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Show on launch
        self.app_window.deiconify()
        self.app_window.mainloop()

if __name__ == "__main__":
    try:
        validate_config()
    except Exception as e:
        print(f"Config error: {e}")
        
    app = DesktopApp()
    app.run()
