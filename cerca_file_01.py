import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def apri_file(file_path):
    """Apre il file con il programma predefinito del sistema operativo"""
    if not os.path.exists(file_path):
        messagebox.showerror("Errore", f"Il file non esiste più:\n{file_path}")
        return
    
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", file_path])
        else:  # Linux e altri
            subprocess.run(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile aprire il file:\n{e}")

def esegui_ricerca(cartella, query, extensions, tree, status_label, btn_cerca, case_insensitive):
    # Pulisce la tabella in modo sicuro
    root.after(0, lambda: tree.delete(*tree.get_children()))
    
    if not cartella or not query:
        root.after(0, lambda: messagebox.showwarning("Attenzione", "Seleziona una cartella e inserisci una stringa da cercare."))
        root.after(0, lambda: btn_cerca.config(state=tk.NORMAL))
        root.after(0, lambda: status_label.config(text="Pronto"))
        return
    
    ext_list = []
    if extensions.strip():
        ext_list = [ext.strip().lower() for ext in extensions.split(',') if ext.strip()]
        ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]

    risultati_trovati = 0
    root.after(0, lambda: status_label.config(text="Ricerca in corso..."))
    
    query_search = query.lower() if case_insensitive else query
    
    for root_dir, dirs, files in os.walk(cartella):
        for file in files:
            if ext_list:
                _, file_ext = os.path.splitext(file)
                if file_ext.lower() not in ext_list:
                    continue
            
            file_path = os.path.join(root_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_to_check = line.lower() if case_insensitive else line
                        
                        if query_search in line_to_check:
                            risultati_trovati += 1
                            rel_path = os.path.relpath(file_path, cartella)
                            testo_linea = line.strip()
                            
                            # Determina lo stile zebra in base al numero di risultati trovati
                            tag_zebra = "even" if risultati_trovati % 2 == 0 else "odd"
                            
                            root.after(0, lambda rp=rel_path, ln=line_num, txt=testo_linea, fp=file_path, tz=tag_zebra: 
                                tree.insert("", tk.END, values=(rp, ln, txt), tags=(fp, tz))
                            )
            except Exception:
                continue
                
    root.after(0, lambda: status_label.config(text=f"Ricerca completata. Trovate {risultati_trovati} occorrenze. (Doppio click per aprire il file)"))
    root.after(0, lambda: btn_cerca.config(state=tk.NORMAL))

def avvia_ricerca():
    cartella = entry_path.get()
    query = entry_query.get()
    extensions = entry_ext.get()
    case_insensitive = var_case.get()
    
    btn_cerca.config(state=tk.DISABLED)
    
    t = threading.Thread(
        target=esegui_ricerca, 
        args=(cartella, query, extensions, tree_results, label_status, btn_cerca, case_insensitive)
    )
    t.daemon = True
    t.start()

def seleziona_cartella():
    path = filedialog.askdirectory()
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)

def on_item_double_click(event):
    selected_item = tree_results.selection()
    if selected_item:
        item = tree_results.item(selected_item)
        tags = item.get("tags")
        if tags:
            file_path = tags[0] # Il primo tag è sempre il percorso completo del file
            apri_file(file_path)

def ordina_colonna(tree, col, reverse):
    """Ordina la tabella quando si clicca sull'intestazione di una colonna"""
    # Prende tutti gli elementi della colonna
    l = [(tree.set(k, col), k) for k in tree.get_children('')]
    
    # Se è la colonna della riga (numerica), converte il valore in intero per un ordinamento corretto
    if col == "riga":
        l.sort(key=lambda t: int(t[0]) if t[0].isdigit() else 0, reverse=reverse)
    else:
        l.sort(reverse=reverse)

    # Ridisposiziona gli elementi ordinati nella tabella
    for index, (val, k) in enumerate(l):
        tree.move(k, '', index)
        # Re-imposta il colore zebra dopo l'ordinamento
        tag_zebra = "even" if index % 2 == 0 else "odd"
        current_tags = list(tree.item(k, "tags"))
        # Mantiene il percorso del file (primo tag) e aggiorna il tag zebra
        file_tag = current_tags[0] if current_tags else ""
        tree.item(k, tags=(file_tag, tag_zebra))

    # Inverte l'ordine per il prossimo click sulla stessa colonna
    tree.heading(col, command=lambda: ordina_colonna(tree, col, not reverse))

