import json
import customtkinter as ctk
import learning_items

LOCAL_USER_ID = 1

class FlashcardFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # Mode Selection
        self.mode_var = ctk.StringVar(value="Học kết hợp (Mix)")
        self.modes = [
            "Học kết hợp (Mix)",
            "Chỉ thẻ mới (New Only)",
            "Chỉ thẻ ôn tập (Review Only)",
            "Từ vựng",
            "Kanji",
            "Ngữ pháp",
            "Kaiwa"
        ]
        self.mode_dropdown = ctk.CTkComboBox(self, values=self.modes, variable=self.mode_var, width=200)
        self.mode_dropdown.pack(pady=(20, 10))

        self.start_btn = ctk.CTkButton(self, text="Bắt đầu học", command=self.load_next_card)
        self.start_btn.pack(pady=10)

        # Card Display Area
        self.card_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.front_label = ctk.CTkLabel(self.card_frame, text="", font=("Arial", 24, "bold"), wraplength=500)
        self.front_label.pack(pady=(0, 20))

        self.back_label = ctk.CTkLabel(self.card_frame, text="", font=("Arial", 16), justify="left", wraplength=500)
        # Initially hidden
        
        self.show_answer_btn = ctk.CTkButton(self.card_frame, text="Hiện đáp án", height=50, command=self.show_answer)
        
        self.grade_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.again_btn = ctk.CTkButton(self.grade_frame, text="Quên", fg_color="#E74C3C", hover_color="#C0392B", command=lambda: self.grade_card("again"))
        self.hard_btn = ctk.CTkButton(self.grade_frame, text="Khó", fg_color="#F39C12", hover_color="#D68910", command=lambda: self.grade_card("hard"))
        self.good_btn = ctk.CTkButton(self.grade_frame, text="Nhớ", fg_color="#2ECC71", hover_color="#27AE60", command=lambda: self.grade_card("good"))
        self.easy_btn = ctk.CTkButton(self.grade_frame, text="Dễ", fg_color="#3498DB", hover_color="#2980B9", command=lambda: self.grade_card("easy"))
        
        self.again_btn.pack(side="left", padx=5, fill="x", expand=True)
        self.hard_btn.pack(side="left", padx=5, fill="x", expand=True)
        self.good_btn.pack(side="left", padx=5, fill="x", expand=True)
        self.easy_btn.pack(side="left", padx=5, fill="x", expand=True)

        self.current_card = None

    def _settings_filters(self):
        settings = learning_items.get_user_settings(LOCAL_USER_ID)
        return {
            "level": settings.get("level"),
            "item_type": settings.get("item_type"),
            "deck_id": settings.get("deck_id"),
            "tags": settings.get("tags"),
        }

    def load_next_card(self):
        mode = self.mode_var.get()
        card = None
        filters = self._settings_filters()
        current_direction = "front_to_back"

        if mode == "Học kết hợp (Mix)":
            card = learning_items.pick_mix_item(LOCAL_USER_ID)
            current_direction = "mix"
        elif mode == "Chỉ thẻ mới (New Only)":
            card = learning_items.pick_new_item(LOCAL_USER_ID, **filters)
        elif mode == "Chỉ thẻ ôn tập (Review Only)":
            card = learning_items.pick_due_item(LOCAL_USER_ID, **filters)
        else:
            lane_map = {"Từ vựng": "vocab", "Kanji": "kanji", "Ngữ pháp": "grammar", "Kaiwa": "kaiwa"}
            lane = lane_map.get(mode, "vocab")
            card = learning_items.pick_next_lane_item(LOCAL_USER_ID, lane)
            current_direction = f"lane:{lane}"

        self.current_card = card
        self.back_label.pack_forget()
        self.grade_frame.pack_forget()

        if card:
            learning_items.set_current_session(LOCAL_USER_ID, card["id"], answer_shown=False, current_direction=current_direction)
            self.front_label.configure(text=card.get("front") or card.get("word") or "-")
            self.show_answer_btn.pack(pady=20, fill="x", padx=100)
        else:
            self.front_label.configure(text="Tuyệt vời! Bạn đã hoàn thành mục tiêu hoặc không có thẻ nào phù hợp.")
            self.show_answer_btn.pack_forget()

    def _format_item_answer(self, item):
        raw = item.get("extra_json")
        extra = {}
        if raw:
            try:
                extra = json.loads(raw)
            except:
                pass

        item_type = item.get("item_type") or "vocab"
        lines = []

        if item_type == "kanji":
            if item.get("hanviet"): lines.append(f"Hán Việt: {item['hanviet']}")
            lines.append(f"Nghĩa: {item.get('meaning') or item.get('back') or '-'}")
            if extra.get("onyomi"): lines.append(f"Onyomi: {extra['onyomi']}")
            if extra.get("kunyomi"): lines.append(f"Kunyomi: {extra['kunyomi']}")
            if extra.get("examples"): lines.append(f"Ví dụ: {extra['examples']}")
            if extra.get("memo"):
                lines.extend(["", "Cách nhớ:"])
                lines.extend(str(extra["memo"]).splitlines())
        elif item_type == "grammar":
            lines.append(f"Nghĩa: {item.get('meaning') or item.get('back') or '-'}")
            if extra.get("usage"): lines.append(f"Cách dùng: {extra['usage']}")
            if item.get("example_jp"): lines.append(f"Ví dụ: {item['example_jp']}")
            if item.get("example_vi"): lines.append(f"Dịch: {item['example_vi']}")
        else:
            reading = item.get("reading") or "-"
            lines.append(f"Cách đọc: {reading}")
            if item.get("hanviet"): lines.append(f"Hán Việt: {item['hanviet']}")
            lines.append(f"Nghĩa: {item.get('meaning') or item.get('back') or '-'}")
            if item.get("example_jp"): lines.append(f"Ví dụ: {item['example_jp']}")
            if item.get("example_vi"): lines.append(f"Dịch: {item['example_vi']}")

        return "\n".join(lines)

    def show_answer(self):
        if not self.current_card:
            return
            
        learning_items.reveal_current_session(LOCAL_USER_ID)
        self.show_answer_btn.pack_forget()
        
        answer_text = self._format_item_answer(self.current_card)
        self.back_label.configure(text=answer_text)
        self.back_label.pack(pady=20)
        
        self.grade_frame.pack(fill="x", pady=20)

    def grade_card(self, grade):
        updated, error = learning_items.grade_current_item(LOCAL_USER_ID, grade)
        if error:
            print(f"Error grading card: {error}")
        self.load_next_card()
