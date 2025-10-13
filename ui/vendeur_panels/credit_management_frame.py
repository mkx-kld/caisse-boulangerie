# Fichier: ui/vendeur_panels/credit_management_frame.py
# Version 3.1 - Version de secours compatible avec les anciennes versions de tkcalendar

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from database.db_manager import execute_query
from tkcalendar import Calendar # Librairie pour le calendrier

from translations import get_text
from services.partner_service import PartnerService
from utils import format_currency
from ..dialogs.credit_dialogs import CreateOrEditPrivateClientDialog, RecordPaymentDialog, AddSaleToCreditDialog

class CreditManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller
        self.main_controller = controller.main_controller
        self.partner_service = PartnerService()
        self.selected_partner_id = None
        self.selected_partner_type = None

        self.type_reverse_map = {'client_pro': get_text("partner_type_pro_client"), 'client_particulier': get_text("partner_type_private_client")}
        self.btn_config = {'font': ("Cairo", 14, "bold"), 'pady': 8, 'relief': 'raised', 'fg': 'black'}

        self.columnconfigure(0, weight=1); self.columnconfigure(1, weight=2); self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        tk.Label(self, text=get_text("credit_management_title"), font=("Cairo", 24, "bold"), bg="#eaf0f6").grid(row=0, column=0, columnspan=3, pady=20)
        
        self.create_daily_history_panel()
        self.create_client_history_panel()
        self.create_client_list_panel()
        
        self.load_clients()
        self.load_daily_history(date.today().strftime("%Y-%m-%d"))

    def create_daily_history_panel(self):
        left_frame = tk.LabelFrame(self, text=get_text("daily_history_title"), font=("Cairo", 16), bg="white", bd=2, relief="groove", padx=10, pady=10)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(10,5), pady=10)
        left_frame.rowconfigure(1, weight=1); left_frame.columnconfigure(0, weight=1)
        
        self.cal = Calendar(left_frame)
        self.cal.pack(pady=10, fill="x")
        self.cal.bind("<<CalendarSelected>>", self.on_date_select)
        
        self.daily_history_tree = ttk.Treeview(left_frame, columns=("amount", "details", "client"), show="headings")
        self.daily_history_tree.heading("client", text=get_text("col_client_daily")); self.daily_history_tree.column("client", anchor="e")
        self.daily_history_tree.heading("details", text=get_text("col_details_daily")); self.daily_history_tree.column("details", anchor="e")
        self.daily_history_tree.heading("amount", text=get_text("col_amount_daily")); self.daily_history_tree.column("amount", width=100, anchor="e")
        self.daily_history_tree.tag_configure('credit', foreground='red')
        self.daily_history_tree.pack(fill="both", expand=True)

    def create_client_history_panel(self):
        middle_frame = tk.LabelFrame(self, text=get_text("no_client_selected"), font=("Cairo", 16), bg="white", bd=2, relief="groove", padx=10, pady=10)
        middle_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=10)
        middle_frame.rowconfigure(0, weight=1); middle_frame.columnconfigure(0, weight=1)
        self.client_history_frame = middle_frame
        
        self.history_tree = ttk.Treeview(middle_frame, columns=("amount", "desc", "date"), show="headings")
        self.history_tree.heading("date", text=get_text("col_date")); self.history_tree.column("date", width=150, anchor="e")
        self.history_tree.heading("desc", text=get_text("col_description")); self.history_tree.heading("amount", text=get_text("col_amount")); self.history_tree.column("amount", width=120, anchor="e")
        self.history_tree.tag_configure('gain', foreground='green'); self.history_tree.tag_configure('perte', foreground='red')
        self.history_tree.grid(row=0, column=0, sticky="nsew", pady=5)
        
        action_frame = tk.Frame(middle_frame, bg="white")
        action_frame.grid(row=1, column=0, pady=(10,0), sticky="ew")
        self.add_sale_button = tk.Button(action_frame, text="➕ " + get_text("add_delivery_button"), state="disabled", command=self.add_sale_to_client, **self.btn_config, bg="#e67e22")
        self.add_sale_button.pack(side="left", expand=True, fill="x", padx=(0,2))
        self.payment_button = tk.Button(action_frame, text="💰 " + get_text("process_payment_button"), state="disabled", command=self.record_payment, **self.btn_config, bg="#16a085")
        self.payment_button.pack(side="left", expand=True, fill="x", padx=(2,0))

    def create_client_list_panel(self):
        right_frame = tk.LabelFrame(self, text=get_text("credit_clients_list"), font=("Cairo", 16), bg="white", bd=2, relief="groove", padx=10, pady=10)
        right_frame.grid(row=1, column=2, sticky="nsew", padx=(5,10), pady=10)
        right_frame.rowconfigure(0, weight=1); right_frame.columnconfigure(0, weight=1)

        # --- CORRECTION : Ajout de la colonne #0 pour afficher le nom ---
        self.client_tree = ttk.Treeview(right_frame, columns=("type", "balance"), show="headings")
        self.client_tree.heading("#0", text=get_text("partner_list_col_name")); self.client_tree.column("#0", anchor="e")
        self.client_tree.heading("type", text=get_text("partner_list_col_type")); self.client_tree.column("type", width=120, anchor="center")
        self.client_tree.heading("balance", text=get_text("partner_list_col_balance")); self.client_tree.column("balance", width=120, anchor="e")
        self.client_tree.grid(row=0, column=0, sticky="nsew")
        self.client_tree.bind("<<TreeviewSelect>>", self.on_client_select)

        btn_frame = tk.Frame(right_frame, bg="white")
        btn_frame.grid(row=1, column=0, pady=(10,0), sticky="ew")
        tk.Button(btn_frame, text="➕ " + get_text("create_private_client_button"), command=self.create_private_client, **self.btn_config, bg="#27ae60").pack(side="left", expand=True, fill='x', padx=2)
        self.edit_button = tk.Button(btn_frame, text="📝 " + get_text("edit_client_title"), command=self.edit_private_client, state="disabled", **self.btn_config, bg="#3498db")
        self.edit_button.pack(side="left", expand=True, fill='x', padx=2)
        self.delete_button = tk.Button(btn_frame, text="🗑️ " + get_text("delete_button"), command=self.delete_private_client, state="disabled", **self.btn_config, bg="#c0392b")
        self.delete_button.pack(side="left", expand=True, fill='x', padx=2)
        
    def on_date_select(self, event=None):
        selected_date = self.cal.selection_get().strftime("%Y-%m-%d")
        self.load_daily_history(selected_date)
        
    def load_daily_history(self, date_str):
        for i in self.daily_history_tree.get_children(): self.daily_history_tree.delete(i)
        daily_sales = self.partner_service.get_credit_sales_for_day(date_str)
        for client, prod, qte, total in daily_sales:
            details = f"{qte}x {prod}"
            self.daily_history_tree.insert("", "end", values=(format_currency(total), details, client), tags=('credit',))
            
    def load_clients(self):
        self.clear_right_panel()
        for i in self.client_tree.get_children(): self.client_tree.delete(i)
        clients = self.partner_service.get_all_credit_clients()
        for client_id, nom, p_type, solde in clients:
            type_affiche = self.type_reverse_map.get(p_type, p_type)
            tag = 'dette' if solde < 0 else ('creance' if solde > 0 else 'zero')
            self.client_tree.insert("", "end", iid=client_id, text=nom, values=(type_affiche, format_currency(solde)), tags=(tag,))

    def on_client_select(self, event=None):
        selection = self.client_tree.selection()
        if not selection:
            self.clear_right_panel(); return
        
        self.selected_partner_id = selection[0]
        partner_data = execute_query("SELECT nom, type_partenaire FROM partenaires WHERE id=?", (self.selected_partner_id,), fetch='one')
        self.selected_partner_type = partner_data[1] if partner_data else None

        self.client_history_frame.config(text=f" {get_text('client_history_title').format(name=partner_data[0])} ")
        self.add_sale_button.config(state="normal"); self.payment_button.config(state="normal")
        
        if self.selected_partner_type == 'client_particulier':
            self.edit_button.config(state="normal"); self.delete_button.config(state="normal")
        else:
            self.edit_button.config(state="disabled"); self.delete_button.config(state="disabled")
        
        self.load_history()

    def load_history(self):
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        history_items = []
        trans_history = execute_query("SELECT date, description, montant FROM transactions WHERE partenaire_id = ? ORDER BY date DESC", (self.selected_partner_id,), fetch='all') or []
        for date, desc, montant in trans_history:
            history_items.append({'date': datetime.fromisoformat(date), 'desc': desc, 'montant': montant})
        
        delivery_history = execute_query("SELECT l.date_livraison, l.quantite, l.prix_vente_unitaire, p.nom FROM livraisons_clients l JOIN produits p ON l.produit_id=p.id WHERE l.partenaire_id = ?", (self.selected_partner_id,), fetch='all') or []
        for date, qte, prix, prod_name in delivery_history:
            desc = f"Vente: {qte}x {prod_name}"
            montant = qte * prix
            history_items.append({'date': datetime.fromisoformat(date), 'desc': desc, 'montant': montant})
        
        history_items.sort(key=lambda x: x['date'], reverse=True)
        for item in history_items:
            tag = 'gain' if item['montant'] > 0 else 'perte'
            self.history_tree.insert("", "end", values=(format_currency(item['montant']), item['desc'], item['date'].strftime('%Y-%m-%d %H:%M')), tags=(tag,))

    def clear_right_panel(self):
        self.selected_partner_id = None; self.selected_partner_type = None
        self.client_history_frame.config(text=get_text("no_client_selected"))
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        self.add_sale_button.config(state="disabled"); self.payment_button.config(state="disabled")
        self.edit_button.config(state="disabled"); self.delete_button.config(state="disabled")

    def create_private_client(self):
        dialog = CreateOrEditPrivateClientDialog(self)
        if dialog.show(): self.load_clients()

    def edit_private_client(self):
        if not self.selected_partner_id or self.selected_partner_type != 'client_particulier': return
        client_data = execute_query("SELECT nom, telephone FROM partenaires WHERE id=?", (self.selected_partner_id,), fetch='one')
        client_info = {'id': self.selected_partner_id, 'nom': client_data[0], 'tel': client_data[1]}
        dialog = CreateOrEditPrivateClientDialog(self, client_info=client_info)
        if dialog.show(): self.load_clients()

    def delete_private_client(self):
        if not self.selected_partner_id or self.selected_partner_type != 'client_particulier': return
        if messagebox.askyesno(get_text("confirm_delete_title"), get_text("item_delete_confirm"), parent=self):
            success, message = self.partner_service.delete_private_client(self.selected_partner_id)
            if success: messagebox.showinfo(get_text("success"), message, parent=self); self.load_clients()
            else: messagebox.showerror(get_text("error"), message, parent=self)
            
    def add_sale_to_client(self):
        if not self.selected_partner_id: return
        partner_data = execute_query("SELECT nom, solde_credit FROM partenaires WHERE id=?", (self.selected_partner_id,), fetch='one')
        partner_info = {'id': self.selected_partner_id, 'nom': partner_data[0]}
        dialog = AddSaleToCreditDialog(self, self.main_controller, partner_info)
        if dialog.show(): self.load_clients(); self.on_client_select()

    def record_payment(self):
        if not self.selected_partner_id: return
        partner_data = execute_query("SELECT nom, solde_credit FROM partenaires WHERE id=?", (self.selected_partner_id,), fetch='one')
        dialog = RecordPaymentDialog(self, self.main_controller, self.selected_partner_id, partner_data[0], partner_data[1])
        if dialog.show(): self.load_clients(); self.on_client_select()