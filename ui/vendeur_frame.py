# Fichier: ui/vendeur_frame.py
# Rôle: "Chef d'orchestre" qui assemble et coordonne les différents panneaux de la page de vente.

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from database.db_manager import execute_query
from translations import get_text
from config import FONDS_DE_CAISSE

# --- NOUVELLE STRUCTURE D'IMPORTS ---
# Panneaux de la page de vente directe
from .sales_page.product_panel import ProductPanel
from .sales_page.cart_panel import CartPanel
from .sales_page.calculator_panel import CalculatorPanel
from services.sales_service import SalesService

# Nouveaux panneaux pour les autres fonctions du vendeur
from .vendeur_panels.credit_management_frame import CreditManagementFrame
from .vendeur_panels.expenses_management_frame import ExpensesManagementFrame

# Dialogues de clôture
from .dialogs.closure_dialogs import DemandeClotureWindow, InvendusWindow, RapportClotureWindow


class VendeurFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller
        # Le main_controller est la classe MainApp, pour accéder aux données globales
        self.main_controller = controller.controller if hasattr(controller, 'controller') else controller
        self.sales_service = SalesService()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Barre du haut
        self.rowconfigure(1, weight=1) # Contenu principal

        self._create_top_bar()
        self._create_main_container()
        
        # Afficher la page de vente par défaut
        self.show_sales_page()

    def _create_top_bar(self):
        """Crée la barre du haut avec le nom du vendeur, les boutons de navigation et le bouton de clôture."""
        top_bar = tk.Frame(self, bg="#34495e", height=60)
        top_bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        top_bar.pack_propagate(False)

        # Frame pour les boutons de navigation à droite
        nav_frame = tk.Frame(top_bar, bg="#34495e")
        nav_frame.pack(side="right", padx=10)

        nav_btn_config = {'font': ("Cairo", 14, "bold"), 'fg': 'white', 'relief': 'flat', 'activebackground': '#4e657e'}
        tk.Button(nav_frame, text=get_text("sales_page_button"), bg="#27ae60", command=self.show_sales_page, **nav_btn_config).pack(side="right", padx=5)
        tk.Button(nav_frame, text=get_text("credit_page_button"), bg="#2980b9", command=self.show_credit_page, **nav_btn_config).pack(side="right", padx=5)
        tk.Button(nav_frame, text=get_text("expenses_page_button"), bg="#f39c12", command=self.show_expenses_page, **nav_btn_config).pack(side="right", padx=5)
        
        self.label_vendeur_actif = tk.Label(top_bar, text="", font=("Cairo", 18, "bold"), bg="#34495e", fg="white")
        self.label_vendeur_actif.pack(side="right", padx=20)

        # Bouton de clôture à gauche
        btn_cloture = tk.Button(top_bar, text=get_text("close_cash_register_button"), font=("Cairo", 14, "bold"),
                                bg="#e67e22", fg="white", relief="flat",
                                activebackground="#d35400", command=self.cloturer_session)
        btn_cloture.pack(side="left", padx=20)
    
    def _create_main_container(self):
        """Crée le conteneur qui affichera les différentes pages (vente, crédit, etc.)."""
        self.main_container = tk.Frame(self, bg="#eaf0f6")
        self.main_container.grid(row=1, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # --- Création des différentes pages ---
        self.pages = {}

        # Page 1: Vente directe
        sales_page_frame = tk.Frame(self.main_container, bg="#eaf0f6")
        self.pages["sales"] = sales_page_frame
        sales_page_frame.grid(row=0, column=0, sticky="nsew")
        # Configuration de la grille pour la page de vente
        sales_page_frame.columnconfigure(0, weight=1)
        sales_page_frame.columnconfigure(1, weight=0)
        sales_page_frame.columnconfigure(2, weight=0)
        sales_page_frame.rowconfigure(0, weight=1)
        # Création des panneaux de la page de vente
        product_panel = ProductPanel(sales_page_frame, on_product_select_callback=self.handle_product_selection)
        product_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        self.cart_panel = CartPanel(sales_page_frame, controller=self, on_cart_update_callback=self.handle_cart_update)
        # --- MODIFICATION: "ns" -> "nsew" ---
        self.cart_panel.grid(row=0, column=1, sticky="nsew", pady=10, padx=0)
        
        self.calculator_panel = CalculatorPanel(sales_page_frame, on_add_item_callback=self.handle_add_item, on_confirm_sale_callback=self.handle_confirm_sale, on_cancel_cart_callback=self.handle_cancel_cart)
        # --- MODIFICATION: "ns" -> "nsew" ---
        self.calculator_panel.grid(row=0, column=2, sticky="nsew", pady=10, padx=(5, 10))

        # Page 2: Gestion des crédits
        credit_page_frame = CreditManagementFrame(self.main_container, controller=self)
        self.pages["credit"] = credit_page_frame
        credit_page_frame.grid(row=0, column=0, sticky="nsew")

        # Page 3: Gestion des dépenses
        expenses_page_frame = ExpensesManagementFrame(self.main_container, self)
        self.pages["expenses"] = expenses_page_frame
        expenses_page_frame.grid(row=0, column=0, sticky="nsew")

    def show_page(self, page_name):
        """Affiche une page spécifique en la mettant au premier plan."""
        page = self.pages.get(page_name)
        if page:
            if hasattr(page, 'charger_donnees'):
                page.charger_donnees()
            page.tkraise()

    def show_sales_page(self):
        self.show_page("sales")

    def show_credit_page(self):
        self.show_page("credit")
        self.pages["credit"].load_clients()

    def show_expenses_page(self):
        self.show_page("expenses")
        if hasattr(self.pages["expenses"], 'charger_donnees'):
             self.pages["expenses"].charger_donnees()

    def handle_product_selection(self, produit):
        self.calculator_panel.set_selected_product(produit)

    def handle_add_item(self, produit, quantite):
        item = {'nom': produit['nom'], 'qte': quantite, 'prix': produit['prix']}
        self.cart_panel.add_item_to_cart(item)

    def handle_cart_update(self, total_amount):
        self.calculator_panel.update_total(total_amount)

    def handle_confirm_sale(self):
        panier = self.cart_panel.get_cart_items()
        if not panier:
            messagebox.showinfo(get_text("info"), get_text("cart_empty_info"), parent=self)
            return

        id_vendeur = self.main_controller.user_id
        if id_vendeur is None:
            messagebox.showerror(get_text("error"), get_text("no_user_connected_error"), parent=self)
            return

        vente_id = self.sales_service.record_sale(panier, id_vendeur)
        if vente_id:
            messagebox.showinfo(get_text("success"), get_text("sale_success_message"), parent=self)
            self.cart_panel.clear_cart()
        else:
            messagebox.showerror(get_text("error"), get_text("sale_record_error"), parent=self)

    def handle_cancel_cart(self):
        panier = self.cart_panel.get_cart_items()
        if panier and messagebox.askyesno(get_text("confirm_cancellation_title"), get_text("confirm_cancellation_message"), parent=self):
            self.cart_panel.clear_cart()
    
    def on_show(self, event=None):
        nom_vendeur = self.main_controller.nom_utilisateur
        if nom_vendeur:
            self.label_vendeur_actif.config(text=get_text("user_label").format(username=nom_vendeur))
        else:
            self.label_vendeur_actif.config(text=get_text("user_not_defined"))
            
    def cloturer_session(self):
        choix = DemandeClotureWindow(self).show()
        if not choix: return
        
        if choix == 'journee':
            invendus = InvendusWindow(self).show()
            if invendus is None: return
            
            id_admin = self.main_controller.user_id
            for item in invendus:
                description = get_text("unsold_loss_description").format(qte=item['qte'], nom=item['nom'])
                execute_query("INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)", (description, -item['cout_perte'], 'Perte Invendus', id_admin))
                execute_query("UPDATE produits SET stock = 0 WHERE id = ?", (item['id'],))
            
            if invendus:
                messagebox.showinfo(get_text("success"), get_text("unsold_loss_success"), parent=self)
            
        self.afficher_rapport_final(choix)

    def afficher_rapport_final(self, type_rapport):
        nom_vendeur_rapport = None
        id_vendeur = self.main_controller.user_id
        today = datetime.now().strftime('%Y-%m-%d')
        
        if type_rapport == 'service':
            if id_vendeur is None: 
                messagebox.showerror(get_text("error"), get_text("no_user_for_closure_error"), parent=self)
                return
            titre_rapport = get_text("service_end_report_title")
            nom_vendeur_rapport = self.main_controller.nom_utilisateur
            ventes_query = "SELECT SUM(total) FROM ventes WHERE vendeur_id = ? AND date(date_vente) = ?"
            ventes_params = (id_vendeur, today)
            depenses_query = "SELECT SUM(montant) FROM transactions WHERE vendeur_id = ? AND date(date) = ?"
            depenses_params = (id_vendeur, today)
        else: # 'journee'
            titre_rapport = get_text("final_daily_report_title")
            ventes_query = "SELECT SUM(total) FROM ventes WHERE date(date_vente) = ?"
            ventes_params = (today,)
            depenses_query = "SELECT SUM(montant) FROM transactions WHERE date(date) = ?"
            depenses_params = (today,)
            
        result_ventes = execute_query(ventes_query, ventes_params, fetch='one')
        result_depenses = execute_query(depenses_query, depenses_params, fetch='one')
        total_ventes = result_ventes[0] if result_ventes and result_ventes[0] is not None else 0
        total_depenses = result_depenses[0] if result_depenses and result_depenses[0] is not None else 0
        solde_final = FONDS_DE_CAISSE + total_ventes + total_depenses
        
        report_data = {
            "titre_rapport": titre_rapport, "nom_vendeur": nom_vendeur_rapport, "date": today, "heure": datetime.now().strftime('%H:%M:%S'),
            "fonds_de_caisse": FONDS_DE_CAISSE, "total_ventes": total_ventes, "total_depenses": total_depenses, "solde_final": solde_final
        }
        
        RapportClotureWindow(self, report_data)
        
        if type_rapport == 'service':
            self.cart_panel.clear_cart()
            self.main_controller.show_frame("LoginFrame")