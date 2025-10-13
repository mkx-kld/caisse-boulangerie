# Fichier: ui/components/input_popups.py
# Version finale entièrement traduite

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar

from translations import get_text
from .base_toplevel import DynamicToplevel

class CalculatorPopup(DynamicToplevel):
    def __init__(self, parent, initial_value=""):
        super().__init__(parent, title=get_text("calculator_title"))
        self.entry_var = tk.StringVar(value=str(initial_value))
        
        entry = tk.Entry(self, textvariable=self.entry_var, font=("Cairo", 28, "bold"), relief='solid', bd=1, bg='white', justify="center")
        entry.pack(pady=15, padx=15, ipady=15, fill="x")

        calc_frame = tk.Frame(self, bg="#eaf0f6")
        calc_frame.pack(pady=10, padx=15)
        
        buttons = ['7','8','9','4','5','6','1','2','3','C','0','←']
        btn_style = {'font': ("Cairo", 20, "bold"), 'relief': 'flat', 'bg': "#ffffff", 'width': 5, 'height': 2}
        
        for i, b in enumerate(buttons):
            btn = tk.Button(calc_frame, text=b, **btn_style, command=lambda t=b: self.on_calc_press(t))
            if b == 'C': btn.config(fg='#c0392b')
            if b == '←': btn.config(fg='#3498db')
            btn.grid(row=i//3, column=i%3, padx=4, pady=4)

        ok_button = tk.Button(self, text=get_text("confirm_button_long"), font=("Cairo", 18, "bold"), bg="#27ae60", fg="white", height=2, relief="flat", command=self.on_confirm)
        ok_button.pack(pady=10, padx=15, fill="x", ipady=5)
        
        self.center_window()
        entry.focus_set()

    def on_calc_press(self, touche):
        current = self.entry_var.get()
        if touche == "C": self.entry_var.set("")
        elif touche == "←": self.entry_var.set(current[:-1])
        else: self.entry_var.set(current + touche)

    def on_confirm(self):
        self.on_ok(self.entry_var.get())

class KeyboardPopup(DynamicToplevel):
    """Clavier virtuel multilingue (FR/AR) amélioré."""
    def __init__(self, parent, initial_value=""):
        # MODIFIÉ : Le titre utilise maintenant get_text
        super().__init__(parent, title=get_text("virtual_keyboard_title"))
        self.entry_var = tk.StringVar(value=str(initial_value))
        
        entry = tk.Entry(self, textvariable=self.entry_var, font=("Cairo", 24, "bold"), justify="right", relief="solid", bd=1, bg="white")
        entry.pack(pady=15, padx=15, ipady=10, fill="x")

        self.keyboard_frame = tk.Frame(self, bg="#eaf0f6")
        self.keyboard_frame.pack(pady=5, padx=15)
        
        self.keys_fr = [
            ['a', 'z', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['q', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm'],
            ['w', 'x', 'c', 'v', 'b', 'n']
        ]
        self.keys_ar = [
            ['ض', 'ص', 'ث', 'ق', 'ف', 'غ', 'ع', 'ه', 'خ', 'ح', 'ج', 'د'],
            ['ش', 'س', 'ي', 'ب', 'ل', 'ا', 'أ', 'ت', 'ن', 'م', 'ك', 'ط'],
            ['ئ', 'ء', 'ؤ', 'ر', 'لا', 'ى', 'ة', 'و', 'ز', 'ظ', 'ذ']
        ]
        self.current_layout = 'ar'
        
        self.draw_keyboard()

        btn_frame = tk.Frame(self, bg="#eaf0f6")
        btn_frame.pack(pady=10, padx=15, fill="x", expand=True)
        btn_frame.columnconfigure(2, weight=1)

        action_btn_style = {'font': ("Cairo", 14, "bold"), 'relief': 'flat', 'height': 2, 'bg': '#bdc3c7', 'fg': '#2c3e50'}
        
        tk.Button(btn_frame, text="🌐 AR/FR", **action_btn_style, command=self.toggle_layout).grid(row=0, column=0, padx=2)
        tk.Button(btn_frame, text="←", **action_btn_style, width=4, command=lambda: self.on_key_press('←')).grid(row=0, column=1, padx=2)
        # MODIFIÉ : Le bouton "Espace" utilise get_text
        tk.Button(btn_frame, text=get_text("space_key"), **action_btn_style, command=lambda: self.on_key_press(' ')).grid(row=0, column=2, padx=2, sticky="ew")
        # MODIFIÉ : Le bouton de confirmation utilise get_text
        tk.Button(btn_frame, text=get_text("confirm_button_long"), font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", height=2, relief="flat", command=self.on_confirm).grid(row=0, column=3, padx=2)
        
        self.center_window()

    # ... (Le reste de la classe KeyboardPopup ne change pas)
    def draw_keyboard(self):
        for widget in self.keyboard_frame.winfo_children(): widget.destroy()
        
        keys = self.keys_ar if self.current_layout == 'ar' else self.keys_fr
        btn_style = {'font': ("Cairo", 16, "bold"), 'relief': 'flat', 'bg': "#ffffff", 'width': 4, 'height': 2}
        
        for r, row_keys in enumerate(keys):
            row_frame = tk.Frame(self.keyboard_frame, bg="#eaf0f6")
            row_frame.pack(pady=2)
            for key in row_keys:
                tk.Button(row_frame, text=key, **btn_style, command=lambda t=key: self.on_key_press(t)).pack(side="left", padx=2)

    def toggle_layout(self):
        self.current_layout = 'fr' if self.current_layout == 'ar' else 'ar'
        self.draw_keyboard()

    def on_key_press(self, touche):
        current = self.entry_var.get()
        if touche == "←":
            self.entry_var.set(current[:-1])
        else:
            self.entry_var.set(current + touche)

    def on_confirm(self):
        self.on_ok(self.entry_var.get())


class CalendarPopup(DynamicToplevel):
    def __init__(self, parent, initial_value=None):
        super().__init__(parent, title=get_text("calendar_title"))
        self.cal = calendar.Calendar()
        try: self.date = datetime.strptime(initial_value, "%Y-%m-%d")
        except (ValueError, TypeError): self.date = datetime.now()
        
        self.header_frame = tk.Frame(self, bg="#3498db"); self.header_frame.pack(fill="x")
        btn_header_style = {'font': ("Cairo", 14, "bold"), 'bg': '#3498db', 'fg': 'white', 'relief': 'flat'}
        tk.Button(self.header_frame, text=">", **btn_header_style, command=self.next_month).pack(side="right", padx=10, pady=5)
        self.month_year_label = tk.Label(self.header_frame, font=("Cairo", 16, "bold"), bg="#3498db", fg="white"); self.month_year_label.pack(side="right", expand=True, fill="x")
        tk.Button(self.header_frame, text="<", **btn_header_style, command=self.prev_month).pack(side="right", padx=10, pady=5)
        
        self.days_frame = tk.Frame(self, bg="#eaf0f6"); self.days_frame.pack(pady=10, padx=10)
        
        self.draw_calendar()
        self.center_window()

    def draw_calendar(self):
        for widget in self.days_frame.winfo_children(): widget.destroy()
        
        # Traduction des mois
        month_keys = ["month_jan", "month_feb", "month_mar", "month_apr", "month_may", "month_jun", "month_jul", "month_aug", "month_sep", "month_oct", "month_nov", "month_dec"]
        month_names_ar = [get_text(key) for key in month_keys]
        self.month_year_label.config(text=f"{month_names_ar[self.date.month - 1]} {self.date.year}")
        
        # Traduction des jours
        day_keys = ["day_mon", "day_tue", "day_wed", "day_thu", "day_fri", "day_sat", "day_sun"]
        day_names_ar = [get_text(key) for key in day_keys]
        for i, day in enumerate(day_names_ar): tk.Label(self.days_frame, text=day, font=("Cairo", 12, "bold"), bg="#eaf0f6", fg="#7f8c8d").grid(row=0, column=i, padx=5, pady=5)
        
        month_days = self.cal.monthdayscalendar(self.date.year, self.date.month)
        today = datetime.now()
        for r, week in enumerate(month_days, 1):
            for c, day in enumerate(week):
                if day != 0:
                    is_today = (self.date.year == today.year and self.date.month == today.month and day == today.day)
                    btn_bg = "#2ecc71" if is_today else "white"
                    btn_fg = "white" if is_today else "black"
                    btn = tk.Button(self.days_frame, text=str(day), font=("Cairo", 12), relief="flat", bg=btn_bg, fg=btn_fg, command=lambda d=day: self.select_date(d))
                    btn.grid(row=r, column=c, padx=3, pady=3, ipadx=5, ipady=5, sticky="nsew")

    def prev_month(self): 
        self.date = (self.date.replace(day=1) - timedelta(days=1))
        self.draw_calendar()

    def next_month(self): 
        self.date = (self.date.replace(day=28) + timedelta(days=4)).replace(day=1)
        self.draw_calendar()

    def select_date(self, day): 
        self.on_ok(datetime(self.date.year, self.date.month, day).strftime("%Y-%m-%d"))
