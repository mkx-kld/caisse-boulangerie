# Fichier: ui/credit_management_frame.py
# Rôle: Interface pour gérer les crédits clients (pros et particuliers).

import tkinter as tk
from tkinter import ttk, messagebox
from translations import get_text
from services.partner_service import PartnerService
from ui.dialogs.credit_dialogs import CreatePrivateClientDialog

class CreditManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller
        self.main_controller = controller.controller
        self.service = PartnerService()

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        self.create_left_panel()
        self.create_right_panel()
        
        self.load_credit_clients()

    def create_left_panel(self):
        left_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(left_frame, text=get_text("credit_clients_list"), font=("Cairo", 16, "bold"), bg="white").pack(pady=10)

        self.client_tree = ttk.Treeview(left_frame, columns=("type", "balance"), show="headings")
        self.client_tree.heading("type", text=get_text("partner_list_col_type"))
        self.client_tree.heading("balance", text=get_text("partner_list_col_balance"))
        # Le nom sera affiché dans la première colonne (tree)
        self.client_tree.pack(expand=True, fill="both")
        
        # Ajout des boutons d'action
        btn_frame = tk.Frame(left_frame, bg="white")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text=get_text("create_private_client_button"), command=self.create_private_client).pack(side="left", padx=5)
        tk.Button(btn_frame, text=get_text("add_delivery_button"), command=self.add_pro_delivery).pack(side="left", padx=5)

    def create_right_panel(self):
        right_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)
        # Ce panneau affichera l'historique du client sélectionné
        # et le bouton pour "Encaisser un Paiement".

    def load_credit_clients(self):
        for i in self.client_tree.get_children():
            self.client_tree.delete(i)
        
        clients = self.service.get_credit_clients()
        for client in clients:
            client_id, nom, _, type_partenaire, solde = client
            # On utilise le nom comme texte principal de l'item
            self.client_tree.insert("", "end", iid=client_id, text=nom, values=(type_partenaire, f"{solde:,.2f} DA"))

    def create_private_client(self):
        dialog = CreatePrivateClientDialog(self, self.main_controller.user_id)
        if dialog.show():
            self.load_credit_clients() # Recharger la liste si un client a été ajouté

    def add_pro_delivery(self):
        # Ouvre la boîte de dialogue pour les livraisons aux pros
        pass