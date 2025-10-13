# Fichier: ui/dialogs/credit_dialogs.py
# AMÉLIORATIONS : Titres traduits, boutons plus grands, claviers virtuels ajoutés.

import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import execute_query, get_prix_pour_partenaire
from translations import get_text
from services.partner_service import PartnerService
from ..components.base_toplevel import DynamicToplevel
from ..components.input_popups import KeyboardPopup, CalculatorPopup
from utils import format_currency

class CreateOrEditPrivateClientDialog(DynamicToplevel):
    def __init__(self, parent, client_info=None):
        self.client_info = client_info
        # Le titre est maintenant traduit
        title_key = "edit_client_title" if client_info else "create_private_client_button"
        super().__init__(parent, title=get_text(title_key))
        
        self.partner_service = PartnerService()
        # Style pour les boutons plus grands et lisibles
        btn_config = {'font': ("Cairo", 14, "bold"), 'relief': 'flat', 'fg': 'white', 'pady': 10}

        tk.Label(self, text=get_text("partner_name_label"), font=("Cairo", 14), bg="#eaf0f6").pack(pady=(15,0))
        name_frame = tk.Frame(self, bg="#eaf0f6"); name_frame.pack(padx=20, pady=5, fill='x')
        self.nom_var = tk.StringVar(value=client_info['nom'] if client_info else "")
        tk.Entry(name_frame, textvariable=self.nom_var, font=("Cairo", 14), justify="right").pack(side='right', expand=True, fill='x')
        # Ajout du clavier virtuel
        tk.Button(name_frame, text="✏️", font=("Arial", 12), command=lambda: self.open_popup(KeyboardPopup, self.nom_var)).pack(side='right', padx=(0,5))

        tk.Label(self, text=get_text("partner_phone_label"), font=("Cairo", 14), bg="#eaf0f6").pack(pady=(10,0))
        phone_frame = tk.Frame(self, bg="#eaf0f6"); phone_frame.pack(padx=20, pady=5, fill='x')
        self.tel_var = tk.StringVar(value=client_info['tel'] if client_info else "")
        tk.Entry(phone_frame, textvariable=self.tel_var, font=("Cairo", 14), justify="right").pack(side='right', expand=True, fill='x')
        # Ajout du pavé numérique
        tk.Button(phone_frame, text="✏️", font=("Arial", 12), command=lambda: self.open_popup(CalculatorPopup, self.tel_var)).pack(side='right', padx=(0,5))
        
        confirm_text_key = "save_button" if self.client_info else "confirm"
        tk.Button(self, text=get_text(confirm_text_key), command=self.confirm, bg="#27ae60", **btn_config).pack(pady=20, fill="x", padx=20)
        
        self.center_window()

    def open_popup(self, popup_class, target_var):
        new_val = popup_class(self, initial_value=target_var.get()).show()
        if new_val is not None: target_var.set(new_val)

    def confirm(self):
        nom = self.nom_var.get().strip()
        tel = self.tel_var.get().strip()
        if not nom:
            messagebox.showwarning(get_text("warning"), get_text("partner_name_required"), parent=self)
            return
        
        if self.client_info:
            success, message = self.partner_service.update_private_client(self.client_info['id'], nom, tel)
        else:
            success, message = self.partner_service.create_private_client(nom, tel)
        
        if success:
            messagebox.showinfo(get_text("success"), message, parent=self)
            self.on_ok(True)
        else:
            messagebox.showerror(get_text("error"), message, parent=self)


