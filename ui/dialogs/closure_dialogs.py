# Fichier: ui/dialogs/closure_dialogs.py
# Contient les fenêtres de dialogue pour la clôture de service et de journée.

import tkinter as tk
from tkinter import ttk, messagebox
from translations import get_text
from ..components.base_toplevel import DynamicToplevel
from utils import format_currency
from database.db_manager import execute_query

class DemandeClotureWindow(DynamicToplevel):
    """Fenêtre pour choisir le type de clôture (service ou journée)."""
    def __init__(self, parent):
        super().__init__(parent, title=get_text("closure_type_title"))
        tk.Label(self, text=get_text("closure_type_prompt"), font=("Cairo", 18, "bold"), bg="#eaf0f6").pack(pady=30, padx=20)
        btn_frame = tk.Frame(self, bg="#eaf0f6")
        btn_frame.pack(pady=20, fill="x", expand=True)
        btn_config = {'font': ("Cairo", 16, "bold"), 'fg': 'white', 'pady': 15, 'relief':'flat'}
        tk.Button(btn_frame, text=get_text("end_of_service_button"), bg="#3498db", **btn_config, command=lambda: self.on_ok('service')).pack(pady=10, fill="x", padx=50)
        tk.Button(btn_frame, text=get_text("end_of_day_button"), bg="#c0392b", **btn_config, command=lambda: self.on_ok('journee')).pack(pady=10, fill="x", padx=50)
        self.center_window()

class InvendusWindow(DynamicToplevel):
    """Fenêtre pour déclarer les produits invendus en fin de journée."""
    def __init__(self, parent):
        super().__init__(parent, title=get_text("unsold_products_title"))
        self.entries = {}
        tk.Label(self, text=get_text("unsold_products_prompt"), font=("Cairo", 20, "bold"), bg="#eaf0f6").pack(pady=20, padx=40)
        canvas_frame = tk.Frame(self, bg="#eaf0f6"); canvas_frame.pack(pady=10, padx=20, fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0); scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview); scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        query = "SELECT id, nom, prix_achat, stock FROM produits WHERE mode_gestion = 'quotidien' ORDER BY nom"
        produits_invendus = execute_query(query, fetch='all') or []
        if not produits_invendus: 
            tk.Label(scrollable_frame, text=get_text("no_daily_products"), font=("Cairo", 16), bg="white").pack(pady=50)
        else:
            for prod_id, nom, prix_achat, stock in produits_invendus:
                row_frame = tk.Frame(scrollable_frame, bg="white"); row_frame.pack(fill="x", pady=5, padx=10)
                tk.Label(row_frame, text=nom, font=("Cairo", 16), bg="white").pack(side="right", padx=10)
                entry = tk.Entry(row_frame, font=("Cairo", 16), width=10, justify="center"); entry.insert(0, str(int(stock or 0))); entry.pack(side="left", padx=10)
                self.entries[prod_id] = {'entry': entry, 'prix_achat': prix_achat, 'nom': nom}
        
        btn_frame = tk.Frame(self, bg="#eaf0f6"); btn_frame.pack(pady=20, padx=40, fill="x")
        tk.Button(btn_frame, text=get_text("confirm_and_record_losses"), font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", relief="flat", command=self.valider, height=2).pack(fill="x")
        self.center_window()

    def valider(self):
        resultat = []
        try:
            for prod_id, data in self.entries.items():
                qte_restante = int(data['entry'].get())
                if qte_restante > 0:
                    resultat.append({'id': prod_id, 'nom': data['nom'], 'qte': qte_restante, 'cout_perte': qte_restante * (data['prix_achat'] or 0)})
            self.on_ok(resultat)
        except ValueError: 
            messagebox.showerror(get_text("error"), get_text("invalid_quantity_warning"), parent=self)

class RapportClotureWindow(DynamicToplevel):
    """Fenêtre affichant le rapport de clôture."""
    def __init__(self, parent, data):
        super().__init__(parent, title=data['titre_rapport'])
        self.geometry("600x650")
        self.configure(bg="#ffffff")
        header_font = ("Cairo", 26, "bold"); label_font = ("Cairo", 20); value_font = ("Cairo", 20, "bold"); total_font = ("Cairo", 24, "bold")
        tk.Label(self, text=data['titre_rapport'], font=header_font, bg="white", fg="#2c3e50").pack(pady=25)
        container = tk.Frame(self, bg="white")
        container.pack(pady=15, padx=40, fill="both", expand=True)
        container.columnconfigure(0, weight=1); container.columnconfigure(1, weight=1)
        
        info = []
        if data['nom_vendeur']: 
            info.append((get_text("final_report_seller_name"), data['nom_vendeur']))
        
        info.extend([
            (get_text("final_report_date"), data['date']), 
            (get_text("final_report_closing_time"), data['heure']), 
            (get_text("final_report_initial_cash"), format_currency(data['fonds_de_caisse'])), 
            (get_text("final_report_total_sales"), f"+ {format_currency(data['total_ventes'])}"), 
            (get_text("final_report_total_expenses"), format_currency(data['total_depenses']))
        ])
        
        for i, (label_text, value_text) in enumerate(info):
            tk.Label(container, text=label_text, font=label_font, bg="white", fg="#34495e").grid(row=i, column=1, sticky="e", pady=8, padx=10)
            tk.Label(container, text=value_text, font=value_font, bg="white", fg="#2c3e50").grid(row=i, column=0, sticky="e", pady=8, padx=10)
        
        ttk.Separator(container, orient='horizontal').grid(row=len(info), column=0, columnspan=2, sticky='ew', pady=20)
        
        tk.Label(container, text=get_text("final_report_final_balance"), font=total_font, bg="white", fg="#16a085").grid(row=len(info)+1, column=1, sticky="e", pady=10)
        tk.Label(container, text=format_currency(data['solde_final']), font=total_font, bg="white", fg="#16a085").grid(row=len(info)+1, column=0, sticky="e", pady=10, padx=10)
        
        tk.Button(self, text=get_text("close_button_generic"), font=("Cairo", 18, "bold"), bg="#3498db", fg="white", relief="flat", command=self.destroy).pack(pady=25, ipadx=30)
        self.center_window()