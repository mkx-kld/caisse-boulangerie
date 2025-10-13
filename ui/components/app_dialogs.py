# Fichier: ui/components/app_dialogs.py
# Version 2.0 - Ajout de la fenêtre de transformation de stock

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from PIL import Image, ImageTk, ImageOps

from translations import get_text 

# Imports depuis nos nouveaux modules
from .base_toplevel import DynamicToplevel
from .input_popups import CalculatorPopup, KeyboardPopup, CalendarPopup
from config import FONDS_DE_CAISSE
from database.db_manager import execute_query, get_prix_pour_partenaire

from utils import format_currency


# --- NOUVELLE FENÊTRE: Transformation de Stock ---
class TransformationStockWindow(DynamicToplevel):
    """
    Fenêtre pour transformer une quantité d'un produit de stock en un autre.
    Ex: Transformer 20 "Baguette Nature" en 20 "Pain au Sésame".
    """
    def __init__(self, parent):
        super().__init__(parent, title="تحويل المخزون")
        self.parent = parent
        # Récupérer le contrôleur principal pour l'ID utilisateur
        self.main_controller = self.parent.main_controller

        # Charger uniquement les produits marqués comme "produit de stock"
        stock_prods = execute_query("SELECT id, nom FROM produits WHERE is_stock_product = 1 ORDER BY nom", fetch='all') or []
        self.stock_products_map = {name: prod_id for prod_id, name in stock_prods}
        product_names = list(self.stock_products_map.keys())

        # --- Interface ---
        tk.Label(self, text="تحويل منتج إلى آخر", font=("Cairo", 22, "bold"), bg="#eaf0f6").pack(pady=20, padx=40)
        
        form_frame = tk.Frame(self, bg="#eaf0f6", padx=20, pady=10)
        form_frame.pack(fill="x")
        form_frame.columnconfigure(1, weight=1)

        # Produit Source
        tk.Label(form_frame, text="من المنتج (المصدر):", font=("Cairo", 16), bg="#eaf0f6").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.source_var = tk.StringVar()
        source_combo = ttk.Combobox(form_frame, textvariable=self.source_var, values=product_names, state="readonly", font=("Cairo", 14), justify="right")
        source_combo.grid(row=0, column=1, sticky="ew")

        # Quantité
        tk.Label(form_frame, text="الكمية المراد تحويلها:", font=("Cairo", 16), bg="#eaf0f6").grid(row=1, column=2, padx=10, pady=10, sticky="e")
        qte_frame = tk.Frame(form_frame, bg="#eaf0f6")
        qte_frame.grid(row=1, column=1, sticky="ew")
        qte_frame.columnconfigure(0, weight=1)
        self.qte_var = tk.StringVar()
        qte_entry = tk.Entry(qte_frame, textvariable=self.qte_var, font=("Cairo", 14), justify="center", relief="solid", bd=1)
        qte_entry.grid(row=0, column=0, sticky="ew")
        tk.Button(qte_frame, text="✏️", font=("Cairo", 12), command=lambda: self.open_popup(CalculatorPopup, self.qte_var)).grid(row=0, column=1, padx=(5,0))

        # Produit Destination
        tk.Label(form_frame, text="إلى المنتج (الوجهة):", font=("Cairo", 16), bg="#eaf0f6").grid(row=2, column=2, padx=10, pady=10, sticky="e")
        self.dest_var = tk.StringVar()
        dest_combo = ttk.Combobox(form_frame, textvariable=self.dest_var, values=product_names, state="readonly", font=("Cairo", 14), justify="right")
        dest_combo.grid(row=2, column=1, sticky="ew")

        # Bouton de validation
        tk.Button(self, text="✔️ تأكيد التحويل", font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", relief="flat", height=2, command=self.valider).pack(pady=20, padx=20, fill="x")
        
        self.center_window()

    def open_popup(self, popup_class, target_var):
        new_value = popup_class(self, initial_value=target_var.get()).show()
        if new_value is not None and new_value.isdigit():
            target_var.set(new_value)

    def valider(self):
        source_name = self.source_var.get()
        dest_name = self.dest_var.get()
        qte_str = self.qte_var.get()

        # --- Validation des entrées ---
        if not all([source_name, dest_name, qte_str]):
            messagebox.showwarning("حقول فارغة", "الرجاء ملء جميع الحقول.", parent=self)
            return
        
        if source_name == dest_name:
            messagebox.showerror("خطأ", "لا يمكن تحويل المنتج إلى نفسه.", parent=self)
            return

        try:
            quantite = int(qte_str)
            if quantite <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("خطأ", "الرجاء إدخال كمية صحيحة (رقم أكبر من صفر).", parent=self)
            return

        source_id = self.stock_products_map.get(source_name)
        dest_id = self.stock_products_map.get(dest_name)

        # --- Vérification du stock disponible ---
        current_stock_res = execute_query("SELECT stock FROM produits WHERE id = ?", (source_id,), fetch='one')
        if not current_stock_res or current_stock_res[0] < quantite:
            messagebox.showerror("مخزون غير كاف", f"المخزون الحالي لـ '{source_name}' غير كافٍ للتحويل.", parent=self)
            return

        # --- Exécution des requêtes ---
        if messagebox.askyesno("تأكيد التحويل", f"هل أنت متأكد من تحويل {quantite} من '{source_name}' إلى '{dest_name}'؟", parent=self):
            # 1. Soustraire du stock source
            execute_query("UPDATE produits SET stock = stock - ? WHERE id = ?", (quantite, source_id))
            
            # 2. Ajouter au stock destination
            execute_query("UPDATE produits SET stock = stock + ? WHERE id = ?", (quantite, dest_id))
            
            # 3. Enregistrer la transaction pour la traçabilité
            user_id = self.main_controller.user_id
            date_trans = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            execute_query(
                "INSERT INTO stock_transformations (source_produit_id, destination_produit_id, quantite, date_transformation, user_id) VALUES (?, ?, ?, ?, ?)",
                (source_id, dest_id, quantite, date_trans, user_id)
            )

            messagebox.showinfo("نجاح", "تم التحويل بنجاح.", parent=self)
            self.parent.charger_donnees_page() # Rafraîchir le panneau parent
            self.destroy()

# --- Dialogues de Vendeur / Clôture ---

class CustomMessageBox(DynamicToplevel):
    """Boîte de dialogue de confirmation personnalisée (Oui/Non)."""
    def __init__(self, parent, title, message):
        super().__init__(parent, title=title)
        tk.Label(self, text=message, font=("Cairo", 18), bg="#eaf0f6", wraplength=400).pack(pady=30, padx=20)
        btn_frame = tk.Frame(self, bg="#eaf0f6")
        btn_frame.pack(pady=20)
        btn_config = {'font': ("Cairo", 16, "bold"), 'fg': 'white', 'width': 10, 'pady': 10, 'relief':'flat'}
        tk.Button(btn_frame, text="نعم", bg="#27ae60", **btn_config, command=lambda: self.on_ok(True)).pack(side="right", padx=15)
        tk.Button(btn_frame, text="لا", bg="#c0392b", **btn_config, command=self.on_cancel).pack(side="right", padx=15)
        self.center_window()

class DemandeClotureWindow(DynamicToplevel):
    """Fenêtre pour choisir le type de clôture (service ou journée)."""
    def __init__(self, parent):
        super().__init__(parent, title="اختيار نوع الإغلاق")
        tk.Label(self, text="ما هو نوع الإغلاق الذي تريد القيام به؟", font=("Cairo", 18, "bold"), bg="#eaf0f6").pack(pady=30)
        btn_frame = tk.Frame(self, bg="#eaf0f6")
        btn_frame.pack(pady=20, fill="x", expand=True)
        btn_config = {'font': ("Cairo", 16, "bold"), 'fg': 'white', 'pady': 15, 'relief':'flat'}
        tk.Button(btn_frame, text="إنهاء الخدمة (تغيير المستخدم)", bg="#3498db", **btn_config, command=lambda: self.on_ok('service')).pack(pady=10, fill="x", padx=50)
        tk.Button(btn_frame, text="الإغلاق النهائي لليوم (تقرير المدير)", bg="#c0392b", **btn_config, command=lambda: self.on_ok('journee')).pack(pady=10, fill="x", padx=50)
        self.center_window()

class RapportClotureWindow(DynamicToplevel):
    """Fenêtre affichant le rapport de clôture."""
    def __init__(self, parent, data):
        super().__init__(parent, title=data['titre_rapport'])
        self.geometry("600x650")
        self.configure(bg="#ffffff")
        header_font = ("Cairo", 26, "bold"); label_font = ("Cairo", 20); value_font = ("Cairo", 20, "bold"); total_font = ("Cairo", 24, "bold")
        tk.Label(self, text=data['titre_rapport'], font=header_font, bg="white", fg="#2c3e50").pack(pady=25)
        container = tk.Frame(self, bg="white")
        container.pack(pady=15, padx=40, fill="both", expand=True)
        container.columnconfigure(0, weight=1); container.columnconfigure(1, weight=1)
        info = []
        if data['nom_vendeur']: info.append(("👤 اسم البائع", data['nom_vendeur']))
        info.extend([("📅 التاريخ", data['date']), ("⏰ وقت الإغلاق", data['heure']), ("💰 صندوق النقد الأولي", f"{data['fonds_de_caisse']:.2f} د.ج"), ("📈 إجمالي المبيعات", f"+ {data['total_ventes']:.2f} د.ج"), ("📉 إجمالي المصاريف", f"{data['total_depenses']:.2f} د.ج")])
        for i, (label_text, value_text) in enumerate(info):
            tk.Label(container, text=label_text, font=label_font, bg="white", fg="#34495e").grid(row=i, column=1, sticky="e", pady=8, padx=10)
            tk.Label(container, text=value_text, font=value_font, bg="white", fg="#2c3e50").grid(row=i, column=0, sticky="e", pady=8, padx=10)
        ttk.Separator(container, orient='horizontal').grid(row=len(info), column=0, columnspan=2, sticky='ew', pady=20)
        tk.Label(container, text="💵 الرصيد النظري في الصندوق", font=total_font, bg="white", fg="#16a085").grid(row=len(info)+1, column=1, sticky="e", pady=10)
        tk.Label(container, text=f"{data['solde_final']:.2f} د.ج", font=total_font, bg="white", fg="#16a085").grid(row=len(info)+1, column=0, sticky="e", pady=10, padx=10)
        tk.Button(self, text="إغلاق", font=("Cairo", 18, "bold"), bg="#3498db", fg="white", relief="flat", command=self.destroy).pack(pady=25, ipadx=30)
        self.center_window()

class AjouterDepenseWindow(DynamicToplevel):
    """Fenêtre pour ajouter une dépense manuelle."""
    def __init__(self, parent, controller):
        super().__init__(parent, title="إضافة مصروف جديد")
        self.parent = parent; self.controller = controller
        tk.Label(self, text="تسجيل مصروف يدوي", font=("Cairo", 22, "bold"), bg="#eaf0f6").pack(pady=20)
        form_frame = tk.Frame(self, bg="#eaf0f6"); form_frame.pack(pady=10, padx=30)
        entry_font = ("Cairo", 16)
        tk.Label(form_frame, text="الوصف (السبب)", font=entry_font, bg="#eaf0f6").pack(anchor="e")
        self.entry_description = tk.Entry(form_frame, font=entry_font, justify="right", width=30); self.entry_description.pack(pady=5, ipady=5)
        tk.Label(form_frame, text="المبلغ (د.ج)", font=entry_font, bg="#eaf0f6").pack(anchor="e", pady=(15, 0))
        self.entry_montant = tk.Entry(form_frame, font=entry_font, justify="right", width=30); self.entry_montant.pack(pady=5, ipady=5)
        btn_frame = tk.Frame(self, bg="#eaf0f6"); btn_frame.pack(pady=25)
        tk.Button(btn_frame, text="✔️ تسجيل المصروف", font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", width=15, command=self.valider).pack(side="right", padx=10)
        tk.Button(btn_frame, text="إلغاء", font=("Cairo", 14, "bold"), bg="#c0392b", fg="white", width=15, command=self.destroy).pack(side="right", padx=10)
        self.center_window()

    def valider(self):
        description = self.entry_description.get().strip(); montant_str = self.entry_montant.get().strip()
        if not description or not montant_str: messagebox.showwarning("حقول فارغة", "الرجاء إدخال الوصف والمبلغ.", parent=self); return
        try:
            montant = float(montant_str)
            if montant <= 0: raise ValueError
        except ValueError: messagebox.showerror("خطأ", "الرجاء إدخال مبلغ صحيح (رقم أكبر من صفر).", parent=self); return
        id_vendeur_actif = self.controller.user_id
        if id_vendeur_actif is None: messagebox.showerror("Erreur Critique", "Aucun utilisateur n'est connecté.", parent=self); return
        montant_negatif = -abs(montant)
        query = "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)"
        params = (description, montant_negatif, 'Dépense Manuelle', id_vendeur_actif)
        execute_query(query, params)
        messagebox.showinfo("نجاح", "تم تسجيل المصروف بنجاح.", parent=self)
        self.destroy()

class InvendusWindow(DynamicToplevel):
    """Fenêtre pour déclarer les produits invendus en fin de journée."""
    def __init__(self, parent):
        super().__init__(parent, title="تسجيل المنتجات غير المباعة")
        self.entries = {}
        tk.Label(self, text="الرجاء إدخال الكمية المتبقية لكل منتج", font=("Cairo", 20, "bold"), bg="#eaf0f6").pack(pady=20, padx=40)
        canvas_frame = tk.Frame(self, bg="#eaf0f6"); canvas_frame.pack(pady=10, padx=20, fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0); scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview); scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        query = "SELECT id, nom, prix_achat, stock FROM produits WHERE mode_gestion = 'quotidien' ORDER BY nom"
        produits_invendus = execute_query(query, fetch='all') or []
        if not produits_invendus: tk.Label(scrollable_frame, text="لا توجد منتجات ذات إدارة يومية.", font=("Cairo", 16), bg="white").pack(pady=50)
        else:
            for prod_id, nom, prix_achat, stock in produits_invendus:
                row_frame = tk.Frame(scrollable_frame, bg="white"); row_frame.pack(fill="x", pady=5, padx=10)
                tk.Label(row_frame, text=nom, font=("Cairo", 16), bg="white").pack(side="right", padx=10)
                entry = tk.Entry(row_frame, font=("Cairo", 16), width=10, justify="center"); entry.insert(0, str(stock)); entry.pack(side="left", padx=10)
                self.entries[prod_id] = {'entry': entry, 'prix_achat': prix_achat, 'nom': nom}
        btn_frame = tk.Frame(self, bg="#eaf0f6"); btn_frame.pack(pady=20, padx=40, fill="x")
        tk.Button(btn_frame, text="✔️ تأكيد وتسجيل الخسائر", font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", relief="flat", command=self.valider, height=2).pack(fill="x")
        self.center_window()

    def valider(self):
        resultat = []
        try:
            for prod_id, data in self.entries.items():
                qte_restante = int(data['entry'].get())
                if qte_restante > 0:
                    resultat.append({'id': prod_id, 'nom': data['nom'], 'qte': qte_restante, 'cout_perte': qte_restante * (data['prix_achat'] or 0)})
            self.on_ok(resultat)
        except ValueError: messagebox.showerror("خطأ", "الرجاء إدخال أرقام صحيحة للكميات.", parent=self)

# --- Dialogues de Gestion (Depenses, Employes, etc.) ---

class PayerSalaireWindow(DynamicToplevel):
    """Fenêtre pour enregistrer le paiement d'un salaire."""
    def __init__(self, parent):
        super().__init__(parent, title="دفع راتب")
        self.parent = parent
        self.employes = execute_query("SELECT id, nom, salaire FROM employes ORDER BY nom", fetch='all') or []
        employe_names = [emp[1] for emp in self.employes]
        
        tk.Label(self, text="تسجيل دفع راتب", font=("Cairo", 22, "bold"), bg="#eaf0f6").pack(pady=20, padx=40)
        form_frame = tk.Frame(self, bg="#eaf0f6"); form_frame.pack(pady=10, padx=40)
        
        tk.Label(form_frame, text="اختر الموظف", font=("Cairo", 16), bg="#eaf0f6").pack()
        self.combo_employes = ttk.Combobox(form_frame, values=employe_names, font=("Cairo", 14), state="readonly", justify="right", width=30)
        self.combo_employes.pack(pady=5, ipady=5)
        self.combo_employes.bind("<<ComboboxSelected>>", self.on_employe_select)

        tk.Label(form_frame, text="مبلغ الدفع (د.ج)", font=("Cairo", 16), bg="#eaf0f6").pack(pady=(15, 0))
        montant_frame = tk.Frame(form_frame, bg="#eaf0f6"); montant_frame.pack(pady=5)
        self.montant_var = tk.StringVar()
        entry_montant = tk.Entry(montant_frame, textvariable=self.montant_var, font=("Cairo", 14), justify="right", width=26, state="readonly", relief="solid", bd=1)
        entry_montant.pack(side="right", ipady=5)
        tk.Button(montant_frame, text="✏️", font=("Cairo", 14), command=self.open_calculator).pack(side="left", padx=5)

        btn_frame = tk.Frame(self, bg="#eaf0f6"); btn_frame.pack(pady=25, padx=40, fill="x")
        tk.Button(btn_frame, text="✔️ تأكيد الدفع", font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", relief="flat", command=self.valider, height=2).pack(fill="x")
        self.center_window()

    def open_calculator(self):
        new_value = CalculatorPopup(self, initial_value=self.montant_var.get()).show()
        if new_value is not None: self.montant_var.set(new_value)

    def on_employe_select(self, event):
        selected_name = self.combo_employes.get()
        for emp in self.employes:
            if emp[1] == selected_name:
                self.montant_var.set(str(int(emp[2] or 0)))
                break

    def valider(self):
        selected_name = self.combo_employes.get(); montant_str = self.montant_var.get()
        if not selected_name or not montant_str: messagebox.showwarning("حقول مطلوبة", "الرجاء اختيار موظف وإدخال مبلغ.", parent=self); return
        try:
            montant = float(montant_str)
            if montant <= 0: raise ValueError
        except ValueError: messagebox.showerror("خطأ", "الرجاء إدخال مبلغ رقمي صحيح وموجب.", parent=self); return

        employe_id = next((emp[0] for emp in self.employes if emp[1] == selected_name), None)
        id_admin = self.parent.main_controller.user_id
        description = f"دفع راتب: {selected_name}"
        montant_negatif = -abs(montant)
        
        query = "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)"
        execute_query(query, (description, montant_negatif, 'Salaire', id_admin))
        
        self.parent.charger_donnees()
        self.destroy()

class EnregistrerConsommationWindow(DynamicToplevel):
    """Fenêtre pour enregistrer une consommation interne de produit."""
    def __init__(self, parent):
        super().__init__(parent, title="تسجيل استهلاك")
        self.parent = parent
        self.produits = execute_query("SELECT id, nom, prix_achat, stock FROM produits WHERE type='consommation' ORDER BY nom", fetch='all') or []
        produit_names = [p[1] for p in self.produits]

        tk.Label(self, text="تسجيل استهلاك داخلي", font=("Cairo", 22, "bold"), bg="#eaf0f6").pack(pady=20, padx=40)
        form_frame = tk.Frame(self, bg="#eaf0f6"); form_frame.pack(pady=10, padx=40)
        
        tk.Label(form_frame, text="اختر المنتج", font=("Cairo", 16), bg="#eaf0f6").pack()
        self.combo_produits = ttk.Combobox(form_frame, values=produit_names, font=("Cairo", 14), state="readonly", justify="right", width=30)
        self.combo_produits.pack(pady=5, ipady=5)
        self.combo_produits.bind("<<ComboboxSelected>>", self.on_produit_select)

        tk.Label(form_frame, text="سعر الشراء للوحدة", font=("Cairo", 16), bg="#eaf0f6").pack(pady=(15,0))
        prix_frame = tk.Frame(form_frame, bg="#eaf0f6"); prix_frame.pack(pady=5)
        self.prix_var = tk.StringVar()
        tk.Entry(prix_frame, textvariable=self.prix_var, font=("Cairo", 14), justify="right", width=26, state="readonly", relief="solid", bd=1).pack(side="right", ipady=5)
        tk.Button(prix_frame, text="✏️", font=("Cairo", 14), command=lambda: self.open_calculator(self.prix_var)).pack(side="left", padx=5)

        tk.Label(form_frame, text="الكمية المستهلكة", font=("Cairo", 16), bg="#eaf0f6").pack(pady=(15,0))
        qte_frame = tk.Frame(form_frame, bg="#eaf0f6"); qte_frame.pack(pady=5)
        self.qte_var = tk.StringVar(value="1")
        tk.Entry(qte_frame, textvariable=self.qte_var, font=("Cairo", 14), justify="right", width=26, state="readonly", relief="solid", bd=1).pack(side="right", ipady=5)
        tk.Button(qte_frame, text="✏️", font=("Cairo", 14), command=lambda: self.open_calculator(self.qte_var)).pack(side="left", padx=5)

        btn_frame = tk.Frame(self, bg="#eaf0f6"); btn_frame.pack(pady=25, padx=40, fill="x")
        tk.Button(btn_frame, text="✔️ تأكيد الاستهلاك", font=("Cairo", 16, "bold"), bg="#8e44ad", fg="white", relief="flat", command=self.valider, height=2).pack(fill="x")
        self.center_window()

    def open_calculator(self, target_var):
        new_value = CalculatorPopup(self, initial_value=target_var.get()).show()
        if new_value is not None: target_var.set(new_value)

    def on_produit_select(self, event):
        selected_name = self.combo_produits.get()
        for p in self.produits:
            if p[1] == selected_name:
                self.prix_var.set(str(int(p[2] or 0)))
                break

    def valider(self):
        selected_name = self.combo_produits.get(); qte_str = self.qte_var.get(); prix_str = self.prix_var.get()
        if not all([selected_name, qte_str, prix_str]): messagebox.showwarning("حقول مطلوبة", "الرجاء ملء جميع الحقول.", parent=self); return
        try:
            qte = int(qte_str); prix_unitaire = float(prix_str)
            if qte <= 0 or prix_unitaire < 0: raise ValueError
        except ValueError: messagebox.showerror("خطأ", "الرجاء إدخال كمية وسعر صحيحين.", parent=self); return
        
        produit_data = next((p for p in self.produits if p[1] == selected_name), None)
        if not produit_data: return

        if qte > produit_data[3]: messagebox.showwarning("مخزون غير كاف", f"مخزون {selected_name} هو {produit_data[3]}. لا يمكن استهلاك {qte}.", parent=self); return

        id_admin = self.parent.main_controller.user_id
        cout_total = -abs(qte * prix_unitaire)
        description = f"استهلاك: {qte}x {selected_name}"
        execute_query("INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)", (description, cout_total, 'Consommation', id_admin))
        execute_query("UPDATE produits SET stock = stock - ? WHERE id = ?", (qte, produit_data[0]))
        self.parent.charger_donnees()
        self.destroy()

class TraitementMasseWindow(DynamicToplevel):
    """Fenêtre pour enregistrer plusieurs dépenses (salaires, consommations) en même temps."""
    def __init__(self, parent):
        super().__init__(parent, title="المعالجة الجماعية للمصاريف")
        self.parent = parent
        self.entries = {}
        self.geometry("800x700")

        tk.Label(self, text="تسجيل جميع المصاريف اليومية", font=("Cairo", 22, "bold"), bg="#eaf0f6").pack(pady=20, padx=40)
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=20, expand=True, fill="both")

        emp_tab = tk.Frame(notebook, bg="white"); notebook.add(emp_tab, text='  دفع الرواتب  ')
        self.creer_liste_salaire(emp_tab)
        
        cons_tab = tk.Frame(notebook, bg="white"); notebook.add(cons_tab, text='  استهلاك المنتجات  ')
        self.creer_liste_consommation(cons_tab)
        
        btn_frame = tk.Frame(self, bg="#eaf0f6"); btn_frame.pack(pady=20, padx=40, fill="x")
        tk.Button(btn_frame, text="✔️ تسجيل كل المصاريف المحددة", font=("Cairo", 18, "bold"), bg="#27ae60", fg="white", relief="flat", command=self.valider_tout, height=2).pack(fill="x")
        
    def creer_liste_salaire(self, parent_tab):
        canvas = tk.Canvas(parent_tab, bg="white", highlightthickness=0); scrollbar = ttk.Scrollbar(parent_tab, orient="vertical", command=canvas.yview); scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        
        employes = execute_query("SELECT id, nom, salaire FROM employes ORDER BY nom", fetch='all') or []
        for emp in employes:
            row = tk.Frame(scrollable_frame, bg="white"); row.pack(fill="x", pady=4, padx=10)
            tk.Label(row, text=emp[1], font=("Cairo", 14), bg="white").pack(side="right", padx=5)
            montant_var = tk.StringVar(value=str(int(emp[2] or 0)))
            tk.Entry(row, textvariable=montant_var, font=("Cairo", 14, "bold"), width=10, justify="center", relief="solid", bd=1, state="readonly").pack(side="left", padx=5)
            tk.Button(row, text="✏️", font=("Cairo", 10), command=lambda v=montant_var: self.open_calculator(v)).pack(side="left")
            self.entries[f"emp-{emp[0]}"] = {'var': montant_var, 'type': 'Salaire', 'data': emp}

    def creer_liste_consommation(self, parent_tab):
        canvas = tk.Canvas(parent_tab, bg="white", highlightthickness=0); scrollbar = ttk.Scrollbar(parent_tab, orient="vertical", command=canvas.yview); scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

        produits = execute_query("SELECT id, nom, prix_achat, stock FROM produits WHERE type='consommation' ORDER BY nom", fetch='all') or []
        for prod in produits:
            row = tk.Frame(scrollable_frame, bg="white"); row.pack(fill="x", pady=4, padx=10)
            label_text = f"{prod[1]} (المخزون: {prod[3]})"; tk.Label(row, text=label_text, font=("Cairo", 14), bg="white").pack(side="right", padx=5)
            entry_frame = tk.Frame(row, bg="white"); entry_frame.pack(side="left", padx=5)
            qte_var = tk.StringVar(value="0")
            tk.Label(entry_frame, text="كمية:", font=("Cairo", 12), bg="white").pack(side="left")
            tk.Entry(entry_frame, textvariable=qte_var, font=("Cairo", 14), width=7, justify="center", state="readonly").pack(side="left")
            tk.Button(entry_frame, text="✏️", font=("Cairo", 10), command=lambda v=qte_var: self.open_calculator(v)).pack(side="left", padx=(0,5))
            self.entries[f"prod-{prod[0]}"] = {'qte_var': qte_var, 'type': 'Consommation', 'data': prod}

    def open_calculator(self, target_var):
        new_value = CalculatorPopup(self, initial_value=target_var.get()).show()
        if new_value is not None and new_value.isdigit(): target_var.set(new_value)

    def valider_tout(self):
        depenses_a_enregistrer = []; id_admin = self.parent.main_controller.user_id
        for key, value in self.entries.items():
            try:
                if value['type'] == 'Salaire':
                    montant = float(value['var'].get())
                    if montant > 0: depenses_a_enregistrer.append({'type': 'Salaire', 'nom': f"دفع راتب: {value['data'][1]}", 'montant': montant, 'id_admin': id_admin})
                elif value['type'] == 'Consommation':
                    qte = int(value['qte_var'].get())
                    if qte > 0:
                        prod_id, nom_produit, prix_achat, stock_actuel = value['data']
                        if qte > stock_actuel: messagebox.showwarning("مخزون غير كاف", f"مخزون {nom_produit} غير كاف.", parent=self); continue
                        cout_total = qte * prix_achat
                        depenses_a_enregistrer.append({'type': 'Consommation', 'nom': f"استهلاك: {qte}x {nom_produit}", 'montant': cout_total, 'id_admin': id_admin, 'prod_id': prod_id, 'qte_consommee': qte})
            except (ValueError, TypeError): continue
        if not depenses_a_enregistrer: messagebox.showinfo("لا يوجد شيء", "لم يتم إدخال أي مصروف.", parent=self); return
        if not messagebox.askyesno("تأكيد التسجيل", f"هل أنت متأكد من تسجيل {len(depenses_a_enregistrer)} مصروف جديد؟", parent=self): return
        for depense in depenses_a_enregistrer:
            montant_negatif = -abs(depense['montant'])
            execute_query("INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?)", (depense['nom'], montant_negatif, depense['type'], depense['id_admin']))
            if depense['type'] == 'Consommation':
                execute_query("UPDATE produits SET stock = stock - ? WHERE id = ?", (depense['qte_consommee'], depense['prod_id']))
        messagebox.showinfo("نجاح", f"تم تسجيل {len(depenses_a_enregistrer)} مصروف بنجاح.", parent=self); self.parent.charger_donnees(); self.destroy()

class EmployeDetailsWindow(DynamicToplevel):
    """Fenêtre affichant les détails et l'historique de paiement d'un employé."""
    def __init__(self, parent, employe_id):
        super().__init__(parent, title="تفاصيل الموظف")
        self.parent = parent
        self.employe_id = employe_id
        self.creer_widgets()
        self.charger_donnees()
        self.center_window()

    def creer_widgets(self):
        main_frame = tk.Frame(self, bg="#f0f2f5"); main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1); main_frame.rowconfigure(1, weight=1)
        info_frame = tk.LabelFrame(main_frame, text=" معلومات شخصية ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", bd=2, relief="groove")
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.photo_label = tk.Label(info_frame, text="لا توجد صورة", font=("Cairo", 12), bg="#ecf0f1", width=15, height=8)
        self.photo_label.grid(row=0, column=2, rowspan=4, padx=20, pady=10)
        self.nom_label = tk.Label(info_frame, text="الاسم: ", font=("Cairo", 14), bg="white", anchor="e"); self.nom_label.grid(row=0, column=1, sticky="e", padx=10)
        self.poste_label = tk.Label(info_frame, text="المنصب: ", font=("Cairo", 14), bg="white", anchor="e"); self.poste_label.grid(row=1, column=1, sticky="e", padx=10)
        self.salaire_label = tk.Label(info_frame, text="الراتب: ", font=("Cairo", 14), bg="white", anchor="e"); self.salaire_label.grid(row=2, column=1, sticky="e", padx=10)
        self.certificat_label = tk.Label(info_frame, text="صلاحية الشهادة: ", font=("Cairo", 14), bg="white", anchor="e"); self.certificat_label.grid(row=3, column=1, sticky="e", padx=10)
        hist_frame = tk.LabelFrame(main_frame, text=" سجل المدفوعات ", font=("Cairo", 16, "bold"), bg="white", fg="#34495e", bd=2, relief="groove")
        hist_frame.grid(row=1, column=0, sticky="nsew"); hist_frame.rowconfigure(0, weight=1); hist_frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(hist_frame, columns=("commentaire", "date", "montant"), show="headings", style="Employes.Treeview")
        tree.heading("montant", text="المبلغ"); tree.column("montant", anchor="center", width=150)
        tree.heading("date", text="التاريخ"); tree.column("date", anchor="center", width=200)
        tree.heading("commentaire", text="ملاحظة"); tree.column("commentaire", anchor="e")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        nom_employe_res = execute_query("SELECT nom FROM employes WHERE id=?", (self.employe_id,), fetch='one')
        if not nom_employe_res: return
        nom_employe = nom_employe_res[0]
        
        paiements = execute_query("SELECT montant, date, description FROM transactions WHERE type_transaction='Salaire' AND description LIKE ? ORDER BY date DESC", (f"%{nom_employe}%",), fetch='all') or []
        for montant, date, commentaire in paiements:
            date_formattee = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            commentaire_propre = commentaire.replace(f"دفع راتب: {nom_employe}", "").strip("- ")
            tree.insert("", tk.END, values=(commentaire_propre, date_formattee, f"{abs(int(montant))} د.ج"))

    def charger_donnees(self):
        employe_data = execute_query("SELECT nom, poste, salaire, photo_path, date_certificat FROM employes WHERE id=?", (self.employe_id,), fetch='one')
        if not employe_data: self.destroy(); return
        
        nom, poste, salaire, photo_path, date_cert = employe_data
        self.nom_label.config(text=f"الاسم: {nom}")
        self.poste_label.config(text=f"المنصب: {poste}")
        self.salaire_label.config(text=f"الراتب: {int(salaire or 0)} د.ج")
        self.certificat_label.config(text=f"صلاحية الشهادة: {date_cert or 'غير محدد'}")

        if photo_path and os.path.exists(photo_path):
            try:
                img = Image.open(photo_path); img = ImageOps.exif_transpose(img); img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                self.photo_label.config(image=photo, text=""); self.photo_label.image = photo
            except Exception: pass

class GestionCategoriesWindow(DynamicToplevel):
    """Fenêtre pour gérer les catégories de produits."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("إدارة الأصناف")
        self.geometry("500x600")
        self.configure(bg="#eaf0f6")
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="إدارة الأصناف", font=("Cairo", 22, "bold"), bg="#eaf0f6", fg="#2c3e50").pack(pady=20)
        
        list_frame = tk.Frame(self, bg="#ffffff", relief="solid", bd=1)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.listbox = tk.Listbox(list_frame, font=("Cairo", 16), justify="right", height=10, bg="#ffffff", fg="#34495e", relief="flat", selectbackground="#3498db", selectforeground="white")
        self.listbox.pack(side="right", fill="both", expand=True, padx=(0,10))
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")
        
        form_frame = tk.Frame(self, bg="#eaf0f6")
        form_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(form_frame, text="اسم الصنف:", font=("Cairo", 16), bg="#eaf0f6", fg="#2c3e50").pack(anchor="e")
        
        # --- MODIFICATION: Ajout du clavier virtuel ---
        entry_frame = tk.Frame(form_frame, bg="#eaf0f6")
        entry_frame.pack(fill="x", pady=5)
        entry_frame.columnconfigure(0, weight=1)

        self.entry_var = tk.StringVar()
        self.entry_categorie = tk.Entry(entry_frame, textvariable=self.entry_var, font=("Cairo", 16), justify="right", relief="solid", bd=1)
        self.entry_categorie.grid(row=0, column=0, sticky="ew")
        
        tk.Button(entry_frame, text="✏️", font=("Cairo", 14), command=self.open_keyboard).grid(row=0, column=1, padx=(5,0))
        # --- FIN DE LA MODIFICATION ---
        
        button_container = tk.Frame(form_frame, bg="#eaf0f6")
        button_container.pack(pady=10)
        
        btn_config = {'font': ("Cairo", 12, "bold"), 'fg': 'white', 'relief': 'raised', 'bd': 2, 'pady': 5, 'padx': 10}
        
        tk.Button(button_container, text="➕ إضافة", bg="#27ae60", **btn_config, command=self.ajouter).pack(side="right", padx=5)
        tk.Button(button_container, text="📝 تعديل", bg="#3498db", **btn_config, command=self.renommer).pack(side="right", padx=5)
        tk.Button(button_container, text="🗑️ حذف", bg="#c0392b", **btn_config, command=self.supprimer).pack(side="right", padx=5)
        
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.charger_categories()
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.fermer)

    def open_keyboard(self):
        """Ouvre le clavier virtuel pour l'entrée de catégorie."""
        new_value = KeyboardPopup(self, initial_value=self.entry_var.get()).show()
        if new_value is not None:
            self.entry_var.set(new_value)

    def charger_categories(self):
        self.listbox.delete(0, tk.END)
        categories = execute_query("SELECT nom FROM categories ORDER BY nom ASC", fetch='all')
        if categories:
            for cat in categories: self.listbox.insert(tk.END, cat[0])

    def on_select(self, event=None):
        selection = self.listbox.curselection()
        if selection:
            nom_selectionne = self.listbox.get(selection[0])
            self.entry_var.set(nom_selectionne)

    def ajouter(self):
        nouveau_nom = self.entry_var.get().strip()
        if not nouveau_nom: messagebox.showwarning("تنبيه", "اسم الصنف لا يمكن أن يكون فارغًا.", parent=self); return
        if execute_query("SELECT id FROM categories WHERE nom = ?", (nouveau_nom,), fetch='one'): messagebox.showerror("خطأ", "هذا الصنف موجود بالفعل.", parent=self); return
        execute_query("INSERT INTO categories (nom) VALUES (?)", (nouveau_nom,))
        self.charger_categories()
        self.entry_var.set("")

    def renommer(self):
        selection = self.listbox.curselection()
        if not selection: messagebox.showwarning("تنبيه", "الرجاء اختيار صنف لتعديله.", parent=self); return
        ancien_nom = self.listbox.get(selection[0])
        nouveau_nom = self.entry_var.get().strip()
        if not nouveau_nom: messagebox.showwarning("تنبيه", "اسم الصنف لا يمكن أن يكون فارغًا.", parent=self); return
        if nouveau_nom != ancien_nom and execute_query("SELECT id FROM categories WHERE nom = ?", (nouveau_nom,), fetch='one'): messagebox.showerror("خطأ", "هذا الاسم مستخدم بالفعل لصنف آخر.", parent=self); return
        execute_query("UPDATE categories SET nom = ? WHERE nom = ?", (nouveau_nom, ancien_nom))
        self.charger_categories()
        self.entry_var.set("")

    def supprimer(self):
        selection = self.listbox.curselection()
        if not selection: messagebox.showwarning("تنبيه", "الرجاء اختيار صنف لحذفه.", parent=self); return
        nom_a_supprimer = self.listbox.get(selection[0])
        if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف الصنف '{nom_a_supprimer}'؟\nسيؤدي هذا إلى إزالة الصنف من جميع المنتجات المرتبطة به.", parent=self):
            execute_query("DELETE FROM categories WHERE nom = ?", (nom_a_supprimer,))
            self.charger_categories()
            self.entry_var.set("")

    def fermer(self):
        self.parent.charger_donnees_initiales()
        self.destroy()


# --- FENÊTRE D'ACHAT/VENTE À CRÉDIT ---
# Cette classe est maintenant corrigée pour bien enregistrer les achats
class VenteCreditWindow(DynamicToplevel):
    def __init__(self, parent, partenaire, on_success=None):
        title = get_text("credit_sale_for").format(nom=partenaire['nom']) if partenaire['type'] == 'client_pro' else f"تسجيل شراء من {partenaire['nom']}"
        super().__init__(parent, title=title)
        
        self.parent = parent
        self.partenaire = partenaire
        self.panier = []
        self.on_success_callback = on_success

        main_frame = tk.Frame(self, bg="#eaf0f6", padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1); main_frame.rowconfigure(2, weight=1)
        
        form_frame_text = get_text("add_product_to_delivery") if partenaire['type'] == 'client_pro' else "إضافة منتج للشراء"
        form_frame = tk.LabelFrame(main_frame, text=f" {form_frame_text} ", font=("Cairo", 14, "bold"), bg="white", padx=10, pady=10)
        form_frame.grid(row=0, column=0, sticky="ew", pady=(0,10))
        
        if partenaire['type'] == 'client_pro':
            produits_query = "SELECT id, nom, prix FROM produits WHERE type='vente' ORDER BY nom"
        else: # fournisseur
            produits_query = "SELECT id, nom, prix_achat FROM produits WHERE type='consommation' OR origine='achete' ORDER BY nom"
            
        produits_disponibles = execute_query(produits_query, fetch='all') or []
        produit_names = [p[1] for p in produits_disponibles]
        self.produits_map = {p[1]: {'id': p[0], 'prix': p[2] or 0} for p in produits_disponibles}

        tk.Label(form_frame, text=get_text("product_label"), font=("Cairo", 12), bg="white").pack(side="right", padx=5)
        self.combo_produits = ttk.Combobox(form_frame, values=produit_names, state="readonly", justify="right", font=("Cairo", 12))
        self.combo_produits.pack(side="right", padx=5)
        self.combo_produits.bind("<<ComboboxSelected>>", self.on_produit_select)
        
        tk.Label(form_frame, text=get_text("quantity_label"), font=("Cairo", 12), bg="white").pack(side="right", padx=5)
        self.qte_entry = tk.Entry(form_frame, font=("Cairo", 12), width=8, justify="center")
        self.qte_entry.pack(side="right", padx=5)
        
        prix_label_text = get_text("special_price_label") if partenaire['type'] == 'client_pro' else "السعر:"
        tk.Label(form_frame, text=prix_label_text, font=("Cairo", 12), bg="white").pack(side="right", padx=5)
        self.prix_entry = tk.Entry(form_frame, font=("Cairo", 12, "bold"), width=10, justify="center", relief="solid", bd=1)
        self.prix_entry.pack(side="right", padx=5)
        
        tk.Button(form_frame, text="➕", font=("Cairo", 12, "bold"), bg="#3498db", fg="white", command=self.ajouter_au_panier).pack(side="right", padx=10)

        panier_frame_text = get_text("delivery_list") if partenaire['type'] == 'client_pro' else "قائمة المشتريات"
        panier_frame = tk.LabelFrame(main_frame, text=f" {panier_frame_text} ", font=("Cairo", 14, "bold"), bg="white", padx=10, pady=10)
        panier_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        panier_frame.rowconfigure(0, weight=1); panier_frame.columnconfigure(0, weight=1)
        
        self.panier_tree = ttk.Treeview(panier_frame, columns=("total", "prix", "qte", "nom"), show="headings")
        self.panier_tree.heading("nom", text="المنتج", anchor="e"); self.panier_tree.column("nom", anchor="e")
        self.panier_tree.heading("qte", text="الكمية", anchor="center"); self.panier_tree.column("qte", anchor="center", width=80)
        self.panier_tree.heading("prix", text="السعر", anchor="center"); self.panier_tree.column("prix", anchor="center", width=100)
        self.panier_tree.heading("total", text="المجموع", anchor="e"); self.panier_tree.column("total", anchor="e", width=120)
        self.panier_tree.grid(row=0, column=0, sticky="nsew")
        
        confirm_button_text = get_text("confirm_delivery_button") if partenaire['type'] == 'client_pro' else "✔️ تأكيد الشراء وتسجيل الدين"
        tk.Button(main_frame, text=confirm_button_text, font=("Cairo", 16, "bold"), bg="#27ae60", fg="white", command=self.valider_operation).grid(row=3, column=0, pady=10, sticky="ew")
        self.center_window()

    def on_produit_select(self, event):
        nom_produit = self.combo_produits.get(); _=event
        if not nom_produit: return
        produit_id = self.produits_map[nom_produit]['id']
        partenaire_id = self.partenaire['id']
        self.prix_entry.delete(0, tk.END)
        if self.partenaire['type'] == 'client_pro':
            prix_applicable = get_prix_pour_partenaire(produit_id, partenaire_id)
            self.prix_entry.insert(0, str(int(prix_applicable or 0)))
        else:
            prix_achat_defaut = self.produits_map[nom_produit].get('prix', 0)
            self.prix_entry.insert(0, str(int(prix_achat_defaut)))

    def ajouter_au_panier(self):
        nom = self.combo_produits.get(); qte_str = self.qte_entry.get(); prix_str = self.prix_entry.get()
        if not all([nom, qte_str, prix_str]): messagebox.showerror(get_text("error"), get_text("fill_all_fields_warning"), parent=self); return
        try:
            qte = int(qte_str); prix = float(prix_str)
            if qte <= 0 or prix < 0: raise ValueError
        except ValueError: messagebox.showerror(get_text("error"), get_text("invalid_amount_warning"), parent=self); return
        produit_id = self.produits_map[nom]['id']
        total_ligne = qte * prix
        self.panier.append({'id': produit_id, 'nom': nom, 'qte': qte, 'prix': prix, 'total': total_ligne})
        self.panier_tree.insert("", "end", values=(f"{total_ligne:.2f}", f"{prix:.2f}", qte, nom))
        self.combo_produits.set(''); self.qte_entry.delete(0, tk.END); self.prix_entry.delete(0, tk.END)

    def valider_operation(self):
        if not self.panier: messagebox.showwarning(get_text("warning"), "القائمة فارغة.", parent=self); return
        montant_total = sum(item['total'] for item in self.panier)
        date_operation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.partenaire['type'] == 'client_pro':
            confirm_msg = get_text("confirm_delivery_message").format(amount=montant_total)
            if not messagebox.askyesno(get_text("confirm"), confirm_msg, parent=self): return
            for item in self.panier:
                execute_query("INSERT INTO livraisons_clients (partenaire_id, produit_id, quantite, prix_vente_unitaire, montant_total, date_livraison) VALUES (?, ?, ?, ?, ?, ?)", (self.partenaire['id'], item['id'], item['qte'], item['prix'], item['total'], date_operation))
                execute_query("UPDATE produits SET stock = stock - ? WHERE id = ?", (item['qte'], item['id']))
            execute_query("UPDATE partenaires SET solde_credit = solde_credit + ? WHERE id = ?", (montant_total, self.partenaire['id']))
            messagebox.showinfo(get_text("success"), get_text("delivery_success_message"), parent=self)
        else: # Achat
            confirm_msg = f"هل أنت متأكد من تسجيل شراء بمبلغ {montant_total:.2f} د.ج؟\nسيتم إضافة هذا المبلغ إلى دين المورد."
            if not messagebox.askyesno("تأكيد الشراء", confirm_msg, parent=self): return
            user_id = self.parent.main_controller.user_id
            for item in self.panier:
                # CORRECTION : La logique d'enregistrement est maintenant complète et correcte
                execute_query(
                    "INSERT INTO stock_entries (produit_id, quantite_ajoutee, prix_achat_unitaire, cout_total, date_ajout, user_id, partenaire_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (item['id'], item['qte'], item['prix'], item['total'], date_operation, user_id, self.partenaire['id'])
                )
                execute_query("UPDATE produits SET stock = stock + ? WHERE id = ?", (item['qte'], item['id']))
            execute_query("UPDATE partenaires SET solde_credit = solde_credit - ? WHERE id = ?", (montant_total, self.partenaire['id']))
            messagebox.showinfo("نجاح", "تم تسجيل عملية الشراء بنجاح.", parent=self)
        
        if self.on_success_callback:
            self.on_success_callback()
        self.destroy()


# --- FENÊTRE DE PAIEMENT ---
# Cette classe est déjà correcte, mais incluse ici pour avoir le fichier complet.
class EnregistrerPaiementWindow(DynamicToplevel):
    def __init__(self, parent, main_controller, partenaire, on_success=None):
        super().__init__(parent, title=get_text("register_payment_for").format(nom=partenaire['nom']))
        self.parent = parent
        self.controller = main_controller
        self.partenaire = partenaire
        self.on_success_callback = on_success
        
        main_frame = tk.Frame(self, bg="#eaf0f6", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(main_frame, text=f"{get_text('register_payment_for').format(nom=partenaire['nom'])}", font=("Cairo", 20, "bold"), bg="#eaf0f6").pack(pady=10)
        solde_text = f"{get_text('current_balance')}: {format_currency(partenaire['solde_credit'])}"
        tk.Label(main_frame, text=solde_text, font=("Cairo", 14), bg="#eaf0f6").pack(pady=5)
        
        tk.Label(main_frame, text=get_text("amount_paid"), font=("Cairo", 14), bg="#eaf0f6").pack(pady=(10,0))
        self.montant_var = tk.StringVar()
        montant_entry = tk.Entry(main_frame, textvariable=self.montant_var, font=("Cairo", 14), justify="center", width=20, relief="solid", bd=1)
        montant_entry.pack(pady=5)
        
        tk.Button(main_frame, text=get_text("confirm_payment_button"), font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", command=self.valider_paiement).pack(pady=20, fill="x", ipady=5)
        self.center_window()

    def valider_paiement(self):
        user_id = self.controller.user_id
        try:
            montant_paiement = float(self.montant_var.get())
            if montant_paiement <= 0: raise ValueError
        except (ValueError, TypeError): 
            messagebox.showerror(get_text("error"), get_text("invalid_amount_warning"), parent=self)
            return
        
        partenaire_type = execute_query("SELECT type_partenaire FROM partenaires WHERE id=?", (self.partenaire['id'],), fetch='one')[0]
        montant_a_enregistrer = 0
        trans_type = ""
        
        if partenaire_type == 'client_pro':
            execute_query("UPDATE partenaires SET solde_credit = solde_credit - ? WHERE id = ?", (montant_paiement, self.partenaire['id']))
            montant_a_enregistrer = montant_paiement
            trans_type = get_text("payment_from_client")
        else: # fournisseur
            execute_query("UPDATE partenaires SET solde_credit = solde_credit + ? WHERE id = ?", (montant_paiement, self.partenaire['id']))
            montant_a_enregistrer = -abs(montant_paiement)
            trans_type = get_text("payment_to_supplier")
        
        trans_desc = f"{trans_type}: {self.partenaire['nom']}"
        execute_query("INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id, partenaire_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?)", (trans_desc, montant_a_enregistrer, trans_type, user_id, self.partenaire['id']))
        
        messagebox.showinfo(get_text("success"), get_text("payment_success_message"), parent=self)
        
        if self.on_success_callback:
            self.on_success_callback()
        self.destroy()

# Fichier: ui/components/app_dialogs.py
# Remplacez votre classe EnregistrerPaiementWindow par celle-ci

class EnregistrerPaiementWindow(DynamicToplevel):
    def __init__(self, parent, main_controller, partenaire, on_success=None):
        
        super().__init__(parent, title=get_text("register_payment_for").format(nom=partenaire['nom']))
        self.parent = parent
        self.controller = main_controller
        self.partenaire = partenaire
        # MODIFIÉ : On sauvegarde le signal pour l'utiliser plus tard
        self.on_success_callback = on_success 
        
        main_frame = tk.Frame(self, bg="#eaf0f6", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(main_frame, text=f"{get_text('register_payment_for').format(nom=partenaire['nom'])}", font=("Cairo", 20, "bold"), bg="#eaf0f6").pack(pady=10)
        tk.Label(main_frame, text=f"{get_text('current_balance')}: {partenaire['solde_credit']:.2f} د.ج", font=("Cairo", 14), bg="#eaf0f6").pack(pady=5)
        
        tk.Label(main_frame, text=get_text("amount_paid"), font=("Cairo", 14), bg="#eaf0f6").pack(pady=(10,0))
        self.montant_var = tk.StringVar()
        montant_entry = tk.Entry(main_frame, textvariable=self.montant_var, font=("Cairo", 14), justify="center", width=20, relief="solid", bd=1)
        montant_entry.pack(pady=5)
        
        tk.Button(main_frame, text=get_text("confirm_payment_button"), font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", command=self.valider_paiement).pack(pady=20, fill="x", ipady=5)
        self.center_window()

    def valider_paiement(self):
        user_id = self.controller.user_id
        try:
            montant_paiement = float(self.montant_var.get())
            if montant_paiement <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(get_text("error"), get_text("invalid_amount_warning"), parent=self)
            return

        partenaire_type = execute_query("SELECT type_partenaire FROM partenaires WHERE id=?", (self.partenaire['id'],), fetch='one')[0]

        montant_a_enregistrer = 0
        trans_type = ""
        if partenaire_type == 'client_pro':
            execute_query("UPDATE partenaires SET solde_credit = solde_credit - ? WHERE id = ?", (montant_paiement, self.partenaire['id']))
            montant_a_enregistrer = montant_paiement
            trans_type = get_text("payment_from_client")
        else: # fournisseur
            execute_query("UPDATE partenaires SET solde_credit = solde_credit + ? WHERE id = ?", (montant_paiement, self.partenaire['id']))
            montant_a_enregistrer = -abs(montant_paiement)
            trans_type = get_text("payment_to_supplier")
        
        trans_desc = f"{trans_type}: {self.partenaire['nom']}"
        
        execute_query(
            "INSERT INTO transactions (description, montant, date, type_transaction, vendeur_id, partenaire_id) VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?)",
            (trans_desc, montant_a_enregistrer, trans_type, user_id, self.partenaire['id'])
        )

        messagebox.showinfo(get_text("success"), get_text("payment_success_message"), parent=self)
        
        # MODIFIÉ : On active le signal de rafraîchissement avant de fermer
        if self.on_success_callback:
            self.on_success_callback()

        self.destroy()


class NotificationsWindow(DynamicToplevel):
    """Fenêtre affichant les notifications importantes (certificats, etc.)."""
    def __init__(self, parent, notifications):
        super().__init__(parent)
        self.title("🔔 تذكيرات هامة")
        self.configure(bg="#eaf0f6")
        self.transient(parent); self.grab_set(); self.resizable(False, False)

        main_frame = tk.Frame(self, bg="#eaf0f6", padx=20, pady=10); main_frame.pack(fill="both", expand=True)
        tk.Label(main_frame, text="🔔 تذكيرات هامة !", font=("Cairo", 22, "bold"), bg="#eaf0f6", fg="#2c3e50").pack(pady=(10, 20))

        for notif in notifications:
            notif_frame = tk.Frame(main_frame, bg="white", bd=1, relief="solid", highlightbackground="#d0d0d0")
            notif_frame.pack(pady=8, fill="x")
            icon = "⚠️" if notif['type'] == 'expiree' else "🔔"
            icon_color = "#c0392b" if notif['type'] == 'expiree' else "#f39c12"
            tk.Label(notif_frame, text=icon, font=("Arial", 24), bg="white", fg=icon_color).pack(side="right", padx=15, pady=10)
            text_frame = tk.Frame(notif_frame, bg="white"); text_frame.pack(side="right", fill="x", expand=True, pady=10)
            tk.Label(text_frame, text=notif['titre'], font=("Cairo", 16, "bold"), bg="white", fg="#2c3e50", anchor="e").pack(fill="x")
            tk.Label(text_frame, text=f"الموظف: {notif['nom']}", font=("Cairo", 14), bg="white", anchor="e").pack(fill="x")
            tk.Label(text_frame, text=notif['details'], font=("Cairo", 12, "italic"), bg="white", fg="#7f8c8d", anchor="e").pack(fill="x")
        
        tk.Button(main_frame, text="حسنا، مفهوم", font=("Cairo", 14, "bold"), bg="#3498db", fg="white", relief="flat", command=self.destroy, width=20, pady=8).pack(pady=20)
        
        self.center_window(notifications)

    def center_window(self, notifications):
        self.update_idletasks()
        width = 600
        height = 150 + (len(notifications) * 100)
        if height > 700: height = 700
        parent_x = self.master.winfo_x(); parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width(); parent_height = self.master.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')



# Fichier: ui/components/app_dialogs.py

class GererTarifsPartenaireWindow(DynamicToplevel):
    """
    Fenêtre pour définir des prix spéciaux pour un partenaire.
    Affiche les produits pertinents selon que le partenaire
    est un client (produits de vente) ou un fournisseur (tous produits achetables).
    """
    def __init__(self, parent, partenaire_id, partenaire_nom, partenaire_type):
        super().__init__(parent, title=get_text("manage_prices_title"))
        self.partenaire_id = partenaire_id
        self.entries = {}

        # ... (le reste de l'interface graphique ne change pas) ...
        main_frame = tk.Frame(self, bg="#eaf0f6", padx=10, pady=10)
        main_frame.pack(expand=True, fill="both")

        title_text = f"{get_text('special_prices_for')} : {partenaire_nom}"
        tk.Label(main_frame, text=title_text, font=("Cairo", 20, "bold"), bg="#f0f2f6", fg="#2c3e50").pack(pady=15)

        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(expand=True, fill="both", padx=10)
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- LOGIQUE DYNAMIQUE ---
        if partenaire_type == 'client_pro':
            # Pour un client, on affiche les produits à vendre.
            query = "SELECT id, nom, prix FROM produits WHERE type='vente' ORDER BY nom"
            default_price_col_key = "col_default_price"
        
        elif partenaire_type == 'fournisseur':
            # Pour un fournisseur, on affiche les matières premières ET les produits de revente.
            query = "SELECT id, nom, prix_achat FROM produits WHERE type='consommation' OR origine='achete' ORDER BY nom"
            default_price_col_key = "col_default_purchase_price"
        
        else:
            query = "" 
            default_price_col_key = "col_default_price"

        produits_a_afficher = execute_query(query, fetch='all') if query else []
        # --- FIN DE LA LOGIQUE DYNAMIQUE ---

        # ... (le reste de la classe pour afficher les produits et sauvegarder ne change pas) ...
        header_frame = tk.Frame(scrollable_frame, bg="#34495e", pady=5)
        header_frame.pack(fill='x')
        header_frame.columnconfigure((0, 1, 2), weight=1)
        tk.Label(header_frame, text=get_text("col_special_price"), font=("Cairo", 12, "bold"), bg="#34495e", fg="white").grid(row=0, column=0)
        tk.Label(header_frame, text=get_text(default_price_col_key), font=("Cairo", 12, "bold"), bg="#34495e", fg="white").grid(row=0, column=1)
        tk.Label(header_frame, text=get_text("col_product_name"), font=("Cairo", 12, "bold"), bg="#34495e", fg="white").grid(row=0, column=2)

        prix_speciaux_existants = execute_query("SELECT produit_id, prix_special FROM partenaire_prix WHERE partenaire_id = ?", (self.partenaire_id,), fetch='all') or []
        prix_map = {prod_id: prix for prod_id, prix in prix_speciaux_existants}

        for prod_id, nom, prix_defaut in produits_a_afficher:
            row_frame = tk.Frame(scrollable_frame, bg="white", highlightbackground="#dfe6e9", highlightthickness=1)
            row_frame.pack(fill="x", pady=2, padx=2)
            row_frame.columnconfigure((0, 1, 2), weight=1)
            prix_special_var = tk.StringVar()
            prix_special_entry = tk.Entry(row_frame, textvariable=prix_special_var, font=("Cairo", 12, "bold"), width=12, justify="center", relief="solid", bd=1, fg="#e67e22")
            prix_special_entry.grid(row=0, column=0, pady=5)
            if prod_id in prix_map: prix_special_var.set(int(prix_map[prod_id]))
            
            prix_defaut_affiche = prix_defaut or 0
            tk.Label(row_frame, text=f"{int(prix_defaut_affiche)} د.ج", font=("Cairo", 12), bg="white").grid(row=0, column=1)
            tk.Label(row_frame, text=nom, font=("Cairo", 12), bg="white", anchor="e").grid(row=0, column=2, sticky="ew", padx=(0, 10))
            self.entries[prod_id] = prix_special_var

        save_button = tk.Button(main_frame, text=get_text("save_prices_button"), font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", relief="raised", bd=2, command=self.sauvegarder_prix, pady=8)
        save_button.pack(pady=15, padx=10, fill="x")
        self.geometry("700x600")
        self.center_window()

    def sauvegarder_prix(self):
        for produit_id, prix_var in self.entries.items():
            prix_special_str = prix_var.get().strip()
            if not prix_special_str:
                execute_query("DELETE FROM partenaire_prix WHERE partenaire_id = ? AND produit_id = ?", (self.partenaire_id, produit_id))
                continue
            try:
                prix_special = float(prix_special_str)
                execute_query("INSERT OR REPLACE INTO partenaire_prix (partenaire_id, produit_id, prix_special) VALUES (?, ?, ?)", (self.partenaire_id, produit_id, prix_special))
            except ValueError:
                messagebox.showwarning(get_text("invalid_price_warning"), parent=self)
        messagebox.showinfo(get_text("success"), get_text("save_prices_success"), parent=self)
        self.destroy()

# Fichier: ui/components/app_dialogs.py
# Ajoutez ces 3 classes à la fin du fichier

class CreerClientParticulierWindow(DynamicToplevel):
    """Fenêtre pour créer un nouveau client crédit particulier."""
    def __init__(self, parent):
        super().__init__(parent, title="إضافة زبون كريدي جديد")
        self.nom_var = tk.StringVar()
        self.tel_var = tk.StringVar()
        
        tk.Label(self, text="اسم الزبون:", font=("Cairo", 14)).pack(pady=(10,0))
        tk.Entry(self, textvariable=self.nom_var, font=("Cairo", 12), justify="right").pack(pady=5, padx=20)
        
        tk.Label(self, text="رقم الهاتف (اختياري):", font=("Cairo", 14)).pack(pady=(10,0))
        tk.Entry(self, textvariable=self.tel_var, font=("Cairo", 12), justify="right").pack(pady=5, padx=20)
        
        tk.Button(self, text="✔️ حفظ الزبون", font=("Cairo", 14, "bold"), bg="#27ae60", fg="white", command=self.valider).pack(pady=20, padx=20, fill="x")
        self.center_window()

    def valider(self):
        nom = self.nom_var.get().strip()
        if not nom:
            messagebox.showwarning("إدخال ناقص", "اسم الزبون إلزامي.", parent=self)
            return
        
        # On l'ajoute comme un partenaire de type 'client_particulier'
        # Ce type n'existe pas dans la DB, mais SQLite l'acceptera.
        # Idéalement, il faudrait mettre à jour la table 'partenaires' dans init_db.py
        new_id = execute_query(
            "INSERT INTO partenaires (nom, telephone, type_partenaire, solde_credit) VALUES (?, ?, ?, 0)",
            (nom, self.tel_var.get(), 'client_particulier')
        )
        if new_id:
            messagebox.showinfo("نجاح", "تمت إضافة الزبون بنجاح.", parent=self)
            self.on_ok(True)
        else:
            messagebox.showerror("خطأ", "لم يتم إضافة الزبون.", parent=self)
            self.on_cancel()

class SelectionnerPartenaireProWindow(DynamicToplevel):
    """Fenêtre pour sélectionner un client professionnel existant."""
    def __init__(self, parent):
        super().__init__(parent, title="اختر زبون محترف")
        clients = execute_query("SELECT id, nom FROM partenaires WHERE type_partenaire = 'client_pro' ORDER BY nom", fetch='all') or []
        
        self.listbox = tk.Listbox(self, font=("Cairo", 16), justify="right")
        for client_id, nom in clients:
            self.listbox.insert(tk.END, f"{nom} ({client_id})")
        self.listbox.pack(pady=10, padx=10, fill="both", expand=True)
        
        btn_frame = tk.Frame(self, bg="#eaf0f6")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="✔️ اختيار", command=self.valider).pack(side="left", padx=10)
        tk.Button(btn_frame, text="إلغاء", command=self.on_cancel).pack(side="right", padx=10)
        self.center_window()

    def valider(self):
        selection = self.listbox.curselection()
        if not selection: return
        
        selected_text = self.listbox.get(selection[0])
        # Format "Nom (ID)" -> on extrait l'ID
        client_id = int(selected_text.split('(')[-1].replace(')', ''))
        self.on_ok(client_id)

class AjouterLivraisonWindow(DynamicToplevel):
    # Cette classe est une version simplifiée de VenteCreditWindow pour une tâche unique
    # C'est volontairement non inclus pour l'instant pour ne pas surcharger.
    # On utilisera VenteCreditWindow directement pour l'instant.
    pass