def esporta_log():
    items = tree_results.get_children()
    if not items:
        messagebox.showwarning("Attenzione", "Non ci sono risultati da esportare.")
        return
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("File di testo", "*.txt"), ("File di log", "*.log"), ("Tutti i file", "*.*")],
        title="Salva log dei risultati"
    )
    
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Risultati ricerca file\n" + "-"*80 + "\n")
                for item_id in items:
                    values = tree_results.item(item_id, "values")
                    tags = tree_results.item(item_id, "tags")
                    f.write(f"File: {values[0]} | Riga: {values[1]} | Percorso: {tags[0]}\n")
                    f.write(f"Testo: {values[2]}\n")
                    f.write("-" * 80 + "\n")
            messagebox.showinfo("Successo", f"Risultati esportati con successo in:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare il file:\n{e}")

# --- Configurazione della Finestra Grafica (GUI) ---
root = tk.Tk()
root.title("Cerca Testo nei File - Tabella Professionale")
root.geometry("950x680")

# Configurazione Stile Tabella (Tema moderno e riga spaziosa)
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", rowheight=28, font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

# Frame superiore per i controlli
frame_top = tk.Frame(root, padx=10, pady=10)
frame_top.pack(fill=tk.X)

tk.Label(frame_top, text="Cartella:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_path = tk.Entry(frame_top, width=70)
entry_path.grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame_top, text="Sfoglia...", command=seleziona_cartella).grid(row=0, column=2, padx=5, pady=5)

tk.Label(frame_top, text="Stringa da cercare:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
entry_query = tk.Entry(frame_top, width=70)
entry_query.grid(row=1, column=1, padx=5, pady=5)

btn_cerca = tk.Button(frame_top, text="Cerca", command=avvia_ricerca, font=("Arial", 10, "bold"))
btn_cerca.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

tk.Label(frame_top, text="Estensioni (es. .txt, .py):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
entry_ext = tk.Entry(frame_top, width=70)
entry_ext.grid(row=2, column=1, padx=5, pady=5)
entry_ext.insert(0, "")

var_case = tk.BooleanVar(value=False)
check_case = tk.Checkbutton(frame_top, text="Ignora maiuscole/minuscole (Case-insensitive)", variable=var_case)
check_case.grid(row=3, column=1, sticky="w", padx=5, pady=2)

# --- Area centrale con Tabella (Treeview) e Scrollbar ---
frame_center = tk.Frame(root, padx=10, pady=5)
frame_center.pack(fill=tk.BOTH, expand=True)

columns = ("file", "riga", "testo")
tree_results = ttk.Treeview(frame_center, columns=columns, show="headings", selectmode="browse")

# Configurazione Intestazioni (Cliccabili per ordinare)
tree_results.heading("file", text="File ↕", command=lambda: ordina_colonna(tree_results, "file", False))
tree_results.heading("riga", text="Riga ↕", command=lambda: ordina_colonna(tree_results, "riga", False))
tree_results.heading("testo", text="Contenuto della riga ↕", command=lambda: ordina_colonna(tree_results, "testo", False))

tree_results.column("file", width=280, anchor="w")
tree_results.column("riga", width=70, anchor="center")
tree_results.column("testo", width=550, anchor="w")

# Configurazione colori alternati (Zebra)
tree_results.tag_configure("even", background="#ffffff")
tree_results.tag_configure("odd", background="#f4f6f8")

# Scrollbar per la tabella
scrollbar = ttk.Scrollbar(frame_center, orient=tk.VERTICAL, command=tree_results.yview)
tree_results.configure(yscrollcommand=scrollbar.set)

tree_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Associa il doppio click per aprire il file
tree_results.bind("<Double-1>", on_item_double_click)

# --- Frame inferiore (Stato e Pulsante Export) ---
frame_bottom = tk.Frame(root, padx=10, pady=10)
frame_bottom.pack(fill=tk.X)

label_status = tk.Label(frame_bottom, text="Pronto", fg="gray", font=("Arial", 9))
label_status.pack(side=tk.LEFT, padx=5)

btn_export = tk.Button(frame_bottom, text="Esporta Risultati in File di Log...", command=esporta_log, font=("Arial", 10, "bold"))
btn_export.pack(side=tk.RIGHT, padx=5)

root.mainloop()