# Samba Web Authentication Server

This project provides a secure web-based authentication layer for a Linux Samba server. Users must log in via the web app and complete OTP verification before their Samba access is enabled.

## Features
- Flask Backend with Session Management.
- Email-based OTP (supports simulation mode).
- Dynamic Samba user enabling/disabling via system commands.
- Premium Dark UI with Glassmorphism.

## Prerequisites
1. **Linux Server** with Samba installed.
2. **Python 3.8+**
3. **Sudo access** for the web application user.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install flask flask-mail
```

### 2. Configure Samba for File-Level Security
To enforce the requirement that only owners can delete their own files, use the following configuration in your `/etc/samba/smb.conf`:

```ini
[SharedFiles]
    path = /srv/samba/shared
    browseable = yes
    read only = no
    guest ok = no
    # Secure Masks: Owners get full access, others get read-only
    create mask = 0644
    directory mask = 0755
    # Force ownership of files created via Samba
    force create mode = 0644
    force directory mode = 0755
```

### 3. Linux Permissions (Sticky Bit)
The **Sticky Bit** prevents users from deleting or renaming files owned by others, even if they have write access to the directory. Run these commands to set up your share:

```bash
# Create the directory
sudo mkdir -p /srv/samba/shared
# Grant group write access (e.g., to a common group 'smbusers')
sudo chgrp smbusers /srv/samba/shared
sudo chmod 2775 /srv/samba/shared
# SET THE STICKY BIT (+t)
sudo chmod +t /srv/samba/shared
```

### 4. Grant Sudo Privileges
The web server needs to run access control commands. Edit `/etc/sudoers`:
```text
www-data ALL=(ALL) NOPASSWD: /usr/bin/smbpasswd, /usr/bin/chmod, /usr/bin/chown
```

### 4. Configuration
Edit `config.py` to add your SMTP credentials if you want to use real email OTP. By default, it runs in **Simulation Mode** (OTP is printed to the terminal).

### 5. Run the App
```bash
python app.py
```

## Security Note
- **Timeout Logic**: Currently, access is disabled on manual logout. You should implement a background cron job or a TTL script to run `smbpasswd -d` for users whose sessions have expired if they don't logout manually.
- **SSL**: Always run the web app behind a reverse proxy (like Nginx) with SSL enabled to protect credentials.

## Client Access Guide

Once you have successfully logged in via the web application and entered your OTP, your Samba account is dynamically enabled. 

### Connecting from Windows
1. Press `Win + R` on your keyboard.
2. Type `\\<SERVER_IP>\SharedFiles` (e.g., `\\192.168.1.100\SharedFiles`).
3. When prompted, enter your **Linux Username** and **Samba Password**.
4. You should now see the shared folder.

### Connecting from macOS
1. Open **Finder**.
2. Press `Cmd + K` or go to **Go > Connect to Server**.
3. Type `smb://<SERVER_IP>/SharedFiles`.
4. Click **Connect**.
5. Select **Registered User** and enter your credentials.

---

## How it works (Security Enforcement)
The "Only after web login" requirement is enforced at the system level:
- **Before Login**: Your Samba account is in a "Disabled" state (`smbpasswd -d`). Any attempt to connect from Windows/macOS will fail even with the correct password.
- **After OTP**: The Flask app executes `sudo smbpasswd -e <user>`. Samba now accepts connections for your user.
- **On Logout/Timeout**: The app executes `sudo smbpasswd -d <user>`. Active sessions are usually dropped or cached until the next request, at which point access is denied.

---

## Troubleshooting

| Issue | Potential Cause | Solution |
| :--- | :--- | :--- |
| **Access Denied** | OTP not verified or expired | Ensure you see the "Samba Access Enabled" badge on the web dashboard. |
| **Connection Timed Out** | Firewall blocking ports | Ensure ports `137, 138, 139, 445` are open: `sudo ufw allow samba`. |
| **Password Rejected**| Samba password not set | Ensure you ran `sudo smbpasswd -a username` initially. |
| **Permission Denied** | Linux folder permissions | Check `/srv/samba/shared` permissions. It should be `1777` with sticky bit. |
| **"Account Disabled"** | Web app error | Check Flask app logs: `manage_samba_access` might have failed to run `sudo`. |

## License
MIT

## Developed by:-
Syed Ahmad Galib
Computer Science and Engineering
Daffodil International University