

# Fichier: ui/admin_panels/employes_panel.py
# Version entièrement traduite via get_text

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk, ImageOps
from datetime import datetime

from database.db_manager import execute_query
from ui.components.input_popups import CalculatorPopup, KeyboardPopup, CalendarPopup
from ui.components.app_dialogs import EmployeDetailsWindow # sera déplacé dans employee_dialogs
from translations import get_text

class EmployesPanel(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f2f5")
        self.controller = controller
        self.photo_path = None
        
        style = ttk.Style(self)
        style.configure("Employes.Treeview", font=("Cairo", 14), rowheight=40)
        style.configure("Employes.Treeview.Heading", font=("Cairo", 16, "bold"))

        self.columnconfigure(0, weight=2) 
        self.columnconfigure(1, weight=1) 
        self.rowconfigure(0, weight=1)

        self.creer_panneau_liste()
        self.creer_panneau_formulaire()
        
        self.charger_employes()

    def creer_panneau_formulaire(self):
        form_container = tk.LabelFrame(self, text=f" {get_text('employee_form_title')} ", font=("Cairo", 18, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=15, pady=15)
        form_container.grid(row=0, column=1, padx=(10,25), pady=20, sticky="nsew")
        
        fields_frame = tk.Frame(form_container, bg="white")
        fields_frame.pack(pady=10)
        
        self.nom_var = self.creer_champ_saisie(fields_frame, 0, get_text("employee_name"), 'keyboard')
        self.poste_var = self.creer_champ_saisie(fields_frame, 1, get_text("employee_position"), 'keyboard')
        self.salaire_var = self.creer_champ_saisie(fields_frame, 2, get_text("employee_salary"), 'calculator')
        self.certificat_var = self.creer_champ_saisie(fields_frame, 3, get_text("health_cert_date"), 'calendar')
        
        photo_frame = tk.Frame(fields_frame, bg="white", width=200, height=200, bd=1, relief="solid")
        photo_frame.grid(row=4, column=0, columnspan=3, pady=15)
        photo_frame.grid_propagate(False)
        self.photo_label = tk.Label(photo_frame, text=get_text("no_photo"), font=("Cairo", 12), bg="#ecf0f1")
        self.photo_label.pack(fill="both", expand=True)
        tk.Button(fields_frame, text=get_text("choose_photo"), font=("Cairo", 12, "bold"), command=self.choisir_photo).grid(row=5, column=0, columnspan=3, pady=10)
        
        btn_actions_frame = tk.Frame(form_container, bg="white")
        btn_actions_frame.pack(pady=20, fill="x")
        btn_config = {'font':("Cairo", 14, "bold"), 'fg':'white', 'pady':8, 'relief':'flat'}
        
        tk.Button(btn_actions_frame, text=get_text("add_button"), bg="#27ae60", **btn_config, command=self.ajouter_employe).pack(fill="x", pady=3)
        tk.Button(btn_actions_frame, text=get_text("save_button"), bg="#3498db", **btn_config, command=self.modifier_employe).pack(fill="x", pady=3)
        tk.Button(btn_actions_frame, text=get_text("delete_button"), bg="#c0392b", **btn_config, command=self.supprimer_employe).pack(fill="x", pady=3)
        tk.Button(btn_actions_frame, text=get_text("clear_button"), bg="#95a5a6", **btn_config, command=self.vider_champs).pack(fill="x", pady=3)

    def creer_champ_saisie(self, parent, row, label_text, popup_type):
        tk.Label(parent, text=label_text, font=("Cairo", 14), bg="white").grid(row=row, column=1, padx=5, pady=8, sticky="w")
        var = tk.StringVar()
        entry = tk.Entry(parent, textvariable=var, font=("Cairo", 14), justify="right", width=20, relief="solid", bd=1)
        entry.grid(row=row, column=0, padx=5, pady=8)
        
        if popup_type == 'keyboard': btn_cmd = lambda v=var: self.open_popup(KeyboardPopup, v)
        elif popup_type == 'calculator': btn_cmd = lambda v=var: self.open_popup(CalculatorPopup, v)
        else: btn_cmd = lambda v=var: self.open_popup(CalendarPopup, v)
        
        tk.Button(parent, text="✏️", font=("Cairo", 14), command=btn_cmd).grid(row=row, column=2, padx=(5,0))
        return var

    def open_popup(self, popup_class, target_var):
        """Ouvre une fenêtre popup et met à jour la variable cible avec le résultat."""
        new_value = popup_class(self, initial_value=target_var.get()).show()
        if new_value is not None:
            target_var.set(new_value)

    def creer_panneau_liste(self):
        liste_container = tk.LabelFrame(self, text=f" {get_text('employee_list_title')} ", font=("Cairo", 18, "bold"), bg="white", fg="#34495e", bd=2, relief="groove", padx=10, pady=10)
        liste_container.grid(row=0, column=0, padx=(25,10), pady=20, sticky="nsew")
        liste_container.rowconfigure(0, weight=1)
        liste_container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(liste_container, columns=("certificat", "salaire", "poste", "nom"), show="headings", style="Employes.Treeview")
        self.tree.heading("nom", text=get_text("col_name"), anchor="e")
        self.tree.column("nom", anchor="e")
        self.tree.heading("poste", text=get_text("col_position"), anchor="center")
        self.tree.column("poste", anchor="center", width=200)
        self.tree.heading("salaire", text=get_text("col_salary"), anchor="center")
        self.tree.column("salaire", anchor="center", width=150)
        self.tree.heading("certificat", text=get_text("col_cert_validity"), anchor="center")
        self.tree.column("certificat", anchor="center", width=200)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(liste_container, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.bind("<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        """Ouvre la fenêtre de détails de l'employé au double-clic."""
        selection = self.tree.selection()
        if not selection: return
        selected_id = selection[0]
        EmployeDetailsWindow(self, selected_id)

    def vider_champs(self):
        """Réinitialise tous les champs du formulaire."""
        self.tree.selection_remove(self.tree.selection())
        self.photo_path = None
        self.nom_var.set("")
        self.poste_var.set("")
        self.salaire_var.set("")
        self.certificat_var.set("")
        self.photo_label.config(image="", text="لا توجد صورة")
        self.photo_label.image = None
        
    def charger_employes(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        employes = execute_query("SELECT id, nom, poste, salaire, date_certificat FROM employes ORDER BY nom", fetch='all') or []
        for emp_id, nom, poste, salaire, date_cert in employes:
            self.tree.insert("", "end", iid=emp_id, values=(date_cert or get_text("cert_date_not_set"), f"{int(salaire or 0)} {get_text('currency_symbol')}", poste, nom))

    def on_item_select(self, event):
        """Remplit le formulaire avec les données de l'employé sélectionné."""
        selection = self.tree.selection()
        if not selection: return
        
        selected_id = selection[0]
        employe = execute_query("SELECT nom, poste, salaire, photo_path, date_certificat FROM employes WHERE id=?", (selected_id,), fetch='one')
        if not employe: return
        
        nom, poste, salaire, photo_path, date_cert = employe
        self.nom_var.set(nom)
        self.poste_var.set(poste)
        self.salaire_var.set(int(salaire or 0))
        self.certificat_var.set(date_cert or "")
        self.photo_path = photo_path
        self.afficher_photo()

    def choisir_photo(self):
        """Ouvre une boîte de dialogue pour sélectionner une photo."""
        filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if filepath:
            self.photo_path = filepath
            self.afficher_photo()

    def afficher_photo(self):
        """Affiche la photo sélectionnée dans le label dédié."""
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                img = Image.open(self.photo_path)
                img = ImageOps.exif_transpose(img)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.photo_label.config(image=photo, text="")
                self.photo_label.image = photo
            except Exception:
                self.photo_label.config(image="", text="خطأ في الصورة")
                self.photo_label.image = None
        else:
            self.photo_label.config(image="", text="لا توجد صورة")
            self.photo_label.image = None

    def ajouter_employe(self):
        nom = self.nom_var.get(); poste = self.poste_var.get(); salaire_str = self.salaire_var.get(); date_cert = self.certificat_var.get()
        if not nom or not poste or not salaire_str:
            messagebox.showerror(get_text("error"), get_text("name_pos_salary_required"), parent=self); return
        if execute_query("SELECT id FROM employes WHERE nom = ?", (nom,), fetch='one'):
            messagebox.showerror(get_text("error"), get_text("employee_name_exists"), parent=self); return
        try:
            salaire = float(salaire_str)
        except ValueError:
            messagebox.showerror(get_text("error"), get_text("salary_must_be_number"), parent=self); return
        query = "INSERT INTO employes (nom, poste, salaire, photo_path, date_embauche, date_certificat) VALUES (?, ?, ?, ?, ?, ?)"
        params = (nom, poste, salaire, self.photo_path, datetime.now().strftime('%Y-%m-%d'), date_cert)
        execute_query(query, params)
        messagebox.showinfo(get_text("success"), get_text("employee_added_success"), parent=self)
        self.charger_employes(); self.vider_champs()

        
    def modifier_employe(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(get_text("warning"), get_text("select_employee_to_edit"), parent=self); return
        selected_id = selection[0]
        nom = self.nom_var.get(); poste = self.poste_var.get(); salaire_str = self.salaire_var.get(); date_cert = self.certificat_var.get()
        if not nom or not poste or not salaire_str:
            messagebox.showerror(get_text("error"), get_text("name_pos_salary_required"), parent=self); return
        if execute_query("SELECT id FROM employes WHERE nom = ? AND id != ?", (nom, selected_id), fetch='one'):
            messagebox.showerror(get_text("error"), get_text("other_employee_name_exists"), parent=self); return
        try:
            salaire = float(salaire_str)
        except ValueError:
            messagebox.showerror(get_text("error"), get_text("salary_must_be_number"), parent=self); return
        query = "UPDATE employes SET nom=?, poste=?, salaire=?, photo_path=?, date_certificat=? WHERE id=?"
        execute_query(query, (nom, poste, salaire, self.photo_path, date_cert, selected_id))
        messagebox.showinfo(get_text("success"), get_text("employee_edited_success"), parent=self)
        self.charger_employes(); self.vider_champs()


    def supprimer_employe(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(get_text("warning"), get_text("select_employee_to_delete"), parent=self); return
        selected_id = selection[0]
        if not messagebox.askyesno(get_text("confirm_delete_title"), get_text("employee_delete_confirm"), parent=self): return
        execute_query("DELETE FROM employes WHERE id=?", (selected_id,))
        messagebox.showinfo(get_text("success"), get_text("employee_deleted_success"), parent=self)
        self.charger_employes(); self.vider_champs()
