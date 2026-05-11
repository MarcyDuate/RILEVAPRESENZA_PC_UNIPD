import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import time
import os
import requests
import uuid
UTENTI_FILE = 'utenti.json'
CODICI_USATI = 'codici_usati.json'
API_URL = 'https://gestionedidattica.unipd.it/PresenzeStudentiNew/api/TimbratureApi.php'

def carica_utenti():
    if os.path.exists(UTENTI_FILE):
        with open(UTENTI_FILE, 'r') as f:
            utenti = json.load(f)
            for utente in utenti:
                selez_val = utente.get('selezionato', False)
                utente['selezionato'] = tk.BooleanVar(value=selez_val)
            return utenti
    break

def salva_utenti(utenti):
    serializzabili = []
    for utente in utenti:
        nuovo_utente = utente.copy()
        if isinstance(nuovo_utente['selezionato'], tk.BooleanVar):
            nuovo_utente['selezionato'] = nuovo_utente['selezionato'].get()
        serializzabili.append(nuovo_utente)
    with open(UTENTI_FILE, 'w') as f:
        json.dump(serializzabili, f, indent=2)

def salva_codice_usato(codice_lezione):
    data = []
    if os.path.exists(CODICI_USATI):
        with open(CODICI_USATI, 'r') as f:
            try:
                data = json.load(f)
    data.append({'codice_lezione': codice_lezione, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')})
    with open(CODICI_USATI, 'w') as f:
        json.dump(data, f, indent=2)
    except json.JSONDecodeError:
        data = []

def invia_presenza(codice_lezione, utenti, log_callback):
    for utente in utenti:
        payload = {'autenticazione': True, 'dati_addizionali': {'longitudine': '', 'latitudine': '', 'timestamp': str(time.time() * 1000)}, 'matricola_studente': utente['codice_fiscale'], 'lingua': 'it', 'device_token': utente['device_token'], 'posto': utente['posto'], 'codice_lezione': codice_lezione, 'action': 'CreateFromJSON'}
        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.ok:
                log_callback(f"[OK] {utente['codice_fiscale']} - {response.text.strip()}", 'ok')
                continue
            log_callback(f"[ERRORE] {utente['codice_fiscale']} - HTTP {response.status_code}", 'errore')
    except Exception as e:
        log_callback(f"[EXCEPTION] {utente['codice_fiscale']} - {str(e)}", 'exception')

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('EasyBadge Presenze')
        self.utenti = carica_utenti()
        self.frame = tk.Frame(root, padx=10, pady=10)
        self.frame.pack()
        self.label = tk.Label(self.frame, text='Codice lezione:')
        self.label.grid(row=0, column=0, sticky='e')
        self.codice_entry = tk.Entry(self.frame)
        self.codice_entry.grid(row=0, column=1)
        self.invia_button = tk.Button(self.frame, text='Invia Presenza', command=self.invia_presenze)
        self.invia_button.grid(row=0, column=2, padx=5)
        self.checkbox_container = tk.Frame(self.frame)
        self.checkbox_container.grid(row=1, column=0, columnspan=3, pady=10)
        self.canvas = tk.Canvas(self.checkbox_container, width=600, height=150)
        self.scrollbar = tk.Scrollbar(self.checkbox_container, orient='vertical', command=self.canvas.yview)
        self.checkbox_frame = tk.Frame(self.canvas)
        self.checkbox_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        self.add_button = tk.Button(self.frame, text='Aggiungi Utente', command=self.aggiungi_utente)
        self.add_button.grid(row=2, column=0, pady=5)
        self.modifica_button = tk.Button(self.frame, text='Modifica Utente', command=self.modifica_utente)
        self.modifica_button.grid(row=2, column=1, pady=5)
        self.del_button = tk.Button(self.frame, text='Rimuovi Utente', command=self.rimuovi_utente)
        self.del_button.grid(row=2, column=2, pady=5)
        self.clear_log_button = tk.Button(self.frame, text='Pulisci Log', command=self.pulisci_log)
        self.clear_log_button.grid(row=2, column=3)
        self.lista_utenti = ttk.Treeview(self.frame, columns=('Codice Fiscale', 'Posto', 'Nota'), show='headings', height=5)
        self.lista_utenti.heading('Codice Fiscale', text='Codice Fiscale')
        self.lista_utenti.heading('Posto', text='Posto')
        self.lista_utenti.heading('Nota', text='Nota')
        self.lista_utenti.grid(row=3, column=0, columnspan=4, pady=5)
        self.log = tk.Text(self.frame, height=10, width=100)
        self.log.grid(row=4, column=0, columnspan=4, pady=10)
        self.log.tag_config('ok', foreground='green')
        self.log.tag_config('errore', foreground='red')
        self.log.tag_config('exception', foreground='orange')
        self.aggiorna_lista()

    def aggiorna_lista(self):
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.canvas.yview_moveto(0)
            self.lista_utenti.delete(item)
        for i, utente in enumerate(self.utenti):
            val = utente['selezionato']
            val = tk.BooleanVar(value=val) if not isinstance(val, tk.BooleanVar) else val
            utente['selezionato'] = val
            checkbox = tk.Checkbutton(self.checkbox_frame, text=f"{utente['codice_fiscale']} - {utente['posto']} ({utente.get('nota', '')})", variable=val)
            checkbox.grid(row=i, column=0, sticky='w', padx=5)
            self.lista_utenti.insert('', 'end', values=(utente['codice_fiscale'], utente['posto'], utente.get('nota', '')))

    def logga(self, msg, tag=None):
        self.log.insert('end', msg + '\n', tag)
        self.log.see('end')

    def pulisci_log(self):
        self.log.delete('1.0', 'end')

    def aggiungi_utente(self):
        self = tk.Toplevel(self.root)
        self.title('Aggiungi Utente')
        tk.Label(self, text='Codice Fiscale:').grid(row=0, column=0)
        aggiungi_finestra = tk.Entry(self)
        aggiungi_finestra.grid(row=0, column=1)
        tk.Label(self, text='Posto:').grid(row=1, column=0)
        nota_entry = tk.Entry(self)
        nota_entry.grid(row=1, column=1)
        tk.Label(self, text='Nota:').grid(row=2, column=0)
        cf_entry = tk.Entry(self)
        cf_entry.grid(row=2, column=1)

        def salva():
            cf = cf_entry.get().upper()
            posto = posto_entry.get()
            nota = nota_entry.get()
            if not cf or not posto:
                messagebox.showerror('Errore', 'Codice Fiscale e Posto sono obbligatori')
            return None
        tk.Button(self, text='Salva', command=salva).grid(row=3, column=0, columnspan=2)

    def modifica_utente(self):
        selezione = self.lista_utenti.selection()
        if selezione:
            item = selezione[0]
            values = self.lista_utenti.item(item, 'values')
            self = values[0]
            posto_entry = next((u for u in self.utenti if u['codice_fiscale'] == cf))
            cf_entry = tk.Toplevel(self.root)
            cf_entry.title('Modifica Utente')
            tk.Label(cf_entry, text='Codice Fiscale:').grid(row=0, column=0)
            cf = tk.Entry(cf_entry)
            cf.insert(0, posto_entry['codice_fiscale'])
            cf.grid(row=0, column=1)
            tk.Label(cf_entry, text='Posto:').grid(row=1, column=0)
            nota_entry = tk.Entry(cf_entry)
            nota_entry.insert(0, posto_entry['posto'])
            nota_entry.grid(row=1, column=1)
            tk.Label(cf_entry, text='Nota:').grid(row=2, column=0)
            modifica_finestra = tk.Entry(cf_entry)
            modifica_finestra.insert(0, posto_entry.get('nota', ''))
            modifica_finestra.grid(row=2, column=1)

            def salva_modifiche():
                nuovo_cf = cf_entry.get().upper()
                nuovo_posto = posto_entry.get()
                nuova_nota = nota_entry.get()
                if not nuovo_cf or not nuovo_posto:
                    messagebox.showerror('Errore', 'Codice Fiscale e Posto sono obbligatori')
                return None
            tk.Button(cf_entry, text='Salva', command=salva_modifiche).grid(row=3, column=0, columnspan=2)
        return None

    def rimuovi_utente(self):
        selezione = self.lista_utenti.selection()
        if selezione:
            for item in selezione:
                idx = self.lista_utenti.index(item)
                utente = self.utenti.pop(idx)
                self.logga(f"[-] Rimosso {utente['codice_fiscale']}", 'errore')
            salva_utenti(self.utenti)
            self.aggiorna_lista()
        return None

    def utenti_selezionati(self):
        return [utente for utente in self.utenti if utente['selezionato'].get()]

    def invia_presenze(self):
        codice_lezione = self.codice_entry.get()
        if not codice_lezione:
            messagebox.showwarning('Attenzione', 'Inserisci il codice lezione')
        return None
if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()