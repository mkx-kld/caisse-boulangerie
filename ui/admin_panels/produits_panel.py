# Fichier: ui/admin_panels/produits_panel.py
# Version 4.1 - Entièrement traduite via get_text

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk, ImageOps

from database.db_manager import execute_query
from ui.components.app_dialogs import GestionCategoriesWindow # sera déplacé dans product_dialogs
from ui.components.input_popups import CalculatorPopup, KeyboardPopup
from translations import get_text

class ProduitsPanel(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller
        self.photo_path = None
        self.selected_produit_id = None
        self.all_products_map = {}

        # Dictionnaires de traduction
        self.type_display_map = {get_text("product_type_sale"): "vente", get_text("product_type_consumption"): "consommation"}
        self.type_reverse_map = {v: k for k, v in self.type_display_map.items()}
        self.origine_display_map = {get_text("product_origin_local"): "local", get_text("product_origin_bought"): "achete"}
        self.origine_reverse_map = {v: k for k, v in self.origine_display_map.items()}
        self.mode_gestion_map = {get_text("stock_mode_permanent"): "permanent", get_text("stock_mode_daily"): "quotidien"}
        self.mode_gestion_reverse_map = {v: k for k, v in self.mode_gestion_map.items()}
        
        style = ttk.Style(self)
        style.configure("TEntry", font=("Cairo", 14), padding=5)
        style.configure("TCombobox", font=("Cairo", 14), padding=5)
        self.option_add('*TCombobox*Listbox.font', ('Cairo', 14))
        style.configure("Treeview", font=("Cairo", 14), rowheight=35)
        style.configure("Treeview.Heading", font=("Cairo", 16, "bold"))
        style.map('Treeview', background=[('selected', '#3498db')])
        
        self.creer_widgets()
        self.charger_donnees_initiales()

    def creer_widgets(self):
        tk.Label(self, text=get_text("products_panel_title"), font=("Cairo", 32, "bold"), bg="#eaf0f6", fg="#2c3e50").pack(pady=(20, 10))
        
        main_form_frame = tk.Frame(self, bg="#eaf0f6")
        main_form_frame.pack(fill="x", padx=25, pady=10)
        main_form_frame.columnconfigure(0, weight=1)
        
        form_fields_frame = tk.LabelFrame(main_form_frame, text=f" {get_text('product_form_title')} ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=10, pady=10)
        form_fields_frame.grid(row=0, column=0, sticky="nsew")
        form_fields_frame.columnconfigure(1, weight=1)

        self.creer_champs_formulaire(form_fields_frame)
        
        photo_frame = tk.Frame(main_form_frame, bg="white", bd=1, relief="solid")
        photo_frame.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self.photo_label = tk.Label(photo_frame, text=get_text("no_photo"), font=("Cairo", 14), bg="#ecf0f1", width=20, height=10)
        self.photo_label.pack(padx=10, pady=10)
        tk.Button(photo_frame, text=get_text("choose_photo"), font=("Cairo", 14, "bold"), command=self.choisir_photo).pack(padx=10, pady=(0, 10), fill="x")

        button_frame = tk.Frame(self, bg="#eaf0f6")
        button_frame.pack(pady=20)
        btn_config = {'font': ("Cairo", 14, "bold"), 'fg': 'white', 'relief': 'flat', 'width': 15, 'pady': 8}
        tk.Button(button_frame, text=get_text("clear_fields_button"), bg="#95a5a6", **btn_config, command=self.vider_champs).pack(side="right", padx=10)
        tk.Button(button_frame, text=get_text("delete_selected_button"), bg="#c0392b", **btn_config, command=self.supprimer_produit).pack(side="right", padx=10)
        tk.Button(button_frame, text=get_text("edit_selected_button"), bg="#3498db", **btn_config, command=self.modifier_produit).pack(side="right", padx=10)
        tk.Button(button_frame, text=get_text("add_product_button"), bg="#27ae60", **btn_config, command=self.ajouter_produit).pack(side="right", padx=10)

        tree_container = tk.LabelFrame(self, text=f" {get_text('product_list_title_admin')} ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", bd=2, relief="groove")
        tree_container.pack(padx=25, pady=(0, 20), fill="both", expand=True)
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_container, columns=("composition", "stock", "prix_vente", "nom"), show="headings")
        self.tree.heading("nom", text=get_text("col_name"), anchor="e"); self.tree.column("nom", anchor="e", width=400)
        self.tree.heading("prix_vente", text=get_text("col_selling_price"), anchor="center"); self.tree.column("prix_vente", anchor="center", width=150)
        self.tree.heading("stock", text=get_text("col_stock"), anchor="center"); self.tree.column("stock", anchor="center", width=150)
        self.tree.heading("composition", text=get_text("col_composition"), anchor="e"); self.tree.column("composition", anchor="e", width=300)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def creer_champs_formulaire(self, parent):
        font_label = ("Cairo", 14); font_entry = ("Cairo", 12)
        parent.columnconfigure(1, weight=1)

        self.nom_var = tk.StringVar(); self.prix_vente_var = tk.StringVar(); self.prix_achat_var = tk.StringVar()
        self.categorie_var = tk.StringVar(); self.type_var = tk.StringVar(); self.origine_var = tk.StringVar()
        self.mode_gestion_var = tk.StringVar(); self.ingredient_var = tk.StringVar(); self.qte_ingredient_var = tk.StringVar()

        row = 0
        tk.Label(parent, text=get_text("product_name"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        ttk.Entry(parent, textvariable=self.nom_var, font=font_entry, justify="right").grid(row=row, column=1, columnspan=2, sticky="ew", padx=5)
        tk.Button(parent, text="✏️", font=font_entry, command=lambda: self.open_popup(KeyboardPopup, self.nom_var)).grid(row=row, column=0, padx=(5,0))
        row += 1

        tk.Label(parent, text=get_text("selling_price"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        ttk.Entry(parent, textvariable=self.prix_vente_var, font=font_entry, justify="right").grid(row=row, column=1, columnspan=2, sticky="ew", padx=5)
        tk.Button(parent, text="✏️", font=font_entry, command=lambda: self.open_popup(CalculatorPopup, self.prix_vente_var)).grid(row=row, column=0, padx=(5,0))
        row += 1
        
        recette_frame = tk.LabelFrame(parent, text=f" {get_text('product_composition_title')} ", font=("Cairo", 14, "bold"), bg="white", padx=10, pady=10)
        recette_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
        recette_frame.columnconfigure(1, weight=1)
        tk.Label(recette_frame, text=get_text("composed_of"), font=font_label, bg="white").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.ingredient_combo = ttk.Combobox(recette_frame, textvariable=self.ingredient_var, font=font_entry, justify="right", state="readonly")
        self.ingredient_combo.grid(row=0, column=1, sticky="ew")
        tk.Label(recette_frame, text=get_text("quantity_used"), font=font_label, bg="white").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        qte_entry = ttk.Entry(recette_frame, textvariable=self.qte_ingredient_var, font=font_entry, justify="right")
        qte_entry.grid(row=1, column=1, sticky="ew")
        tk.Button(recette_frame, text="✏️", font=font_entry, command=lambda: self.open_popup(CalculatorPopup, self.qte_ingredient_var)).grid(row=1, column=0, padx=(5,0))
        row += 1

        tk.Label(parent, text=get_text("product_origin"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        self.origine_combo = ttk.Combobox(parent, textvariable=self.origine_var, font=font_entry, justify="right", state="readonly", values=list(self.origine_display_map.keys()))
        self.origine_combo.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1

        tk.Label(parent, text=get_text("purchase_price"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        ttk.Entry(parent, textvariable=self.prix_achat_var, font=font_entry, justify="right").grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        tk.Button(parent, text="✏️", font=font_entry, command=lambda: self.open_popup(CalculatorPopup, self.prix_achat_var)).grid(row=row, column=0, padx=(5,0))
        row += 1

        tk.Label(parent, text=get_text("product_category"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        cat_frame = tk.Frame(parent, bg="white")
        cat_frame.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        cat_frame.columnconfigure(1, weight=1)
        tk.Button(cat_frame, text="⚙️", font=("Arial", 14), command=self.ouvrir_gestion_categories, relief="flat", bg="#95a5a6", fg="white").grid(row=0, column=0, padx=(0, 10))
        self.categorie_combo = ttk.Combobox(cat_frame, textvariable=self.categorie_var, font=font_entry, justify="right", state="readonly")
        self.categorie_combo.grid(row=0, column=1, sticky="ew")
        row += 1

        tk.Label(parent, text=get_text("product_type"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        self.type_combo = ttk.Combobox(parent, textvariable=self.type_var, font=font_entry, justify="right", state="readonly", values=list(self.type_display_map.keys()))
        self.type_combo.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1

        tk.Label(parent, text=get_text("stock_management_mode"), font=font_label, bg="white").grid(row=row, column=3, padx=5, pady=5, sticky="e")
        self.mode_gestion_combo = ttk.Combobox(parent, textvariable=self.mode_gestion_var, font=font_entry, justify="right", state="readonly", values=list(self.mode_gestion_map.keys()))
        self.mode_gestion_combo.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

    def charger_donnees_initiales(self):
        self.charger_categories()
        self.charger_all_products_for_recipe()
        self.charger_produits()
        self.vider_champs()

    def charger_all_products_for_recipe(self):
        all_prods = execute_query("SELECT id, nom FROM produits ORDER BY nom", fetch='all') or []
        self.all_products_map = {name: prod_id for prod_id, name in all_prods}
        self.ingredient_combo['values'] = [get_text("no_ingredient")] + list(self.all_products_map.keys())


    def charger_produits(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        query = """
            SELECT p.id, p.nom, p.prix, p.stock, ing.nom, comp.quantite_ingredient
            FROM produits p
            LEFT JOIN produit_composition comp ON p.id = comp.produit_final_id
            LEFT JOIN produits ing ON comp.ingredient_id = ing.id
            ORDER BY p.nom
        """
        rows = execute_query(query, fetch='all') or []
        for prod_id, nom, prix, stock, ing_nom, ing_qte in rows:
            composition_text = f"{ing_qte} x {ing_nom}" if ing_nom else "—"
            self.tree.insert("", "end", iid=prod_id, values=(composition_text, stock, int(prix or 0), nom))
    
    def on_item_select(self, event=None):
        selection = self.tree.selection()
        if not selection: return
        self.selected_produit_id = selection[0]
        
        prod_query = "SELECT * FROM produits WHERE id=?"
        p = execute_query(prod_query, (self.selected_produit_id,), fetch='one')
        if not p: return

        self.vider_champs(keep_selection=True)
        
        self.nom_var.set(p[1])
        self.prix_achat_var.set(p[2] or "")
        self.prix_vente_var.set(p[3] or "")
        
        cat_name = execute_query("SELECT nom FROM categories WHERE id=?", (p[5],), fetch='one')
        if cat_name: self.categorie_var.set(cat_name[0])
        
        self.type_var.set(self.type_reverse_map.get(p[6], ""))
        self.origine_var.set(self.origine_reverse_map.get(p[7], ""))
        self.photo_path = p[8]
        self.mode_gestion_var.set(self.mode_gestion_reverse_map.get(p[10], ""))
        
        # Charger la recette
        comp_query = "SELECT ingredient_id, quantite_ingredient FROM produit_composition WHERE produit_final_id = ?"
        comp_res = execute_query(comp_query, (self.selected_produit_id,), fetch='one')
        if comp_res:
            ing_id, ing_qte = comp_res
            ing_name = next((name for name, pid in self.all_products_map.items() if pid == ing_id), "")
            self.ingredient_var.set(ing_name)
            self.qte_ingredient_var.set(ing_qte)
        else:
            self.ingredient_var.set("(لا يوجد)")
            self.qte_ingredient_var.set("")
        
        self.afficher_photo()

    def _get_form_data(self):
        data = {}
        data['nom'] = self.nom_var.get().strip()
        data['prix_vente'] = self.prix_vente_var.get().strip() or '0'
        data['prix_achat'] = self.prix_achat_var.get().strip() or '0'
        
        cat_name = self.categorie_var.get()
        cat_res = execute_query("SELECT id FROM categories WHERE nom=?", (cat_name,), fetch='one')
        data['categorie_id'] = cat_res[0] if cat_res else None
        
        data['type_db'] = self.type_display_map.get(self.type_var.get())
        data['origine_db'] = self.origine_display_map.get(self.origine_var.get())
        data['mode_gestion_db'] = self.mode_gestion_map.get(self.mode_gestion_var.get())
        
        # Données de la recette
        data['ingredient_name'] = self.ingredient_var.get()
        data['qte_ingredient'] = self.qte_ingredient_var.get().strip()
        
        return data

    def _save_product(self, query, params):
        produit_id = execute_query(query, params)
        if not produit_id:
            produit_id = self.selected_produit_id if "UPDATE" in query.upper() else None
        if not produit_id:
            messagebox.showerror(get_text("error"), "Impossible de sauvegarder le produit.", parent=self)
            return
        execute_query("DELETE FROM produit_composition WHERE produit_final_id = ?", (produit_id,))
        data = self._get_form_data()
        ing_name = data['ingredient_name']
        ing_qte = data['qte_ingredient']
        if ing_name and ing_name != get_text("no_ingredient") and ing_qte:
            ing_id = self.all_products_map.get(ing_name)
            if ing_id:
                try:
                    qte_float = float(ing_qte)
                    execute_query("INSERT INTO produit_composition (produit_final_id, ingredient_id, quantite_ingredient) VALUES (?, ?, ?)", (produit_id, ing_id, qte_float))
                except ValueError:
                    messagebox.showwarning(get_text("warning"), get_text("invalid_ingredient_quantity_warning"), parent=self)

    def ajouter_produit(self):
        data = self._get_form_data()
        if not data['nom']: messagebox.showwarning(get_text("warning"), get_text("name_required_warning"), parent=self); return
        query = "INSERT INTO produits (nom, prix, prix_achat, categorie_id, origine, type, mode_gestion, photo_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        params = (data['nom'], data['prix_vente'], data['prix_achat'], data['categorie_id'], data['origine_db'], data['type_db'], data['mode_gestion_db'], self.photo_path)
        self._save_product(query, params)
        messagebox.showinfo(get_text("success"), get_text("product_added_success"), parent=self)
        self.charger_donnees_initiales()

    def modifier_produit(self):
        if not self.selected_produit_id: messagebox.showwarning(get_text("warning"), get_text("select_product_to_edit_warning"), parent=self); return
        data = self._get_form_data()
        if not data['nom']: messagebox.showwarning(get_text("warning"), get_text("name_required_warning"), parent=self); return
        query = "UPDATE produits SET nom=?, prix=?, prix_achat=?, categorie_id=?, origine=?, type=?, mode_gestion=?, photo_path=? WHERE id=?"
        params = (data['nom'], data['prix_vente'], data['prix_achat'], data['categorie_id'], data['origine_db'], data['type_db'], data['mode_gestion_db'], self.photo_path, self.selected_produit_id)
        self._save_product(query, params)
        messagebox.showinfo(get_text("success"), get_text("product_edited_success"), parent=self)
        self.charger_donnees_initiales()

    def vider_champs(self, keep_selection=False):
        if not keep_selection:
            self.selected_produit_id = None
            if self.tree.selection(): self.tree.selection_remove(self.tree.selection()[0])
        
        self.photo_path = None
        self.nom_var.set(""); self.prix_vente_var.set(""); self.prix_achat_var.set("")
        self.categorie_var.set(""); self.type_var.set(""); self.origine_var.set("")
        self.mode_gestion_var.set(""); self.ingredient_var.set("(لا يوجد)"); self.qte_ingredient_var.set("")
        
        self.vider_apercu_photo()

    # --- Fonctions utilitaires (inchangées) ---
    def open_popup(self, popup_class, target_var):
        new_value = popup_class(self, initial_value=target_var.get()).show()
        if new_value is not None: target_var.set(new_value)

    def supprimer_produit(self):
        if not self.selected_produit_id: messagebox.showwarning(get_text("warning"), get_text("select_product_to_delete_warning"), parent=self); return
        if messagebox.askyesno(get_text("confirm_delete_title"), get_text("product_delete_confirm"), parent=self):
            execute_query("DELETE FROM produits WHERE id=?", (self.selected_produit_id,))
            messagebox.showinfo(get_text("success"), get_text("product_deleted_success"), parent=self)
            self.charger_donnees_initiales()

    def choisir_photo(self):
        filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if filepath: self.photo_path = filepath; self.afficher_photo()

    def afficher_photo(self):
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                img = Image.open(self.photo_path); img = ImageOps.exif_transpose(img); img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.photo_label.config(image=photo, text=""); self.photo_label.image = photo
            except Exception: self.vider_apercu_photo()
        else: self.vider_apercu_photo()

    def vider_apercu_photo(self):
        self.photo_label.config(image="", text="لا توجد صورة"); self.photo_label.image = None
    
    def ouvrir_gestion_categories(self):
        GestionCategoriesWindow(self)

    def charger_categories(self):
        rows = execute_query("SELECT nom FROM categories ORDER BY nom ASC", fetch='all')
        categories_list = [row[0] for row in rows] if rows else []
        self.categorie_combo['values'] = categories_list