class AddSaleToCreditDialog(DynamicToplevel):
    def __init__(self, parent, controller, partner_info):
        # Titre traduit
        title = get_text("add_credit_sale_title").format(name=partner_info['nom'])
        super().__init__(parent, title=title)
        
        self.controller = controller
        self.partner_info = partner_info
        self.partner_service = PartnerService()
        self.panier = []

        produits_disponibles = execute_query("SELECT id, nom, prix FROM produits WHERE type='vente' ORDER BY nom", fetch='all') or []
        self.produits_map = {p[1]: {'id': p[0], 'prix': p[2] or 0} for p in produits_disponibles}

        main_frame = tk.Frame(self, bg="#eaf0f6", padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1); main_frame.rowconfigure(1, weight=1)

        form_frame = tk.LabelFrame(main_frame, text=get_text("add_product_button_popup"), font=("Cairo", 14), bg="white", padx=10, pady=10)
        form_frame.grid(row=0, column=0, sticky="ew")
        
        tk.Label(form_frame, text=get_text("product_label_popup"), font=("Cairo", 12), bg="white").pack(side="left", padx=5)
        self.combo_produits = ttk.Combobox(form_frame, values=list(self.produits_map.keys()), state="readonly", font=("Cairo", 12), justify="right")
        self.combo_produits.pack(side="left", padx=5, expand=True, fill='x')
        self.combo_produits.bind("<<ComboboxSelected>>", self.on_produit_select)
        
        tk.Label(form_frame, text=get_text("quantity_label_popup"), font=("Cairo", 12), bg="white").pack(side="left", padx=5)
        self.qte_entry = tk.Entry(form_frame, font=("Cairo", 12), width=5, justify="center")
        self.qte_entry.pack(side="left", padx=5)
        
        tk.Label(form_frame, text=get_text("price_label_popup"), font=("Cairo", 12), bg="white").pack(side="left", padx=5)
        self.prix_entry = tk.Entry(form_frame, font=("Cairo", 12), width=8, justify="center")
        self.prix_entry.pack(side="left", padx=5)

        tk.Button(form_frame, text="➕", font=("Cairo", 12, "bold"), bg="#3498db", fg="white", command=self.add_to_cart).pack(side="left", padx=10)

        panier_frame = tk.LabelFrame(main_frame, text=get_text("cart_title_popup"), font=("Cairo", 14), bg="white", padx=10, pady=10)
        panier_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        panier_frame.rowconfigure(0, weight=1); panier_frame.columnconfigure(0, weight=1)
        
        self.panier_tree = ttk.Treeview(panier_frame, columns=("total", "prix", "qte", "nom"), show="headings")
        self.panier_tree.heading("nom", text=get_text("col_product_popup")); self.panier_tree.column("nom", anchor="e")
        self.panier_tree.heading("qte", text=get_text("col_quantity_popup")); self.panier_tree.column("qte", width=60, anchor="center")
        self.panier_tree.heading("prix", text=get_text("col_price_popup")); self.panier_tree.column("prix", width=80, anchor="e")
        self.panier_tree.heading("total", text=get_text("col_total_popup")); self.panier_tree.column("total", width=100, anchor="e")
        self.panier_tree.grid(row=0, column=0, sticky="nsew")

        tk.Button(main_frame, text=get_text("validate_and_add_credit"), font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", pady=10, command=self.validate_sale).grid(row=2, column=0, pady=10, sticky="ew")
        
        self.geometry("600x500")
        self.center_window()

    def on_produit_select(self, event):
        nom_produit = self.combo_produits.get()
        prix_applicable = get_prix_pour_partenaire(self.produits_map[nom_produit]['id'], self.partner_info['id'])
        self.prix_entry.delete(0, tk.END)
        self.prix_entry.insert(0, prix_applicable)
        self.qte_entry.delete(0, tk.END)
        self.qte_entry.insert(0, "1")

    def add_to_cart(self):
        nom = self.combo_produits.get(); qte_str = self.qte_entry.get(); prix_str = self.prix_entry.get()
        if not all([nom, qte_str, prix_str]): return
        qte = int(qte_str); prix = float(prix_str)
        produit_id = self.produits_map[nom]['id']
        total_ligne = qte * prix
        self.panier.append({'id': produit_id, 'nom': nom, 'qte': qte, 'prix': prix, 'total': total_ligne})
        self.panier_tree.insert("", "end", values=(format_currency(total_ligne), format_currency(prix), qte, nom))
        self.combo_produits.set(''); self.qte_entry.delete(0, tk.END); self.prix_entry.delete(0, tk.END)

    def validate_sale(self):
        if not self.panier:
            messagebox.showwarning(get_text("warning"), get_text("cart_empty_warning"), parent=self)
            return
        
        success, message = self.partner_service.add_credit_sale(self.partner_info['id'], self.panier, self.controller.user_id)
        if success:
            messagebox.showinfo(get_text("success"), message, parent=self)
            self.on_ok(True)
        else:
            messagebox.showerror(get_text("error"), message, parent=self)
            

class RecordPaymentDialog(DynamicToplevel):
    def __init__(self, parent, controller, partenaire_id, partenaire_nom, solde_actuel):
        super().__init__(parent, title=get_text("register_payment_button"))
        self.controller = controller
        self.partner_service = PartnerService()
        self.partenaire_id = partenaire_id

        main_frame = tk.Frame(self, bg="#eaf0f6", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(main_frame, text=f"{get_text('register_payment_for').format(nom=partenaire_nom)}", font=("Cairo", 20, "bold"), bg="#eaf0f6").pack(pady=10)
        tk.Label(main_frame, text=f"{get_text('current_balance')}: {format_currency(solde_actuel)}", font=("Cairo", 14), bg="#eaf0f6").pack(pady=5)
        
        tk.Label(main_frame, text=get_text("amount_paid"), font=("Cairo", 14), bg="#eaf0f6").pack(pady=(10,0))
        self.montant_var = tk.StringVar()
        montant_entry = tk.Entry(main_frame, textvariable=self.montant_var, font=("Cairo", 14), justify="center", width=20, relief="solid", bd=1)
        montant_entry.pack(pady=5)
        
        tk.Button(main_frame, text=get_text("confirm_payment_button"), font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", command=self.validate_payment).pack(pady=20, fill="x", ipady=5)
        
        self.center_window()
        montant_entry.focus_set()

    def validate_payment(self):
        user_id = self.controller.user_id
        montant_str = self.montant_var.get()
        if not montant_str:
            messagebox.showerror(get_text("error"), get_text("invalid_amount_warning"), parent=self)
            return

        try:
            montant = float(montant_str)
            if montant <= 0: raise ValueError
        except (ValueError, TypeError): 
            messagebox.showerror(get_text("error"), get_text("invalid_amount_warning"), parent=self)
            return
        
        success, message = self.partner_service.record_payment(self.partenaire_id, montant, user_id)

        if success:
            messagebox.showinfo(get_text("success"), message, parent=self)
            self.on_ok(True) # Succès
        else:
            messagebox.showerror(get_text("error"), message, parent=self)