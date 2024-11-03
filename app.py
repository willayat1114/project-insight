#Author: Wilayat Ali Kawoosa, Siyan Showkat, Fatima Shah, Mohmmad Zain

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sqlite3
from pathlib import Path
import hashlib
import requests

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / 'templates'
ASSETS_DIR = TEMPLATES_DIR / 'assets'

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create a table to store user information
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    weight INTEGER NOT NULL,
    height INTEGER NOT NULL,
    age INTEGER NOT NULL,
    medical_history TEXT,
    alergies TEXT
)
''')
conn.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_name TEXT NOT NULL,
            address TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        );
    ''')
conn.execute('''
        CREATE TABLE IF NOT EXISTS emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            weight TEXT,
            height TEXT,
            location TEXT,
            email TEXT,
            age INTEGER,
            medical_history TEXT,
            alergies TEXT
        );
    ''')

conn.commit()
conn.close()

# Connect to the contact SQLite database (or create it if it doesn't exist)
conn_contact = sqlite3.connect('contact.db')
c_contact = conn_contact.cursor()

# Create a table to store contact information
c_contact.execute('''
CREATE TABLE IF NOT EXISTS contact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL
)
''')

conn_contact.commit()
conn_contact.close()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_contact_db_connection():
    conn = sqlite3.connect('contact.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        full_name = request.form['Name']
        email = request.form['Email']
        password = request.form['Password']
        confirm_password = request.form['ConfirmPassword']
        weight = request.form['Weight']
        height = request.form['Height']
        age = request.form['Age']
        medical_history = request.form['MedicalHistory']
        alergies = request.form['Allergies']  # Corrected line

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match."

        # Hash the password
        hashed_password = hash_password(password)

        # Connect to the database and insert the user data
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''INSERT INTO users (full_name, password, email, weight, height, age, medical_history, alergies)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (full_name, hashed_password, email, weight, height, age, medical_history, alergies))

        conn.commit()
        conn.close()

        # Redirect to the login page after successful signup
        return redirect(url_for('login'))

    # If the request method is GET, render the signup form
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        full_name = request.form.get('Name')  # Use .get() to avoid KeyError
        password = request.form.get('Password')  # Use .get() here too

        # Check if the retrieved values are not None or empty
        if not full_name or not password:
            return "Please provide both name and password."

        hashed_password = hash_password(password)

        # Connect to the database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE full_name = ? AND password = ?', (full_name, hashed_password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['full_name']
            session['weight'] = user['weight']
            session['height'] = user['height']
            session['email'] = user['email']
            session['age'] = user['age']
            session['medical_history'] = user['medical_history']
            session['alergies'] = user['alergies']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid full name or password"
    
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')

def get_location(lat, lon):
    here_api_key = 'E5Vp5ot7eyDvR1xXV1qTemn4CeKc8ioHEz4dXrJO9r8'  # Replace with your HERE API key
    url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={lat},{lon}&apikey={here_api_key}"
    
    response = requests.get(url)
    
    print("Raw API response:", response.text)  # Add this to log the raw response
    
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and data['items']:
            return data['items'][0]['address']['label']
        else:
            return 'Unknown location (No Results)'
    return 'Unknown location (API Error)'

# Handle emergency button click
@app.route('/send_emergency', methods=['POST'])
def send_emergency():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']
    weight = session['weight']
    height = session['height']
    email = session['email']
    age = session['age']
    medical_history = session['medical_history']
    alergies = session['alergies']
    
    lat = request.form.get('lat')  # get latitude from form
    lon = request.form.get('lon')  # get longitude from form

    # Use the Ola Reverse Geocode API to get the location
    location = get_location(lat, lon)

    conn = get_db_connection()
    conn.execute('INSERT INTO emergencies (user_id, username, weight, height, location, email, age, medical_history, alergies) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 (user_id, username, weight, height, location, email, age, medical_history, alergies))
    conn.commit()
    conn.close()

    return jsonify({"message": "Help is on the way!"})

@app.route('/signup+hospital', methods=['GET', 'POST'])
def signup_hospital():
    if request.method == 'POST':
        # Get form data
        hospital_name = request.form['HospitalName']
        address = request.form['Address']
        email = request.form['Email']
        password = request.form['Password']
        confirm_password = request.form['ConfirmPassword']

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match."

        # Hash the password
        hashed_password = hash_password(password)

        # Connect to the database and insert the user data
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''INSERT INTO hospitals (hospital_name, address, email, password)
                      VALUES (?, ?, ?, ?)''', (hospital_name, address, email, hashed_password))

        conn.commit()
        conn.close()

        # Redirect to the login page after successful signup
        return redirect(url_for('login_hospital'))

    # If the request method is GET, render the signup form
    return render_template('signup+hospital.html')

@app.route('/login+hospital', methods=['GET', 'POST'])
def login_hospital():
    if request.method == 'POST':
        email = request.form.get('Email')  # Use .get() to avoid KeyError
        password = request.form.get('Password') # Use .get() here too

        # Check if the retrieved values are not None or empty
        if not email or not password:
            return "Please provide both name and password."

        hashed_password = hash_password(password)

        # Connect to the database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM hospitals WHERE email = ? AND password = ?', (email, hashed_password))
        hospital = c.fetchone()
        conn.close()

        if hospital:
            session['hospital_id'] = hospital['id']
            session['email'] = hospital['email']
            return redirect(url_for('dashboard_hospital'))
        else:
            return "Invalid hospital name or password"
        
    return render_template('login+hospital.html')

@app.route('/dashboard+hospital', methods=['GET', 'POST'])
def dashboard_hospital():
    emergencies = get_all_emergencies()
    return render_template('dashboard+hospital.html', emergencies=emergencies)

def get_all_emergencies():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM emergencies')
    emergencies = c.fetchall()
    conn.close()
    return emergencies

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        conn = get_contact_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO contact (name, email, message) VALUES (?, ?, ?)''', (name, email, message))
        conn.commit()
        conn.close()

        return "Thank you for contacting us!"

    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)