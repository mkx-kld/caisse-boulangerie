# Fichier: ui/expenses_management_frame.py
# Rôle: Interface pour la gestion des dépenses avec 4 onglets.

import tkinter as tk
from tkinter import ttk, messagebox
from translations import get_text
from services.expense_service import ExpenseService

class ExpensesManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#eaf0f6")
        self.controller = controller
        self.main_controller = controller.controller
        self.service = ExpenseService()

        # Titre de la Page
        title = tk.Label(self, text=get_text("expenses_management_title"), font=("Cairo", 24, "bold"), bg="#eaf0f6")
        title.pack(pady=20)

        # Création des onglets
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Création des cadres pour chaque onglet
        self.create_purchase_tab(notebook)
        self.create_supplier_payment_tab(notebook)
        self.create_salary_tab(notebook)
        self.create_other_expense_tab(notebook)

    def create_purchase_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_buy_product"))
        
        # Logique et widgets pour l'achat de produits
        # Le vendeur sélectionne un produit, le prix d'achat est suggéré mais modifiable.
        
    def create_supplier_payment_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_pay_supplier"))
        # ...

    def create_salary_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_pay_salary"))
        
        tk.Label(tab, text=get_text("select_employee")).pack(pady=5)
        self.employee_combo = ttk.Combobox(tab, state="readonly")
        self.employee_combo.pack(pady=5)
        
        tk.Label(tab, text=get_text("salary_amount")).pack(pady=5)
        self.salary_entry = tk.Entry(tab)
        self.salary_entry.pack(pady=5)

        self.employee_combo.bind("<<ComboboxSelected>>", self.on_employee_select)
        
        tk.Button(tab, text=get_text("confirm_expense_button"), command=self.record_salary).pack(pady=20)

        self.load_employees()

    def load_employees(self):
        self.employees = self.service.get_employees()
        self.employee_combo['values'] = [e[1] for e in self.employees]

    def on_employee_select(self, event):
        selected_name = self.employee_combo.get()
        for emp in self.employees:
            if emp[1] == selected_name:
                self.salary_entry.delete(0, tk.END)
                self.salary_entry.insert(0, str(emp[2])) # Suggestion du salaire
                break

    def record_salary(self):
        # Logique pour enregistrer le salaire avec le montant de l'Entry
        pass

    def create_other_expense_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=get_text("tab_other_expense"))
        # ...