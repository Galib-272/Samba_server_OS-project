<div align="center">

# 🔐 Samba Web Authentication Server

**A secure, OTP-verified web gateway for Linux Samba file sharing.**


</div>

---

## ✨ Overview

Users must authenticate through the web app and complete **OTP verification** before their Samba share access is dynamically enabled — enforced at the system level using `smbpasswd`.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🧩 **Flask Backend** | Session-managed authentication flow |
| 📧 **Email OTP** | Real email or simulation mode (OTP in terminal) |
| ⚙️ **Dynamic Access Control** | Enables/disables Samba users via `smbpasswd` |
| 🎨 **Premium Dark UI** | Glassmorphism design |

---

## 🛠️ Prerequisites

- Linux server with **Samba** installed
- **Python 3.8+**
- **Sudo access** for the web application user

---

## 📦 Setup Instructions

### 1 · Install Dependencies

```bash
pip install flask flask-mail
```

---

### 2 · Configure Samba (`/etc/samba/smb.conf`)

```ini
[SharedFiles]
    path = /srv/samba/shared
    browseable = yes
    read only = no
    guest ok = no
    # Owners get full access, others get read-only
    create mask = 0644
    directory mask = 0755
    force create mode = 0644
    force directory mode = 0755
```

---

### 3 · Set Linux Permissions (Sticky Bit)

The **Sticky Bit** prevents users from deleting or renaming files owned by others, even with write access to the directory.

```bash
# Create the shared directory
sudo mkdir -p /srv/samba/shared

# Assign group ownership
sudo chgrp smbusers /srv/samba/shared
sudo chmod 2775 /srv/samba/shared

# Set the Sticky Bit
sudo chmod +t /srv/samba/shared
```

---

### 4 · Grant Sudo Privileges

Edit `/etc/sudoers` to allow the web server to run access control commands:

```text
www-data ALL=(ALL) NOPASSWD: /usr/bin/smbpasswd, /usr/bin/chmod, /usr/bin/chown
```

---

### 5 · App Configuration

Edit `config.py` to add your SMTP credentials for real email OTP.
By default, the app runs in **Simulation Mode** — the OTP is printed to the terminal.

---

### 6 · Run the App

```bash
python app.py
```

---

## 🔒 How It Works

```
User visits web app
        │
        ▼
  Enters credentials
        │
        ▼
  OTP sent via email
        │
        ▼
  OTP verified ──► sudo smbpasswd -e <user>  ──► ✅ Samba Access ENABLED
        │
        ▼
  User logs out ──► sudo smbpasswd -d <user>  ──► ❌ Samba Access DISABLED
```

| State | Behavior |
|---|---|
| **Before Login** | Account is disabled — connections fail even with correct password |
| **After OTP** | Flask runs `sudo smbpasswd -e <user>` — Samba accepts connections |
| **On Logout / Timeout** | Flask runs `sudo smbpasswd -d <user>` — access is revoked |

---

## 💻 Client Access Guide

### 🪟 Windows

1. Press `Win + R`
2. Type `\\<SERVER_IP>\SharedFiles` (e.g., `\\192.168.1.100\SharedFiles`)
3. Enter your **Linux Username** and **Samba Password**

### 🍎 macOS

1. Open **Finder** → Press `Cmd + K`
2. Type `smb://<SERVER_IP>/SharedFiles`
3. Click **Connect** → Select **Registered User** → Enter credentials

---

## ⚠️ Security Notes

> **Timeout Logic** — Access is currently disabled on manual logout. Implement a background cron job or TTL script to run `smbpasswd -d` for users with expired sessions.

> **SSL** — Always run the web app behind a reverse proxy (e.g., **Nginx**) with SSL enabled to protect credentials in transit.

---

## 🐛 Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| **Access Denied** | OTP not verified or expired | Check for "Samba Access Enabled" badge on dashboard |
| **Connection Timed Out** | Firewall blocking ports | Run `sudo ufw allow samba` (ports 137–139, 445) |
| **Password Rejected** | Samba password not initialized | Run `sudo smbpasswd -a username` |
| **Permission Denied** | Wrong folder permissions | Verify `/srv/samba/shared` is `1777` with sticky bit |
| **"Account Disabled"** | Flask `manage_samba_access` failed | Check Flask logs for sudo errors |

---

## 📄 License

This project is licensed under the **MIT License**.

---

<div align="center">

## 👨‍💻 Developed By

**Syed Ahmad Galib**<br>
Computer Science and Engineering<br>
Daffodil International University

</div>