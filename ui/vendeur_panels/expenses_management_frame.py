# Fichier: ui/vendeur_panels/expenses_management_frame.py

import tkinter as tk
from tkinter import ttk, messagebox
from translations import get_text
from services.expense_service import ExpenseService
from services.partner_service import PartnerService

class ExpensesManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller
        self.main_controller = controller.main_controller
        self.expense_service = ExpenseService()
        self.partner_service = PartnerService()

        # Titre de la Page
        title = tk.Label(self, text=get_text("expenses_management_title"), font=("Cairo", 24, "bold"), bg="#eaf0f6")
        title.pack(pady=20)

        # Création des onglets
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=20, expand=True, fill="both")

        # --- Création des cadres pour chaque onglet ---
        # Chaque fonction de création est maintenant indépendante
        self.create_purchase_tab(notebook)
        self.create_supplier_payment_tab(notebook)
        self.create_salary_tab(notebook)
        self.create_other_expense_tab(notebook)
    
    # --- Onglet 1: Achat de Produits ---
    def create_purchase_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_buy_product"))
        
        tk.Label(tab, text=get_text("product_purchase_title"), font=("Cairo", 16)).pack(pady=10)
        
        # --- Données ---
        self.consumable_products = self.expense_service.get_consumable_products()
        product_names = [p[1] for p in self.consumable_products]
        
        # --- Widgets ---
        tk.Label(tab, text=get_text("select_product")).pack(pady=5)
        self.purchase_product_combo = ttk.Combobox(tab, values=product_names, state="readonly", justify="right")
        self.purchase_product_combo.pack(pady=5)
        
        tk.Label(tab, text=get_text("purchase_price")).pack(pady=5)
        self.purchase_price_entry = tk.Entry(tab, justify="center")
        self.purchase_price_entry.pack(pady=5)

        tk.Label(tab, text=get_text("quantity")).pack(pady=5)
        self.purchase_quantity_entry = tk.Entry(tab, justify="center")
        self.purchase_quantity_entry.pack(pady=5)

        self.purchase_product_combo.bind("<<ComboboxSelected>>", self.on_consumable_product_select)
        
        tk.Button(tab, text=get_text("confirm_purchase_button"), command=self.record_product_purchase).pack(pady=20)
        
    def on_consumable_product_select(self, event=None):
        selected_name = self.purchase_product_combo.get()
        for prod in self.consumable_products:
            if prod[1] == selected_name:
                self.purchase_price_entry.delete(0, tk.END)
                # Suggestion du dernier prix d'achat
                self.purchase_price_entry.insert(0, str(prod[2] or '')) 
                self.purchase_quantity_entry.delete(0, tk.END)
                self.purchase_quantity_entry.insert(0, "1")
                break

    def record_product_purchase(self):
        # Logique pour enregistrer l'achat d'un produit
        # Note: Cette logique est simplifiée. Pour un cas réel, on lierait l'achat à un fournisseur.
        messagebox.showinfo("Info", "La logique d'enregistrement d'achat sera complétée.")
        pass

    # --- Onglet 2: Paiement Fournisseur ---
    def create_supplier_payment_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_pay_supplier"))
        
        tk.Label(tab, text=get_text("supplier_payment_title"), font=("Cairo", 16)).pack(pady=10)
        
        self.resale_suppliers = self.expense_service.get_resale_suppliers()
        supplier_names = [s[1] for s in self.resale_suppliers]
        
        tk.Label(tab, text=get_text("select_supplier")).pack(pady=5)
        self.supplier_combo = ttk.Combobox(tab, values=supplier_names, state="readonly", justify="right")
        self.supplier_combo.pack(pady=5)
        
        tk.Label(tab, text=get_text("amount_to_pay")).pack(pady=5)
        self.supplier_amount_entry = tk.Entry(tab, justify="center")
        self.supplier_amount_entry.pack(pady=5)
        
        tk.Button(tab, text=get_text("confirm_expense_button"), command=self.record_supplier_payment).pack(pady=20)

    def record_supplier_payment(self):
        selected_name = self.supplier_combo.get()
        amount_str = self.supplier_amount_entry.get()
        user_id = self.main_controller.user_id

        if not selected_name or not amount_str:
            messagebox.showwarning(get_text("warning"), get_text("fill_all_fields_warning"), parent=self)
            return

        supplier_id = next((s[0] for s in self.resale_suppliers if s[1] == selected_name), None)
        
        success, message = self.partner_service.record_payment(supplier_id, amount_str, user_id)
        if success:
            messagebox.showinfo(get_text("success"), message, parent=self)
            self.supplier_combo.set('')
            self.supplier_amount_entry.delete(0, tk.END)
        else:
            messagebox.showerror(get_text("error"), message, parent=self)

    # --- Onglet 3: Paiement Salaires ---
    def create_salary_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_pay_salary"))
        
        tk.Label(tab, text=get_text("salary_payment_title"), font=("Cairo", 16)).pack(pady=10)
        
        self.employees = self.expense_service.get_employees()
        employee_names = [e[1] for e in self.employees]
        
        tk.Label(tab, text=get_text("select_employee")).pack(pady=5)
        self.employee_combo = ttk.Combobox(tab, values=employee_names, state="readonly", justify="right")
        self.employee_combo.pack(pady=5)
        
        tk.Label(tab, text=get_text("salary_amount")).pack(pady=5)
        self.salary_entry = tk.Entry(tab, justify="center")
        self.salary_entry.pack(pady=5)

        self.employee_combo.bind("<<ComboboxSelected>>", self.on_employee_select)
        
        tk.Button(tab, text=get_text("confirm_expense_button"), command=self.record_salary).pack(pady=20)

    def on_employee_select(self, event=None):
        selected_name = self.employee_combo.get()
        for emp in self.employees:
            if emp[1] == selected_name:
                self.salary_entry.delete(0, tk.END)
                # Suggestion du salaire de base, mais le champ reste modifiable
                self.salary_entry.insert(0, str(emp[2] or '')) 
                break

    def record_salary(self):
        selected_name = self.employee_combo.get()
        amount_str = self.salary_entry.get()
        user_id = self.main_controller.user_id
        
        if not selected_name or not amount_str:
            messagebox.showwarning(get_text("warning"), get_text("fill_all_fields_warning"), parent=self)
            return
            
        employee_id = next((e[0] for e in self.employees if e[1] == selected_name), None)
        
        success, message = self.expense_service.record_salary_payment(employee_id, amount_str, user_id)
        if success:
            messagebox.showinfo(get_text("success"), message, parent=self)
            self.employee_combo.set('')
            self.salary_entry.delete(0, tk.END)
        else:
            messagebox.showerror(get_text("error"), message, parent=self)

    # --- Onglet 4: Autre Dépense ---
    def create_other_expense_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_other_expense"))
        
        tk.Label(tab, text=get_text("manual_expense_title"), font=("Cairo", 16)).pack(pady=10)

        tk.Label(tab, text=get_text("description_label")).pack(pady=5)
        self.other_desc_entry = tk.Entry(tab, justify="right", width=40)
        self.other_desc_entry.pack(pady=5)
        
        tk.Label(tab, text=get_text("amount_label")).pack(pady=5)
        self.other_amount_entry = tk.Entry(tab, justify="center")
        self.other_amount_entry.pack(pady=5)
        
        tk.Button(tab, text=get_text("confirm_expense_button"), command=self.record_other_expense).pack(pady=20)

    def record_other_expense(self):
        description = self.other_desc_entry.get()
        amount = self.other_amount_entry.get()
        user_id = self.main_controller.user_id

        if not description or not amount:
            messagebox.showwarning(get_text("warning"), get_text("fill_all_fields_warning"), parent=self)
            return

        success, message = self.expense_service.record_manual_expense(description, amount, user_id)
        if success:
            messagebox.showinfo(get_text("success"), message, parent=self)
            self.other_desc_entry.delete(0, tk.END)
            self.other_amount_entry.delete(0, tk.END)
        else:
            messagebox.showerror(get_text("error"), message, parent=self)

    def charger_donnees(self):
        """Recharge les données dynamiques si nécessaire (appelée par le parent)."""
        # On pourrait recharger les listes ici si elles peuvent changer pendant que l'app est ouverte
        pass