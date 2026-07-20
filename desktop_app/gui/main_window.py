import customtkinter as ctk

# We'll import these frames once they are created
# For now, we will create placeholders
try:
    from .daily_lesson_frame import DailyLessonFrame
except ImportError:
    class DailyLessonFrame(ctk.CTkFrame):
        def __init__(self, master):
            super().__init__(master)
            ctk.CTkLabel(self, text="Daily Lesson Placeholder").pack(pady=20)

try:
    from .flashcard_frame import FlashcardFrame
except ImportError:
    class FlashcardFrame(ctk.CTkFrame):
        def __init__(self, master):
            super().__init__(master)
            ctk.CTkLabel(self, text="Flashcard Placeholder").pack(pady=20)

try:
    from .stats_frame import StatsFrame
except ImportError:
    class StatsFrame(ctk.CTkFrame):
        def __init__(self, master):
            super().__init__(master)
            ctk.CTkLabel(self, text="Stats Placeholder").pack(pady=20)

try:
    from .settings_frame import SettingsFrame
except ImportError:
    class SettingsFrame(ctk.CTkFrame):
        def __init__(self, master):
            super().__init__(master)
            ctk.CTkLabel(self, text="Settings Placeholder").pack(pady=20)


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Learn Japanese - JLPT")
        self.geometry("800x600")
        self.minsize(600, 500)

        # TabView
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Add tabs
        self.tabview.add("Bài học mỗi ngày")
        self.tabview.add("Flashcards")
        self.tabview.add("Thống kê")
        self.tabview.add("Cài đặt")

        # Initialize frames
        self.daily_lesson_frame = DailyLessonFrame(self.tabview.tab("Bài học mỗi ngày"))
        self.daily_lesson_frame.pack(fill="both", expand=True)

        self.flashcard_frame = FlashcardFrame(self.tabview.tab("Flashcards"))
        self.flashcard_frame.pack(fill="both", expand=True)

        self.stats_frame = StatsFrame(self.tabview.tab("Thống kê"))
        self.stats_frame.pack(fill="both", expand=True)

        self.settings_frame = SettingsFrame(self.tabview.tab("Cài đặt"))
        self.settings_frame.pack(fill="both", expand=True)
