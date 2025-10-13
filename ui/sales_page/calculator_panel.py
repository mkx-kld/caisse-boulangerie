# Fichier: ui/sales_page/calculator_panel.py
# Rôle: Affiche la calculatrice pour la quantité, le total, et les boutons de validation/annulation de vente.

import tkinter as tk
from tkinter import ttk, messagebox
from translations import get_text
from utils import format_currency

class CalculatorPanel(tk.Frame):
    def __init__(self, parent, on_add_item_callback, on_confirm_sale_callback, on_cancel_cart_callback):
        super().__init__(parent, bg="#ffffff", width=420, bd=1, relief="solid")
        
        self.on_add_item = on_add_item_callback
        self.on_confirm_sale = on_confirm_sale_callback
        self.on_cancel_cart = on_cancel_cart_callback
        
        self.produit_selectionne = None
        self.nouvelle_saisie_calc = True

        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=0)

        self._create_widgets()

    def _create_widgets(self):
        # --- Zone du Total ---
        total_frame = tk.Frame(self, bg="#2c3e50")
        total_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.total_var = tk.StringVar(value=format_currency(0))
        tk.Label(total_frame, text=get_text("total_label"), font=("Cairo", 26, "bold"), fg="white", bg="#2c3e50").pack(side="right", padx=15, pady=10)
        tk.Label(total_frame, textvariable=self.total_var, font=("Cairo", 26, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=15, pady=10)

        # --- Label du produit sélectionné ---
        self.label_produit_selectionne = tk.Label(self, text=get_text("select_product_prompt"), font=("Cairo", 16, "italic"), bg="white", fg="#7f8c8d")
        self.label_produit_selectionne.grid(row=1, column=0, pady=(10, 0))

        # --- Calculatrice ---
        calc_frame = tk.Frame(self, bg="#ffffff")
        calc_frame.grid(row=2, column=0, pady=5, padx=10, sticky="nsew")
        calc_frame.columnconfigure((0, 1, 2), weight=1)
        
        self.entry_calc = tk.Entry(calc_frame, font=("Cairo", 28, "bold"), justify="center", relief="solid", bd=1)
        self.entry_calc.grid(row=0, column=0, columnspan=3, pady=10, ipady=10, sticky="ew")
        
        boutons_calc = [("3", 1, 0), ("2", 1, 1), ("1", 1, 2), ("6", 2, 0), ("5", 2, 1), ("4", 2, 2), ("9", 3, 0), ("8", 3, 1), ("7", 3, 2), ("←", 4, 0), ("0", 4, 1), ("C", 4, 2)]
        btn_calc_font = ("Cairo", 20, "bold")
        for text, r, c in boutons_calc:
            btn = tk.Button(calc_frame, text=text, font=btn_calc_font, relief="raised", bd=1, bg="#ecf0f1", command=lambda t=text: self._handle_calc_press(t))
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew", ipady=15)
            
        tk.Button(calc_frame, text=get_text("add_quantity_button"), font=("Cairo", 18, "bold"), bg="#3498db", fg="white", command=self._validate_quantity).grid(row=5, column=0, columnspan=3, pady=(10, 5), sticky="ew", ipady=10)
        
        # --- Boutons d'action principaux ---
        btn_action_frame = tk.Frame(self, bg="#ffffff")
        btn_action_frame.grid(row=3, column=0, pady=15, padx=10, sticky="s")
        btn_action_config = {'font': ("Cairo", 18, "bold"), 'fg': 'white', 'relief': 'raised', 'bd': 2, 'pady': 12}
        
        tk.Button(btn_action_frame, text=get_text("confirm_sale_button"), bg="#27ae60", **btn_action_config, command=self.on_confirm_sale).pack(fill="x", expand=True, pady=3)
        tk.Button(btn_action_frame, text=get_text("cancel_cart_button"), bg="#c0392b", **btn_action_config, command=self.on_cancel_cart).pack(fill="x", expand=True, pady=3)

    def set_selected_product(self, produit):
        """Méthode publique pour mettre à jour le produit sélectionné depuis l'extérieur."""
        self.produit_selectionne = produit
        self.label_produit_selectionne.config(text=f"{produit['nom']} - {format_currency(produit['prix'])}", font=("Cairo", 18, "bold"), fg="#3498db")
        self.entry_calc.focus_set()
        self.entry_calc.delete(0, tk.END)
        self.entry_calc.insert(0, "1")
        self.nouvelle_saisie_calc = True

    def update_total(self, total_amount):
        """Méthode publique pour mettre à jour le total."""
        self.total_var.set(format_currency(total_amount))

    def _validate_quantity(self):
        """Valide la quantité et notifie le parent pour ajouter au panier."""
        qte_str = self.entry_calc.get()
        if not self.produit_selectionne:
            messagebox.showwarning(get_text("warning"), get_text("select_product_warning"), parent=self)
            return
        if not qte_str.isdigit() or int(qte_str) <= 0:
            messagebox.showwarning(get_text("warning"), get_text("invalid_quantity_warning"), parent=self)
            return
        
        # Notifie le parent via le callback
        self.on_add_item(self.produit_selectionne, int(qte_str))
        
        # Réinitialise l'état
        self.entry_calc.delete(0, tk.END)
        self.produit_selectionne = None
        self.nouvelle_saisie_calc = True
        self.label_produit_selectionne.config(text=get_text("select_product_prompt"), font=("Cairo", 16, "italic"), fg="#7f8c8d")

    def _handle_calc_press(self, touche):
        """Gère les appuis sur les touches de la calculatrice."""
        if self.nouvelle_saisie_calc and touche not in ["C", "←"]:
            self.entry_calc.delete(0, tk.END)
            self.nouvelle_saisie_calc = False
            
        current_text = self.entry_calc.get()
        if touche == "C":
            self.entry_calc.delete(0, tk.END)
        elif touche == "←":
            self.entry_calc.delete(len(current_text) - 1, tk.END)
        else:
            self.entry_calc.insert(tk.END, touche)