import customtkinter as ctk
import learning_items

LOCAL_USER_ID = 1
LANE_LABELS = {
    "vocab": "Từ mới",
    "kanji": "Kanji",
    "grammar": "Ngữ pháp",
}

class StatsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.title_label = ctk.CTkLabel(self, text="Thống kê học tập", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=(20, 10))
        
        self.refresh_btn = ctk.CTkButton(self, text="Làm mới (Refresh)", command=self.load_stats)
        self.refresh_btn.pack(pady=10)
        
        self.stats_textbox = ctk.CTkTextbox(self, font=("Arial", 16), wrap="word")
        self.stats_textbox.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.load_stats()
        
    def _settings_filters(self):
        settings = learning_items.get_user_settings(LOCAL_USER_ID)
        return {
            "level": settings.get("level"),
            "item_type": settings.get("item_type"),
            "deck_id": settings.get("deck_id"),
            "tags": settings.get("tags"),
        }

    def load_stats(self):
        settings = learning_items.get_user_settings(LOCAL_USER_ID)
        overall_stats = learning_items.get_learning_stats(LOCAL_USER_ID, **self._settings_filters())
        
        lines = []
        lines.append("=== TỔNG QUAN FLASHCARD ===")
        lines.append(f"Tổng thẻ: {overall_stats['total']}")
        lines.append(f"Thẻ mới: {overall_stats['new']}")
        lines.append(f"Đến hạn: {overall_stats['due']}")
        lines.append(f"Đang học: {overall_stats['learning']}")
        lines.append(f"Đã vào review: {overall_stats['review']}")
        lines.append(f"Số lần quên: {overall_stats['lapses']}")
        lines.append("")
        
        for lane in ["vocab", "kanji", "grammar"]:
            lane_stats = learning_items.get_lane_stats(LOCAL_USER_ID, lane)
            lines.append(f"=== {LANE_LABELS[lane].upper()} ===")
            lines.append(f"Tổng thẻ: {lane_stats['total']}")
            lines.append(f"Thẻ mới: {lane_stats['new']}")
            lines.append(f"Đến hạn: {lane_stats['due']}")
            lines.append(f"Đang học: {lane_stats['learning']}")
            lines.append(f"Đã vào review: {lane_stats['review']}")
            lines.append(f"Số lần quên: {lane_stats['lapses']}")
            lines.append("")
            
        self.stats_textbox.configure(state="normal")
        self.stats_textbox.delete("1.0", "end")
        self.stats_textbox.insert("1.0", "\n".join(lines))
        self.stats_textbox.configure(state="disabled")
