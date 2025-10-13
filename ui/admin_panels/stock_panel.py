# Fichier: ui/admin_panels/stock_panel.py (Version Finale Corrigée et Nettoyée)

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from translations import get_text

from database.db_manager import execute_query
from ui.components.input_popups import CalculatorPopup
from ui.components.app_dialogs import TransformationStockWindow

class StockPanel(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f2f5")
        self.controller = controller
        self.main_controller = controller.controller if hasattr(controller, 'controller') else controller
        self.selected_produit = None

        # Les variables sont définies UNE SEULE FOIS ici.
        self.nom_produit_var = tk.StringVar(value=get_text("select_product_placeholder"))
        self.qte_var = tk.StringVar()
        self.prix_var = tk.StringVar()
        self.fournisseur_var = tk.StringVar()

        # Charger la liste des fournisseurs
        fournisseurs_list = execute_query("SELECT id, nom FROM partenaires WHERE type_partenaire='fournisseur' ORDER BY nom", fetch='all') or []
        self.fournisseurs_map = {nom: fid for fid, nom in fournisseurs_list}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.creer_panneau_formulaire()
        self.creer_panneau_liste_et_historique()
        self.charger_donnees_page()

    def creer_panneau_formulaire(self):
        # Cette fonction utilise maintenant les variables existantes, elle ne les recrée plus.
        form_frame = tk.LabelFrame(self, text=f" {get_text('stock_operations_title')} ", font=("Cairo", 18, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=15, pady=15)
        form_frame.grid(row=0, column=0, padx=25, pady=(20,10), sticky="ew")
        form_frame.columnconfigure(1, weight=1)
        
        font_label = ("Cairo", 16)
        font_entry = ("Cairo", 16)

        tk.Label(form_frame, text=get_text("selected_product_label"), font=font_label, bg="white").grid(row=0, column=5, padx=(20,5), pady=5, sticky="w")
        tk.Label(form_frame, textvariable=self.nom_produit_var, font=(font_label[0], 16, 'bold'), bg="white", fg="#2980b9").grid(row=0, column=4, sticky="e")
        
        tk.Label(form_frame, text=get_text("quantity_label_stock"), font=font_label, bg="white").grid(row=0, column=3, padx=(20,5), pady=5, sticky="w")
        qte_entry = ttk.Entry(form_frame, textvariable=self.qte_var, font=font_entry, justify="center", width=10)
        qte_entry.grid(row=0, column=2, padx=5, pady=5)
        tk.Button(form_frame, text="✏️", font=("Cairo", 14), command=lambda: self.open_popup(CalculatorPopup, self.qte_var)).grid(row=0, column=1, padx=(5,0))

        self.label_prix = tk.Label(form_frame, text=get_text("purchase_price_label"), font=font_label, bg="white")
        self.prix_entry = ttk.Entry(form_frame, textvariable=self.prix_var, font=font_entry, justify="center", width=10)
        
        self.label_fournisseur = tk.Label(form_frame, text=get_text("supplier_label"), font=font_label, bg="white")
        self.fournisseur_combo = ttk.Combobox(form_frame, textvariable=self.fournisseur_var, values=list(self.fournisseurs_map.keys()), state="readonly", font=font_entry, justify="center", width=15)
        
        self.btn_valider = tk.Button(form_frame, text=get_text("add_button_stock"), font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", relief="flat", width=15, height=2, command=self.valider_ajout)
        self.btn_valider.grid(row=0, column=0, rowspan=2, padx=(15, 20), pady=5)

    def creer_panneau_liste_et_historique(self):
        main_liste_frame = tk.Frame(self, bg="#f0f2f5")
        main_liste_frame.grid(row=1, column=0, rowspan=2, padx=25, pady=10, sticky="nsew")
        main_liste_frame.columnconfigure(0, weight=1)
        main_liste_frame.columnconfigure(1, weight=1)
        main_liste_frame.rowconfigure(0, weight=1)
        
        liste_produits_frame = tk.LabelFrame(main_liste_frame, text=f" {get_text('product_list_title')} ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", bd=2, relief="groove")
        liste_produits_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        liste_produits_frame.rowconfigure(0, weight=1); liste_produits_frame.columnconfigure(0, weight=1)
        
        style = ttk.Style(self)
        style.configure("Stock.Treeview", font=("Cairo", 14), rowheight=35)
        style.configure("Stock.Treeview.Heading", font=("Cairo", 16, "bold"))
        self.produits_tree = ttk.Treeview(liste_produits_frame, columns=("stock", "nom"), show="headings", style="Stock.Treeview")
        self.produits_tree.heading("nom", text=get_text("product_col_stock"), anchor="e"); self.produits_tree.column("nom", anchor="e")
        self.produits_tree.heading("stock", text=get_text("current_stock_col"), anchor="center"); self.produits_tree.column("stock", anchor="center", width=150)
        self.produits_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_produits = ttk.Scrollbar(liste_produits_frame, orient="vertical", command=self.produits_tree.yview)
        scrollbar_produits.grid(row=0, column=1, sticky="ns")
        self.produits_tree.configure(yscrollcommand=scrollbar_produits.set)
        self.produits_tree.bind("<<TreeviewSelect>>", self.on_produit_select)
        
        historique_frame = tk.LabelFrame(main_liste_frame, text=f" {get_text('stock_entry_log_title')} ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", bd=2, relief="groove")
        historique_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        historique_frame.rowconfigure(0, weight=1); historique_frame.columnconfigure(0, weight=1)
        
        self.historique_tree = ttk.Treeview(historique_frame, columns=("user", "qte", "date"), show="headings", style="Stock.Treeview")
        self.historique_tree.heading("date", text=get_text("datetime_col"), anchor="e"); self.historique_tree.column("date", anchor="e", width=200)
        self.historique_tree.heading("qte", text=get_text("added_quantity_col"), anchor="center"); self.historique_tree.column("qte", anchor="center", width=150)
        self.historique_tree.heading("user", text=get_text("user_col"), anchor="center"); self.historique_tree.column("user", anchor="center", width=150)
        self.historique_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_hist = ttk.Scrollbar(historique_frame, orient="vertical", command=self.historique_tree.yview)
        scrollbar_hist.grid(row=0, column=1, sticky="ns")
        self.historique_tree.configure(yscrollcommand=scrollbar_hist.set)

    def charger_donnees_page(self):
        self.charger_produits_liste()
        self.vider_formulaire()

    def vider_formulaire(self):
        self.selected_produit = None
        self.nom_produit_var.set(get_text("select_product_placeholder"))
        self.qte_var.set("")
        self.prix_var.set("")
        self.fournisseur_var.set("")
        self.label_prix.grid_remove()
        self.prix_entry.grid_remove()
        self.label_fournisseur.grid_remove()
        self.fournisseur_combo.grid_remove()
        for row in self.historique_tree.get_children():
            self.historique_tree.delete(row)

    def on_produit_select(self, event=None):
        selection = self.produits_tree.selection()
        if not selection: return
        produit_id = selection[0]
        produit_data = execute_query("SELECT id, nom, origine, prix_achat FROM produits WHERE id = ?", (produit_id,), fetch='one')
        if not produit_data: return

        self.selected_produit = {'id': produit_data[0], 'nom': produit_data[1], 'origine': produit_data[2], 'prix_achat': produit_data[3]}
        self.nom_produit_var.set(self.selected_produit['nom'])
        self.qte_var.set("1")
        self.fournisseur_var.set("")

        if self.selected_produit['origine'] == 'achete':
            self.prix_var.set(str(int(self.selected_produit['prix_achat'] or 0)))
            self.label_prix.grid(row=1, column=5, padx=5, pady=5, sticky="w")
            self.prix_entry.grid(row=1, column=4, padx=5, pady=5)
            self.label_fournisseur.grid(row=1, column=3, padx=5, pady=5, sticky="w")
            self.fournisseur_combo.grid(row=1, column=2, padx=5, pady=5)
        else:
            self.prix_var.set("")
            self.label_prix.grid_remove(); self.prix_entry.grid_remove()
            self.label_fournisseur.grid_remove(); self.fournisseur_combo.grid_remove()
        
        self.charger_historique()

    def valider_ajout(self):
        if not self.selected_produit:
            messagebox.showerror(get_text("error"), get_text("select_product_error"), parent=self)
            return
        try:
            quantite = int(self.qte_var.get())
            if quantite <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(get_text("error"), get_text("enter_valid_quantity_error"), parent=self)
            return
        
        id_produit = self.selected_produit['id']
        nom_produit = self.selected_produit['nom']
        user_id = self.main_controller.user_id
        fournisseur_id, prix_unitaire = None, 0

        if self.selected_produit['origine'] == 'achete':
            nom_fournisseur = self.fournisseur_var.get()
            if not nom_fournisseur:
                messagebox.showerror(get_text("error"), get_text("select_supplier_error"), parent=self)
                return
            
            fournisseur_id = self.fournisseurs_map.get(nom_fournisseur)
            prix_unitaire = float(self.prix_var.get())
            cout_total = quantite * prix_unitaire
            
            execute_query("UPDATE partenaires SET solde_credit = solde_credit - ? WHERE id = ?", (cout_total, fournisseur_id))
            execute_query("UPDATE produits SET prix_achat = ? WHERE id = ?", (prix_unitaire, id_produit))
        
        execute_query("INSERT INTO stock_entries (produit_id, quantite_ajoutee, partenaire_id, date_ajout, user_id, prix_achat_unitaire) VALUES (?, ?, ?, datetime('now', 'localtime'), ?, ?)",
                      (id_produit, quantite, fournisseur_id, user_id, prix_unitaire))
        
        execute_query("UPDATE produits SET stock = stock + ? WHERE id = ?", (quantite, id_produit))
        messagebox.showinfo(get_text("success"), get_text("stock_update_success").format(product_name=nom_produit))
        self.charger_donnees_page()
    
    def charger_produits_liste(self):
        for row in self.produits_tree.get_children(): self.produits_tree.delete(row)
        produits = execute_query("SELECT id, nom, stock FROM produits ORDER BY nom", fetch='all') or []
        for pid, nom, stock in produits:
            self.produits_tree.insert("", "end", iid=pid, values=(int(stock or 0), nom))

    def charger_historique(self):
        for row in self.historique_tree.get_children(): self.historique_tree.delete(row)
        if not self.selected_produit: return
        query = "SELECT se.date_ajout, se.quantite_ajoutee, u.username FROM stock_entries se LEFT JOIN users u ON se.user_id = u.id WHERE se.produit_id = ? ORDER BY se.date_ajout DESC LIMIT 50"
        historique = execute_query(query, (self.selected_produit['id'],), fetch='all') or []
        for date, qte, user in historique:
            date_formattee = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            self.historique_tree.insert("", "end", values=(user or "N/A", int(qte), date_formattee))
            
    def open_popup(self, popup_class, target_var):
        new_value = popup_class(self, initial_value=target_var.get()).show()
        if new_value is not None:
            target_var.set(new_value)