import sqlite3, os, csv, shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
from pathlib import Path
import json, urllib.request, urllib.error, tempfile, subprocess, sys

BASE = Path(__file__).resolve().parent
# Dane użytkownika są przechowywane poza Program Files, aby aplikacja działała
# bez uprawnień administratora i aby aktualizacja programu nie kasowała danych.
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WypozyczalniaInstrumentow"
DB = DATA / "rental.db"
PHOTOS = DATA / "photos"
APP_VERSION = "2.0.0"
APP_NAME = "Wypożyczalnia Instrumentów"
CONFIG_FILE = BASE / "config.json"

def load_app_config():
    default = {
        "app_name": APP_NAME,
        "company_name": APP_NAME,
        "version": APP_VERSION,
        "update_manifest_url": "",
        "update_channel": "stable"
    }
    try:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                default.update(json.load(f))
    except Exception:
        pass
    return default

APP_CONFIG = load_app_config()
APP_NAME = APP_CONFIG.get("app_name", APP_NAME)
COMPANY_NAME = APP_CONFIG.get("company_name", APP_NAME)
UPDATE_MANIFEST_URL = APP_CONFIG.get("update_manifest_url", "")
DATA.mkdir(parents=True, exist_ok=True)
PHOTOS.mkdir(parents=True, exist_ok=True)

