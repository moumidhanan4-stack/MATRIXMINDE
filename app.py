from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import sqlite3
import random

app = Flask(__name__)
CORS(app)

# --- إعدادات الإيميل ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'contact.agrosolar@gmail.com' 
app.config['MAIL_PASSWORD'] = 'wbml kxxb idbk icfh'
app.config['MAIL_DEFAULT_SENDER'] = ('MATRIXMIND', 'contact.agrosolar@gmail.com')

mail = Mail(app)
verification_codes = {}
DATABASE_USERS = 'users.db'

# --- تهيئة قاعدة بيانات المستخدمين فقط ---
def init_db():
    conn = sqlite3.connect(DATABASE_USERS)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT NOT NULL, 
        email TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# --- ROUTES ---

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200
    data = request.json
    try:
        conn = sqlite3.connect(DATABASE_USERS)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                       (data['username'], data['email'], data['password']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Compte créé"}), 201
    except:
        return jsonify({"status": "error", "message": "Email déjà utilisé"}), 400

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200
    data = request.json
    conn = sqlite3.connect(DATABASE_USERS)
    cursor = conn.cursor()
    cursor.execute('SELECT username, password FROM users WHERE email = ?', (data.get('email'),))
    row = cursor.fetchone()
    conn.close()
    if row and row[1] == data.get('password'):
        return jsonify({"status": "success", "username": row[0]}), 200
    return jsonify({"status": "error", "message": "Ce compte n'existe pas"}), 401

@app.route('/api/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200
    email = request.json.get('email')
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code
    try:
        msg = Message("Code de récupération", recipients=[email], body=f"Ton code est : {code}")
        mail.send(msg)
        return jsonify({"status": "success", "message": "Code envoyé"})
    except:
        return jsonify({"status": "error", "message": "Erreur envoi email"}), 500

@app.route('/api/verify-code', methods=['POST', 'OPTIONS'])
def verify_code():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200
    data = request.json
    if verification_codes.get(data['email']) == data['code']:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Code incorrect"}), 400

@app.route('/api/reset-password', methods=['POST', 'OPTIONS'])
def reset_password():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200
    data = request.json
    conn = sqlite3.connect(DATABASE_USERS)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (data['password'], data['email']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Mot de passe mis à jour"})

# دالة باش نكريو جدول المشاريع يلا ما كانش
def init_projects_db():
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT, 
                        data_json TEXT)''')
    conn.commit()
    conn.close()

# عيطي ليها باش تخدم ملي يبدا السيرفر
init_projects_db()

@app.route('/api/save-project', methods=['POST'])
def save_project():
    data = request.json
    email = data.get('email')
    project_data = str(data.get('project_data')) # كنحولو البيانات لـ نص باش تخزن
    
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO projects (user_email, data_json) VALUES (?, ?)', (email, project_data))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Projet enregistré"})

@app.route('/api/get-history', methods=['POST'])
def get_history():
    data = request.json
    email = data.get('email')
    
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    # كنجيبو غير المشاريع اللي الإيميل ديالها كيساوي الإيميل اللي صيفطنا
    cursor.execute('SELECT data_json FROM projects WHERE user_email = ?', (email,))
    rows = cursor.fetchall()
    conn.close()
    
    # كنرجعو قائمة فيها غير البيانات
    history = [row[0] for row in rows]
    return jsonify({"status": "success", "history": history})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

