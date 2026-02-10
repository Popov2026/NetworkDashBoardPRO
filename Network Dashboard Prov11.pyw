import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import os, json, subprocess, socket, threading, time, webbrowser, re, binascii
import sys
from concurrent.futures import ThreadPoolExecutor

# --- Chemins des fichiers et constantes système ---
if getattr(sys, 'frozen', False):
    # Si l'application est compilée, on utilise le dossier de l'EXE
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    # Sinon, on utilise le dossier du script .py
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(SCRIPT_DIR, "config_reseau_pro_v11.json")
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings_pro.json")
CREATE_NO_WINDOW = 0x08000000

class NetworkDashboard:
    def __init__(self, root):
        # --- Initialisation de la fenêtre principale ---
        self.root = root
        self.root.title("Network Dashboard Pro v1.1 - By Popov - ©2026")
        self.root.geometry("650x850")
     
        # --- Chargement des configurations ---
        self.data = self.load_config()
        self.settings = self.load_settings()
        self.status_widgets = {}
        self.scan_results = []
        
        # --- Création de la barre d'outils supérieure ---
        self.toolbar = tk.Frame(root, pady=10)
        self.toolbar.pack(fill="x")
        tk.Button(self.toolbar, text="🚀 Scan Plage IP", bg="#bbdefb", font=("Arial", 9, "bold"), command=self.open_scanner).pack(side="left", padx=10)
        tk.Button(self.toolbar, text="📁 + Catégorie", bg="#cfd8dc", command=self.add_category).pack(side="left", padx=10)
        
        self.ping_enabled = tk.BooleanVar(value=self.settings.get("ping_enabled", True))
        tk.Checkbutton(self.toolbar, text="Activer Ping", variable=self.ping_enabled, command=self.save_all).pack(side="left", padx=20)
        
        tk.Button(self.toolbar, text="📥 Import JSON", bg="#b2dfdb", command=self.import_config).pack(side="right", padx=10)
        tk.Button(self.toolbar, text="📄 Export TXT", bg="#ffe0b2", command=self.exporter_txt).pack(side="right", padx=5)
        
        # --- Zone de saisie pour l'ajout manuel ---
        self.frame_add = tk.LabelFrame(root, text="Ajout manuel", padx=10, pady=10)
        self.frame_add.pack(pady=10, padx=10, fill="x")
        self.e_name = tk.Entry(self.frame_add, width=15)
        self.e_name.insert(0, "Nom"); self.e_name.pack(side="left", padx=2)
        self.e_ip = tk.Entry(self.frame_add, width=15); self.e_ip.insert(0, self.settings.get("ip_start", "192.168.1.2"))
        self.e_ip.pack(side="left", padx=2)
        self.e_mac = tk.Entry(self.frame_add, width=19); self.e_mac.insert(0, "AA:BB:CC:DD:EE:FF")
        self.e_mac.pack(side="left", padx=2)
        # Ajout du séparateur automatique pour la MAC
        self.e_mac.bind("<KeyRelease>", self.format_mac_event)
        
        self.cat_var = tk.StringVar()
        self.cat_menu = ttk.Combobox(self.frame_add, textvariable=self.cat_var, width=20, state="readonly")
        self.cat_menu.pack(side="left", padx=5)
        self.update_cat_menu()
        if self.settings.get("last_cat") in self.data: self.cat_var.set(self.settings["last_cat"])
        tk.Button(self.frame_add, text="Ajouter", bg="#c8e6c9", command=self.add_manual).pack(side="left", padx=5)

        # --- Zone principale avec défilement (Scrollbar) ---
        self.outer_frame = tk.Frame(root)
        self.outer_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(self.outer_frame, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.outer_frame, orient="vertical", command=self.canvas.yview)
        self.main_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True); self.scrollbar.pack(side="right", fill="y")
        self.main_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.refresh_ui()
        # Démarrage du thread de surveillance Ping
        threading.Thread(target=self.ping_loop, daemon=True).start()

    # --- Formattage automatique MAC ---
    def format_mac_event(self, event):
        if event.keysym == "BackSpace": return
        val = self.e_mac.get().upper().replace(":", "")
        
        if len(val) > 12: val = val[:12]
        new_val = ":".join(val[i:i+2] for i in range(0, len(val), 2))
        self.e_mac.delete(0, tk.END)
        self.e_mac.insert(0, new_val)

    # --- Affichage et mise à jour de l'interface ---
    def refresh_ui(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()
        self.status_widgets = {}
        for cat_name, content in sorted(self.data.items(), key=lambda x: x[1].get('index', 99)):
            f_cat = tk.Frame(self.main_frame, bg="#37474f", pady=5)
            f_cat.pack(fill="x", pady=(15, 2))
            lbl_cat = tk.Label(f_cat, text=cat_name.upper(), font=("Arial", 10, "bold"), bg="#37474f", fg="white")
            lbl_cat.pack(side="left", padx=10)
            lbl_cat.bind("<Button-3>", lambda e, c=cat_name: self.show_category_menu(e, c))
            
            tk.Button(f_cat, text="IP(s)", font=("Arial", 7), bg="#455a64", fg="white", command=lambda c=cat_name: self.sort_devs(c, 'ip')).pack(side="right", padx=2)
            tk.Button(f_cat, text="Nom(s)", font=("Arial", 7), bg="#455a64", fg="white", command=lambda c=cat_name: self.sort_devs(c, 'name')).pack(side="right", padx=2)
            
            for i, d in enumerate(content["devices"]):
                row = tk.Frame(self.main_frame, pady=2)
                row.pack(fill="x", padx=10); sid = f"{cat_name}_{i}"
                dot = tk.Label(row, text="●", fg=d.get('status', 'gray'), font=("Arial", 12))
                dot.pack(side="left", padx=5); self.status_widgets[sid] = dot
                n_l = tk.Label(row, text=d['name'], width=18, anchor="w", font=("Arial", 9, "bold"))
                n_l.pack(side="left")
                n_l.bind("<Button-3>", lambda e, c=cat_name, idx=i: self.show_device_menu(e, c, idx))
                tk.Label(row, text=d['ip'], width=13, anchor="w").pack(side="left")
                
                # Visibilité MAC
                tk.Label(row, text=d.get('mac', ''), width=18, anchor="w", fg="#607d8b", font=("Arial", 8)).pack(side="left")
 
                active_tools = d.get("tools", content.get("tools", ["UNC", "URL", "WOL", "MSTSC"]))
                
                if "UNC" in active_tools:
                    b = tk.Button(row, text="UNC", width=5, command=lambda ip=d['ip'], dev=d: os.startfile(f"\\\\{ip}\\{dev.get('unc_path', '')}"))
                    b.pack(side="left", padx=1)
                    b.bind("<Button-3>", lambda e, c=cat_name, idx=i: self.set_extra(c, idx, "unc_path", "Dossier"))
                if "URL" in active_tools:
                    b = tk.Button(row, text="URL", width=5, bg="#e3f2fd", command=lambda u=d.get('url', d['ip']): webbrowser.open(u if "http" in u else f"http://{u}"))
                    b.pack(side="left", padx=1)
                    b.bind("<Button-3>", lambda e, c=cat_name, idx=i: self.set_extra(c, idx, "url", "URL"))
                if "WOL" in active_tools:
                    b = tk.Button(row, text="WOL", width=5, bg="#e8f5e9", command=lambda m=d['mac'], dev=d: self.wake_on_lan(m, dev))
                    b.pack(side="left", padx=1)
                    b.bind("<Button-3>", lambda e, c=cat_name, idx=i: self.show_wol_cfg(c, idx))
                if "MSTSC" in active_tools:
                    b = tk.Button(row, text="RDP", width=5, bg="#fff9c4", command=lambda ip=d['ip'], dev=d: subprocess.Popen(f"mstsc /v:{ip} {dev.get('rdp_args', '')}", creationflags=CREATE_NO_WINDOW))
                    b.pack(side="left", padx=1)
                    b.bind("<Button-3>", lambda e, c=cat_name, idx=i: self.set_extra(c, idx, "rdp_args", "Arguments RDP"))
                tk.Button(row, text="🗑", fg="#ef5350", bd=0, command=lambda c=cat_name, idx=i: self.delete_dev(c, idx)).pack(side="right", padx=10)

    # --- Tri des appareils ---
    def sort_devs(self, c, k):
        if k == 'ip': self.data[c]["devices"].sort(key=lambda x: [int(y) for y in re.findall(r'\d+', x[k])])
        else: self.data[c]["devices"].sort(key=lambda x: x[k].lower())
        self.save_all()
        self.refresh_ui()

    # --- Menu contextuel pour les catégories ---
    def show_category_menu(self, e, cat):
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="🛠 Configurer outils (Catégorie)", command=lambda: self.manage_tools_category(cat))
        m.add_command(label="🔢 Changer Index (Ordre)", command=lambda: self.set_category_index(cat))
        m.add_command(label="🗑 Supprimer Catégorie", command=lambda: self.delete_cat(cat))
        m.post(e.x_root, e.y_root)

    # --- Gestion de l'index de la catégorie ---
    def set_category_index(self, cat):
        idx = simpledialog.askinteger("Ordre", f"Position (index) pour {cat} :", initialvalue=self.data[cat].get('index', 99))
        if idx is not None:
            self.data[cat]['index'] = idx
            self.save_all()
            self.refresh_ui()

    # --- Configuration des outils activés pour toute une catégorie ---
    def manage_tools_category(self, cat):
        win = tk.Toplevel(self.root)
        win.title(f"Outils : {cat}")
        win.geometry("250x220")
        current = self.data[cat].get("tools", ["UNC", "URL", "WOL", "MSTSC"])
        vars = {}
        for t in ["UNC", "URL", "WOL", "MSTSC"]:
            vars[t] = tk.BooleanVar(value=t in current)
            tk.Checkbutton(win, text=t, variable=vars[t]).pack(anchor="w", padx=30, pady=2)
        tk.Button(win, text="Appliquer à la catégorie", bg="#cfd8dc", command=lambda: [self.data[cat].update({"tools": [t for t, v in vars.items() if v.get()]}), self.save_all(), self.refresh_ui(), win.destroy()]).pack(pady=10)

    # --- Logique du Scanner IP ---
    def open_scanner(self):
        sw = tk.Toplevel(self.root)
        sw.title("Scanner"); sw.geometry("500x600")
        f = tk.Frame(sw, pady=10)
        f.pack(fill="x")
        s_e = tk.Entry(f, width=12); s_e.insert(0, "192.168.1.2")
        s_e.pack(side="left", padx=5)
        e_e = tk.Entry(f, width=12); e_e.insert(0, "192.168.1.100")
        e_e.pack(side="left", padx=5)
        cat_v = tk.StringVar(value=self.cat_var.get())
        cb_scan = ttk.Combobox(f, textvariable=cat_v, values=list(self.data.keys()), width=15, state="readonly")
        cb_scan.pack(side="left", padx=5)
        p = ttk.Progressbar(sw, length=500)
        p.pack(pady=5)
        c = tk.Canvas(sw); v = tk.Scrollbar(sw, command=c.yview); fr = tk.Frame(c)
        c.create_window((0,0), window=fr, anchor="nw", width=580)
        c.configure(yscrollcommand=v.set); c.pack(side="left", fill="both", expand=True)
        v.pack(side="right", fill="y")
        fr.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        tk.Button(sw, text="Scanner", command=lambda: [cb_scan.config(values=list(self.data.keys())), threading.Thread(target=self.run_scan, args=(s_e.get(), e_e.get(), fr, p, cat_v), daemon=True).start()]).pack(pady=10)

    # --- Exécution du scan en multithread ---
    def run_scan(self, start, end, frame, prog, cat_v):
        self.scan_results = []
        for w in frame.winfo_children(): w.destroy()
        base = ".".join(start.split(".")[:-1])
        s, e = int(start.split(".")[-1]), int(end.split(".")[-1])
        ips = [f"{base}.{i}" for i in range(s, e + 1)]
        prog["maximum"] = len(ips)
        prog["value"] = 0
        with ThreadPoolExecutor(max_workers=50) as ex:
            for ip in ips: ex.submit(self.do_scan, ip, prog)
        self.scan_results.sort(key=lambda x: [int(y) for y in re.findall(r'\d+', x[0])])
        self.root.after(0, lambda: self.display_scan_results(frame, cat_v))

    # --- Scan unitaire (Ping + ARP) ---
    def do_scan(self, ip, prog):
        subprocess.call(f"ping -n 1 -w 150 {ip}", stdout=subprocess.DEVNULL, shell=True, creationflags=CREATE_NO_WINDOW)
        try:
            out = subprocess.check_output(f"arp -a {ip}", shell=True, creationflags=CREATE_NO_WINDOW).decode('cp1252')
            m = re.search(r'([0-9a-f-]{17})', out, re.I)
            if m:
                mac = m.group(1).replace("-", ":").upper()
                dns = "Inconnu"
                try: dns = socket.gethostbyaddr(ip)[0]
                except: pass
                self.scan_results.append((ip, mac, dns))
        except: pass
        self.root.after(0, lambda: prog.step(1))

    # --- Affichage des résultats du scan ---
    def display_scan_results(self, frame, cat_v_ref):
        for ip, mac, dns in self.scan_results:
            r = tk.Frame(frame)
            r.pack(fill="x", padx=10, pady=2)
            tk.Button(r, text="+", bg="#c8e6c9", command=lambda i=ip, m=mac, d=dns: self.add_from_scan(i, m, d, cat_v_ref.get())).pack(side="left", padx=5)
            tk.Label(r, text=f"{ip} | {mac} | {dns}", font=("Consolas", 9)).pack(side="left")

    # --- Ajout d'un résultat de scan aux données ---
    def add_from_scan(self, ip, mac, dns, cat):
        if cat in self.data:
            self.data[cat]["devices"].append({"name": dns.split('.')[0] if dns != "Inconnu" else ip, "ip": ip, "mac": mac})
            self.save_all()
            self.refresh_ui()

    # --- Menu contextuel pour un appareil ---
    def show_device_menu(self, e, cat, idx):
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="✎ Renommer", command=lambda: self.edit_name(cat, idx))
        m.add_command(label="⭐ Configurer outils (Appareil)", command=lambda: self.manage_tools_device(cat, idx))
        m.add_separator()
        m.add_command(label="📦 Déplacer", command=lambda: self.move_device(cat, idx))
        m.post(e.x_root, e.y_root)

    # --- Configuration outils spécifique à un appareil ---
    def manage_tools_device(self, cat, idx):
        win = tk.Toplevel(self.root)
        win.title("Outils Perso")
        win.geometry("200x200")
        d = self.data[cat]["devices"][idx]
        current = d.get("tools", self.data[cat].get("tools", ["UNC", "URL", "WOL", "MSTSC"]))
        vars = {}
        for t in ["UNC", "URL", "WOL", "MSTSC"]:
            vars[t] = tk.BooleanVar(value=t in current)
            tk.Checkbutton(win, text=t, variable=vars[t]).pack(anchor="w", padx=20)
        tk.Button(win, text="OK", command=lambda: [d.update({"tools": [t for t, v in vars.items() if v.get()]}), self.save_all(), self.refresh_ui(), win.destroy()]).pack(pady=10)

    # --- Fonction Wake-On-LAN ---
    def wake_on_lan(self, mac, dev):
        try:
            clean_mac = re.sub(r'[^a-fA-F0-9]', '', mac)
            mac_bytes = binascii.unhexlify(clean_mac)
            magic_packet = b'\xff' * 6 + mac_bytes * 16
            repeat = max(2, int(dev.get('wol_repeat', 3)))
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                for _ in range(repeat):
                    s.sendto(magic_packet, (dev['ip'], int(dev.get('wol_port', 9))))
                    s.sendto(magic_packet, ('255.255.255.255', int(dev.get('wol_port', 9))))
                time.sleep(0.1)
            messagebox.showinfo("WOL", "Signal envoyé")
        except: pass

    # --- Gestion des fichiers JSON ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding='utf-8') as f: return json.load(f)
        return {"Général": {"devices": [], "tools": ["UNC", "URL", "WOL", "MSTSC"], "index": 1}}

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding='utf-8') as f: return json.load(f)
        return {"ip_start": "192.168.1.2", "ip_end": "192.168.1.100", "last_cat": "Général", "ping_enabled": True}

    def save_all(self):
        with open(CONFIG_FILE, "w", encoding='utf-8') as f: json.dump(self.data, f, indent=4)
        self.settings.update({"last_cat": self.cat_var.get(), "ip_start": self.e_ip.get(), "ping_enabled": self.ping_enabled.get()})
        with open(SETTINGS_FILE, "w", encoding='utf-8') as f: json.dump(self.settings, f, indent=4)

    # --- Boucle de surveillance Ping ---
    def ping_loop(self):
        while True:
            if self.ping_enabled.get():
                for cat, content in self.data.items():
                    for i, d in enumerate(content["devices"]):
                        res = subprocess.call(f"ping -n 1 -w 200 {d['ip']}", stdout=subprocess.DEVNULL, shell=True, creationflags=CREATE_NO_WINDOW)
                        sid = f"{cat}_{i}"
                        if sid in self.status_widgets: self.root.after(0, lambda s=sid, c="green" if res==0 else "red": self.status_widgets[s].config(fg=c))
            time.sleep(20)

    # --- Fonctions utilitaires diverses ---
    def show_wol_cfg(self, cat, idx):
        d = self.data[cat]["devices"][idx]
        new = simpledialog.askstring("WOL", "Port,TTL,Repeat :", initialvalue=f"{d.get('wol_port',9)},{d.get('wol_ttl',128)},{d.get('wol_repeat',3)}")
        if new:
            try: p, t, r = map(int, new.split(',')); d.update({"wol_port": p, "wol_ttl": t, "wol_repeat": r}); self.save_all()
            except: pass

    def set_extra(self, cat, idx, key, hint):
        d = self.data[cat]["devices"][idx]
        old = d.get(key, "")
        if not old:
            if key == 'url': old = f"http://{d['ip']}"
            elif key == 'unc_path': old = "c$"
            elif key == 'rdp_args': old = "/f /admin"
        val = simpledialog.askstring("Config", f"{hint} :", initialvalue=str(old))
        if val is not None: 
            d[key] = val; self.save_all()
            self.refresh_ui()

    def exporter_txt(self):
        fp = filedialog.asksaveasfilename(defaultextension=".txt")
        if fp:
            with open(fp, "w") as f:
                for c, ct in self.data.items():
                    f.write(f"[{c}]\n")
                    for d in ct["devices"]: 
                        f.write(f"{d['name']} - {d['ip']} - {d.get('mac', '')}\n")

    # --- Gestion des catégories et appareils (CRUD) ---
    def update_cat_menu(self): self.cat_menu['values'] = list(self.data.keys())
    
    def add_manual(self):
        c = self.cat_var.get()
        if c in self.data: self.data[c]["devices"].append({"name": self.e_name.get(), "ip": self.e_ip.get(), "mac": self.e_mac.get()})
        self.save_all(); self.refresh_ui()
        
    def delete_dev(self, cat, idx): 
        if messagebox.askyesno("Suppr", "Supprimer ?"): del self.data[cat]["devices"][idx]
        self.save_all(); self.refresh_ui()
        
    def add_category(self):
        n = simpledialog.askstring("Cat", "Nom :", parent=self.root)
        if n:
            i = simpledialog.askinteger("Index", "Numéro d'ordre :", initialvalue=99, parent=self.root)
            self.data[n] = {"devices": [], "tools": ["UNC", "URL", "WOL", "MSTSC"], "index": i if i is not None else 99}
            self.update_cat_menu()
            self.save_all(); self.refresh_ui()
        
    def delete_cat(self, cat):
        if messagebox.askyesno("X", f"Supprimer {cat} ?"): del self.data[cat]
        self.save_all(); self.update_cat_menu(); self.refresh_ui()
        
    def edit_name(self, cat, idx):
        n = simpledialog.askstring("Nom", "Nom :", initialvalue=self.data[cat]["devices"][idx]["name"])
        if n: self.data[cat]["devices"][idx]["name"] = n
        self.save_all(); self.refresh_ui()
        
    def move_device(self, oc, idx):
        mv = tk.Toplevel(self.root)
        ch = ttk.Combobox(mv, values=list(self.data.keys()), state="readonly"); ch.pack(padx=20, pady=20); ch.set(oc)
        tk.Button(mv, text="OK", command=lambda: [self.data[ch.get()]["devices"].append(self.data[oc]["devices"].pop(idx)), self.save_all(), self.refresh_ui(), mv.destroy()]).pack()
        
    def import_config(self):
        fp = filedialog.askopenfilename()
        if fp:
            with open(fp, "r", encoding='utf-8') as f: self.data = json.load(f)
            self.save_all()
            self.update_cat_menu(); self.refresh_ui()

if __name__ == "__main__":
    root = tk.Tk(); app = NetworkDashboard(root); root.mainloop()