# Jednorazowa migracja danych ze starszej wersji aplikacji.
legacy_db = BASE / "rental.db"
legacy_photos = BASE / "photos"
if not DB.exists() and legacy_db.exists():
    try:
        shutil.copy2(legacy_db, DB)
        if legacy_photos.exists():
            for old_photo in legacy_photos.iterdir():
                if old_photo.is_file():
                    shutil.copy2(old_photo, PHOTOS / old_photo.name)
    except Exception:
        pass

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS instruments(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      inventory_no TEXT UNIQUE,
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      brand TEXT DEFAULT '',
      price_day REAL NOT NULL DEFAULT 0,
      deposit REAL NOT NULL DEFAULT 0,
      instrument_value REAL NOT NULL DEFAULT 0,
      photo TEXT DEFAULT '',
      status TEXT NOT NULL DEFAULT 'Dostępny'
    );
    CREATE TABLE IF NOT EXISTS customers(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      phone TEXT DEFAULT '',
      email TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS rentals(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      instrument_id INTEGER NOT NULL,
      customer_id INTEGER NOT NULL,
      start_date TEXT NOT NULL,
      due_date TEXT NOT NULL,
      return_date TEXT,
      total REAL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'Aktywne',
      FOREIGN KEY(instrument_id) REFERENCES instruments(id),
      FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    """)
    cols = {r["name"] for r in c.execute("PRAGMA table_info(instruments)").fetchall()}
    migrations = {
        "inventory_no":"ALTER TABLE instruments ADD COLUMN inventory_no TEXT",
        "instrument_value":"ALTER TABLE instruments ADD COLUMN instrument_value REAL NOT NULL DEFAULT 0",
        "photo":"ALTER TABLE instruments ADD COLUMN photo TEXT DEFAULT ''",
    }
    for col, sql in migrations.items():
        if col not in cols:
            c.execute(sql)
    if c.execute("SELECT COUNT(*) FROM instruments").fetchone()[0] == 0:
        c.executemany("""INSERT INTO instruments
          (inventory_no,name,category,brand,price_day,deposit,instrument_value)
          VALUES(?,?,?,?,?,?,?)""", [
            ("INS-0001","Gitara akustyczna","Gitara","Yamaha",35,200,1800),
            ("INS-0002","Gitara elektryczna","Gitara","Fender",55,300,3200),
            ("INS-0003","Keyboard","Klawiszowe","Casio",60,250,2100),
            ("INS-0004","Perkusja","Perkusyjne","Pearl",90,500,6500),
            ("INS-0005","Saksofon altowy","Dęte","Yamaha",75,400,4800),
        ])
    if c.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        c.executemany("INSERT INTO customers(name,phone,email) VALUES(?,?,?)", [
            ("Jan Kowalski","600 100 200","jan@example.com"),
            ("Anna Nowak","601 200 300","anna@example.com"),
        ])
    c.commit(); c.close()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  •  v{APP_VERSION}")
        self.geometry("1240x760")
        self.minsize(1000,620)
        self.configure(bg="#eef1f5")
        self.style()
        self.build()
        self.refresh_all()

    def check_for_updates(self, silent=False):
        if not UPDATE_MANIFEST_URL:
            if not silent:
                messagebox.showinfo("Aktualizacje", "Mechanizm aktualizacji jest przygotowany.\n\nAby go włączyć, ustaw adres manifestu aktualizacji w config.json.")
            return
        try:
            req = urllib.request.Request(UPDATE_MANIFEST_URL, headers={"User-Agent": APP_NAME})
            with urllib.request.urlopen(req, timeout=8) as response:
                manifest = json.loads(response.read().decode("utf-8"))
            latest = str(manifest.get("version", APP_VERSION))
            installer_url = manifest.get("installer_url", "")
            if latest == APP_VERSION or not installer_url:
                if not silent:
                    messagebox.showinfo("Aktualizacje", f"Masz najnowszą wersję: {APP_VERSION}.")
                return
            if messagebox.askyesno("Dostępna aktualizacja",
                                   f"Dostępna jest wersja {latest}.\n\nZainstalować ją teraz?"):
                self.download_and_run_installer(installer_url, latest)
        except Exception as e:
            if not silent:
                messagebox.showwarning("Aktualizacje", f"Nie udało się sprawdzić aktualizacji.\n\n{e}")

    def download_and_run_installer(self, url, version):
        try:
            fd, path = tempfile.mkstemp(prefix="WypozyczalniaInstrumentow_", suffix=".exe")
            os.close(fd)
            req = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
            with urllib.request.urlopen(req, timeout=60) as response, open(path, "wb") as out:
                shutil.copyfileobj(response, out)
            messagebox.showinfo("Aktualizacja", f"Instalator wersji {version} został pobrany.\n\nProgram zostanie zamknięty i uruchomi się instalator.")
            subprocess.Popen([path], shell=False)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Aktualizacja", f"Nie udało się pobrać aktualizacji.\n\n{e}")

    def style(self):
        s=ttk.Style(self); s.theme_use("clam")
        s.configure("Treeview",rowheight=29,font=("Segoe UI",10))
        s.configure("Treeview.Heading",font=("Segoe UI",10,"bold"))
        s.configure("TButton",font=("Segoe UI",10),padding=7)
        s.configure("Title.TLabel",font=("Segoe UI",22,"bold"),background="#eef1f5")
        s.configure("Sub.TLabel",font=("Segoe UI",10),background="#eef1f5",foreground="#555")
        s.configure("KPI.TLabel",font=("Segoe UI",18,"bold"))

    def build(self):
        h=ttk.Frame(self,padding=(25,18,25,8)); h.pack(fill="x")
        ttk.Label(h,text=APP_NAME,style="Title.TLabel").pack(anchor="w")
        ttk.Label(h,text=f"{COMPANY_NAME}  •  ewidencja • zdjęcia • wypożyczenia • raporty • v{APP_VERSION}",style="Sub.TLabel").pack(anchor="w")
        nb=ttk.Notebook(self); nb.pack(fill="both",expand=True,padx=20,pady=10)
        actions = ttk.Frame(h)
        actions.pack(anchor="e", pady=(8,0))
        ttk.Button(actions, text="Sprawdź aktualizacje", command=self.check_for_updates).pack(side="right")
        self.tabs={}
        for n in ["Instrumenty","Klienci","Wypożyczenia","Historia","Raporty"]:
            f=ttk.Frame(nb,padding=12); nb.add(f,text=n); self.tabs[n]=f
        self.instrument_tab(); self.customer_tab(); self.rental_tab(); self.history_tab(); self.reports_tab()

    def refresh_all(self):
        self.refresh_instruments(); self.refresh_customers()
        self.refresh_rental_choices(); self.refresh_rentals(); self.refresh_history(); self.refresh_reports()

    # INSTRUMENTS
    def instrument_tab(self):
        f=self.tabs["Instrumenty"]; top=ttk.Frame(f); top.pack(fill="x",pady=(0,10))
        self.i_search=tk.StringVar()
        ttk.Entry(top,textvariable=self.i_search,width=32).pack(side="left")
        ttk.Button(top,text="Szukaj",command=self.refresh_instruments).pack(side="left",padx=5)
        ttk.Button(top,text="Wyczyść",command=lambda:(self.i_search.set(""),self.refresh_instruments())).pack(side="left")
        ttk.Button(top,text="Dodaj instrument",command=self.add_instrument).pack(side="right")
        cols=("inv","name","cat","brand","price","value","status")
        self.itree=ttk.Treeview(f,columns=cols,show="headings")
        for col,txt,w in zip(cols,["Nr ewid.","Instrument","Kategoria","Marka","Cena/dzień","Wartość","Status"],[105,220,125,130,100,110,110]):
            self.itree.heading(col,text=txt); self.itree.column(col,width=w)
        self.itree.pack(fill="both",expand=True)
        self.itree.bind("<Double-1>",lambda e:self.edit_instrument())
        bar=ttk.Frame(f); bar.pack(fill="x",pady=8)
        ttk.Button(bar,text="Edytuj",command=self.edit_instrument).pack(side="left")
        ttk.Button(bar,text="Usuń",command=self.delete_instrument).pack(side="left",padx=6)
        self.photo_label=ttk.Label(bar,text="Zaznacz instrument, aby zobaczyć zdjęcie.")
        self.photo_label.pack(side="right")

    def refresh_instruments(self):
        q=self.i_search.get().strip() if hasattr(self,"i_search") else ""
        for x in self.itree.get_children(): self.itree.delete(x)
        c=db()
        rows=c.execute("""SELECT * FROM instruments
          WHERE inventory_no LIKE ? OR name LIKE ? OR category LIKE ? OR brand LIKE ?
          ORDER BY id DESC""",(f"%{q}%",f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
        for r in rows:
            self.itree.insert("", "end", iid=r["id"],
              values=(r["inventory_no"] or "",r["name"],r["category"],r["brand"],
                      f'{r["price_day"]:.2f} zł',f'{r["instrument_value"]:.2f} zł',r["status"]))
        c.close()
        self.itree.bind("<<TreeviewSelect>>",self.show_photo)

    def show_photo(self,event=None):
        s=self.itree.selection()
        if not s: return
        c=db(); r=c.execute("SELECT photo FROM instruments WHERE id=?",(s[0],)).fetchone(); c.close()
        p=(PHOTOS / Path(r["photo"]).name) if r and r["photo"] else None
        if p and p.exists():
            try:
                from PIL import Image, ImageTk
                im=Image.open(p); im.thumbnail((100,100))
                self.photo_img=ImageTk.PhotoImage(im)
                self.photo_label.configure(image=self.photo_img,text="")
            except Exception:
                self.photo_label.configure(text="Zdjęcie zapisane (podgląd wymaga Pillow).",image="")
        else:
            self.photo_label.configure(text="Brak zdjęcia",image="")

    def add_instrument(self): self.instrument_dialog()
    def edit_instrument(self):
        s=self.itree.selection()
        if not s: return messagebox.showinfo("Wybierz","Zaznacz instrument.")
        c=db(); r=c.execute("SELECT * FROM instruments WHERE id=?",(s[0],)).fetchone(); c.close()
        self.instrument_dialog(r)

    def delete_instrument(self):
        s=self.itree.selection()
        if not s: return
        c=db()
        if c.execute("SELECT COUNT(*) FROM rentals WHERE instrument_id=?",(s[0],)).fetchone()[0]:
            c.close(); return messagebox.showwarning("Nie można usunąć","Instrument ma historię wypożyczeń. Pozostaw go w ewidencji.")
        c.execute("DELETE FROM instruments WHERE id=?",(s[0],)); c.commit(); c.close(); self.refresh_all()

    def instrument_dialog(self,r=None):
        w=tk.Toplevel(self); w.title("Instrument"); w.grab_set()
        fields=[("Numer ewidencyjny","inventory_no"),("Nazwa","name"),("Kategoria","category"),
                ("Marka","brand"),("Cena za dzień","price_day"),("Kaucja","deposit"),("Wartość instrumentu","instrument_value")]
        vars={}
        for i,(lab,key) in enumerate(fields):
            ttk.Label(w,text=lab).grid(row=i,column=0,padx=12,pady=6,sticky="w")
            v=tk.StringVar(value="" if not r else str(r[key] or "")); vars[key]=v
            ttk.Entry(w,textvariable=v,width=34).grid(row=i,column=1,padx=12,pady=6)
        ttk.Label(w,text="Zdjęcie").grid(row=7,column=0,padx=12,pady=6,sticky="w")
        pv=tk.StringVar(value="" if not r else str(r["photo"] or ""))
        ttk.Entry(w,textvariable=pv,width=26).grid(row=7,column=1,padx=12,pady=6,sticky="w")
        def choose():
            p=filedialog.askopenfilename(title="Wybierz zdjęcie",filetypes=[("Obrazy","*.jpg *.jpeg *.png *.webp"),("Wszystkie","*.*")])
            if p:
                ext=Path(p).suffix.lower() or ".jpg"
                name=(vars["inventory_no"].get().strip() or "instrument") + ext
                dest=PHOTOS/name
                try: shutil.copy2(p,dest); pv.set(str(Path("photos")/name))
                except Exception as e: messagebox.showerror("Błąd",str(e))
        ttk.Button(w,text="Wybierz zdjęcie…",command=choose).grid(row=7,column=2,padx=5)
        ttk.Label(w,text="Status").grid(row=8,column=0,padx=12,pady=6,sticky="w")
        status=tk.StringVar(value="Dostępny" if not r else r["status"])
        ttk.Combobox(w,textvariable=status,values=["Dostępny","Wypożyczony","Serwis","Wycofany"],state="readonly",width=31).grid(row=8,column=1,padx=12,pady=6)
        def save():
            try:
                if not vars["name"].get().strip() or not vars["category"].get().strip(): raise ValueError()
                price=float(vars["price_day"].get().replace(",",".")); dep=float(vars["deposit"].get().replace(",",".")); val=float(vars["instrument_value"].get().replace(",","."))
                inv=vars["inventory_no"].get().strip()
                if not inv: raise ValueError()
            except: return messagebox.showerror("Błąd","Numer ewidencyjny, nazwa, kategoria i poprawne wartości są wymagane.")
            c=db()
            try:
                if r:
                    c.execute("""UPDATE instruments SET inventory_no=?,name=?,category=?,brand=?,price_day=?,deposit=?,instrument_value=?,photo=?,status=? WHERE id=?""",
                              (inv,vars["name"].get(),vars["category"].get(),vars["brand"].get(),price,dep,val,pv.get(),status.get(),r["id"]))
                else:
                    c.execute("""INSERT INTO instruments(inventory_no,name,category,brand,price_day,deposit,instrument_value,photo,status)
                                 VALUES(?,?,?,?,?,?,?,?,?)""",
                              (inv,vars["name"].get(),vars["category"].get(),vars["brand"].get(),price,dep,val,pv.get(),status.get()))
                c.commit()
            except sqlite3.IntegrityError:
                c.close(); return messagebox.showerror("Błąd","Numer ewidencyjny musi być unikalny.")
            c.close(); w.destroy(); self.refresh_all()
        ttk.Button(w,text="Zapisz",command=save).grid(row=9,column=1,pady=12,sticky="e")

    # CUSTOMERS
    def customer_tab(self):
        f=self.tabs["Klienci"]; ttk.Button(f,text="Dodaj klienta",command=self.add_customer).pack(anchor="e",pady=(0,10))
        self.ctree=ttk.Treeview(f,columns=("name","phone","email"),show="headings")
        for c,t,w in [("name","Imię i nazwisko",300),("phone","Telefon",180),("email","E-mail",320)]:
            self.ctree.heading(c,text=t); self.ctree.column(c,width=w)
        self.ctree.pack(fill="both",expand=True)
        ttk.Button(f,text="Edytuj",command=self.edit_customer).pack(anchor="w",pady=8)
    def refresh_customers(self):
        for x in self.ctree.get_children(): self.ctree.delete(x)
        c=db()
        for r in c.execute("SELECT * FROM customers ORDER BY name").fetchall():
            self.ctree.insert("", "end", iid=r["id"], values=(r["name"],r["phone"],r["email"]))
        c.close()
    def add_customer(self): self.customer_dialog()
    def edit_customer(self):
        s=self.ctree.selection()
        if not s: return
        c=db(); r=c.execute("SELECT * FROM customers WHERE id=?",(s[0],)).fetchone(); c.close(); self.customer_dialog(r)
    def customer_dialog(self,r=None):
        w=tk.Toplevel(self); w.title("Klient"); w.grab_set(); vars={}
        for i,(lab,key) in enumerate([("Imię i nazwisko","name"),("Telefon","phone"),("E-mail","email")]):
            ttk.Label(w,text=lab).grid(row=i,column=0,padx=12,pady=7,sticky="w")
            v=tk.StringVar(value="" if not r else r[key]); vars[key]=v; ttk.Entry(w,textvariable=v,width=35).grid(row=i,column=1,padx=12,pady=7)
        def save():
            if not vars["name"].get().strip(): return
            c=db()
            if r: c.execute("UPDATE customers SET name=?,phone=?,email=? WHERE id=?",(vars["name"].get(),vars["phone"].get(),vars["email"].get(),r["id"]))
            else: c.execute("INSERT INTO customers(name,phone,email) VALUES(?,?,?)",(vars["name"].get(),vars["phone"].get(),vars["email"].get()))
            c.commit(); c.close(); w.destroy(); self.refresh_all()
        ttk.Button(w,text="Zapisz",command=save).grid(row=3,column=1,pady=12,sticky="e")

    # RENTALS
    def rental_tab(self):
        f=self.tabs["Wypożyczenia"]
        form=ttk.LabelFrame(f,text="Nowe wypożyczenie",padding=15); form.pack(fill="x")
        ttk.Label(form,text="Instrument").grid(row=0,column=0,sticky="w",padx=5,pady=5)
        self.inst_combo=ttk.Combobox(form,width=42,state="readonly"); self.inst_combo.grid(row=0,column=1,padx=5)
        ttk.Label(form,text="Klient").grid(row=0,column=2,sticky="w",padx=5)
        self.cust_combo=ttk.Combobox(form,width=34,state="readonly"); self.cust_combo.grid(row=0,column=3,padx=5)
        ttk.Label(form,text="Liczba dni").grid(row=1,column=0,sticky="w",padx=5,pady=5)
        self.days=tk.IntVar(value=3); ttk.Spinbox(form,from_=1,to=365,textvariable=self.days,width=10).grid(row=1,column=1,sticky="w",padx=5)
        ttk.Button(form,text="Wypożycz",command=self.rent).grid(row=1,column=3,sticky="e",pady=5)
        self.rtree=ttk.Treeview(f,columns=("inv","inst","cust","start","due","total","status"),show="headings")
        for c,t,w in [("inv","Nr ewid.",95),("inst","Instrument",200),("cust","Klient",190),("start","Od",95),("due","Do",95),("total","Kwota",90),("status","Status",100)]:
            self.rtree.heading(c,text=t); self.rtree.column(c,width=w)
        self.rtree.pack(fill="both",expand=True,pady=15); ttk.Button(f,text="Zwróć zaznaczone",command=self.return_rental).pack(anchor="w")
    def refresh_rental_choices(self):
        c=db()
        self.inst_map={f'{r["inventory_no"]} | {r["name"]} | {r["price_day"]:.2f} zł/dzień':r["id"] for r in c.execute("SELECT * FROM instruments WHERE status='Dostępny'").fetchall()}
        self.cust_map={f'{r["name"]} | {r["phone"]}':r["id"] for r in c.execute("SELECT * FROM customers ORDER BY name").fetchall()}
        c.close()
        if hasattr(self,"inst_combo"): self.inst_combo["values"]=list(self.inst_map); self.cust_combo["values"]=list(self.cust_map)
    def rent(self):
        if not self.inst_combo.get() or not self.cust_combo.get(): return messagebox.showwarning("Brak danych","Wybierz instrument i klienta.")
        days=max(1,int(self.days.get())); inst=self.inst_map[self.inst_combo.get()]; cust=self.cust_map[self.cust_combo.get()]
        c=db(); r=c.execute("SELECT price_day FROM instruments WHERE id=?",(inst,)).fetchone()
        total=r["price_day"]*days; start=date.today(); due=start+timedelta(days=days)
        c.execute("INSERT INTO rentals(instrument_id,customer_id,start_date,due_date,total) VALUES(?,?,?,?,?)",(inst,cust,start.isoformat(),due.isoformat(),total))
        c.execute("UPDATE instruments SET status='Wypożyczony' WHERE id=?",(inst,)); c.commit(); c.close(); self.refresh_all()
        messagebox.showinfo("Gotowe",f"Wypożyczono na {days} dni.\nKwota: {total:.2f} zł")
    def refresh_rentals(self):
        if not hasattr(self,"rtree"): return
        for x in self.rtree.get_children(): self.rtree.delete(x)
        c=db()
        for r in c.execute("""SELECT rentals.*,instruments.name iname,instruments.inventory_no inv,customers.name cname
          FROM rentals JOIN instruments ON instruments.id=instrument_id JOIN customers ON customers.id=customer_id
          WHERE rentals.status='Aktywne' ORDER BY due_date""").fetchall():
            self.rtree.insert("", "end",iid=r["id"],values=(r["inv"],r["iname"],r["cname"],r["start_date"],r["due_date"],f'{r["total"]:.2f} zł',r["status"]))
        c.close()
    def return_rental(self):
        s=self.rtree.selection()
        if not s: return
        c=db(); r=c.execute("SELECT instrument_id FROM rentals WHERE id=?",(s[0],)).fetchone()
        c.execute("UPDATE rentals SET status='Zwrócone',return_date=? WHERE id=?",(date.today().isoformat(),s[0]))
        c.execute("UPDATE instruments SET status='Dostępny' WHERE id=?",(r["instrument_id"],)); c.commit(); c.close(); self.refresh_all()

    # HISTORY
    def history_tab(self):
        f=self.tabs["Historia"]
        ttk.Button(f,text="Eksportuj historię do CSV",command=self.export_history).pack(anchor="e",pady=(0,8))
        self.htree=ttk.Treeview(f,columns=("inv","inst","cust","start","due","ret","total","status"),show="headings")
        for c,t,w in [("inv","Nr ewid.",90),("inst","Instrument",180),("cust","Klient",180),("start","Od",90),("due","Do",90),("ret","Zwrot",90),("total","Kwota",90),("status","Status",90)]:
            self.htree.heading(c,text=t); self.htree.column(c,width=w)
        self.htree.pack(fill="both",expand=True)
    def refresh_history(self):
        if not hasattr(self,"htree"): return
        for x in self.htree.get_children(): self.htree.delete(x)
        c=db()
        self.history_rows=c.execute("""SELECT rentals.*,instruments.name iname,instruments.inventory_no inv,customers.name cname
          FROM rentals JOIN instruments ON instruments.id=instrument_id JOIN customers ON customers.id=customer_id ORDER BY rentals.id DESC""").fetchall()
        for r in self.history_rows:
            self.htree.insert("", "end",values=(r["inv"],r["iname"],r["cname"],r["start_date"],r["due_date"],r["return_date"] or "-",f'{r["total"]:.2f} zł',r["status"]))
        c.close()
    def export_history(self):
        p=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile="historia_wypozyczen.csv")
        if not p: return
        with open(p,"w",newline="",encoding="utf-8-sig") as f:
            wr=csv.writer(f,delimiter=";"); wr.writerow(["Nr ewid.","Instrument","Klient","Od","Do","Zwrot","Kwota","Status"])
            for r in self.history_rows: wr.writerow([r["inv"],r["iname"],r["cname"],r["start_date"],r["due_date"],r["return_date"] or "-",f'{r["total"]:.2f}',r["status"]])
        messagebox.showinfo("Raport",f"Zapisano:\n{p}")

    # REPORTS
    def reports_tab(self):
        f=self.tabs["Raporty"]
        self.kpi=ttk.Frame(f); self.kpi.pack(fill="x",pady=10)
        self.report_text=tk.Text(f,height=18,font=("Consolas",11),state="disabled")
        self.report_text.pack(fill="both",expand=True,pady=10)
        bar=ttk.Frame(f); bar.pack(fill="x")
        ttk.Button(bar,text="Odśwież raport",command=self.refresh_reports).pack(side="left")
        ttk.Button(bar,text="Eksportuj raport CSV",command=self.export_report).pack(side="left",padx=6)
    def refresh_reports(self):
        if not hasattr(self,"report_text"): return
        c=db()
        total=c.execute("SELECT COUNT(*) n FROM instruments").fetchone()["n"]
        available=c.execute("SELECT COUNT(*) n FROM instruments WHERE status='Dostępny'").fetchone()["n"]
        rented=c.execute("SELECT COUNT(*) n FROM instruments WHERE status='Wypożyczony'").fetchone()["n"]
        value=c.execute("SELECT COALESCE(SUM(instrument_value),0) v FROM instruments").fetchone()["v"]
        revenue=c.execute("SELECT COALESCE(SUM(total),0) v FROM rentals").fetchone()["v"]
        active_revenue=c.execute("SELECT COALESCE(SUM(total),0) v FROM rentals WHERE status='Aktywne'").fetchone()["v"]
        overdue=c.execute("SELECT COUNT(*) n FROM rentals WHERE status='Aktywne' AND due_date < ?",(date.today().isoformat(),)).fetchone()["n"]
        clients=c.execute("SELECT COUNT(*) n FROM customers").fetchone()["n"]
        popular=c.execute("""SELECT instruments.name n,COUNT(*) cnt FROM rentals
          JOIN instruments ON instruments.id=instrument_id GROUP BY instrument_id ORDER BY cnt DESC LIMIT 5""").fetchall()
        c.close()
        for x in self.kpi.winfo_children(): x.destroy()
        for label,val in [("Instrumenty",total),("Dostępne",available),("Wypożyczone",rented),("Wartość ewidencyjna",f"{value:,.2f} zł"),("Klienci",clients)]:
            card=ttk.Frame(self.kpi,padding=12,relief="ridge"); card.pack(side="left",fill="x",expand=True,padx=4)
            ttk.Label(card,text=label).pack(); ttk.Label(card,text=str(val),style="KPI.TLabel").pack()
        lines=[
            "RAPORT WYPOŻYCZALNI", "="*55,
            f"Przychód zarejestrowanych wypożyczeń: {revenue:,.2f} zł",
            f"Wartość aktywnych wypożyczeń: {active_revenue:,.2f} zł",
            f"Przeterminowane wypożyczenia: {overdue}",
            "", "NAJCZĘŚCIEJ WYPOŻYCZANE INSTRUMENTY", "-"*55
        ]
        lines += [f"{i}. {r['n']} — {r['cnt']} wypożyczeń" for i,r in enumerate(popular,1)]
        lines += ["", "Raport można wyeksportować do CSV."]
        self.report_text.configure(state="normal"); self.report_text.delete("1.0","end"); self.report_text.insert("1.0","\n".join(lines)); self.report_text.configure(state="disabled")
    def export_report(self):
        p=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile="raport_wypozyczalni.csv")
        if not p: return
        c=db()
        rows=[
          ("Liczba instrumentów",c.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]),
          ("Dostępne",c.execute("SELECT COUNT(*) FROM instruments WHERE status='Dostępny'").fetchone()[0]),
          ("Wypożyczone",c.execute("SELECT COUNT(*) FROM instruments WHERE status='Wypożyczony'").fetchone()[0]),
          ("Wartość instrumentów",c.execute("SELECT COALESCE(SUM(instrument_value),0) FROM instruments").fetchone()[0]),
          ("Klienci",c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]),
          ("Przychód wypożyczeń",c.execute("SELECT COALESCE(SUM(total),0) FROM rentals").fetchone()[0]),
          ("Przeterminowane",c.execute("SELECT COUNT(*) FROM rentals WHERE status='Aktywne' AND due_date < ?",(date.today().isoformat(),)).fetchone()[0])
        ]; c.close()
        with open(p,"w",newline="",encoding="utf-8-sig") as f:
            wr=csv.writer(f,delimiter=";"); wr.writerow(["Metryka","Wartość"]); wr.writerows(rows)
        messagebox.showinfo("Raport",f"Zapisano:\n{p}")

if __name__=="__main__":
    init_db(); App().mainloop()
