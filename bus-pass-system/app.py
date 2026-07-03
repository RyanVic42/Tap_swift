from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import qrcode
from PIL import Image
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import logging
import json  # Added missing import
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Project paths should not depend on the terminal's current directory.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PASSES_DIR = os.path.join(BASE_DIR, "static", "passes")
IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database initialization
DB_NAME = os.path.join(BASE_DIR, "buspass.db")

MOBILE_PAYMENT_METHODS = {"M-Pesa", "Airtel Money"}
KENYAN_BANKS = {
    "Absa Bank Kenya PLC",
    "Access Bank (Kenya) PLC",
    "African Banking Corporation Limited",
    "Bank of Africa Kenya Limited",
    "Bank of Baroda (Kenya) Limited",
    "Bank of India",
    "Citibank N.A. Kenya",
    "Consolidated Bank of Kenya Limited",
    "Co-operative Bank of Kenya Limited",
    "Credit Bank PLC",
    "Development Bank of Kenya Limited",
    "Diamond Trust Bank Kenya Limited",
    "DIB Bank Kenya Limited",
    "Ecobank Kenya Limited",
    "Equity Bank Kenya Limited",
    "Family Bank Limited",
    "First Community Bank Limited",
    "Guaranty Trust Bank (Kenya) Limited",
    "Guardian Bank Limited",
    "Gulf African Bank Limited",
    "Habib Bank AG Zurich",
    "HFC Limited",
    "I&M Bank Limited",
    "KCB Bank Kenya Limited",
    "Kingdom Bank Limited",
    "Mayfair CIB Bank Limited",
    "Middle East Bank Kenya Limited",
    "M Oriental Bank Limited",
    "National Bank of Kenya Limited",
    "NCBA Bank Kenya PLC",
    "Paramount Bank Limited",
    "Premier Bank Kenya Limited",
    "Prime Bank Limited",
    "SBM Bank Kenya Limited",
    "Sidian Bank Limited",
    "Stanbic Bank Kenya Limited",
    "Standard Chartered Bank Kenya Limited",
    "United Bank for Africa Kenya Limited",
    "Victoria Commercial Bank PLC",
}

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                created_date TEXT,
                status TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passengers (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                passenger_id TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                created_date TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_date TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passes (
                username TEXT PRIMARY KEY,
                pass_id TEXT NOT NULL,
                validity TEXT NOT NULL,
                qr_path TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES passengers(username)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                amount INTEGER NOT NULL,
                method TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES passengers(username)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saccos (
                sacco_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                routes TEXT NOT NULL,
                fleet_size INTEGER NOT NULL,
                contact TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sacco TEXT NOT NULL,
                schedule TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        """)
        
        # Insert default admin if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO admins (username, password, role, created_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin123", "admin", "2024-01-01", "active"))
        
        # Insert default sacco
        cursor.execute("""
            INSERT OR IGNORE INTO saccos (sacco_id, name, routes, fleet_size, contact)
            VALUES (?, ?, ?, ?, ?)
        """, ("MU84", "MU84 Sacco", '["Moi University to Eldoret Town", "Moi University to Kesses"]', 15, "mu84@example.com"))
        
        # Insert default routes
        default_routes = [
            ("Moi University to Eldoret Town", "MU84", '["07:00", "09:00", "12:00"]', 100),
            ("Moi University to Kesses", "MU84", '["08:00", "10:00", "13:00"]', 50),
            ("Moi University to Annex Campus", "Moi University Shuttle", '["07:30", "11:00", "14:00"]', 70),
            ("Moi University to Cheptiret", "Eldoret Express", '["09:30", "12:30", "15:00"]', 80)
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO routes (name, sacco, schedule, price)
            VALUES (?, ?, ?, ?)
        """, default_routes)
        
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Message sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if role == 'passenger':
                cursor.execute("SELECT * FROM passengers WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                if user:
                    session['username'] = username
                    session['role'] = 'passenger'
                    return redirect(url_for('passenger_dashboard', username=username))
            elif role == 'driver':
                cursor.execute("SELECT * FROM drivers WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                if user:
                    session['username'] = username
                    session['role'] = 'driver'
                    return redirect(url_for('driver_portal', username=username))
            flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
            admin = cursor.fetchone()
            if admin:
                session['username'] = username
                session['role'] = 'admin'
                return redirect(url_for('admin_portal'))
            flash('Invalid admin credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        admin_key = request.form['admin_key']
        full_name = request.form['full_name']
        email = request.form['email']
        
        if admin_key != "BUSPASS_ADMIN_2024":
            flash('Invalid admin registration key.', 'error')
            return render_template('admin_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('admin_register.html')
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM admins WHERE username = ?", (username,))
            if cursor.fetchone():
                flash('Admin username already exists.', 'error')
                return render_template('admin_register.html')
            
            cursor.execute("""
                INSERT INTO admins (username, password, role, full_name, email, created_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, password, 'admin', full_name, email, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'))
            conn.commit()
            
            flash('Admin registration successful! You can now login.', 'success')
            logger.info(f"New admin registered: {username}")
            return redirect(url_for('admin_login'))
    
    return render_template('admin_register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if role == 'passenger':
                cursor.execute("SELECT username FROM passengers WHERE username = ?", (username,))
                if not cursor.fetchone():
                    passenger_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO passengers (username, password, role, passenger_id, points, balance, created_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (username, password, role, passenger_id, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    flash('Registration successful!', 'success')
                    return redirect(url_for('login'))
            elif role == 'driver':
                cursor.execute("SELECT username FROM drivers WHERE username = ?", (username,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO drivers (username, password, role, created_date)
                        VALUES (?, ?, ?, ?)
                    """, (username, password, role, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    flash('Registration successful!', 'success')
                    return redirect(url_for('login'))
            flash('Username already exists.', 'error')
    return render_template('register.html')

@app.route('/passenger_dashboard/<username>')
def passenger_dashboard(username):
    if 'username' not in session or session['username'] != username or session['role'] != 'passenger':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM passes WHERE username = ?", (username,))
        user_pass = cursor.fetchone()
        user_pass = {
            'id': user_pass[1],
            'validity': user_pass[2],
            'qr_path': user_pass[3]
        } if user_pass else {}
        
        cursor.execute("SELECT points, balance FROM passengers WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        user_points, user_balance = user_data if user_data else (0, 0)
        
        cursor.execute("SELECT amount, method, date FROM payment_history WHERE username = ?", (username,))
        user_payments = [{'amount': row[0], 'method': row[1], 'date': row[2]} for row in cursor.fetchall()]
        
        cursor.execute("SELECT name, sacco, schedule, price FROM routes")
        routes = [{'name': row[0], 'sacco': row[1], 'schedule': json.loads(row[2]), 'price': row[3]} for row in cursor.fetchall()]
    
    return render_template('passenger_dashboard.html', 
                         username=username, 
                         routes=routes, 
                         user_pass=user_pass,
                         points=user_points, 
                         balance=user_balance, 
                         payments=user_payments)

@app.route('/driver_portal/<username>')
def driver_portal(username):
    if 'username' not in session or session['username'] != username or session['role'] != 'driver':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, sacco, schedule, price FROM routes")
        routes = [{'name': row[0], 'sacco': row[1], 'schedule': json.loads(row[2]), 'price': row[3]} for row in cursor.fetchall()]
    
    return render_template('driver_portal.html', username=username, routes=routes)

@app.route('/admin_portal')
def admin_portal():
    if 'username' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('admin_login'))
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, role, passenger_id, points, balance, created_date FROM passengers")
        passengers = {row[0]: {'password': row[1], 'role': row[2], 'passenger_id': row[3], 'points': row[4], 'balance': row[5], 'created_date': row[6]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT username, password, role, created_date FROM drivers")
        drivers = {row[0]: {'password': row[1], 'role': row[2], 'created_date': row[3]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT username, password, role, full_name, email, created_date, status FROM admins")
        admins = {row[0]: {'password': row[1], 'role': row[2], 'full_name': row[3], 'email': row[4], 'created_date': row[5], 'status': row[6]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT sacco_id, name, routes, fleet_size, contact FROM saccos")
        saccos = {row[0]: {'name': row[1], 'routes': json.loads(row[2]), 'fleet_size': row[3], 'contact': row[4]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT name, sacco, schedule, price FROM routes")
        routes = [{'name': row[0], 'sacco': row[1], 'schedule': json.loads(row[2]), 'price': row[3]} for row in cursor.fetchall()]
    
    return render_template('admin_portal.html', 
                         passengers=passengers, 
                         drivers=drivers, 
                         routes=routes,
                         saccos=saccos,
                         admins=admins)

@app.route('/generate_pass/<username>', methods=['POST'])
def generate_pass(username):
    if 'username' not in session or session['username'] != username or session['role'] != 'passenger':
        return jsonify({'error': 'Unauthorized'}), 403
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM passes WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Pass already exists'}), 400
        
        cursor.execute("SELECT passenger_id FROM passengers WHERE username = ?", (username,))
        passenger_id = cursor.fetchone()[0]
        
        pass_id = str(uuid.uuid4())
        validity = datetime.now() + timedelta(days=365)
        qr_data = f"PassengerID:{passenger_id},PassID:{pass_id},User:{username}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        os.makedirs(PASSES_DIR, exist_ok=True)
        qr_path = f"static/passes/{pass_id}.png"
        qr_file_path = os.path.join(PASSES_DIR, f"{pass_id}.png")
        qr_img.save(qr_file_path)
        
        cursor.execute("""
            INSERT INTO passes (username, pass_id, validity, qr_path)
            VALUES (?, ?, ?, ?)
        """, (username, pass_id, validity.strftime('%Y-%m-%d'), qr_path))
        
        cursor.execute("UPDATE passengers SET points = points + 10 WHERE username = ?", (username,))
        conn.commit()
    
    return jsonify({'success': True, 'qr_path': qr_path})

@app.route('/make_payment/<username>', methods=['POST'])
def make_payment(username):
    if 'username' not in session or session['username'] != username or session['role'] != 'passenger':
        return jsonify({'error': 'Unauthorized'}), 403
    
    amount = request.form['amount']
    payment_method = request.form.get('payment_method', 'M-Pesa')
    payment_reference = payment_method
    
    try:
        amount = int(amount)
        if amount < 50:
            return jsonify({'success': False, 'error': 'Minimum top-up amount is KES 50'}), 400

        if payment_method in MOBILE_PAYMENT_METHODS:
            phone_number = request.form.get('phone_number', '').strip()
            pin = request.form.get('pin', '').strip()

            if not re.fullmatch(r'(\+254|254|0)(7|1)\d{8}', phone_number):
                return jsonify({'success': False, 'error': 'Please enter a valid Kenyan mobile number'}), 400

            if not re.fullmatch(r'\d{4,6}', pin):
                return jsonify({'success': False, 'error': 'Please enter a valid mobile money PIN'}), 400

            payment_reference = f"{payment_method} - {phone_number[-4:]}"
        elif payment_method == 'Bank Transfer':
            bank_name = request.form.get('bank_name', '').strip()
            account_holder = request.form.get('account_holder', '').strip()
            account_number = request.form.get('account_number', '').strip()
            national_id = request.form.get('national_id', '').strip()

            if bank_name not in KENYAN_BANKS:
                return jsonify({'success': False, 'error': 'Please select an eligible Kenyan bank'}), 400

            if not re.fullmatch(r"[A-Za-z\s.'-]{3,}", account_holder):
                return jsonify({'success': False, 'error': 'Please enter the account holder full name'}), 400

            if not re.fullmatch(r'[A-Za-z0-9-]{5,20}', account_number):
                return jsonify({'success': False, 'error': 'Please enter a valid bank account number'}), 400

            if len(national_id) < 5:
                return jsonify({'success': False, 'error': 'Please enter a valid ID or passport number'}), 400

            payment_reference = f"Bank Transfer - {bank_name} - {account_number[-4:]}"
        elif payment_method == 'PayPal':
            paypal_email = request.form.get('paypal_email', '').strip()

            if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', paypal_email):
                return jsonify({'success': False, 'error': 'Please enter a valid PayPal email address'}), 400

            payment_reference = f"PayPal - {paypal_email}"
        else:
            return jsonify({'success': False, 'error': 'Unsupported payment method'}), 400
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE passengers SET balance = balance + ?, points = points + ? WHERE username = ?
            """, (amount, amount // 100, username))
            
            cursor.execute("""
                INSERT INTO payment_history (username, amount, method, date)
                VALUES (?, ?, ?, ?)
            """, (username, amount, payment_reference, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            cursor.execute("SELECT balance FROM passengers WHERE username = ?", (username,))
            new_balance = cursor.fetchone()[0]
            conn.commit()
        
        return jsonify({'success': True, 'new_balance': new_balance})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'}), 400

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/system-admin')
def system_admin():
    return redirect(url_for('admin_login'))

@app.context_processor
def inject_user():
    return dict(session=session)

if __name__ == '__main__':
    os.makedirs(PASSES_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    init_db()
    print("🚌 Bus Pass System Starting...")
    print("📍 Main Application: http://127.0.0.1:5000")
    print("🔐 Admin Login: http://127.0.0.1:5000/admin")
    print("🔑 Admin Registration: http://127.0.0.1:5000/admin/register")
    print("👤 User Login: http://127.0.0.1:5000/login")
    print("📝 Registration: http://127.0.0.1:5000/register")
    print("📞 Contact: http://127.0.0.1:5000/contact")
    print("ℹ️  About: http://127.0.0.1:5000/about")
    print()
    print("🔐 DEFAULT ADMIN CREDENTIALS:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("🔑 ADMIN REGISTRATION KEY: BUSPASS_ADMIN_2024")
    app.run(debug=True, host='127.0.0.1', port=5000)
