# Fichier: database/init_db.py
# Version 5.1 - Ajout du type 'client_particulier'

import os
import sqlite3
from config import DB_PATH

def init_db():
    """
    Initialise la base de données et crée toutes les tables si elles n'existent pas.
    """
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS partenaire_prix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partenaire_id INTEGER NOT NULL,
            produit_id INTEGER NOT NULL,
            prix_special REAL NOT NULL,
            FOREIGN KEY (partenaire_id) REFERENCES partenaires(id) ON DELETE CASCADE,
            FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE CASCADE,
            UNIQUE (partenaire_id, produit_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            prix_achat REAL,
            prix REAL NOT NULL,
            stock REAL DEFAULT 0,
            categorie_id INTEGER,
            type TEXT CHECK(type IN ('vente', 'consommation')),
            origine TEXT CHECK(origine IN ('local', 'achete')),
            photo_path TEXT,
            gere_en_stock INTEGER DEFAULT 0,
            mode_gestion TEXT DEFAULT 'permanent' NOT NULL CHECK(mode_gestion IN ('permanent', 'quotidien')),
            FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produit_composition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_final_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantite_ingredient REAL NOT NULL,
            FOREIGN KEY (produit_final_id) REFERENCES produits(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES produits(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'vendeur'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE
        )
    """)

    # --- MODIFICATION ---
    # Ajout de 'client_particulier' aux types de partenaires autorisés.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partenaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            telephone TEXT,
            type_partenaire TEXT NOT NULL CHECK(type_partenaire IN ('fournisseur', 'client_pro', 'client_particulier')),
            mode_paiement TEXT,
            solde_credit REAL DEFAULT 0.0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            quantite_ajoutee REAL NOT NULL,
            prix_achat_unitaire REAL,
            cout_total REAL,
            date_ajout TEXT NOT NULL,
            user_id INTEGER,
            partenaire_id INTEGER,
            FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (partenaire_id) REFERENCES partenaires(id) ON DELETE SET NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS livraisons_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partenaire_id INTEGER NOT NULL,
            produit_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL,
            prix_vente_unitaire REAL NOT NULL,
            montant_total REAL NOT NULL,
            date_livraison TEXT NOT NULL,
            FOREIGN KEY (partenaire_id) REFERENCES partenaires(id) ON DELETE CASCADE,
            FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            poste TEXT NOT NULL,
            salaire REAL,
            photo_path TEXT,
            date_embauche TEXT,
            date_certificat TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL NOT NULL,
            date_vente TEXT NOT NULL,
            vendeur_id INTEGER,
            FOREIGN KEY (vendeur_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS details_vente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vente_id INTEGER NOT NULL,
            produit_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            FOREIGN KEY (vente_id) REFERENCES ventes(id) ON DELETE CASCADE,
            FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            montant REAL NOT NULL,
            date TEXT NOT NULL,
            type_transaction TEXT NOT NULL,
            vendeur_id INTEGER,
            partenaire_id INTEGER,
            FOREIGN KEY (vendeur_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (partenaire_id) REFERENCES partenaires(id) ON DELETE SET NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_transformations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_produit_id INTEGER NOT NULL,
            destination_produit_id INTEGER NOT NULL,
            quantite REAL NOT NULL,
            date_transformation TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (source_produit_id) REFERENCES produits(id) ON DELETE CASCADE,
            FOREIGN KEY (destination_produit_id) REFERENCES produits(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)


    cur.execute("SELECT COUNT(id) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin", "admin"))
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("ali", "1234", "vendeur"))
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("fatima", "1234", "vendeur"))

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès.")