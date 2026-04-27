import os
from datetime import timedelta

class Config:
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secure-prod-key-782910')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False # Enable in production with HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Database Configuration (SQLite by default, switch to MySQL/Postgres easily)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///samba_auth.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Samba Configuration
    SAMBA_USER_COMMAND = "/usr/bin/sudo /usr/bin/smbpasswd"
    SAMBA_SHARED_PATH = "/srv/samba/shared"
    
    # OTP Configuration
    OTP_EXPIRY_SECONDS = 300 # 5 minutes
    
    # Gmail SMTP Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # Scheduler Settings
    SCHEDULER_API_ENABLED = True
    
    # Simulation Mode
    SIMULATE_EMAIL = True if not os.environ.get('MAIL_USERNAME') else False
