import sys
import os
import threading
import customtkinter as ctk

import learning_items

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools')))
try:
    import import_flashcards
except ImportError:
    pass

LOCAL_USER_ID = 1

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Flashcard Filters ---
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.filter_frame, text="Bộ lọc chung (Global Filters)", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.level_var = ctk.StringVar()
        self.type_var = ctk.StringVar()
        self.deck_var = ctk.StringVar()
        self.tags_var = ctk.StringVar()
        
        self._add_filter_row(self.filter_frame, "Level (VD: N4):", self.level_var)
        self._add_filter_row(self.filter_frame, "Type (vocab, kanji...):", self.type_var)
        self._add_filter_row(self.filter_frame, "Deck ID:", self.deck_var)
        self._add_filter_row(self.filter_frame, "Tags:", self.tags_var)
        
        ctk.CTkButton(self.filter_frame, text="Lưu bộ lọc", command=self.save_filters).pack(pady=10)
        
        # --- Goals ---
        self.goal_frame = ctk.CTkFrame(self)
        self.goal_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.goal_frame, text="Mục tiêu (Goals)", font=("Arial", 16, "bold")).pack(pady=10)
        self.preset_var = ctk.StringVar()
        presets = ["jlpt_sprint", "light", "steady", "heavy"]
        self.preset_dropdown = ctk.CTkComboBox(self.goal_frame, values=presets, variable=self.preset_var)
        self.preset_dropdown.pack(pady=10)
        ctk.CTkButton(self.goal_frame, text="Lưu mục tiêu chung", command=self.save_goal).pack(pady=10)
        
        # --- Sync Data ---
        self.sync_frame = ctk.CTkFrame(self)
        self.sync_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.sync_frame, text="Đồng bộ dữ liệu từ Google Sheets", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.sync_btn = ctk.CTkButton(self.sync_frame, text="Bắt đầu đồng bộ (Sync)", command=self.start_sync)
        self.sync_btn.pack(pady=10)
        
        self.sync_status = ctk.CTkLabel(self.sync_frame, text="")
        self.sync_status.pack(pady=5)
        
        self.load_settings()

    def _add_filter_row(self, parent, label_text, var):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(frame, textvariable=var, width=150).pack(side="right")

    def load_settings(self):
        settings = learning_items.get_user_settings(LOCAL_USER_ID)
        if settings:
            self.level_var.set(settings.get("level") or "")
            self.type_var.set(settings.get("item_type") or "")
            self.deck_var.set(settings.get("deck_id") or "")
            self.tags_var.set(settings.get("tags") or "")
            self.preset_var.set(settings.get("preset") or "steady")

    def save_filters(self):
        learning_items.set_user_learning_filter(
            LOCAL_USER_ID,
            level=self.level_var.get() or None,
            item_type=self.type_var.get() or None,
            deck_id=self.deck_var.get() or None,
            tags=self.tags_var.get() or None
        )
        self.sync_status.configure(text="Đã lưu bộ lọc thành công!")
        
    def save_goal(self):
        learning_items.set_user_goal_preset(LOCAL_USER_ID, self.preset_var.get())
        self.sync_status.configure(text="Đã lưu mục tiêu thành công!")

    def start_sync(self):
        self.sync_btn.configure(state="disabled")
        self.sync_status.configure(text="Đang đồng bộ... Vui lòng chờ...")
        
        def sync_task():
            try:
                # Call learning import
                stats, _ = import_flashcards.run_learning_import(all_decks=True)
                imported = stats.get('imported', 0)
                msg = f"Đồng bộ thành công! {imported} thẻ đã được tải về."
            except Exception as e:
                msg = f"Đồng bộ thất bại: {str(e)}"
            finally:
                # Back to main thread for UI
                self.after(0, lambda: self.sync_complete(msg))
                
        threading.Thread(target=sync_task, daemon=True).start()
        
    def sync_complete(self, msg):
        self.sync_status.configure(text=msg)
        self.sync_btn.configure(state="normal")
