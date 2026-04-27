#!/bin/bash

# --- Samba Server Auto-Setup Script for Kali Linux ---
echo "[-] Starting Samba Server Dependency Installation..."

# 1. Update system packages
echo "[*] Updating package lists..."
sudo apt update -y

# 2. Install System Dependencies
echo "[*] Installing Samba and Python tools..."
sudo apt install -y samba python3-pip python3-venv

# 3. Create Shared Directory
echo "[*] Setting up shared directory at /srv/samba/shared..."
sudo mkdir -p /srv/samba/shared
sudo chmod 1777 /srv/samba/shared

# 4. Setup Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

# 5. Install Python Dependencies
echo "[*] Installing Python requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Setup Sudoers (Check if already present)
SUDO_LINE="$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/smbpasswd, /usr/bin/mkdir, /usr/bin/chmod, /usr/bin/chown"
if ! sudo grep -q "smbpasswd" /etc/sudoers; then
    echo "[!] Adding NOPASSWD rules to /etc/sudoers. You might need to enter password once more..."
    echo "$SUDO_LINE" | sudo tee -a /etc/sudoers > /dev/null
fi

echo "[+] Installation Complete!"
echo "[+] To start the server, run: source venv/bin/activate && python app.py"
