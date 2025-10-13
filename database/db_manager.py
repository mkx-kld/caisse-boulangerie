# Fichier: database/db_manager.py
# MODULE CENTRAL pour toutes les interactions avec la base de données.

import sqlite3
from tkinter import messagebox
import traceback

# On importe le chemin depuis notre fichier de configuration
from config import DB_PATH

def get_prix_pour_partenaire(produit_id, partenaire_id):
    """
    Récupère le prix d'un produit pour un partenaire spécifique.
    Cherche d'abord un prix spécial. Si non trouvé, renvoie le prix de vente par défaut.
    
    Args:
        produit_id (int): L'ID du produit.
        partenaire_id (int): L'ID du partenaire.

    Returns:
        float: Le prix applicable, ou 0 si le produit n'est pas trouvé.
    """
    # 1. Essayer de trouver un prix spécial pour ce partenaire et ce produit
    prix_special_res = execute_query(
        "SELECT prix_special FROM partenaire_prix WHERE partenaire_id = ? AND produit_id = ?",
        (partenaire_id, produit_id),
        fetch='one'
    )
    
    if prix_special_res:
        return prix_special_res[0] # Retourne le prix spécial s'il existe

    # 2. Si aucun prix spécial n'est trouvé, chercher le prix de vente par défaut
    prix_defaut_res = execute_query(
        "SELECT prix FROM produits WHERE id = ?",
        (produit_id,),
        fetch='one'
    )
    
    if prix_defaut_res:
        return prix_defaut_res[0] # Retourne le prix par défaut

    return 0 # Retourne 0 si le produit n'existe pas

def execute_query(query, params=(), fetch=None):
    """
    Exécute une requête sur la base de données SQLite de manière sécurisée.

    Args:
        query (str): La requête SQL à exécuter.
        params (tuple): Les paramètres pour la requête.
        fetch (str, optional): 'one' pour récupérer une ligne, 'all' pour toutes les lignes.

    Returns:
        Le résultat de la requête si fetch est utilisé, 
        l'ID de la dernière ligne insérée pour un INSERT,
        True pour un succès sans fetch,
        ou None en cas d'erreur.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(query, params)
        
        # Pour les opérations qui modifient la base de données
        if any(s in query.upper() for s in ["INSERT", "UPDATE", "DELETE"]):
            conn.commit()
            # Retourne l'ID de la dernière ligne insérée, très utile pour les ventes, etc.
            if "INSERT" in query.upper():
                return cur.lastrowid
        
        if fetch == 'one':
            return cur.fetchone()
        if fetch == 'all':
            return cur.fetchall()
            
        return True  # Succès pour les opérations sans fetch (UPDATE, DELETE)

    except sqlite3.Error as e:
        # Afficher une erreur claire à l'utilisateur
        messagebox.showerror(
            "Erreur de Base de Données",
            f"Une erreur SQL est survenue. Veuillez contacter le support.\n\nErreur: {e}"
        )
        # Afficher les détails dans la console pour le débogage
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()
