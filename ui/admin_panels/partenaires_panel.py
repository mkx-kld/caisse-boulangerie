# Fichier: ui/admin_panels/partenaires_panel.py
# Version avec imports mis à jour

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from translations import get_text
from database.db_manager import execute_query
from utils import format_currency
from ..components.input_popups import CalculatorPopup, KeyboardPopup

# --- MODIFICATION ---
# Les imports pointent maintenant vers le nouveau fichier de dialogs
from ..dialogs.credit_dialogs import RecordPaymentDialog 
# Note: VenteCreditWindow et GererTarifsPartenaireWindow seront déplacés plus tard

class PartenairesPanel(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f2f5")
        self.controller = controller
        self.main_controller = controller.controller if hasattr(controller, 'controller') else controller
        
        self.selected_partenaire_id = None
        self.selected_partenaire_data = None

        self.type_map = {get_text("partner_type_supplier"): "fournisseur", get_text("partner_type_pro_client"): "client_pro"}
        self.type_reverse_map = {v: k for k, v in self.type_map.items()}
        self.paiement_map = {get_text("payment_mode_daily"): "journalier", get_text("payment_mode_monthly"): "mensuel"}
        self.paiement_reverse_map = {v: k for k, v in self.paiement_map.items()}

        self.columnconfigure(0, weight=3); self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        self.creer_panneau_gauche_details()
        self.creer_panneau_droit_liste()
        
        self.charger_partenaires()
        self.disable_details_panel()

    def creer_panneau_gauche_details(self):
        details_frame_text = f" {get_text('partner_details_and_history_title')} "
        details_frame = tk.LabelFrame(self, text=details_frame_text, font=("Cairo", 18, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=10, pady=10)
        details_frame.grid(row=0, column=0, padx=(25,10), pady=20, sticky="nsew")
        details_frame.rowconfigure(2, weight=1); details_frame.columnconfigure(0, weight=1)

        actions_container = tk.Frame(details_frame, bg="white")
        actions_container.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        balance_container = tk.Frame(actions_container, bg="#2c3e50")
        balance_container.pack(fill="x", pady=(0,10))
        
        label_font = ("Cairo", 18, "bold")
        self.balance_status_label = tk.Label(balance_container, text="", font=label_font, bg="#2c3e50", padx=10, pady=10)
        self.balance_amount_label = tk.Label(balance_container, text="", font=label_font, bg="#2c3e50", padx=10, pady=10)
        self.balance_text_label = tk.Label(balance_container, text="", font=label_font, fg="white", bg="#2c3e50", padx=10, pady=10)
        
        self.balance_status_label.pack(side="left", fill="y", padx=5)
        self.balance_amount_label.pack(side="left", fill="y", padx=5)
        self.balance_text_label.pack(side="right", fill="y", padx=5)
        
        self.actions_frame = tk.Frame(actions_container, bg="white")
        self.actions_frame.pack(fill="x")
        btn_config = {'font': ("Cairo", 12, "bold"), 'fg': 'white', 'relief': 'raised', 'bd': 2, 'pady': 5, 'width': 20}
        
        self.btn_gerer_prix = tk.Button(self.actions_frame, text=get_text("manage_prices_button"), bg="#8e44ad", **btn_config, command=self.open_price_manager)
        self.btn_operation = tk.Button(self.actions_frame, bg="#3498db", **btn_config, command=self.open_credit_sale)
        self.btn_paiement = tk.Button(self.actions_frame, text=get_text("register_payment_button"), bg="#27ae60", **btn_config, command=self.open_payment_window)
        
        self.btn_paiement.pack(side="right", expand=True, fill="x", padx=2)
        self.btn_operation.pack(side="right", expand=True, fill="x", padx=2)
        self.btn_gerer_prix.pack(side="right", expand=True, fill="x", padx=2)

        hist_frame = tk.Frame(details_frame, bg="white")
        hist_frame.grid(row=2, column=0, sticky="nsew")
        hist_frame.rowconfigure(0, weight=1); hist_frame.columnconfigure(0, weight=1)
        
        style = ttk.Style(self)
        style.configure("Details.Treeview", font=("Cairo", 14), rowheight=35)
        style.configure("Details.Treeview.Heading", font=("Cairo", 16, "bold"))
        
        self.history_tree = ttk.Treeview(hist_frame, columns=("desc", "amount", "type", "date"), show="headings", style="Details.Treeview")
        self.history_tree.heading("date", text=get_text("col_date"), anchor="e"); self.history_tree.column("date", anchor="e", width=180)
        self.history_tree.heading("type", text=get_text("col_type"), anchor="center"); self.history_tree.column("type", anchor="center", width=120)
        self.history_tree.heading("amount", text=get_text("col_amount"), anchor="e"); self.history_tree.column("amount", anchor="e", width=150)
        self.history_tree.heading("desc", text=get_text("col_description"), anchor="e"); self.history_tree.column("desc", anchor="e")
        self.history_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar = ttk.Scrollbar(hist_frame, orient="vertical", command=self.history_tree.yview); scrollbar.grid(row=0, column=1, sticky="ns", pady=5)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.tag_configure('dette', foreground='red', font=("Cairo", 14, "bold"))
        self.history_tree.tag_configure('creance', foreground='green', font=("Cairo", 14, "bold"))

    def creer_panneau_droit_liste(self):
        right_frame = tk.LabelFrame(self, text=" Gestion des Partenaires ", font=("Cairo", 18, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=10, pady=10)
        right_frame.grid(row=0, column=1, padx=(10,25), pady=20, sticky="nsew")
        right_frame.rowconfigure(1, weight=1); right_frame.columnconfigure(0, weight=1)
        self.creer_formulaire(right_frame)
        liste_container = tk.Frame(right_frame, bg="white")
        liste_container.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        liste_container.rowconfigure(0, weight=1); liste_container.columnconfigure(0, weight=1)
        style = ttk.Style(self)
        style.configure("Partenaires.Treeview", font=("Cairo", 14), rowheight=40)
        style.configure("Partenaires.Treeview.Heading", font=("Cairo", 16, "bold"))
        style.map('Partenaires.Treeview', foreground=[('selected', 'white')], background=[('selected', '#3498db')])
        self.partners_tree = ttk.Treeview(liste_container, columns=("solde", "type", "nom"), show="headings", style="Partenaires.Treeview")
        self.partners_tree.heading("nom", text=get_text("partner_list_col_name"), anchor="e"); self.partners_tree.column("nom", anchor="e")
        self.partners_tree.heading("type", text=get_text("partner_list_col_type"), anchor="center"); self.partners_tree.column("type", anchor="center", width=150)
        self.partners_tree.heading("solde", text=get_text("partner_list_col_balance"), anchor="center"); self.partners_tree.column("solde", anchor="center", width=150)
        self.partners_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(liste_container, orient="vertical", command=self.partners_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.partners_tree.configure(yscrollcommand=scrollbar.set)
        self.partners_tree.tag_configure('dette', foreground='red'); self.partners_tree.tag_configure('creance', foreground='green')
        self.partners_tree.bind("<<TreeviewSelect>>", self.on_partner_select)

    def creer_formulaire(self, parent):
        form_container = tk.Frame(parent, bg="white")
        form_container.grid(row=0, column=0, sticky="ew")
        fields_frame = tk.Frame(form_container, bg="white"); fields_frame.pack(pady=5)
        self.nom_var = self.creer_champ_saisie(fields_frame, 0, get_text("partner_name_label"), 'keyboard')
        self.tel_var = self.creer_champ_saisie(fields_frame, 1, get_text("partner_phone_label"), 'calculator')
        tk.Label(fields_frame, text=get_text("partner_type_label"), font=("Cairo", 14), bg="white").grid(row=2, column=1, padx=5, pady=8, sticky="w")
        self.type_var = tk.StringVar(value=list(self.type_map.keys())[0])
        ttk.Combobox(fields_frame, textvariable=self.type_var, values=list(self.type_map.keys()), state="readonly", font=("Cairo", 12)).grid(row=2, column=0)
        tk.Label(fields_frame, text=get_text("partner_payment_mode_label"), font=("Cairo", 14), bg="white").grid(row=3, column=1, padx=5, pady=8, sticky="w")
        self.paiement_var = tk.StringVar(value=list(self.paiement_map.keys())[0])
        ttk.Combobox(fields_frame, textvariable=self.paiement_var, values=list(self.paiement_map.keys()), state="readonly", font=("Cairo", 12)).grid(row=3, column=0)
        btn_actions_frame = tk.Frame(form_container, bg="white")
        btn_actions_frame.pack(pady=10, fill="x")
        btn_config = {'font':("Cairo", 14, "bold"), 'fg':'white', 'pady':8, 'relief':'flat'}
        tk.Button(btn_actions_frame, text=get_text("add_button"), bg="#27ae60", **btn_config, command=self.ajouter_partenaire).pack(side="right", expand=True, fill="x", padx=2)
        tk.Button(btn_actions_frame, text=get_text("save_button"), bg="#3498db", **btn_config, command=self.modifier_partenaire).pack(side="right", expand=True, fill="x", padx=2)
        tk.Button(btn_actions_frame, text=get_text("delete_button"), bg="#c0392b", **btn_config, command=self.supprimer_partenaire).pack(side="right", expand=True, fill="x", padx=2)
        tk.Button(btn_actions_frame, text=get_text("clear_button"), bg="#95a5a6", **btn_config, command=self.vider_champs).pack(side="right", expand=True, fill="x", padx=2)

    def on_partner_select(self, event=None):
        selection = self.partners_tree.selection()
        if not selection:
            self.disable_details_panel(); return
        
        self.selected_partenaire_id = selection[0]
        partenaire_form_data = execute_query("SELECT nom, telephone, type_partenaire, mode_paiement FROM partenaires WHERE id=?", (self.selected_partenaire_id,), fetch='one')
        if not partenaire_form_data: return
        
        nom, tel, p_type, mode_p = partenaire_form_data
        self.nom_var.set(nom); self.tel_var.set(tel or "")
        self.type_var.set(self.type_reverse_map.get(p_type, "")); self.paiement_var.set(self.paiement_reverse_map.get(mode_p, ""))
        self.selected_partenaire_data = execute_query("SELECT id, nom, telephone, type_partenaire, mode_paiement, solde_credit FROM partenaires WHERE id=?", (self.selected_partenaire_id,), fetch='one')
        self.enable_details_panel()
        self.load_full_history()

    def load_full_history(self):
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        if not self.selected_partenaire_data: return
        
        history = []; partner_id = self.selected_partenaire_data[0]; partner_type = self.selected_partenaire_data[3]
        
        payments = execute_query("SELECT date, montant, description FROM transactions WHERE partenaire_id = ?", (partner_id,), fetch='all') or []
        for date, amount, desc in payments:
            # On inverse le montant ici car dans la DB les paiements fournisseurs sont negatifs et client positifs
            history.append({'date': datetime.fromisoformat(date), 'type': desc.split(':')[0], 'amount': amount, 'desc': desc})

        if partner_type == 'client_pro':
            sales_query = "SELECT date_livraison, montant_total, produits.nom, quantite FROM livraisons_clients JOIN produits ON livraisons_clients.produit_id = produits.id WHERE partenaire_id = ?"
            sales = execute_query(sales_query, (partner_id,), fetch='all') or []
            for date, total, nom_prod, qte in sales:
                history.append({'date': datetime.fromisoformat(date), 'type': get_text('trans_type_sale'), 'amount': total, 'desc': f"{qte}x {nom_prod}"})
        
        if partner_type == 'fournisseur':
            purchases_query = "SELECT se.date_ajout, se.cout_total, se.quantite_ajoutee, p.nom FROM stock_entries se JOIN produits p ON se.produit_id = p.id WHERE se.partenaire_id = ?"
            purchases = execute_query(purchases_query, (partner_id,), fetch='all') or []
            for date, total, qte, nom_prod in purchases:
                history.append({'date': datetime.fromisoformat(date), 'type': get_text('trans_type_purchase'), 'amount': -total, 'desc': f"{qte}x {nom_prod}"})

        history.sort(key=lambda x: x['date'], reverse=True)
        final_balance = self.selected_partenaire_data[5]
        
        balance_text_status = ""; balance_color = "white"
        if final_balance > 0: balance_text_status = f"({get_text('partner_owes_us')})"; balance_color = "#2ECC71"
        elif final_balance < 0: balance_text_status = f"({get_text('we_owe_partner')})"; balance_color = "#E74C3C"
        else: balance_text_status = f"({get_text('balance_zero')})"
        
        self.balance_text_label.config(text=get_text("final_balance_label"), fg="white")
        self.balance_amount_label.config(text=format_currency(final_balance), fg=balance_color)
        self.balance_status_label.config(text=balance_text_status, fg=balance_color)

        for item in history:
            formatted_date = item['date'].strftime('%Y-%m-%d %H:%M')
            formatted_amount = format_currency(item['amount'])
            tag = 'dette' if item['amount'] < 0 else 'creance'
            display_amount = f"+{formatted_amount}" if item['amount'] > 0 else formatted_amount
            self.history_tree.insert("", "end", values=(item['desc'], display_amount, item['type'], formatted_date), tags=(tag,))

    def disable_details_panel(self):
        for child in self.actions_frame.winfo_children(): child.config(state="disabled")
        self.balance_text_label.config(text=get_text("select_partner_prompt"))
        self.balance_amount_label.config(text=""); self.balance_status_label.config(text="")
        for i in self.history_tree.get_children(): self.history_tree.delete(i)

    def enable_details_panel(self):
        for child in self.actions_frame.winfo_children(): child.config(state="normal")
        self.balance_text_label.config(text=get_text("final_balance_label"))
        sale_purchase_text = get_text("credit_sale_button_client") if self.selected_partenaire_data[3] == 'client_pro' else get_text("credit_sale_button_supplier")
        self.btn_operation.config(text=sale_purchase_text)

    def open_price_manager(self):
        # Cette fonction devra être mise à jour pour importer GererTarifsPartenaireWindow depuis son nouvel emplacement.
        pass

    def open_credit_sale(self):
        # Cette fonction devra être mise à jour pour importer VenteCreditWindow depuis son nouvel emplacement.
        pass
    
    def open_payment_window(self):
        if not self.selected_partenaire_data: return
        partenaire_info = {
            'id': self.selected_partenaire_data[0], 
            'nom': self.selected_partenaire_data[1], 
            'solde_credit': self.selected_partenaire_data[5]
        }
        dialog = RecordPaymentDialog(self, self.main_controller, 
                                     partenaire_id=partenaire_info['id'], 
                                     partenaire_nom=partenaire_info['nom'], 
                                     solde_actuel=partenaire_info['solde_credit'])
        if dialog.show():
            self.charger_partenaires()
            self.on_partner_select()


    def charger_partenaires(self):
        selection = self.partners_tree.selection()
        for row in self.partners_tree.get_children(): self.partners_tree.delete(row)
        partenaires = execute_query("SELECT id, nom, type_partenaire, solde_credit FROM partenaires ORDER BY nom", fetch='all') or []
        for p_id, nom, p_type, solde in partenaires:
            type_ar = self.type_reverse_map.get(p_type, p_type)
            # Solde positif = le client nous doit de l'argent (créance pour nous)
            # Solde négatif = nous devons de l'argent au fournisseur (dette pour nous)
            tag = 'creance' if solde > 0 else ('dette' if solde < 0 else '')
            formatted_solde = format_currency(solde)
            self.partners_tree.insert("", "end", iid=p_id, values=(formatted_solde, type_ar, nom), tags=(tag,))
        if selection:
            try: self.partners_tree.selection_set(selection)
            except tk.TclError: pass

    def vider_champs(self):
        if self.partners_tree.selection(): self.partners_tree.selection_remove(self.partners_tree.selection())
        self.selected_partenaire_id = None; self.selected_partenaire_data = None
        self.nom_var.set(""); self.tel_var.set("")
        self.type_var.set(list(self.type_map.keys())[0]); self.paiement_var.set(list(self.paiement_map.keys())[0])
        self.disable_details_panel()

    def creer_champ_saisie(self, parent, row, label_text, popup_type):
        tk.Label(parent, text=label_text, font=("Cairo", 14), bg="white").grid(row=row, column=1, padx=5, pady=8, sticky="w")
        var = tk.StringVar()
        entry = tk.Entry(parent, textvariable=var, font=("Cairo", 14), justify="right", width=20, relief="solid", bd=1)
        entry.grid(row=row, column=0, padx=5, pady=8)
        btn_cmd = lambda v=var: self.open_popup(KeyboardPopup if popup_type == 'keyboard' else CalculatorPopup, v)
        tk.Button(parent, text="✏️", font=("Cairo", 14), command=btn_cmd).grid(row=row, column=2, padx=(5,0))
        return var

    def open_popup(self, popup_class, target_var):
        new_value = popup_class(self, initial_value=target_var.get()).show()
        if new_value is not None: target_var.set(new_value)

    def ajouter_partenaire(self):
        nom = self.nom_var.get(); tel = self.tel_var.get(); type_text = self.type_var.get(); mode_text = self.paiement_var.get()
        if not nom or not type_text: messagebox.showerror(get_text("error"), get_text("partner_name_type_required"), parent=self); return
        if execute_query("SELECT id FROM partenaires WHERE nom = ?", (nom,), fetch='one'): messagebox.showerror(get_text("error"), get_text("partner_name_exists"), parent=self); return
        query = "INSERT INTO partenaires (nom, telephone, type_partenaire, mode_paiement) VALUES (?, ?, ?, ?)"
        execute_query(query, (nom, tel, self.type_map[type_text], self.paiement_map[mode_text]))
        messagebox.showinfo(get_text("success"), get_text("partner_added_success"), parent=self)
        self.charger_partenaires(); self.vider_champs()

    def modifier_partenaire(self):
        if not self.selected_partenaire_id: messagebox.showwarning(get_text("warning"), get_text("select_partner_warning"), parent=self); return
        nom = self.nom_var.get(); tel = self.tel_var.get(); type_text = self.type_var.get(); mode_text = self.paiement_var.get()
        if not nom or not type_text: messagebox.showerror(get_text("error"), get_text("partner_name_type_required"), parent=self); return
        if execute_query("SELECT id FROM partenaires WHERE nom = ? AND id != ?", (nom, self.selected_partenaire_id), fetch='one'): messagebox.showerror(get_text("error"), get_text("other_partner_name_exists"), parent=self); return
        query = "UPDATE partenaires SET nom=?, telephone=?, type_partenaire=?, mode_paiement=? WHERE id=?"
        execute_query(query, (nom, tel, self.type_map[type_text], self.paiement_map[mode_text], self.selected_partenaire_id))
        messagebox.showinfo(get_text("success"), get_text("partner_edited_success"), parent=self)
        self.charger_partenaires(); self.vider_champs()
        
    def supprimer_partenaire(self):
        if not self.selected_partenaire_id: messagebox.showwarning(get_text("warning"), get_text("select_partner_warning"), parent=self); return
        if not messagebox.askyesno(get_text("confirm_delete_title"), get_text("delete_partner_confirm"), parent=self): return
        execute_query("DELETE FROM partenaires WHERE id=?", (self.selected_partenaire_id,))
        messagebox.showinfo(get_text("success"), get_text("partner_deleted_success"), parent=self)
        self.charger_partenaires(); self.vider_champs()