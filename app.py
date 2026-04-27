import secrets
import subprocess
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# --- APP SETUP ---
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
mail = Mail(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger("SambaAuth")

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    samba_username = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class ActiveSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_code = db.Column(db.String(6))
    otp_expires = db.Column(db.DateTime)
    is_authenticated = db.Column(db.Boolean, default=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

# --- UTILITY FUNCTIONS ---
def manage_samba_access(samba_user, enable=True):
    """Executes the system command to enable or disable a Samba user."""
    flag = "-e" if enable else "-d"
    cmd = f"{app.config['SAMBA_USER_COMMAND']} {flag} {samba_user}"
    
    try:
        # Note: Capture output to prevent console clutter and log errors
        result = subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
        logger.info(f"Samba Access: {samba_user} {'ENABLED' if enable else 'DISABLED'}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Samba Command Failed for {samba_user}: {str(e)}")
        # Simulate success in debug mode for development
        return app.debug

def initialize_db():
    """Initializes the database and creates a default admin user if none exists."""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="admin@example.com").first():
            hashed_pw = generate_password_hash("password123")
            admin = User(email="admin@example.com", password_hash=hashed_pw, samba_username="samba_admin")
            db.session.add(admin)
            db.session.commit()
            logger.info("Created default admin user.")

# --- BACKGROUND TASKS ---
@scheduler.task('interval', id='check_timeouts', seconds=60)
def check_session_timeouts():
    """Background task to disable Samba access for expired or inactive sessions."""
    with app.app_context():
        timeout = datetime.utcnow() - timedelta(minutes=30)
        # Find sessions that are either expired or haven't been active
        expired_sessions = ActiveSession.query.filter(
            ActiveSession.is_authenticated == True,
            ActiveSession.last_activity < timeout
        ).all()

        for s in expired_sessions:
            user = User.query.get(s.user_id)
            if user:
                manage_samba_access(user.samba_username, enable=False)
                logger.info(f"AUTO-TIMEOUT: Disabled access for {user.email}")
            db.session.delete(s)
        
        db.session.commit()

# --- ROUTES ---
@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and check_password_hash(user.password_hash, password):
            # 1. Generate OTP
            otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
            expiry = datetime.utcnow() + timedelta(seconds=app.config['OTP_EXPIRY_SECONDS'])
            
            # 2. Store Session state in DB
            # Remove old sessions first
            ActiveSession.query.filter_by(user_id=user.id).delete()
            new_session = ActiveSession(user_id=user.id, otp_code=otp, otp_expires=expiry)
            db.session.add(new_session)
            db.session.commit()
            
            # 3. Send Email
            if app.config['SIMULATE_EMAIL']:
                logger.warning(f"SIMULATION: OTP for {email} is {otp}")
                sent = True
            else:
                try:
                    msg = Message("Verification Code", recipients=[email], body=f"Your code: {otp}")
                    mail.send(msg)
                    sent = True
                except Exception as e:
                    logger.error(f"Mail failed: {e}")
                    sent = False

            if sent:
                session['pending_user_id'] = user.id
                return redirect(url_for('verify_otp'))
            flash("Failed to send OTP.", "error")
        else:
            flash("Invalid credentials.", "error")
            
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('pending_user_id')
    if not user_id: return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        active_sess = ActiveSession.query.filter_by(user_id=user_id).first()
        
        if active_sess and active_sess.otp_code == otp_input:
            if datetime.utcnow() > active_sess.otp_expires:
                flash("OTP Expired.", "error")
                return redirect(url_for('login'))
            
            # Success
            active_sess.is_authenticated = True
            active_sess.last_activity = datetime.utcnow()
            db.session.commit()
            
            session.pop('pending_user_id', None)
            session['user_id'] = user.id
            session['email'] = user.email
            session['samba_user'] = user.samba_username
            
            manage_samba_access(user.samba_username, enable=True)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid OTP.", "error")
            
    return render_template('otp.html', email=user.email)

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    
    # Update activity in DB
    active_sess = ActiveSession.query.filter_by(user_id=user_id).first()
    if active_sess:
        active_sess.last_activity = datetime.utcnow()
        db.session.commit()
        
    return render_template('dashboard.html', email=session['email'], samba_user=session['samba_user'])

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user: manage_samba_access(user.samba_username, enable=False)
        ActiveSession.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(e):
    return render_template('login.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.critical(f"Server Error: {e}")
    return "Internal Server Error", 500

if __name__ == '__main__':
    initialize_db()
    app.run(host='0.0.0.0', port=5000)
