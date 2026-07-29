import customtkinter as ctk

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

        self.title("Learn Japanese - JLPT")
        self.geometry("800x600")
        self.minsize(600, 500)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Daily Lesson")
        self.tabview.add("Flashcards")
        self.tabview.add("Stats")
        self.tabview.add("Settings")

        self.daily_lesson_frame = DailyLessonFrame(self.tabview.tab("Daily Lesson"))
        self.daily_lesson_frame.pack(fill="both", expand=True)

        self.flashcard_frame = FlashcardFrame(self.tabview.tab("Flashcards"))
        self.flashcard_frame.pack(fill="both", expand=True)

        self.stats_frame = StatsFrame(self.tabview.tab("Stats"))
        self.stats_frame.pack(fill="both", expand=True)

        self.settings_frame = SettingsFrame(self.tabview.tab("Settings"))
        self.settings_frame.pack(fill="both", expand=True)

    def show_flashcards(self):
        self.tabview.set("Flashcards")
        self.flashcard_frame.load_next_card()
