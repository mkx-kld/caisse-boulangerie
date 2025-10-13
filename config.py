# Fichier: config.py
# Ce fichier contient les constantes globales de l'application.

import os

# Chemin de base du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin vers la base de données
DB_PATH = os.path.join(BASE_DIR, "data", "caisse.db")

# Constantes financières
FONDS_DE_CAISSE = 5000
