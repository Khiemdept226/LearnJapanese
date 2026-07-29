import datetime
import os
import sys
import threading

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw

# Add src and root to path to reuse existing logic.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import settings_store
import sheets
import study_reminders
from config import DAILY_SEND_TIME, FLASHCARD_DAILY_TIME, FLASHCARD_ENABLED, validate_config
from db import init_db
from gui.main_window import AppWindow
from learning_items import get_learning_stats, get_user_settings, init_learning_db

LOCAL_USER_ID = 1


class DesktopApp:
    def __init__(self):
        init_db()
        init_learning_db()

        self.app_window = None
        self.icon = None
        self.running = True

    def _learning_filters(self):
        settings = get_user_settings(LOCAL_USER_ID)
        return {
            "level": settings.get("level"),
            "item_type": settings.get("item_type"),
            "deck_id": settings.get("deck_id"),
            "tags": settings.get("tags"),
        }

    def _learning_stats(self):
        return get_learning_stats(LOCAL_USER_ID, **self._learning_filters())

    def _save_desktop_setting(self, key, value):
        config = settings_store.load_settings()
        config[key] = value
        settings_store.save_settings(config)

    def create_image(self):
        image = Image.new("RGB", (64, 64), color=(30, 30, 30))
        d = ImageDraw.Draw(image)
        d.text((16, 20), "JLPT", fill=(255, 255, 255))
        return image

    def on_show_window(self, icon, item):
        if self.app_window is None or not self.app_window.winfo_exists():
            return
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
                # pystray's notify takes (message, title).
                self.icon.notify(message, title)
            except Exception as e:
                print(f"Failed to send notification: {e}")

    def _send_daily_lesson_notification(self):
        import db

        user = db.get_user(LOCAL_USER_ID)
        if not user:
            return

        lesson = sheets.get_lesson_by_order(user["current_lesson_order"])
        if lesson:
            self.show_notification(
                "Bai hoc moi hom nay",
                f"Bai {lesson['lesson_id']}: {lesson['title']}. Mo app de hoc nhe!",
            )

    def _send_daily_flashcard_notification(self):
        stats = self._learning_stats()
        if stats.get("due", 0) > 0:
            self.show_notification(
                "Den gio on tap",
                f"Ban co {stats['due']} the den han can on tap hom nay.",
            )

    def _send_workday_study_reminder(self, config, now):
        try:
            stats = self._learning_stats()
            decision = study_reminders.should_send_study_reminder(config, stats, now)
            if decision.should_notify:
                self.show_notification(decision.title, decision.message)
                self._save_desktop_setting(
                    "last_reminder_at",
                    now.replace(microsecond=0).isoformat(),
                )
        except Exception as e:
            print(f"Study reminder check failed: {e}")

    def scheduler_loop(self):
        last_daily_lesson_date = None
        last_daily_flashcard_date = None

        while self.running:
            config = settings_store.load_settings()

            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.date()

            if config.get("daily_reminder_enabled", True) and current_time == DAILY_SEND_TIME:
                if last_daily_lesson_date != current_date:
                    self._send_daily_lesson_notification()
                    last_daily_lesson_date = current_date

            if (
                config.get("daily_reminder_enabled", True)
                and FLASHCARD_ENABLED
                and current_time == FLASHCARD_DAILY_TIME
            ):
                if last_daily_flashcard_date != current_date:
                    self._send_daily_flashcard_notification()
                    last_daily_flashcard_date = current_date

            if config.get("reminder_enabled", True):
                self._send_workday_study_reminder(config, now)

            threading.Event().wait(30)

    def run(self):
        scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        scheduler_thread.start()

        menu = pystray.Menu(
            pystray.MenuItem("Open App", self.on_show_window, default=True),
            pystray.MenuItem("Quit", self.on_exit),
        )
        self.icon = pystray.Icon("LearnJapanese", self.create_image(), "Learn Japanese App", menu)

        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.app_window = AppWindow()
        self.app_window.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.app_window.deiconify()
        self.app_window.mainloop()


if __name__ == "__main__":
    try:
        validate_config()
    except Exception as e:
        print(f"Config error: {e}")

    app = DesktopApp()
    app.run()
