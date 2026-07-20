import os
import sys
import threading
import time
import datetime
import pystray
from PIL import Image, ImageDraw
import customtkinter as ctk

# Add src to path to reuse existing logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from db import init_db
from learning_items import init_learning_db
from config import validate_config, FLASHCARD_DAILY_TIME, DAILY_SEND_TIME, FLASHCARD_ENABLED

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

    def scheduler_loop(self):
        last_notified_date = None
        while self.running:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.date()
            
            # Check if it's time for daily lesson or flashcards
            time_to_notify = False
            if current_time == DAILY_SEND_TIME or (FLASHCARD_ENABLED and current_time == FLASHCARD_DAILY_TIME):
                time_to_notify = True
                
            if time_to_notify and last_notified_date != current_date:
                # Open window to remind user
                if self.app_window:
                    self.app_window.after(0, self.app_window.deiconify)
                    self.app_window.after(100, self.app_window.focus_force)
                last_notified_date = current_date
                
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
