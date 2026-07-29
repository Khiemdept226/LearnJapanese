import datetime
import os
import sys
import threading
from tkinter import messagebox

import customtkinter as ctk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

import learning_items
from desktop_app import settings_store, study_reminders

try:
    from tools import import_flashcards
except ImportError:
    import traceback

    traceback.print_exc()
    import_flashcards = None

LOCAL_USER_ID = 1

MODE_LABELS = {
    "Workday Balanced": "workday_balanced",
    "JLPT Sprint": "jlpt_sprint",
    "Gentle": "gentle",
    "Custom": "custom",
}
MODE_NAMES = {value: label for label, value in MODE_LABELS.items()}


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self._loading_reminder_fields = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_filter_frame()
        self._build_goal_frame()
        self._build_reminder_frame()
        self._build_sync_frame()

        self.load_settings()

    def _build_filter_frame(self):
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.filter_frame,
            text="Global Filters",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        self.level_var = ctk.StringVar()
        self.type_var = ctk.StringVar()
        self.deck_var = ctk.StringVar()
        self.tags_var = ctk.StringVar()

        self._add_filter_row(self.filter_frame, "Level (VD: N4):", self.level_var)
        self._add_filter_row(self.filter_frame, "Type:", self.type_var)
        self._add_filter_row(self.filter_frame, "Deck ID:", self.deck_var)
        self._add_filter_row(self.filter_frame, "Tags:", self.tags_var)

        ctk.CTkButton(
            self.filter_frame,
            text="Luu bo loc",
            command=self.save_filters,
        ).pack(pady=10)

    def _build_goal_frame(self):
        self.goal_frame = ctk.CTkFrame(self)
        self.goal_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.goal_frame,
            text="Goals",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        self.preset_var = ctk.StringVar()
        presets = ["jlpt_sprint", "light", "steady", "heavy"]
        self.preset_dropdown = ctk.CTkComboBox(
            self.goal_frame,
            values=presets,
            variable=self.preset_var,
        )
        self.preset_dropdown.pack(pady=10)

        ctk.CTkButton(
            self.goal_frame,
            text="Luu muc tieu chung",
            command=self.save_goal,
        ).pack(pady=10)

        self.reset_btn = ctk.CTkButton(
            self.goal_frame,
            text="Reset tien do hoc",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.confirm_reset,
        )
        self.reset_btn.pack(pady=(20, 10))

    def _build_reminder_frame(self):
        self.reminder_frame = ctk.CTkFrame(self)
        self.reminder_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.reminder_frame,
            text="Study Reminders",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        self.reminder_enabled_var = ctk.BooleanVar(value=True)
        self.daily_reminder_enabled_var = ctk.BooleanVar(value=True)
        self.reminder_interval_var = ctk.StringVar(value="2")
        self.reminder_mode_var = ctk.StringVar(value="Workday Balanced")
        self.study_window_start_var = ctk.StringVar(value="09:00")
        self.study_window_end_var = ctk.StringVar(value="18:00")
        self.reminder_interval_minutes_var = ctk.StringVar(value="60")
        self.snooze_minutes_var = ctk.StringVar(value="15")
        self.mini_session_card_limit_var = ctk.StringVar(value="8")
        self.quiet_after_target_done_var = ctk.BooleanVar(value=True)

        for var in (
            self.study_window_start_var,
            self.study_window_end_var,
            self.reminder_interval_minutes_var,
            self.snooze_minutes_var,
            self.mini_session_card_limit_var,
        ):
            var.trace_add("write", self._switch_to_custom_mode)

        ctk.CTkCheckBox(
            self.reminder_frame,
            text="Bat nhac on tap",
            variable=self.reminder_enabled_var,
        ).pack(pady=5, anchor="w", padx=20)

        ctk.CTkCheckBox(
            self.reminder_frame,
            text="Bat nhac bai hoc hang ngay",
            variable=self.daily_reminder_enabled_var,
        ).pack(pady=5, anchor="w", padx=20)

        self._add_reminder_mode_row()
        self._add_legacy_interval_row()
        self._add_reminder_entry("Bat dau:", self.study_window_start_var)
        self._add_reminder_entry("Ket thuc:", self.study_window_end_var)
        self._add_reminder_entry("Moi lan nhac (phut):", self.reminder_interval_minutes_var)
        self._add_reminder_entry("Nhac lai sau (phut):", self.snooze_minutes_var)
        self._add_reminder_entry("So the/phien ngan:", self.mini_session_card_limit_var)

        ctk.CTkCheckBox(
            self.reminder_frame,
            text="Im khi xong muc tieu hom nay",
            variable=self.quiet_after_target_done_var,
        ).pack(pady=5, anchor="w", padx=20)

        action_row = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(
            action_row,
            text="Nhac sau",
            command=self.snooze_now,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            action_row,
            text="Bo qua hom nay",
            command=self.skip_today,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            self.reminder_frame,
            text="Luu cai dat nhac",
            command=self.save_reminders,
        ).pack(pady=15)

    def _build_sync_frame(self):
        self.sync_frame = ctk.CTkFrame(self)
        self.sync_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.sync_frame,
            text="Dong bo du lieu tu Google Sheets",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        self.sync_btn = ctk.CTkButton(
            self.sync_frame,
            text="Bat dau dong bo",
            command=self.start_sync,
        )
        self.sync_btn.pack(pady=10)

        self.sync_status = ctk.CTkLabel(self.sync_frame, text="")
        self.sync_status.pack(pady=5)

    def _add_filter_row(self, parent, label_text, var):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(frame, textvariable=var, width=150).pack(side="right")

    def _add_reminder_entry(self, label_text, var):
        frame = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(frame, textvariable=var, width=100).pack(side="right")

    def _add_reminder_mode_row(self):
        mode_row = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(mode_row, text="Che do nhac:", anchor="w").pack(side="left")
        self.reminder_mode_dropdown = ctk.CTkComboBox(
            mode_row,
            values=list(MODE_LABELS.keys()),
            variable=self.reminder_mode_var,
            command=self.on_reminder_mode_changed,
            width=160,
        )
        self.reminder_mode_dropdown.pack(side="right")

    def _add_legacy_interval_row(self):
        interval_row = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        interval_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(interval_row, text="Nhac cu (gio):", anchor="w").pack(side="left")
        self.reminder_interval_dropdown = ctk.CTkComboBox(
            interval_row,
            values=["1", "2", "3", "4", "6", "12", "24"],
            variable=self.reminder_interval_var,
            width=80,
        )
        self.reminder_interval_dropdown.pack(side="right")

    def _switch_to_custom_mode(self, *_args):
        if self._loading_reminder_fields:
            return
        if self.reminder_mode_var.get() != "Custom":
            self.reminder_mode_var.set("Custom")

    def on_reminder_mode_changed(self, _choice=None):
        mode = MODE_LABELS.get(self.reminder_mode_var.get(), "workday_balanced")
        settings = settings_store.load_settings()
        settings["reminder_mode"] = mode
        settings = settings_store.apply_reminder_preset(settings)
        self._set_reminder_fields(settings)

    def _set_reminder_fields(self, settings):
        self._loading_reminder_fields = True
        try:
            self.reminder_mode_var.set(MODE_NAMES.get(settings.get("reminder_mode"), "Workday Balanced"))
            self.study_window_start_var.set(settings.get("study_window_start", "09:00"))
            self.study_window_end_var.set(settings.get("study_window_end", "18:00"))
            self.reminder_interval_minutes_var.set(str(settings.get("reminder_interval_minutes", 60)))
            self.snooze_minutes_var.set(str(settings.get("snooze_minutes", 15)))
            self.mini_session_card_limit_var.set(str(settings.get("mini_session_card_limit", 8)))
            self.quiet_after_target_done_var.set(bool(settings.get("quiet_after_target_done", True)))
        finally:
            self._loading_reminder_fields = False

    def load_settings(self):
        settings = learning_items.get_user_settings(LOCAL_USER_ID)
        if settings:
            self.level_var.set(settings.get("level") or "")
            self.type_var.set(settings.get("item_type") or "")
            self.deck_var.set(settings.get("deck_id") or "")
            self.tags_var.set(settings.get("tags") or "")
            self.preset_var.set(settings.get("preset") or "steady")

        rem_settings = settings_store.load_settings()
        self.reminder_enabled_var.set(rem_settings.get("reminder_enabled", True))
        self.daily_reminder_enabled_var.set(rem_settings.get("daily_reminder_enabled", True))
        self.reminder_interval_var.set(str(rem_settings.get("reminder_interval_hours", 2)))
        self._set_reminder_fields(rem_settings)

    def save_reminders(self):
        try:
            try:
                hours = int(self.reminder_interval_var.get())
            except ValueError:
                hours = 2

            rem_settings = settings_store.load_settings()
            rem_settings.update(
                {
                    "reminder_enabled": self.reminder_enabled_var.get(),
                    "daily_reminder_enabled": self.daily_reminder_enabled_var.get(),
                    "reminder_interval_hours": hours,
                    "reminder_mode": MODE_LABELS.get(
                        self.reminder_mode_var.get(),
                        "workday_balanced",
                    ),
                    "study_window_start": self.study_window_start_var.get(),
                    "study_window_end": self.study_window_end_var.get(),
                    "reminder_interval_minutes": self.reminder_interval_minutes_var.get(),
                    "snooze_minutes": self.snooze_minutes_var.get(),
                    "mini_session_card_limit": self.mini_session_card_limit_var.get(),
                    "quiet_after_target_done": self.quiet_after_target_done_var.get(),
                }
            )
            settings_store.save_settings(rem_settings)
            self.sync_status.configure(text="Da luu cai dat nhac hoc.")
            messagebox.showinfo("Thanh cong", "Da luu cai dat nhac hoc.")
        except Exception as e:
            messagebox.showerror("Loi", f"Khong the luu cai dat nhac hoc: {e}")

    def snooze_now(self):
        settings = settings_store.load_settings()
        settings["snooze_until"] = study_reminders.snooze_until(
            settings,
            datetime.datetime.now(),
        )
        settings_store.save_settings(settings)
        self.sync_status.configure(text="Da nhac lai sau theo thoi gian snooze.")

    def skip_today(self):
        settings = settings_store.load_settings()
        settings["skip_until"] = study_reminders.skip_until_end_of_day(datetime.datetime.now())
        settings_store.save_settings(settings)
        self.sync_status.configure(text="Da bo qua nhac hoc den het hom nay.")

    def save_filters(self):
        learning_items.set_user_learning_filter(
            LOCAL_USER_ID,
            level=self.level_var.get() or None,
            item_type=self.type_var.get() or None,
            deck_id=self.deck_var.get() or None,
            tags=self.tags_var.get() or None,
        )
        self.sync_status.configure(text="Da luu bo loc.")

    def save_goal(self):
        learning_items.set_user_goal_preset(LOCAL_USER_ID, self.preset_var.get())
        self.sync_status.configure(text="Da luu muc tieu.")

    def start_sync(self):
        self.sync_btn.configure(state="disabled")
        self.sync_status.configure(text="Dang dong bo... Vui long cho.")

        def sync_task():
            try:
                if import_flashcards is None:
                    raise RuntimeError("Khong load duoc tools.import_flashcards")
                stats = import_flashcards.run_learning_import(all_decks=True)
                imported = stats.get("imported", 0)
                msg = f"Dong bo thanh cong. Da tai {imported} the."
            except Exception as e:
                msg = f"Dong bo that bai: {e}"
            finally:
                self.after(0, lambda: self.sync_complete(msg))

        threading.Thread(target=sync_task, daemon=True).start()

    def sync_complete(self, msg):
        self.sync_status.configure(text=msg)
        self.sync_btn.configure(state="normal")

    def confirm_reset(self):
        confirm = messagebox.askyesno(
            "Xac nhan reset",
            "Ban co chac muon reset toan bo tien do hoc flashcards khong?\n"
            "Hanh dong nay khong the hoan tac.",
        )
        if confirm:
            try:
                learning_items.reset_user_learning_progress(LOCAL_USER_ID)
                messagebox.showinfo("Thanh cong", "Da reset tien do hoc.")
            except Exception as e:
                messagebox.showerror("Loi", f"Khong the reset tien do: {e}")
