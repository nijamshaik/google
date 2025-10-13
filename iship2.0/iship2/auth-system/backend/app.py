import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_socketio import SocketIO, join_room
from flask_mail import Mail, Message

# --- App and Database Configuration ---

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend'))
app.config['SECRET_KEY'] = 'a_very_secret_key_for_session_management'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# --- Mail Configuration ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') # Your Gmail address
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') # Your 16-digit App Password

# --- Initialize Extensions ---
socketio = SocketIO(app, async_mode='eventlet')
mail = Mail(app)

# --- Database Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- Main Application Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup/<user_type>')
def signup_page(user_type):
    if user_type == 'donor':
        return render_template('signup_donor.html')
    elif user_type == 'receiver':
        return render_template('signup_receiver.html')
    elif user_type == 'hospital':
        return render_template('signup_hospital.html')
    elif user_type == 'club':
        return render_template('signup_club.html')
    return redirect(url_for('index'))

@app.route('/signup', methods=['POST'])
def signup():
    # ... (This function remains unchanged from our previous working version)
    user_type = request.form['user_type']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    contact_no = request.form['contact_no']
    hashed_password = generate_password_hash(password, method='sha256')
    db = get_db()
    cursor = db.cursor()
    try:
        if user_type == 'hospital' or user_type == 'club':
            registration_id = request.form['hospital_id']
            cursor.execute("INSERT INTO users (name, email, password, contact_no, user_type, hospital_id) VALUES (?, ?, ?, ?, ?, ?)",(name, email, hashed_password, contact_no, user_type, registration_id))
        else:
             cursor.execute("INSERT INTO users (name, email, password, contact_no, user_type) VALUES (?, ?, ?, ?, ?)",(name, email, hashed_password, contact_no, user_type))
        user_id = cursor.lastrowid
        if user_type == 'donor':
            blood_group = request.form['blood_group']
            cursor.execute("INSERT INTO donor_details (user_id, blood_group) VALUES (?, ?)",(user_id, blood_group))
        db.commit()
    except sqlite3.IntegrityError:
        flash("Email address already registered.")
        return redirect(url_for('signup_page', user_type=user_type))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # ... (This function remains unchanged)
    email = request.form['email']
    password = request.form['password']
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user and check_password_hash(user['password'], password):
        session.clear()
        session['user_id'] = user['id']
        session['user_type'] = user['user_type']
        session['user_name'] = user['name']
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid email or password.")
        return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    # ... (This function remains unchanged)
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user_type = session['user_type']
    db = get_db()
    if user_type == 'donor':
        pending_requests = db.execute("SELECT r.id, u.name, u.contact_no FROM requests r JOIN users u ON r.requester_id = u.id WHERE r.donor_id = ? AND r.status = 'pending'",(session['user_id'],)).fetchall()
        accepted_requests = db.execute("SELECT u.name, u.contact_no FROM requests r JOIN users u ON r.requester_id = u.id WHERE r.donor_id = ? AND r.status = 'accepted'",(session['user_id'],)).fetchall()
        return render_template('dashboard_donor_status.html', pending=pending_requests, accepted=accepted_requests)
    elif user_type == 'receiver':
        all_donors = db.execute("SELECT u.id, u.name, d.blood_group, d.location FROM users u JOIN donor_details d ON u.id = d.user_id").fetchall()
        sent_requests = db.execute("SELECT r.status, u.name, u.contact_no, d.blood_group FROM requests r JOIN users u ON r.donor_id = u.id JOIN donor_details d ON r.donor_id = d.user_id WHERE r.requester_id = ?",(session['user_id'],)).fetchall()
        return render_template('dashboard_receiver.html', donors=all_donors, requests=sent_requests)
    elif user_type == 'hospital':
        return render_template('dashboard_hospital.html')
    elif user_type == 'club':
        return render_template('dashboard_club.html')
    return redirect(url_for('index'))

@app.route('/edit_donor_profile')
def edit_donor_profile():
    # ... (This function remains unchanged)
    if 'user_id' not in session or session['user_type'] != 'donor':
        return redirect(url_for('login_page'))
    db = get_db()
    donor_info = db.execute("SELECT u.name, u.email, u.contact_no, d.blood_group, d.location, d.age, d.last_donation_months FROM users u JOIN donor_details d ON u.id = d.user_id WHERE u.id = ?",(session['user_id'],)).fetchone()
    return render_template('dashboard_donor_form.html', donor=donor_info)

@app.route('/update_donor', methods=['POST'])
def update_donor_details():
    # ... (This function remains unchanged)
    if 'user_id' not in session or session['user_type'] != 'donor':
        return redirect(url_for('login_page'))
    blood_group = request.form['blood_group']
    location = request.form['location']
    age = request.form['age']
    last_donation = request.form['last_donation']
    db = get_db()
    db.execute("UPDATE donor_details SET blood_group = ?, location = ?, age = ?, last_donation_months = ? WHERE user_id = ?",(blood_group, location, age, last_donation, session['user_id']))
    db.commit()
    flash("Thank you! Your information has been updated. You are now visible to receivers.")
    return redirect(url_for('dashboard'))

@app.route('/request_blood/<int:donor_id>')
def request_blood(donor_id):
    if 'user_id' not in session or session['user_type'] != 'receiver':
        return redirect(url_for('login_page'))
    requester_id = session['user_id']
    db = get_db()
    donor = db.execute("SELECT email, name FROM users WHERE id = ?", (donor_id,)).fetchone()
    requester = db.execute("SELECT name FROM users WHERE id = ?", (requester_id,)).fetchone()
    if not donor:
        flash("Donor not found.")
        return redirect(url_for('dashboard'))
    db.execute("INSERT INTO requests (requester_id, donor_id) VALUES (?, ?)", (requester_id, donor_id))
    db.commit()
    flash(f"Request sent successfully.")
    socketio.emit('new_request', {'message': f'You have a new blood request from {requester["name"]}!'}, room=str(donor_id))
    try:
        msg = Message('New Blood Request on MediSecure Portal', sender=app.config['MAIL_USERNAME'], recipients=[donor['email']])
        msg.body = f"Hello {donor['name']},\n\nYou have received a new blood request from {requester['name']}. Please log in to your MediSecure Portal dashboard to view and respond to the request.\n\nThank you!"
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
    return redirect(url_for('dashboard'))

@app.route('/handle_request/<int:request_id>/<action>')
def handle_request(action, request_id):
    # ... (This function remains unchanged)
    if 'user_id' not in session or session['user_type'] != 'donor':
        return redirect(url_for('login_page'))
    if action not in ['accepted', 'rejected']:
        return redirect(url_for('dashboard'))
    db = get_db()
    request_item = db.execute("SELECT * FROM requests WHERE id = ? AND donor_id = ?", (request_id, session['user_id'])).fetchone()
    if request_item:
        db.execute("UPDATE requests SET status = ? WHERE id = ?", (action, request_id))
        db.commit()
        flash(f"Request has been {action}.")
    else:
        flash("Invalid request.")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        join_room(str(user_id))
        print(f"Client connected: user_id {user_id} joined room {user_id}")

# --- Final Run Command ---
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
        print("Database initialized.")
    print("Starting WebSocket server...")
    socketio.run(app, debug=True)