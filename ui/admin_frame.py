# Fichier: ui/admin_frame.py
# Ce frame principal gère la navigation entre les différents panneaux d'administration.

import tkinter as tk

# Imports des NOUVEAUX panneaux depuis le dossier admin_panels
from .admin_panels.produits_panel import ProduitsPanel
from .admin_panels.employes_panel import EmployesPanel
from .admin_panels.activites_panel import ActivitesPanel
from .admin_panels.stock_panel import StockPanel
from .admin_panels.partenaires_panel import PartenairesPanel
# On importe aussi le frame vendeur pour l'inclure dans l'interface admin
from .vendeur_frame import VendeurFrame

class AdminFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f4f4f4")
        self.controller = controller

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # --- Menu de navigation supérieur ---
        self.menu = tk.Frame(self, bg="#dddddd")
        self.menu.grid(row=0, column=0, sticky="ew")

        # --- Conteneur pour le contenu principal ---
        self.content = tk.Frame(self, bg="#ffffff")
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # --- Initialisation de tous les panneaux ---
        self.frames = {}
        # On utilise les nouveaux noms de classes pour les panneaux
        # Note: Les noms de fichiers ont été changés (ex: produits.py -> produits_panel.py)
        # et les classes renommées (ex: ProduitsFrame -> ProduitsPanel) pour plus de clarté.
        self.frames["produits"] = ProduitsPanel(self.content, self)
        self.frames["employes"] = EmployesPanel(self.content, self)
        self.frames["vendeur"] = VendeurFrame(self.content, self)
        self.frames["activites"] = ActivitesPanel(self.content, self)
        self.frames["stock"] = StockPanel(self.content, self)
        self.frames["partenaires"] = PartenairesPanel(self.content, self)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        # --- Création des boutons du menu ---
        btn_config = {'font': ("Cairo", 16), 'fg': 'white', 'padx': 20, 'pady': 5, 'relief': 'flat'}
        
        tk.Button(self.menu, text="🛒 واجهة البيع", bg="#27ae60", **btn_config, command=self.afficher_vendeur).pack(side="right", padx=10, pady=5)
        tk.Button(self.menu, text="📦 المنتجات", bg="#3498db", **btn_config, command=self.afficher_produits).pack(side="right", padx=10, pady=5)
        tk.Button(self.menu, text="📈 المخزون", bg="#8e44ad", **btn_config, command=self.afficher_stock).pack(side="right", padx=10, pady=5)
        tk.Button(self.menu, text="🤝 الشركاء", bg="#16a085", **btn_config, command=self.afficher_partenaires).pack(side="right", padx=10, pady=5)
        tk.Button(self.menu, text="👷 الموظفين", bg="#f39c12", **btn_config, command=self.afficher_employes).pack(side="right", padx=10, pady=5)
        tk.Button(self.menu, text="📊 النشاط اليومي", bg="#c0392b", **btn_config, command=self.afficher_activites).pack(side="right", padx=10, pady=5)


        # Afficher la page par défaut au lancement
        self.afficher_vendeur()
    
    def afficher_vendeur(self):
        """Affiche le panneau de vente."""
        self.frames["vendeur"].tkraise()

    def afficher_produits(self):
        """Affiche le panneau de gestion des produits et rafraîchit ses données."""
        self.frames["produits"].charger_donnees_initiales()
        self.frames["produits"].tkraise()

    def afficher_employes(self):
        """Affiche le panneau de gestion des employés et rafraîchit ses données."""
        self.frames["employes"].charger_employes()
        self.frames["employes"].tkraise()

    def afficher_activites(self):
        # La fonction charger_donnees va maintenant appliquer les filtres par défaut (aujourd'hui)
        self.frames["activites"].charger_donnees()
        self.frames["activites"].tkraise()

    def afficher_stock(self):
        """Affiche le panneau de gestion du stock et rafraîchit ses données."""
        self.frames["stock"].charger_donnees_page()
        self.frames["stock"].tkraise()
    
    def afficher_partenaires(self):
        """Affiche le panneau de gestion des partenaires et rafraîchit ses données."""
        self.frames["partenaires"].charger_partenaires()
        self.frames["partenaires"].tkraise()
