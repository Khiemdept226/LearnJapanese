import customtkinter as ctk
import db
import sheets

LOCAL_USER_ID = 1

class DailyLessonFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.lesson_title = ctk.CTkLabel(self, text="Đang tải...", font=("Arial", 20, "bold"))
        self.lesson_title.pack(pady=10)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tabview.add("Hội thoại")
        self.tabview.add("Bản dịch")
        self.tabview.add("Từ vựng")
        self.tabview.add("Ngữ pháp")
        self.tabview.add("Quiz")
        self.tabview.add("Shadowing")
        
        # Textboxes for each tab
        self.text_boxes = {}
        for tab_name in self.tabview._name_list:
            tb = ctk.CTkTextbox(self.tabview.tab(tab_name), wrap="word", font=("Arial", 16))
            tb.pack(fill="both", expand=True, padx=10, pady=10)
            self.text_boxes[tab_name] = tb
            
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=20, pady=10)
        
        self.prev_btn = ctk.CTkButton(self.control_frame, text="Bài trước", command=self.prev_lesson)
        self.prev_btn.pack(side="left")
        
        self.next_btn = ctk.CTkButton(self.control_frame, text="Bài tiếp theo", command=self.next_lesson)
        self.next_btn.pack(side="right")
        
        self.current_lesson_order = None
        
        # Initialize
        user = db.get_user(LOCAL_USER_ID)
        if not user:
            initial_order = sheets.get_first_ready_order()
            db.create_or_update_user(LOCAL_USER_ID, LOCAL_USER_ID, "local_user", initial_order)
            self.current_lesson_order = initial_order
        else:
            self.current_lesson_order = user['current_lesson_order']
            
        self.load_lesson()
        
    def load_lesson(self):
        lesson = sheets.get_lesson_by_order(self.current_lesson_order)
        if not lesson:
            self.lesson_title.configure(text="Không tìm thấy bài học.")
            for tb in self.text_boxes.values():
                tb.delete("1.0", "end")
                tb.insert("1.0", "Không có dữ liệu.")
            return
            
        self.lesson_title.configure(text=f"Bài {lesson['lesson_id']} - {lesson['title']}")
        
        # Update tabs
        self._update_tab("Hội thoại", lesson.get('dialogue_jp', ''))
        self._update_tab("Bản dịch", lesson.get('dialogue_vi', ''))
        self._update_tab("Từ vựng", lesson.get('vocab', ''))
        self._update_tab("Ngữ pháp", lesson.get('grammar', ''))
        
        quiz_text = lesson.get('quiz', '')
        quiz_answer = lesson.get('quiz_answer', '')
        if quiz_answer:
            quiz_text += "\n\n--- ĐÁP ÁN ---\n" + quiz_answer
        self._update_tab("Quiz", quiz_text)
        
        self._update_tab("Shadowing", lesson.get('shadowing', ''))
        
    def _update_tab(self, tab_name, content):
        tb = self.text_boxes[tab_name]
        tb.configure(state="normal")
        tb.delete("1.0", "end")
        tb.insert("1.0", content if content else "Không có dữ liệu.")
        tb.configure(state="disabled")
        
    def next_lesson(self):
        next_lesson = sheets.get_next_lesson(self.current_lesson_order)
        if next_lesson:
            self.current_lesson_order = next_lesson['order']
            db.update_user_lesson(LOCAL_USER_ID, self.current_lesson_order)
            self.load_lesson()
            
    def prev_lesson(self):
        # We need a way to go back if we want, but old code only has next_lesson
        # We can just decrement order and try
        prev_order = self.current_lesson_order - 1
        if prev_order > 0:
            prev_lesson = sheets.get_lesson_by_order(prev_order)
            if prev_lesson:
                self.current_lesson_order = prev_order
                db.update_user_lesson(LOCAL_USER_ID, self.current_lesson_order)
                self.load_lesson()
