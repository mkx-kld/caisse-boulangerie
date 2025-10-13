# Fichier: services/partner_service.py
# Rôle: Logique améliorée pour les partenaires, incluant la gestion des clients particuliers.

from database.db_manager import execute_query
from datetime import datetime

class PartnerService:
    @staticmethod
    def _get_ingredient_id(produit_id):
        res = execute_query("SELECT ingredient_id FROM produit_composition WHERE produit_final_id = ?", (produit_id,), fetch='one')
        return res[0] if res else None

    @staticmethod
    def get_all_credit_clients():
        """
        CORRIGÉ : Récupère TOUS les clients (pro et particuliers), peu importe leur solde,
        pour qu'on puisse les voir dans la liste même si leur solde est à zéro.
        """
        return execute_query("SELECT id, nom, type_partenaire, solde_credit FROM partenaires WHERE type_partenaire IN ('client_pro', 'client_particulier') ORDER BY nom", fetch='all') or []

    @staticmethod
    def create_private_client(nom, telephone):
        if execute_query("SELECT id FROM partenaires WHERE nom = ?", (nom,), fetch='one'):
            return None, "Ce nom de client existe déjà."
        query = "INSERT INTO partenaires (nom, telephone, type_partenaire, mode_paiement, solde_credit) VALUES (?, ?, 'client_particulier', 'crédit', 0)"
        client_id = execute_query(query, (nom, telephone))
        return (client_id, "Client créé avec succès.") if client_id else (None, "Erreur lors de la création du client.")
    
    @staticmethod
    def update_private_client(client_id, nom, telephone):
        """NOUVEAU : Met à jour un client particulier."""
        if execute_query("SELECT id FROM partenaires WHERE nom = ? AND id != ?", (nom, client_id), fetch='one'):
            return False, "Un autre client avec ce nom existe déjà."
        query = "UPDATE partenaires SET nom = ?, telephone = ? WHERE id = ?"
        execute_query(query, (nom, telephone, client_id))
        return True, "Client mis à jour avec succès."

    @staticmethod
    def delete_private_client(client_id):
        """NOUVEAU : Supprime un client particulier, uniquement si son solde est à zéro."""
        solde = execute_query("SELECT solde_credit FROM partenaires WHERE id = ?", (client_id,), fetch='one')
        if solde and solde[0] != 0:
            return False, "Impossible de supprimer un client avec un solde non nul."
        
        execute_query("DELETE FROM partenaires WHERE id = ?", (client_id,))
        return True, "Client supprimé avec succès."

    @staticmethod
    def add_credit_sale(partner_id, cart, user_id):
        """NOUVEAU : Logique générique pour ajouter une vente/livraison à crédit."""
        if not all([partner_id, cart, user_id]):
            return False, "Données manquantes pour enregistrer la vente."

        montant_total = sum(item['total'] for item in cart)
        date_operation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            for item in cart:
                execute_query(
                    "INSERT INTO livraisons_clients (partenaire_id, produit_id, quantite, prix_vente_unitaire, montant_total, date_livraison) VALUES (?, ?, ?, ?, ?, ?)",
                    (partner_id, item['id'], item['qte'], item['prix'], item['total'], date_operation)
                )
                ingredient_id = PartnerService._get_ingredient_id(item['id'])
                id_a_decrementer = ingredient_id if ingredient_id else item['id']
                execute_query("UPDATE produits SET stock = stock - ? WHERE id = ?", (item['qte'], id_a_decrementer))
            
            execute_query("UPDATE partenaires SET solde_credit = solde_credit + ? WHERE id = ?", (montant_total, partner_id))
            return True, "Vente à crédit enregistrée avec succès."
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de la vente à crédit: {e}")
            return False, "Une erreur est survenue lors de l'enregistrement."

    @staticmethod

    def get_credit_sales_for_day(date_str):
        """NOUVEAU : Récupère toutes les ventes à crédit pour une date spécifique."""
        query = """
            SELECT p.nom, pr.nom, l.quantite, l.montant_total
            FROM livraisons_clients l
            JOIN partenaires p ON l.partenaire_id = p.id
            JOIN produits pr ON l.produit_id = pr.id
            WHERE date(l.date_livraison) = ?
            ORDER BY l.date_livraison DESC
        """
        return execute_query(query, (date_str,), fetch='all') or []

    def record_payment(partenaire_id, montant, vendeur_id):
        partenaire = execute_query("SELECT nom, type_partenaire FROM partenaires WHERE id=?", (partenaire_id,), fetch='one')
        if not partenaire: return False, "Partenaire non trouvé."
        
        nom_partenaire, type_partenaire = partenaire
        montant_paiement = abs(float(montant))

        if type_partenaire in ['client_pro', 'client_particulier']:
            execute_query("UPDATE partenaires SET solde_credit = solde_credit - ? WHERE id = ?", (montant_paiement, partenaire_id))
            montant_trans, type_trans = montant_paiement, "Paiement Client"
        else: # fournisseur
            execute_query("UPDATE partenaires SET solde_credit = solde_credit + ? WHERE id = ?", (montant_paiement, partenaire_id))
            montant_trans, type_trans = -montant_paiement, "Paiement Fournisseur"
            
        desc = f"{type_trans}: {nom_partenaire}"
        execute_query(
            "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id, partenaire_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?)",
            (desc, montant_trans, type_trans, vendeur_id, partenaire_id)
        )
        return True, "Paiement enregistré avec succès."