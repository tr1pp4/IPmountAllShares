#!/usr/bin/env python3
"""
NAS Mount Manager - GUI Version mit Permanent Mount
Automatisches Mounten aller NAS-Shares mit GUI
Permanent Mounts via fstab (wie Windows Netzlaufwerke)
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
        self.root.geometry("750x650")
        self.root.configure(bg='#f0f0f0')
        
        self.config_file = Path.home() / '.nas_mount_config.json'
        self.cred_file = Path.home() / '.smbcredentials'
        
        self.setup_gui()
        self.load_config()
        self.check_permanent_mount_status()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = tk.Label(main_frame, text="🗄️ NAS Mount Manager", 
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#333')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        row = 1
        
        tk.Label(main_frame, text="🌐 NAS IP-Adresse:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        self.nas_ip_var = tk.StringVar(value="192.168.0.11")
        self.nas_ip_entry = ttk.Entry(main_frame, textvariable=self.nas_ip_var, width=30)
        self.nas_ip_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        row += 1
        tk.Label(main_frame, text="👤 Benutzername:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        row += 1
        tk.Label(main_frame, text="🔒 Passwort:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                       show="*", width=30)
        self.password_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
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
        
        row += 1
        self.permanent_var = tk.BooleanVar(value=False)
        permanent_check = ttk.Checkbutton(main_frame, 
                                         text="🔄 Permanent mounten (wie Windows-Netzlaufwerk)",
                                         variable=self.permanent_var,
                                         command=self.toggle_permanent_mount)
        permanent_check.grid(row=row, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row += 1
        self.permanent_status_var = tk.StringVar(value="")
        self.permanent_status_label = tk.Label(main_frame, 
                                               textvariable=self.permanent_status_var,
                                               font=('Arial', 9, 'italic'),
                                               bg='#f0f0f0', fg='#666')
        self.permanent_status_label.grid(row=row, column=0, columnspan=2, sticky=tk.W)
        
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
        
        row += 1
        self.status_var = tk.StringVar(value="Bereit")
        status_label = tk.Label(main_frame, textvariable=self.status_var, 
                               font=('Arial', 10), bg='#f0f0f0', fg='#666')
        status_label.grid(row=row, column=0, columnspan=2, pady=5)
        
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        row += 2
        tk.Label(main_frame, text="📋 Ausgabe:", font=('Arial', 10, 'bold'), 
                bg='#f0f0f0').grid(row=row, column=0, sticky=tk.W)
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=12, width=80, 
                                                    font=('Courier New', 9))
        self.output_text.grid(row=row+1, column=0, columnspan=2, pady=10, 
                             sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.setup_menu()
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(row+1, weight=1)
        
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Konfiguration speichern", command=self.save_config)
        file_menu.add_command(label="Konfiguration laden", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self.show_about)
    
    def browse_mount_path(self):
        path = filedialog.askdirectory(initialdir=self.mount_path_var.get())
        if path:
            self.mount_path_var.set(path)
    
    def log_output(self, message):
        def update():
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.root.update_idletasks()
        self.root.after(0, update)
    
    def run_command(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=120)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Timeout nach 120 Sekunden"
        except Exception as e:
            return 1, "", str(e)
    
    def check_permanent_mount_status(self):
        try:
            with open('/etc/fstab', 'r') as f:
                fstab_content = f.read()
            if 'NAS Permanent Mounts' in fstab_content:
                self.permanent_var.set(True)
                self.permanent_status_var.set("✅ Permanent-Mount ist aktiviert (fstab)")
            else:
                self.permanent_var.set(False)
                self.permanent_status_var.set("⚪ Permanent-Mount ist deaktiviert")
        except:
            self.permanent_var.set(False)
            self.permanent_status_var.set("")
    
    def toggle_permanent_mount(self):
        def toggle_worker():
            try:
                if self.permanent_var.get():
                    self.setup_permanent_mount()
                else:
                    self.disable_permanent_mount()
            except Exception as e:
                self.log_output(f"❌ Fehler: {str(e)}")
                self.permanent_var.set(not self.permanent_var.get())
        threading.Thread(target=toggle_worker, daemon=True).start()
    
    def setup_permanent_mount(self):
        self.log_output("🔧 Richte Permanent-Mount ein (fstab)...")
        
        nas_ip = self.nas_ip_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        mount_base = self.mount_path_var.get().strip()
        
        if not all([nas_ip, username, password]):
            self.log_output("❌ Bitte alle Felder ausfüllen!")
            self.permanent_var.set(False)
            return
        
        self.log_output(f"📝 Erstelle Credentials-Datei...")
        with open(self.cred_file, 'w') as f:
            f.write(f"username={username}\n")
            f.write(f"password={password}\n")
        os.chmod(self.cred_file, 0o600)
        self.log_output("✅ Credentials gesichert")
        
        cmd = f'timeout 30 smbclient -L "//{nas_ip}" -U "{username}%{password}" 2>/dev/null'
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode != 0:
            self.log_output(f"❌ Kann Shares nicht scannen")
            self.permanent_var.set(False)
            return
        
        shares = []
        for line in stdout.split('\n'):
            if 'Disk' in line:
                parts = line.split('Disk', 1)
                if parts:
                    share_name = parts[0].strip()
                    if share_name and not share_name.startswith('$') and share_name != 'IPC':
                        shares.append(share_name)
        
        if not shares:
            self.log_output("❌ Keine Shares gefunden!")
            self.permanent_var.set(False)
            return
        
        self.log_output(f"📋 Gefunden: {len(shares)} Shares")
        
        for share in shares:
            safe_name = share.replace(' ', '_').replace('/', '_')
            mount_point = f"{mount_base}/{safe_name}"
            subprocess.run(['sudo', 'mkdir', '-p', mount_point], capture_output=True)
        
        subprocess.run("sudo cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)", 
                      shell=True, capture_output=True)
        self.log_output("💾 fstab Backup erstellt")
        
        subprocess.run("sudo sed -i '/# NAS Permanent Mounts/,/^$/d' /etc/fstab", 
                      shell=True, capture_output=True)
        
        uid = os.getuid()
        gid = os.getgid()
        
        fstab_lines = ["\n# NAS Permanent Mounts - Created by NAS Mount Manager\n"]
        for share in shares:
            safe_name = share.replace(' ', '_').replace('/', '_')
            share_escaped = share.replace(' ', '%20')
            mount_point = f"{mount_base}/{safe_name}"
            line = f"//{nas_ip}/{share_escaped} {mount_point} cifs credentials={self.cred_file},uid={uid},gid={gid},file_mode=0777,dir_mode=0777,vers=3.0,_netdev,x-systemd.automount 0 0\n"
            fstab_lines.append(line)
        
        fstab_content = ''.join(fstab_lines)
        with open('/tmp/nas_fstab_append', 'w') as f:
            f.write(fstab_content)
        
        ret = subprocess.run("sudo tee -a /etc/fstab < /tmp/nas_fstab_append > /dev/null", 
                           shell=True, capture_output=True)
        
        if ret.returncode == 0:
            self.log_output("✅ fstab aktualisiert")
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], capture_output=True)
            subprocess.run(['sudo', 'mount', '-a'], capture_output=True)
            
            self.log_output("✅ Permanent-Mount aktiviert!")
            self.log_output(f"💡 {len(shares)} Shares dauerhaft gemountet (überlebt Reboot)")
            self.permanent_status_var.set("✅ Permanent-Mount ist aktiviert (fstab)")
            self.save_config()
        else:
            self.log_output("❌ Fehler beim Schreiben von fstab")
            self.permanent_var.set(False)
    
    def disable_permanent_mount(self):
        self.log_output("🔧 Deaktiviere Permanent-Mount...")
        
        subprocess.run("sudo cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)", 
                      shell=True, capture_output=True)
        self.log_output("💾 fstab Backup erstellt")
        
        ret = subprocess.run("sudo sed -i '/# NAS Permanent Mounts/,/^$/d' /etc/fstab", 
                           shell=True, capture_output=True)
        
        if ret.returncode == 0:
            self.log_output("✅ fstab-Einträge entfernt")
            
            mount_base = self.mount_path_var.get().strip()
            subprocess.run(['killall', 'kioworker'], capture_output=True)
            
            cmd = f'mount -t cifs | grep "{mount_base}"'
            returncode, stdout, _ = self.run_command(cmd)
            
            if returncode == 0 and stdout.strip():
                for line in stdout.strip().split('\n'):
                    if mount_base in line:
                        parts = line.split(' on ')
                        if len(parts) > 1:
                            mount_point = parts[1].split(' type')[0].strip()
                            subprocess.run(['sudo', 'umount', mount_point], capture_output=True)
            
            self.log_output("✅ Permanent-Mount deaktiviert")
            self.permanent_status_var.set("⚪ Permanent-Mount ist deaktiviert")
        else:
            self.log_output("❌ Fehler")
            self.permanent_var.set(True)
    
    def scan_shares(self):
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
                
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'samba-client'], 
                              capture_output=True)
                
                if username and password:
                    cmd = f'timeout 30 smbclient -L "//{nas_ip}" -U "{username}%{password}" 2>/dev/null'
                else:
                    cmd = f'timeout 30 smbclient -L "//{nas_ip}" -N 2>/dev/null'
                
                returncode, stdout, stderr = self.run_command(cmd)
                
                if returncode != 0:
                    self.log_output(f"❌ Verbindungsfehler")
                    return
                
                shares = []
                for line in stdout.split('\n'):
                    if 'Disk' in line:
                        parts = line.split('Disk', 1)
                        if parts:
                            share_name = parts[0].strip()
                            if share_name and not share_name.startswith('$') and share_name != 'IPC':
                                shares.append(share_name)
                
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
        def mount_worker():
            try:
                self.set_busy(True, "Mounte alle Shares...")
                
                nas_ip = self.nas_ip_var.get().strip()
                username = self.username_var.get().strip()
                password = self.password_var.get().strip()
                mount_base = self.mount_path_var.get().strip()
                
                if not all([nas_ip, username, password]):
                    self.log_output("❌ Bitte alle Felder ausfüllen!")
                    return
                
                cmd = f'timeout 30 smbclient -L "//{nas_ip}" -U "{username}%{password}" 2>/dev/null'
                returncode, stdout, stderr = self.run_command(cmd)
                
                if returncode != 0:
                    self.log_output(f"❌ Kann Shares nicht scannen")
                    return
                
                shares = []
                for line in stdout.split('\n'):
                    if 'Disk' in line:
                        parts = line.split('Disk', 1)
                        if parts:
                            share_name = parts[0].strip()
                            if share_name and not share_name.startswith('$') and share_name != 'IPC':
                                shares.append(share_name)
                
                if not shares:
                    self.log_output("❌ Keine Shares gefunden!")
                    return
                
                self.log_output(f"🚀 Mounte {len(shares)} Shares...")
                subprocess.run(['sudo', 'mkdir', '-p', mount_base], capture_output=True)
                
                success_count = 0
                for share in shares:
                    safe_name = share.replace(' ', '_').replace('/', '_')
                    mount_point = os.path.join(mount_base, safe_name)
                    
                    subprocess.run(['sudo', 'mkdir', '-p', mount_point], capture_output=True)
                    
                    cmd = f'sudo mount -t cifs "//{nas_ip}/{share}" "{mount_point}" -o "username={username},password={password},uid=1000,gid=1000,file_mode=0777,dir_mode=0777,vers=3.0,soft,_netdev"'
                    returncode, stdout, stderr = self.run_command(cmd)
                    
                    if returncode == 0:
                        self.log_output(f"✅ {share:<20} → {mount_point}")
                        success_count += 1
                    else:
                        self.log_output(f"❌ {share:<20} → FEHLER")
                
                self.log_output(f"📊 {success_count}/{len(shares)} Shares erfolgreich gemountet")
                self.save_config()
                
            except Exception as e:
                self.log_output(f"❌ Fehler: {str(e)}")
            finally:
                self.set_busy(False)
        
        threading.Thread(target=mount_worker, daemon=True).start()
    
    def unmount_all(self):
        def unmount_worker():
            try:
                self.set_busy(True, "Unmounte alle Shares...")
                mount_base = self.mount_path_var.get().strip()
                
                subprocess.run(['killall', 'kioworker'], capture_output=True)
                
                cmd = f'mount -t cifs | grep "{mount_base}"'
                returncode, stdout, stderr = self.run_command(cmd)
                
                if returncode != 0 or not stdout.strip():
                    self.log_output(f"📭 Keine Mounts gefunden")
                    return
                
                self.log_output("🔽 Unmounte alle Shares...")
                unmounted = 0
                
                for line in stdout.strip().split('\n'):
                    if mount_base in line:
                        parts = line.split(' on ')
                        if len(parts) > 1:
                            mount_point = parts[1].split(' type')[0].strip()
                            returncode, _, _ = self.run_command(f'sudo umount "{mount_point}"')
                            if returncode == 0:
                                self.log_output(f"✅ {mount_point}")
                                unmounted += 1
                
                self.log_output(f"📊 {unmounted} Shares unmounted")
                
            except Exception as e:
                self.log_output(f"❌ Fehler: {str(e)}")
            finally:
                self.set_busy(False)
        
        threading.Thread(target=unmount_worker, daemon=True).start()
    
    def set_busy(self, busy, status=""):
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
        config = {
            'nas_ip': self.nas_ip_var.get(),
            'username': self.username_var.get(),
            'mount_path': self.mount_path_var.get(),
            'permanent': self.permanent_var.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            pass
    
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.nas_ip_var.set(config.get('nas_ip', '192.168.0.11'))
                self.username_var.set(config.get('username', ''))
                self.mount_path_var.set(config.get('mount_path', '/mnt/nas'))
            except:
                pass
    
    def show_about(self):
        messagebox.showinfo("Über", 
            "NAS Mount Manager v3.0\n\n"
            "Einfaches Tool zum Mounten von NAS-Shares\n"
            "✓ Automatische Share-Erkennung\n"
            "✓ Systemweite Mounts\n"
            "✓ Share-Namen mit Leerzeichen\n"
            "✓ Permanent-Mount via fstab\n\n"
            "Erstellt für einfache Linux-NAS-Integration")

if __name__ == '__main__':
    root = tk.Tk()
    app = NASMountManager(root)
    root.mainloop()