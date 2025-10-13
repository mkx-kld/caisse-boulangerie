# Fichier: ui/sales_page/product_panel.py
# Rôle: Affiche les catégories et les produits. Notifie le parent lorsqu'un produit est sélectionné.

import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk, ImageOps
from services.sales_service import SalesService
from utils import format_currency

class ProductPanel(tk.Frame):
    def __init__(self, parent, on_product_select_callback):
        super().__init__(parent, bg="#eaf0f6")
        self.on_product_select = on_product_select_callback
        self.sales_service = SalesService()
        self.images_produits = []

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._create_widgets()
        self.load_data()

    def _create_widgets(self):
        self.categorie_frame = tk.Frame(self, bg="#eaf0f6")
        self.categorie_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        product_container = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        product_container.grid(row=1, column=0, sticky="nsew")
        product_container.rowconfigure(0, weight=1)
        product_container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(product_container, bg="#ffffff", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(product_container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.produit_frame = tk.Frame(canvas, bg="#ffffff")
        self.frame_id = canvas.create_window((0, 0), window=self.produit_frame, anchor="nw")
        
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.frame_id, width=e.width))
        self.produit_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def load_data(self):
        """Charge les catégories et les produits de la première catégorie."""
        self._load_categories()
        if self.liste_categories:
            self._load_products_by_category(self.liste_categories[0])

    def _load_categories(self):
        for widget in self.categorie_frame.winfo_children():
            widget.destroy()
            
        self.liste_categories = self.sales_service.get_categories_for_sale()
        cat_btn_config = {'font': ("Cairo", 14, "bold"), 'relief': 'raised', 'bd': 1, 'bg': '#bdc3c7', 'activebackground': '#3498db', 'pady': 10}
        for cat in self.liste_categories:
            btn = tk.Button(self.categorie_frame, text=cat, **cat_btn_config, command=lambda c=cat: self._load_products_by_category(c))
            btn.pack(side="right", fill="x", expand=True, padx=2)

    def _load_products_by_category(self, categorie):
        for widget in self.produit_frame.winfo_children():
            widget.destroy()
        self.images_produits.clear()
        
        produits = self.sales_service.get_products_by_category(categorie)
        row, col = 0, 0
        for nom, prix, photo_path in produits:
            card = tk.Frame(self.produit_frame, bg="#ecf0f1", bd=1, relief="solid")
            card.grid(row=row, column=col, padx=10, pady=10)
            
            photo_image = None
            if photo_path and os.path.exists(photo_path):
                try:
                    img = Image.open(photo_path)
                    img = ImageOps.exif_transpose(img)
                    img.thumbnail((140, 120))
                    photo_image = ImageTk.PhotoImage(img)
                    self.images_produits.append(photo_image)
                except Exception:
                    photo_image = None
            
            # Utilise une fonction lambda pour passer les données au callback
            command = lambda n=nom, p=int(prix): self.on_product_select({'nom': n, 'prix': p})
            
            img_button = tk.Button(card, image=photo_image, bg="white", relief="flat", command=command)
            img_button.pack(padx=5, pady=5)
            tk.Label(card, text=f"{nom}\n{format_currency(prix)}", font=("Cairo", 14, "bold"), bg="#ecf0f1").pack(pady=(0, 5))
            
            col += 1
            if col == 5:
                col = 0
                row += 1