# Fichier: ui/login_frame.py
# Version finale, entièrement traduite via get_text

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from database.db_manager import execute_query
from translations import get_text

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        login_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid", highlightbackground="#d0d0d0", highlightthickness=1)
        login_card.grid(row=0, column=0)

        content = tk.Frame(login_card, bg="#ffffff", padx=50, pady=40)
        content.pack()

        # --- Titre et Logo ---
        title_frame = tk.Frame(content, bg="#ffffff")
        title_frame.pack(pady=(0, 40))
        
        try:
            logo_path = os.path.join("assets", "logo_boulangerie.png")
            if os.path.exists(logo_path):
                self.logo_image = ImageTk.PhotoImage(Image.open(logo_path).resize((80, 80)))
                tk.Label(title_frame, image=self.logo_image, bg="#ffffff").pack(side="right", padx=(0, 15))
            else:
                tk.Label(title_frame, text="🥐", font=("Arial", 40), bg="#ffffff").pack(side="right", padx=(0, 15))
        except Exception:
            tk.Label(title_frame, text="🥐", font=("Arial", 40), bg="#ffffff").pack(side="right", padx=(0, 15))

        tk.Label(title_frame, text=get_text("login_title"), font=("Cairo", 32, "bold"), bg="#ffffff", fg="#2c3e50").pack(side="right")

        # --- Champs de saisie ---
        entry_font = ("Cairo", 16)
        label_font = ("Cairo", 14)
        
        tk.Label(content, text=get_text("username_label"), font=label_font, bg="#ffffff", fg="#2c3e50").pack(anchor="e", pady=(10, 0))
        self.entry_user = tk.Entry(content, font=entry_font, justify="right", width=25, relief="solid", bd=1, bg="#f8f9fa")
        self.entry_user.pack(ipady=8)

        tk.Label(content, text=get_text("password_label"), font=label_font, bg="#ffffff", fg="#2c3e50").pack(anchor="e", pady=(10, 0))
        self.entry_pass = tk.Entry(content, show="●", font=entry_font, justify="right", width=25, relief="solid", bd=1, bg="#f8f9fa")
        self.entry_pass.pack(ipady=8)
        
        self.entry_user.bind("<Return>", lambda event: self.entry_pass.focus_set())
        self.entry_pass.bind("<Return>", self.verifier_connexion)

        # --- Bouton de connexion ---
        self.login_button = tk.Button(content, text=get_text("login_button"), font=("Cairo", 18, "bold"), 
                                       bg="#27ae60", fg="white", 
                                       activebackground="#2ecc71", activeforeground="white",
                                       width=20, relief="flat", command=self.verifier_connexion)
        self.login_button.pack(pady=(40, 20), ipady=8)

    def verifier_connexion(self, event=None):
        utilisateur = self.entry_user.get()
        motdepasse = self.entry_pass.get()

        if not utilisateur or not motdepasse:
            messagebox.showwarning(get_text("empty_field_title"), get_text("fill_all_fields_warning"), parent=self)
            return

        query = "SELECT id, role FROM users WHERE username = ? AND password = ?"
        result = execute_query(query, (utilisateur, motdepasse), fetch='one')

        if result:
            user_id, role = result
            
            self.controller.user_id = user_id
            self.controller.role = role 
            self.controller.nom_utilisateur = utilisateur
            
            self.entry_user.delete(0, tk.END)
            self.entry_pass.delete(0, tk.END)
            
            if role == "admin":
                self.controller.show_frame("AdminFrame", check_notifications=True)
            else:
                self.controller.show_frame("VendeurFrame", check_notifications=True)
        else:
            messagebox.showerror(get_text("login_error_title"), get_text("invalid_credentials_error"), parent=self)