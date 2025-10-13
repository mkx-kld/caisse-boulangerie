# Fichier: ui/admin_panels/activites_panel.py (Version avec logique financière corrigée)

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from database.db_manager import execute_query
from ui.components.input_popups import CalendarPopup
from translations import get_text
from utils import format_currency

class ActivitesPanel(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f2f5")
        self.controller = controller
        self.main_controller = self.controller.controller

        self.start_date_var = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        self.end_date_var = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        self.type_filter_var = tk.StringVar(value=get_text("filter_all"))
        self.search_var = tk.StringVar()
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        tk.Label(self, text=get_text("activity_page_title"), font=("Cairo", 32, "bold"), bg="#f0f2f5", fg="#2c3e50").grid(row=0, column=0, pady=20)
        self.creer_filtres()
        self.creer_rapport_et_totaux()
        
    def creer_filtres(self):
        filter_frame = tk.LabelFrame(self, text=f" {get_text('filters_title')} ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", padx=15, pady=15)
        filter_frame.grid(row=1, column=0, padx=25, pady=10, sticky="ew")
        font_label = ("Cairo", 14); font_entry = ("Cairo", 12)
        tk.Label(filter_frame, text=get_text("filter_from_date"), font=font_label, bg="white").pack(side="right", padx=(10, 5))
        tk.Entry(filter_frame, textvariable=self.start_date_var, font=font_entry, width=12, state="readonly").pack(side="right")
        tk.Button(filter_frame, text="📅", command=lambda: self.open_calendar(self.start_date_var)).pack(side="right", padx=(0, 10))
        tk.Label(filter_frame, text=get_text("filter_to_date"), font=font_label, bg="white").pack(side="right", padx=(10, 5))
        tk.Entry(filter_frame, textvariable=self.end_date_var, font=font_entry, width=12, state="readonly").pack(side="right")
        tk.Button(filter_frame, text="📅", command=lambda: self.open_calendar(self.end_date_var)).pack(side="right", padx=(0, 20))
        tk.Label(filter_frame, text=get_text("filter_type"), font=font_label, bg="white").pack(side="right", padx=(10, 5))
        type_options = [get_text("filter_all"), get_text("filter_income"), get_text("filter_expenses")]
        ttk.Combobox(filter_frame, textvariable=self.type_filter_var, values=type_options, state="readonly", font=font_entry, width=15).pack(side="right", padx=(0, 20))
        tk.Label(filter_frame, text=get_text("filter_search"), font=font_label, bg="white").pack(side="right", padx=(10, 5))
        tk.Entry(filter_frame, textvariable=self.search_var, font=font_entry, width=30).pack(side="right", padx=(0, 20), fill="x", expand=True)
        tk.Button(filter_frame, text=get_text("filter_button"), font=("Cairo", 14, "bold"), bg="#2980b9", fg="white", command=self.charger_donnees).pack(side="left", padx=5)
        tk.Button(filter_frame, text=get_text("reset_button"), font=("Cairo", 14, "bold"), bg="#7f8c8d", fg="white", command=self.reinitialiser_filtres).pack(side="left", padx=5)

    def creer_rapport_et_totaux(self):
        report_frame = tk.LabelFrame(self, text=f" {get_text('activity_report_title')} ", font=("Cairo", 18, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=10, pady=10)
        report_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(5,15))
        report_frame.rowconfigure(0, weight=1); report_frame.columnconfigure(0, weight=1)
        style = ttk.Style(self)
        style.configure("Activity.Treeview", font=("Cairo", 14), rowheight=35)
        style.configure("Activity.Treeview.Heading", font=("Cairo", 16, "bold"))
        style.map('Activity.Treeview', background=[('selected', '#3498db')])
        self.tree_activites = ttk.Treeview(report_frame, columns=("partner", "user", "type", "amount", "date", "description"), show="headings", style="Activity.Treeview")
        self.tree_activites.heading("description", text=get_text("col_description"), anchor="e"); self.tree_activites.column("description", anchor="e", width=400)
        self.tree_activites.heading("date", text=get_text("col_date"), anchor="center"); self.tree_activites.column("date", anchor="center", width=180)
        self.tree_activites.heading("amount", text=get_text("col_amount"), anchor="e"); self.tree_activites.column("amount", anchor="e", width=150)
        self.tree_activites.heading("type", text=get_text("col_type"), anchor="center"); self.tree_activites.column("type", anchor="center", width=200)
        self.tree_activites.heading("user", text=get_text("user_col"), anchor="center"); self.tree_activites.column("user", anchor="center", width=120)
        self.tree_activites.heading("partner", text=get_text("partner_col"), anchor="center"); self.tree_activites.column("partner", anchor="center", width=150)
        self.tree_activites.grid(row=0, column=0, sticky="nsew")
        self.tree_activites.tag_configure('income', foreground='#27ae60')
        self.tree_activites.tag_configure('expense', foreground='#c0392b')
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.tree_activites.yview)
        scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_activites.configure(yscrollcommand=scrollbar.set)
        totals_frame = tk.Frame(self, bg="#2c3e50", pady=10)
        totals_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 20))
        totals_frame.columnconfigure((0, 1, 2), weight=1)
        self.total_income_var = tk.StringVar(); self.total_expense_var = tk.StringVar(); self.net_balance_var = tk.StringVar()
        font_total = ("Cairo", 18, "bold")
        tk.Label(totals_frame, textvariable=self.net_balance_var, font=font_total, bg="#2c3e50", fg="white").grid(row=0, column=2)
        tk.Label(totals_frame, textvariable=self.total_expense_var, font=font_total, bg="#2c3e50", fg="#e74c3c").grid(row=0, column=1)
        tk.Label(totals_frame, textvariable=self.total_income_var, font=font_total, bg="#2c3e50", fg="#2ecc71").grid(row=0, column=0)

    def charger_donnees(self):
        for i in self.tree_activites.get_children(): self.tree_activites.delete(i)
        start_date = self.start_date_var.get(); end_date = self.end_date_var.get()
        type_filter = self.type_filter_var.get(); search_term = self.search_var.get().strip()

        all_activities = []
        total_income, total_expenses = 0, 0

        # --- CORRECTION DE LA LOGIQUE ---
        # On ne sépare plus les requêtes, on traite chaque transaction individuellement.

        # 1. Récupérer TOUTES les transactions (paiements clients, salaires, consommations...)
        trans_where_clauses = ["date(t.date) BETWEEN ? AND ?"]
        trans_params = [start_date, end_date]
        if search_term:
            trans_where_clauses.append("(t.description LIKE ? OR p.nom LIKE ?)")
            trans_params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        query_transactions = f"""
            SELECT t.description, t.montant, t.type_transaction, t.date, u.username, p.nom 
            FROM transactions t 
            LEFT JOIN users u ON t.vendeur_id = u.id
            LEFT JOIN partenaires p ON t.partenaire_id = p.id
            WHERE {' AND '.join(trans_where_clauses)}
        """
        transactions = execute_query(query_transactions, tuple(trans_params), fetch='all') or []
        
        for desc, montant, type_trans, date_str, user, partner in transactions:
            # Si le montant est positif, c'est un REVENU
            if montant > 0:
                if type_filter in [get_text("filter_all"), get_text("filter_income")]:
                    all_activities.append({"date": datetime.fromisoformat(date_str), "description": desc, "amount": montant, "type": type_trans, "user": user or "N/A", "partner": partner or ""})
                total_income += montant
            # Si le montant est négatif, c'est une DÉPENSE
            else:
                if type_filter in [get_text("filter_all"), get_text("filter_expenses")]:
                    all_activities.append({"date": datetime.fromisoformat(date_str), "description": desc, "amount": montant, "type": type_trans, "user": user or "N/A", "partner": partner or ""})
                total_expenses += montant

        # 2. Récupérer les revenus des ventes directes (si le filtre le permet)
        if type_filter in [get_text("filter_all"), get_text("filter_income")]:
            sales_where_clauses = ["date(v.date_vente) BETWEEN ? AND ?"]
            sales_params = [start_date, end_date]
            if search_term:
                sales_where_clauses.append("u.username LIKE ?") # Recherche par nom d'utilisateur pour les ventes
                sales_params.append(f"%{search_term}%")
            
            query_sales = f"""
                SELECT v.id, v.total, v.date_vente, u.username
                FROM ventes v
                LEFT JOIN users u ON v.vendeur_id = u.id
                WHERE {' AND '.join(sales_where_clauses)}
            """
            sales = execute_query(query_sales, tuple(sales_params), fetch='all') or []
            for sale_id, total, date_str, user in sales:
                all_activities.append({"date": datetime.fromisoformat(date_str), "description": f"{get_text('sale_type')} #{sale_id}", "amount": total, "type": get_text('sale_type'), "user": user or "N/A", "partner": ""})
                total_income += total

        all_activities.sort(key=lambda x: x['date'], reverse=True)

        for activity in all_activities:
            tag = 'income' if activity['amount'] > 0 else 'expense'
            formatted_date = activity['date'].strftime('%Y-%m-%d %H:%M')
            self.tree_activites.insert("", "end", values=(activity['partner'], activity['user'], activity['type'], format_currency(activity['amount']), formatted_date, activity['description']), tags=(tag,))

        self.total_income_var.set(f"{get_text('total_income_label')}: {format_currency(total_income)}")
        self.total_expense_var.set(f"{get_text('total_expenses_label')}: {format_currency(total_expenses)}")
        self.net_balance_var.set(f"{get_text('net_balance_label')}: {format_currency(total_income + total_expenses)}")

    def open_calendar(self, date_var):
        new_date = CalendarPopup(self, initial_value=date_var.get()).show()
        if new_date:
            date_var.set(new_date)
            self.charger_donnees()

    def reinitialiser_filtres(self):
        self.start_date_var.set(date.today().strftime('%Y-%m-%d'))
        self.end_date_var.set(date.today().strftime('%Y-%m-%d'))
        self.type_filter_var.set(get_text("filter_all"))
        self.search_var.set("")
        self.charger_donnees()