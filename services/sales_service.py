# Fichier: services/sales_service.py
# Rôle: Gère toute la logique métier et les interactions avec la base de données pour les ventes.

from datetime import datetime
from database.db_manager import execute_query

class SalesService:
    @staticmethod
    def get_categories_for_sale():
        """Récupère les catégories de produits destinés à la vente."""
        query = "SELECT DISTINCT c.nom FROM categories c JOIN produits p ON c.id = p.categorie_id WHERE p.type = 'vente' ORDER BY c.nom"
        return [row[0] for row in execute_query(query, fetch='all') or []]

    @staticmethod
    def get_products_by_category(categorie):
        """Récupère les produits d'une catégorie spécifique."""
        query = "SELECT p.nom, p.prix, p.photo_path FROM produits p JOIN categories c ON p.categorie_id = c.id WHERE c.nom = ? AND p.type = 'vente' ORDER BY p.nom"
        return execute_query(query, (categorie,), fetch='all') or []

    @staticmethod
    def record_sale(panier, vendeur_id):
        """Enregistre une vente complète (vente, détails, mise à jour stock)."""
        if not panier or vendeur_id is None:
            return None
        
        total_vente = sum(item['prix'] * item['qte'] for item in panier)
        vente_id = execute_query(
            "INSERT INTO ventes (total, date_vente, vendeur_id) VALUES (?, datetime('now', 'localtime'), ?)",
            (total_vente, vendeur_id)
        )

        if not vente_id:
            return None

        for item in panier:
            # Récupère l'ID du produit et de son ingrédient de base (si composite)
            produit_info = execute_query(
                "SELECT id, (SELECT ingredient_id FROM produit_composition WHERE produit_final_id = p.id) as 'id_ingredient' FROM produits p WHERE nom=?",
                (item['nom'],), fetch='one'
            )
            if produit_info:
                produit_id, ingredient_id = produit_info
                
                # Insère les détails de la vente
                execute_query(
                    "INSERT INTO details_vente (vente_id, produit_id, quantite, prix_unitaire) VALUES (?, ?, ?, ?)",
                    (vente_id, produit_id, item['qte'], item['prix'])
                )
                
                # Met à jour le stock du produit de base (ingrédient ou produit simple)
                stock_to_update_id = ingredient_id if ingredient_id else produit_id
                if stock_to_update_id:
                    execute_query(
                        "UPDATE produits SET stock = stock - ? WHERE id = ?",
                        (item['qte'], stock_to_update_id)
                    )
        return vente_id

    @staticmethod
    def get_daily_sales_history():
        """Récupère l'historique des ventes pour la journée en cours."""
        today_date = datetime.now().strftime('%Y-%m-%d')
        ventes = execute_query(
            "SELECT id, time(date_vente), total FROM ventes WHERE date(date_vente) = ? ORDER BY date_vente DESC",
            (today_date,), fetch='all'
        ) or []

        sales_history = []
        for vente_id, heure, total in ventes:
            details_list = execute_query(
                "SELECT p.nom, dv.quantite FROM details_vente dv JOIN produits p ON p.id = dv.produit_id WHERE dv.vente_id = ?",
                (vente_id,), fetch='all'
            ) or []
            details_str = "، ".join([f"{qte}x {nom}" for nom, qte in details_list])
            sales_history.append({
                "id": vente_id,
                "heure": heure.split('.')[0],
                "total": total,
                "details": details_str
            })
        return sales_history

    @staticmethod
    def delete_sale_from_history(vente_id):
        """Supprime une vente et restaure le stock."""
        details_vente = execute_query(
            "SELECT produit_id, quantite FROM details_vente WHERE vente_id = ?",
            (vente_id,), fetch='all'
        ) or []
        
        for prod_id, qte in details_vente:
            # Note: Cette logique doit être validée. Si le produit est composite,
            # il faut remonter à l'ingrédient de base pour restaurer le stock.
            # Pour l'instant, on se base sur le produit_id de details_vente.
            execute_query("UPDATE produits SET stock = stock + ? WHERE id = ?", (qte, prod_id))
            
        execute_query("DELETE FROM ventes WHERE id = ?", (vente_id,))