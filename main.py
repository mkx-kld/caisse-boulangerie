# Fichier: main.py
# Point d'entrée principal de l'application.
# Lance l'application, initialise la base de données et gère les fenêtres principales.

import tkinter as tk
import traceback
from datetime import datetime

# --- Imports depuis notre nouvelle structure ---
from database.init_db import init_db
from database.db_manager import execute_query
from ui.login_frame import LoginFrame
from ui.admin_frame import AdminFrame
from ui.vendeur_frame import VendeurFrame
from ui.components.app_dialogs import NotificationsWindow

class MainApp(tk.Tk):
    """
    Classe principale de l'application. Hérite de tk.Tk et gère les frames
    et les données globales de la session utilisateur.
    """
    def __init__(self):
        super().__init__()
        self.title("برنامج الخباز")
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", self.quitter_plein_ecran)
        self.configure(bg="#cccccc")

        # --- Données de session ---
        self.user_id = None
        self.nom_utilisateur = None
        self.role = None
        self.notifications = []

        # --- Conteneur principal pour les frames ---
        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Initialisation de toutes les fenêtres principales (Login, Admin, Vendeur)
        for F in (LoginFrame, AdminFrame, VendeurFrame):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            # Place chaque frame dans la grille, elles se superposent
            frame.grid(row=0, column=0, sticky="nsew")

        # Affiche l'écran de connexion au démarrage
        self.show_frame("LoginFrame")

    def show_frame(self, page_name, check_notifications=False):
        """
        Affiche un frame spécifique et peut déclencher une vérification des notifications.
        """
        # Si demandé (après une connexion), on vérifie les notifications
        if check_notifications:
            self.verifier_notifications()
        
        frame = self.frames[page_name]
        
        # Logique pour rafraîchir les données du frame avant de l'afficher
        # C'est utile pour que les listes soient à jour
        if hasattr(frame, 'charger_donnees_initiales'):
            frame.charger_donnees_initiales()
        elif hasattr(frame, 'charger_donnees_page'):
            frame.charger_donnees_page()
        elif hasattr(frame, 'charger_donnees'):
            frame.charger_donnees()
        elif hasattr(frame, 'charger_employes'):
             frame.charger_employes()

        # Met le frame demandé au premier plan
        frame.tkraise()

    def quitter_plein_ecran(self, event=None):
        """Permet de sortir du mode plein écran avec la touche 'Echap'."""
        self.attributes("-fullscreen", False)

    def verifier_notifications(self):
        """
        Vérifie les certificats des employés et affiche une fenêtre de notification si nécessaire.
        """
        self.notifications = []
        today = datetime.now()
        
        # Utilise notre fonction centralisée pour interroger la base de données
        query = "SELECT nom, date_certificat FROM employes WHERE date_certificat IS NOT NULL AND date_certificat != ''"
        employes = execute_query(query, fetch='all')
        
        if not employes:
            return

        for nom, date_cert_str in employes:
            try:
                date_cert = datetime.strptime(date_cert_str, "%Y-%m-%d")
                jours_restants = (date_cert - today).days
                
                if jours_restants < 0:
                    self.notifications.append({
                        'titre': "شهادة الصحة منتهية الصلاحية", 'nom': nom,
                        'details': f"منذ {abs(jours_restants)} يوم", 'type': 'expiree'
                    })
                elif jours_restants <= 30:
                    self.notifications.append({
                        'titre': "شهادة الصحة تنتهي قريبا", 'nom': nom,
                        'details': f"في غضون {jours_restants} يوم", 'type': 'alerte'
                    })
            except (ValueError, TypeError):
                # Ignore les dates mal formatées dans la base de données
                continue

        # Si des notifications ont été trouvées, on affiche la fenêtre
        if self.notifications:
            NotificationsWindow(self, self.notifications)


if __name__ == "__main__":
    try:
        # Étape cruciale : initialise la base de données au tout premier lancement
        init_db()
    except Exception as e:
        # En cas d'échec, affiche l'erreur et arrête l'application
        print("Erreur fatale lors de l'initialisation de la base de données.")
        traceback.print_exc()
        exit()

    # Crée et lance l'application principale
    app = MainApp()
    app.mainloop()
