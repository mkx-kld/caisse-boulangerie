# Fichier: ui/components/base_toplevel.py
# CORRECTION : La méthode center_window est maintenant plus robuste.

import tkinter as tk

class DynamicToplevel(tk.Toplevel):
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.configure(bg="#eaf0f6")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.result = None

    def center_window(self):
        """Centre la fenêtre au milieu de l'écran."""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # Obtenir les dimensions de l'écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculer la position x et y pour centrer la fenêtre
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.geometry(f'{width}x{height}+{x}+{y}')

    def on_ok(self, value):
        self.result = value
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

    def show(self):
        self.wait_window(self)
        return self.result