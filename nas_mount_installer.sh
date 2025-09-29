#!/bin/bash
# NAS Mount Manager - Quick Installer
# Verwendung: curl -sSL https://IHR_SERVER/install.sh | bash

set -e

echo "🗄️  NAS Mount Manager - Quick Installer"
echo "========================================"

# Prüfe ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    echo "📦 Installiere Python3..."
    sudo dnf install -y python3 python3-pip python3-tkinter
fi

# Prüfe ob samba-client installiert ist
if ! command -v smbclient &> /dev/null; then
    echo "📦 Installiere samba-client..."
    sudo dnf install -y samba-client
fi

# Download des Scripts
echo "⬇️  Lade NAS Mount Manager herunter..."

# Option A: Von GitHub
SCRIPT_URL="https://raw.githubusercontent.com/IHR_USERNAME/nas-mount-manager/main/nas_mount_gui.py"

# Option B: Von Ihrem NAS/Server
# SCRIPT_URL="http://192.168.0.11/nas_mount_gui.py"

curl -sSL "$SCRIPT_URL" -o /tmp/nas_mount_gui.py

if [ ! -f /tmp/nas_mount_gui.py ]; then
    echo "❌ Download fehlgeschlagen!"
    exit 1
fi

chmod +x /tmp/nas_mount_gui.py

# Desktop-Eintrag erstellen
echo "🖥️  Erstelle Desktop-Verknüpfung..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/nas-mount-manager.desktop << EOF
[Desktop Entry]
Type=Application
Name=NAS Mount Manager
Comment=Mount all NAS shares easily
Exec=python3 /tmp/nas_mount_gui.py
Icon=folder-remote
Terminal=false
Categories=System;Network;
EOF

# Script nach ~/bin verschieben (optional)
mkdir -p ~/bin
cp /tmp/nas_mount_gui.py ~/bin/
chmod +x ~/bin/nas_mount_gui.py

# PATH anpassen falls nötig
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi

echo ""
echo "✅ Installation abgeschlossen!"
echo ""
echo "🚀 Starten Sie das Tool mit:"
echo "   1. python3 ~/bin/nas_mount_gui.py"
echo "   2. Oder über das Startmenü: 'NAS Mount Manager'"
echo ""
echo "💡 Tipp: Pinnen Sie es für schnellen Zugriff ans Panel!"
echo ""