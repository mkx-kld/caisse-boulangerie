# Fichier: ui/sales_page/cart_panel.py
# Rôle: Affiche le panier, permet de supprimer des articles. Affiche l'historique des ventes du jour.

import tkinter as tk
from tkinter import ttk, messagebox
from services.sales_service import SalesService
from utils import format_currency
from translations import get_text

class CartPanel(tk.Frame):
    def __init__(self, parent, controller, on_cart_update_callback):
        super().__init__(parent, bg="#ffffff", bd=1, relief="solid", width=450)
        self.controller = controller
        self.on_cart_update = on_cart_update_callback
        self.sales_service = SalesService()
        self.panier = []
        self.mode_affichage_milieu = 'panier'

        self.grid_propagate(False)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._create_widgets()
        self._toggle_view_to_cart()

    def _create_widgets(self):
        self.label_titre_milieu = tk.Label(self, text="", font=("Cairo", 24, "bold"), bg="white", fg="#2c3e50")
        self.label_titre_milieu.grid(row=0, column=0, pady=10)

        tree_container = tk.Frame(self, bg="white")
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        style = ttk.Style(self)
        style.configure("Panier.Treeview", font=("Cairo", 14), rowheight=35)
        style.configure("Panier.Treeview.Heading", font=("Cairo", 16, "bold"))
        
        # --- Treeview pour le Panier ---
        self.panier_tree = ttk.Treeview(tree_container, columns=("total", "prix", "qte", "nom"), show="headings", style="Panier.Treeview")
        # ... (les headings et columns du panier_tree)
        self.panier_tree.heading("nom", text=get_text("product_col"), anchor="e")
        self.panier_tree.column("nom", width=160, anchor="e")
        self.panier_tree.heading("qte", text=get_text("quantity_col"), anchor="center")
        self.panier_tree.column("qte", width=60, anchor="center")
        self.panier_tree.heading("prix", text=get_text("price_col"), anchor="e")
        self.panier_tree.column("prix", width=80, anchor="e")
        self.panier_tree.heading("total", text=get_text("total_col"), anchor="e")
        self.panier_tree.column("total", width=100, anchor="e")


        # --- Treeview pour l'Historique ---
        self.historique_tree = ttk.Treeview(tree_container, columns=("details", "total", "heure"), show="headings", style="Panier.Treeview")
        # ... (les headings et columns de l'historique_tree)
        self.historique_tree.heading("heure", text=get_text("time_col"), anchor="e")
        self.historique_tree.column("heure", width=100, anchor="e")
        self.historique_tree.heading("total", text=get_text("total_label"), anchor="e")
        self.historique_tree.column("total", width=100, anchor="e")
        self.historique_tree.heading("details", text=get_text("product_col"), anchor="e")
        self.historique_tree.column("details", width=230, anchor="e")


        # --- Boutons ---
        self.panier_btn_frame = tk.Frame(self, bg="white")
        self.panier_btn_frame.grid(row=2, column=0, pady=10)
        
        btn_panier_config = {'font': ("Cairo", 14, "bold"), 'pady': 8}
        self.btn_suppr_article = tk.Button(self.panier_btn_frame, text=get_text("delete_product_button"), bg="#e74c3c", fg="white", command=self._delete_cart_item, **btn_panier_config)
        self.btn_historique = tk.Button(self.panier_btn_frame, text=get_text("daily_log_button"), bg="#34495e", fg="white", command=self._toggle_view_to_history, **btn_panier_config)
        self.btn_retour_panier = tk.Button(self.panier_btn_frame, text=get_text("return_to_cart_button"), bg="#34495e", fg="white", command=self._toggle_view_to_cart, **btn_panier_config)
        self.btn_suppr_vente = tk.Button(self.panier_btn_frame, text=get_text("delete_sale_button"), bg="#c0392b", fg="white", command=self._delete_sale_from_history, **btn_panier_config)

    # --- Méthodes Publiques ---
    def add_item_to_cart(self, item):
        """Ajoute un article au panier."""
        if self.mode_affichage_milieu == 'historique':
            messagebox.showwarning(get_text("warning"), get_text("return_to_cart_warning"), parent=self)
            return
        self.panier.append(item)
        self._update_cart_display()

    def get_cart_items(self):
        return self.panier

    def clear_cart(self):
        self.panier.clear()
        self._update_cart_display()

    # --- Méthodes Privées ---
    def _update_cart_display(self):
        for i in self.panier_tree.get_children(): self.panier_tree.delete(i)
        total = 0
        for item in self.panier:
            total_ligne = item['prix'] * item['qte']
            self.panier_tree.insert("", "end", values=(format_currency(total_ligne), format_currency(item['prix']), item['qte'], item['nom']))
            total += total_ligne
        # Notifie le parent du nouveau total
        self.on_cart_update(total)

    def _delete_cart_item(self):
        selected_item = self.panier_tree.selection()
        if not selected_item:
            messagebox.showwarning(get_text("warning"), get_text("select_item_to_delete_warning"), parent=self)
            return
        index = self.panier_tree.index(selected_item[0])
        del self.panier[index]
        self._update_cart_display()

    def _load_history(self):
        for i in self.historique_tree.get_children(): self.historique_tree.delete(i)
        historique = self.sales_service.get_daily_sales_history()
        for vente in historique:
            self.historique_tree.insert("", "end", iid=vente['id'], values=(vente['details'], format_currency(vente['total']), vente['heure']))
            
    def _delete_sale_from_history(self):
        selected_item = self.historique_tree.selection()
        if not selected_item:
            messagebox.showwarning(get_text("warning"), get_text("select_sale_to_delete_warning"), parent=self)
            return
        if not messagebox.askyesno(get_text("confirm_delete_title"), get_text("confirm_delete_sale_message"), parent=self):
            return
        
        vente_id = selected_item[0]
        self.sales_service.delete_sale_from_history(vente_id)
        self._load_history()

    def _toggle_view_to_history(self):
        self.mode_affichage_milieu = 'historique'
        self.label_titre_milieu.config(text=get_text("daily_history_title"))
        self.panier_tree.grid_remove()
        self.historique_tree.grid(row=0, column=0, sticky="nsew")
        self.btn_suppr_article.pack_forget()
        self.btn_historique.pack_forget()
        self.btn_retour_panier.pack(side="right", padx=5)
        if self.controller.controller.role == 'admin':
            self.btn_suppr_vente.pack(side="right", padx=5)
        self._load_history()

    def _toggle_view_to_cart(self):
        self.mode_affichage_milieu = 'panier'
        self.label_titre_milieu.config(text=get_text("current_cart_title"))
        self.historique_tree.grid_remove()
        self.panier_tree.grid(row=0, column=0, sticky="nsew")
        self.btn_retour_panier.pack_forget()
        self.btn_suppr_vente.pack_forget()
        self.btn_suppr_article.pack(side="right", padx=5)
        self.btn_historique.pack(side="right", padx=5)