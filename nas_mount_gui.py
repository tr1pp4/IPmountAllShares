#!/usr/bin/env python3
"""
NAS Mount Manager - GUI Version
Automatisches Mounten aller NAS-Shares mit GUI
Unterstützt Share-Namen mit Leerzeichen und Mount-Verifikation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import json
from pathlib import Path

class NASMountManager:
    def __init__(self, root):
        self.root = root
        self.root.title("🗄️ NAS Mount Manager")
        self.root.geometry("700x600")
        self.root.configure(bg='#f0f0f0')
        
        # Konfigurationsdatei
        self.config_file = Path.home() / '.nas_mount_config.json'
        
        self.setup_gui()
        self.load_config()
        
    def setup_gui(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(main_frame, text="🗄️ NAS Mount Manager", 
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#333')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Eingabefelder
        row = 1
        
        # NAS IP
        tk.Label(main_frame, text="🌐 NAS IP-Adresse:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        self.nas_ip_var = tk.StringVar(value="192.168.1.100")
        self.nas_ip_entry = ttk.Entry(main_frame, textvariable=self.nas_ip_var, width=30)
        self.nas_ip_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Username
        row += 1
        tk.Label(main_frame, text="👤 Benutzername:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Password
        row += 1
        tk.Label(main_frame, text="🔒 Passwort:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                       show="*", width=30)
        self.password_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Mount Path
        row += 1
        tk.Label(main_frame, text="📁 Mount-Pfad:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        self.mount_path_var = tk.StringVar(value="/mnt/nas")
        self.mount_path_entry = ttk.Entry(path_frame, textvariable=self.mount_path_var, width=25)
        self.mount_path_entry.grid(row=0, column=0)
        
        browse_btn = ttk.Button(path_frame, text="📂", width=3, 
                               command=self.browse_mount_path)
        browse_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Buttons
        row += 1
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        self.scan_btn = ttk.Button(button_frame, text="🔍 Shares Scannen", 
                                  command=self.scan_shares, width=20)
        self.scan_btn.grid(row=0, column=0, padx=5)
        
        self.mount_btn = ttk.Button(button_frame, text="⬆️ Alles Mounten", 
                                   command=self.mount_all, width=20)
        self.mount_btn.grid(row=0, column=1, padx=5)
        
        self.unmount_btn = ttk.Button(button_frame, text="⬇️ Alles Unmounten", 
                                     command=self.unmount_all, width=20)
        self.unmount_btn.grid(row=0, column=2, padx=5)
        
        # Status/Progress
        row += 1
        self.status_var = tk.StringVar(value="Bereit")
        status_label = tk.Label(main_frame, textvariable=self.status_var, 
                               font=('Arial', 10), bg='#f0f0f0', fg='#666')
        status_label.grid(row=row, column=0, columnspan=2, pady=5)
        
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Output Text
        row += 2
        tk.Label(main_frame, text="📋 Ausgabe:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W)
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=80, 
                                                    font=('Courier New', 9))
        self.output_text.grid(row=row+1, column=0, columnspan=2, pady=10, 
                             sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Menu
        self.setup_menu()
        
        # Grid weights für Responsive Design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(row+1, weight=1)
        
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Konfiguration speichern", command=self.save_config)
        file_menu.add_command(label="Konfiguration laden", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self.show_about)
    
    def browse_mount_path(self):
        path = filedialog.askdirectory(initialdir=self.mount_path_var.get())
        if path:
            self.mount_path_var.set(path)
    
    def log_output(self, message):
        """Thread-sichere Ausgabe in das Text-Widget"""
        def update():
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.root.update_idletasks()
        
        self.root.after(0, update)
    
    def run_command(self, cmd):
        """Führt Shell-Befehl aus und gibt Ergebnis zurück"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Timeout nach 30 Sekunden"
        except Exception as e:
            return 1, "", str(e)
    
    def scan_shares(self):
        """Scannt verfügbare Shares"""
        def scan_worker():
            try:
                self.set_busy(True, "Scanne Shares...")
                
                nas_ip = self.nas_ip_var.get().strip()
                username = self.username_var.get().strip()
                password = self.password_var.get().strip()
                
                if not nas_ip:
                    self.log_output("❌ Bitte NAS IP-Adresse eingeben!")
                    return
                
                self.log_output(f"🔍 Scanne Shares auf {nas_ip}...")
                
                # smbclient installieren falls nötig
                self.log_output("📦 Prüfe samba-client Installation...")
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'samba-client'], 
                              capture_output=True)
                
                # Shares scannen - mit Auth falls vorhanden, sonst anonym
                if username and password:
                    cmd = f'timeout 30 smbclient -L "//{nas_ip}" -U "{username}%{password}" 2>/dev/null'
                    self.log_output(f"🔐 Scanne mit Authentifizierung als '{username}'...")
                else:
                    cmd = f'timeout 30 smbclient -L "//{nas_ip}" -N 2>/dev/null'
                    self.log_output(f"🔓 Scanne anonym (ohne Login)...")
                
                returncode, stdout, stderr = self.run_command(cmd)
                
                if returncode != 0:
                    self.log_output(f"❌ Verbindungsfehler: {stderr}")
                    return
                
                # Shares extrahieren - vollständige Namen mit Leerzeichen
                shares = []
                in_share_section = False
                for line in stdout.split('\n'):
                    line = line.strip()
                    if 'Sharename' in line:
                        in_share_section = True
                        continue
                    if in_share_section and line.startswith('-'):
                        continue
                    if in_share_section and 'Disk' in line:
                        # Share-Name ist alles bis zum ersten Tab/mehreren Spaces vor "Disk"
                        parts = line.split('Disk', 1)
                        if parts:
                            share_name = parts[0].strip()
                            # Nur echte Shares, keine System-Shares
                            if share_name and not share_name.startswith('$') and share_name != 'IPC':
                                shares.append(share_name)
                    elif in_share_section and line and not line.startswith(' ') and 'IPC$' in line:
                        break
                
                if not shares:
                    self.log_output("❌ Keine Shares gefunden!")
                    return
                
                self.log_output(f"✅ {len(shares)} Shares gefunden:")
                for i, share in enumerate(shares, 1):
                    self.log_output(f"   {i:2d}. {share}")
                
                self.save_config()
                
            except Exception as e:
                self.log_output(f"❌ Fehler: {str(e)}")
            finally:
                self.set_busy(False)
        
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def mount_all(self):
        """Mountet alle Shares"""
        def mount_worker():
            try:
                self.set_busy(True, "Mounte alle Shares...")
                
                nas_ip = self.nas_ip_var.get().strip()
                username = self.username_var.get().strip()
                password = self.password_var.get().strip()
                mount_base = self.mount_path_var.get().strip()
                
                if not nas_ip:
                    self.log_output("❌ Bitte NAS IP-Adresse eingeben!")
                    return
                
                if not username or not password:
                    self.log_output("❌ Für das Mounten sind Username und Passwort erforderlich!")
                    return
                
                self.log_output(f"🔐 Mounte als Benutzer '{username}'...")
                
                # Erst Shares scannen - mit Auth
                cmd = f'timeout 30 smbclient -L "//{nas_ip}" -U "{username}%{password}" 2>/dev/null'
                returncode, stdout, stderr = self.run_command(cmd)
                
                if returncode != 0:
                    self.log_output(f"❌ Kann Shares nicht scannen: {stderr}")
                    return
                
                # Shares extrahieren aus Scan (vollständige Namen)
                shares = []
                in_share_section = False
                for line in stdout.split('\n'):
                    line_strip = line.strip()
                    if 'Sharename' in line_strip:
                        in_share_section = True
                        continue
                    if in_share_section and line_strip.startswith('-'):
                        continue
                    if in_share_section and 'Disk' in line:
                        # Share-Name extrahieren (alles vor "Disk")
                        parts = line.split('Disk', 1)
                        if parts:
                            share_name = parts[0].strip()
                            if share_name and not share_name.startswith('$') and share_name != 'IPC':
                                shares.append(share_name)
                    elif in_share_section and line_strip and 'IPC$' in line:
                        break
                
                if not shares:
                    self.log_output("❌ Keine Shares zum Mounten gefunden!")
                    return
                
                self.log_output(f"🚀 Mounte {len(shares)} Shares...")
                
                # Basis-Verzeichnis erstellen
                subprocess.run(['sudo', 'mkdir', '-p', mount_base], capture_output=True)
                
                success_count = 0
                for i, share in enumerate(shares):
                    self.status_var.set(f"Mounte {share} ({i+1}/{len(shares)})...")
                    self.root.update_idletasks()
                    
                    # Sicherer Ordnername (Leerzeichen durch _ ersetzen für Ordner)
                    safe_folder_name = share.replace(' ', '_').replace('/', '_')
                    mount_point = os.path.join(mount_base, safe_folder_name)
                    
                    subprocess.run(['sudo', 'mkdir', '-p', mount_point], capture_output=True)
                    
                    # Mount-Befehl - Share-Name in Anführungszeichen für Leerzeichen
                    cmd = f'sudo mount -t cifs "//{nas_ip}/{share}" "{mount_point}" -o "username={username},password={password},uid=1000,gid=1000,file_mode=0777,dir_mode=0777,vers=3.0"'
                    
                    returncode, stdout, stderr = self.run_command(cmd)
                    
                    if returncode == 0:
                        # Prüfen ob Mount wirklich funktioniert hat
                        test_cmd = f'ls -la "{mount_point}" | wc -l'
                        test_ret, test_out, _ = self.run_command(test_cmd)
                        
                        if test_ret == 0 and int(test_out.strip()) > 2:  # Mehr als . und ..
                            self.log_output(f"✅ {share:<20} → {mount_point} (Inhalt gefunden)")
                            success_count += 1
                        else:
                            self.log_output(f"⚠️  {share:<20} → {mount_point} (Mount OK, aber leer)")
                            success_count += 1
                    else:
                        self.log_output(f"❌ {share:<20} → FEHLER: {stderr.strip()}")
                        # Bei Fehlern auch stderr detaillierter ausgeben
                        if "Permission denied" in stderr:
                            self.log_output(f"   💡 Tipp: Prüfen Sie Username/Passwort für Share '{share}'")
                        elif "No such file or directory" in stderr:
                            self.log_output(f"   💡 Tipp: Share '{share}' existiert nicht oder ist nicht verfügbar")
                
                self.log_output(f"📊 {success_count}/{len(shares)} Shares erfolgreich gemountet")
                self.log_output(f"📁 Verfügbar unter: {mount_base}/")
                
                self.save_config()
                
            except Exception as e:
                self.log_output(f"❌ Fehler: {str(e)}")
            finally:
                self.set_busy(False)
        
        threading.Thread(target=mount_worker, daemon=True).start()
    
    def unmount_all(self):
        """Unmountet alle CIFS-Shares"""
        def unmount_worker():
            try:
                self.set_busy(True, "Unmounte alle Shares...")
                
                mount_base = self.mount_path_var.get().strip()
                
                # Alle CIFS-Mounts finden
                cmd = f'mount -t cifs | grep "{mount_base}"'
                returncode, stdout, stderr = self.run_command(cmd)
                
                if returncode != 0 or not stdout.strip():
                    self.log_output(f"📭 Keine CIFS-Mounts in {mount_base} gefunden.")
                    return
                
                self.log_output("🔽 Unmounte alle CIFS-Shares...")
                unmounted = 0
                
                for line in stdout.strip().split('\n'):
                    if mount_base in line:
                        # Mount-Point extrahieren
                        parts = line.split(' on ')
                        if len(parts) > 1:
                            mount_point = parts[1].split(' type')[0].strip()
                            
                            cmd = f'sudo umount "{mount_point}"'
                            returncode, _, stderr = self.run_command(cmd)
                            
                            if returncode == 0:
                                self.log_output(f"✅ {mount_point}")
                                unmounted += 1
                            else:
                                self.log_output(f"❌ {mount_point} → {stderr.strip()}")
                
                self.log_output(f"📊 {unmounted} Shares unmounted")
                
            except Exception as e:
                self.log_output(f"❌ Fehler: {str(e)}")
            finally:
                self.set_busy(False)
        
        threading.Thread(target=unmount_worker, daemon=True).start()
    
    def set_busy(self, busy, status=""):
        """Setzt GUI in Busy-Modus"""
        self.scan_btn.config(state='disabled' if busy else 'normal')
        self.mount_btn.config(state='disabled' if busy else 'normal')
        self.unmount_btn.config(state='disabled' if busy else 'normal')
        
        if busy:
            self.progress.start()
            self.status_var.set(status or "Arbeite...")
        else:
            self.progress.stop()
            self.status_var.set("Bereit")
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        config = {
            'nas_ip': self.nas_ip_var.get(),
            'username': self.username_var.get(),
            'mount_path': self.mount_path_var.get()
            # Passwort wird nicht gespeichert aus Sicherheitsgründen
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.log_output(f"⚠️ Konfiguration konnte nicht gespeichert werden: {e}")
    
    def load_config(self):
        """Lädt gespeicherte Konfiguration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.nas_ip_var.set(config.get('nas_ip', '192.168.1.100'))
                self.username_var.set(config.get('username', ''))
                self.mount_path_var.set(config.get('mount_path', '/mnt/nas'))
                
            except Exception as e:
                self.log_output(f"⚠️ Konfiguration konnte nicht geladen werden: {e}")
    
    def show_about(self):
        messagebox.showinfo("Über", 
            "NAS Mount Manager v1.0\n\n"
            "Einfaches Tool zum Mounten von NAS-Shares\n"
            "Automatische Share-Erkennung und systemweite Mounts\n"
            "Unterstützt Share-Namen mit Leerzeichen\n\n"
            "Erstellt für einfache Linux-NAS-Integration")

if __name__ == '__main__':
    root = tk.Tk()
    app = NASMountManager(root)
    root.mainloop()