# Fichier: services/expense_service.py
# Rôle: Gère la logique des dépenses : récupération des listes et enregistrement des transactions.

from database.db_manager import execute_query

class ExpenseService:

    @staticmethod
    def get_consumable_products():
        """Récupère les produits de type 'consommation' (matières premières)."""
        return execute_query("SELECT id, nom, prix_achat, stock FROM produits WHERE type='consommation' ORDER BY nom", fetch='all') or []

    @staticmethod
    def get_resale_suppliers():
        """
        Récupère les fournisseurs de produits de revente.
        Un fournisseur de revente est un fournisseur qui a fourni un produit destiné à la vente directe (origine='achete').
        """
        query = """
            SELECT DISTINCT p.id, p.nom
            FROM partenaires p
            JOIN stock_entries se ON p.id = se.partenaire_id
            JOIN produits pr ON se.produit_id = pr.id
            WHERE p.type_partenaire = 'fournisseur' AND pr.origine = 'achete'
            ORDER BY p.nom
        """
        return execute_query(query, fetch='all') or []

    @staticmethod
    def get_employees():
        """Récupère la liste des employés avec leur salaire de référence."""
        return execute_query("SELECT id, nom, salaire FROM employes ORDER BY nom", fetch='all') or []

    @staticmethod
    def record_product_purchase(produit_id, quantite, prix_unitaire, fournisseur_id, user_id):
        """Enregistre l'achat d'un produit (consommable ou revente) et met à jour le stock et le solde du fournisseur."""
        cout_total = quantite * prix_unitaire
        
        # 1. Enregistrer l'entrée en stock
        execute_query(
            "INSERT INTO stock_entries (produit_id, quantite_ajoutee, prix_achat_unitaire, cout_total, date_ajout, user_id, partenaire_id) VALUES (?, ?, ?, ?, datetime('now', 'localtime'), ?, ?)",
            (produit_id, quantite, prix_unitaire, cout_total, user_id, fournisseur_id)
        )
        # 2. Mettre à jour la quantité en stock du produit
        execute_query("UPDATE produits SET stock = stock + ? WHERE id = ?", (quantite, produit_id))
        
        # 3. Mettre à jour le dernier prix d'achat
        execute_query("UPDATE produits SET prix_achat = ? WHERE id = ?", (prix_unitaire, produit_id))

        # 4. Augmenter notre dette envers le fournisseur (son solde devient plus négatif)
        if fournisseur_id:
            execute_query("UPDATE partenaires SET solde_credit = solde_credit - ? WHERE id = ?", (cout_total, fournisseur_id))
        
        # 5. Enregistrer la transaction comme une sortie d'argent
        produit = execute_query("SELECT nom FROM produits WHERE id = ?", (produit_id,), fetch='one')
        nom_produit = produit[0] if produit else "Inconnu"
        description = f"Achat: {quantite}x {nom_produit}"
        execute_query(
            "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id, partenaire_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?)",
            (description, -cout_total, 'Achat Produit', user_id, fournisseur_id)
        )
        return True, "Achat enregistré avec succès."

    @staticmethod
    def record_salary_payment(employee_id, montant, user_id):
        """Enregistre le paiement d'un salaire."""
        employe = execute_query("SELECT nom FROM employes WHERE id=?", (employee_id,), fetch='one')
        if not employe:
            return False, "Employé non trouvé."
            
        description = f"Paiement Salaire: {employe[0]}"
        montant_negatif = -abs(float(montant))
        
        query = "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)"
        execute_query(query, (description, montant_negatif, 'Salaire', user_id))
        return True, "Salaire enregistré."

    @staticmethod
    def record_manual_expense(description, montant, user_id):
        """Enregistre une dépense manuelle diverse."""
        montant_negatif = -abs(float(montant))
        query = "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)"
        execute_query(query, (description, montant_negatif, 'Dépense Manuelle', user_id))
        return True, "Dépense enregistrée."