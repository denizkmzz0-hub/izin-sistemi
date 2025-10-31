import os
import sqlite3
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

app = Flask(__name__)

# DATABASE configuration: prefer DATABASE_URL (Postgres) in production, fallback to sqlite
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Return a DB connection object. If DATABASE_URL is set, use psycopg2 for Postgres, otherwise sqlite3."""
    if DATABASE_URL:
        # Lazy import to keep local sqlite simple if not using Postgres
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # use DictCursor for row access by name
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        import sqlite3
        con = sqlite3.connect(os.path.join(os.getcwd(), 'izinler.db'))
        con.row_factory = sqlite3.Row
        return con

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-this')

DB = os.path.join(os.getcwd(), 'izinler.db')

@app.route('/', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        email = request.form['email']
        sifre = request.form['sifre']
        con = get_db()
        cur = con.cursor()
        cur.execute('SELECT * FROM kullanicilar WHERE email = ?', (email,))
        user = cur.fetchone()
        con.close()
        if user and check_password_hash(user['sifre'], sifre):
            session['kullanici_id'] = user['id']
            session['ad'] = user['ad']
            session['rol'] = user['rol']
            if user['rol'] == 'yonetici':
                return redirect(url_for('yonetici_paneli'))
            return redirect(url_for('personel_paneli'))
        flash('Hatalı e-posta veya parola.', 'danger')
    return render_template('login.html')

@app.route('/personel')
def personel_paneli():
    if 'kullanici_id' not in session or session.get('rol') != 'personel':
        return redirect(url_for('giris'))
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM izinler WHERE kullanici_id = ?', (session['kullanici_id'],))
    izinler = cur.fetchall()
    cur.execute('SELECT tur FROM kullanicilar WHERE id = ?', (session['kullanici_id'],))
    row = cur.fetchone()
    toplam = 30 if row and row['tur'] and row['tur'].lower() == 'akademik' else 20
    kullanilan = sum([i['sure'] for i in izinler if i['durum'] == 'Onaylandı'])
    kalan = max(toplam - kullanilan, 0)
    con.close()
    return render_template('personel_panel.html', ad=session['ad'], izinler=izinler, toplam=toplam, kalan=kalan)

@app.route('/izin_talebi', methods=['POST'])
def izin_talebi():
    if 'kullanici_id' not in session:
        return redirect(url_for('giris'))
    izin_turu = request.form['izin_turu']
    sure = int(request.form['sure'])
    baslangic = request.form['baslangic']
    bitis = (date.fromisoformat(baslangic) + timedelta(days=sure - 1)).isoformat()
    con = get_db()
    cur = con.cursor()
    cur.execute('INSERT INTO izinler (kullanici_id, izin_turu, sure, baslangic, bitis) VALUES (?, ?, ?, ?, ?)',
                (session['kullanici_id'], izin_turu, sure, baslangic, bitis))
    con.commit()
    con.close()
    flash('İzin talebin yöneticinin onayına gönderildi.', 'success')
    return redirect(url_for('personel_paneli'))

@app.route('/yonetici')
def yonetici_paneli():
    if 'kullanici_id' not in session or session.get('rol') != 'yonetici':
        return redirect(url_for('giris'))
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT izinler.id, kullanicilar.ad, kullanicilar.tur, izinler.izin_turu, izinler.sure,
               izinler.baslangic, izinler.bitis, izinler.durum
        FROM izinler
        JOIN kullanicilar ON izinler.kullanici_id = kullanicilar.id
        ORDER BY izinler.id ASC
    """)
    izinler = cur.fetchall()
    con.close()
    return render_template('yonetici_panel.html', izinler=izinler)

@app.route('/izin_onayla/<int:izin_id>')
def izin_onayla(izin_id):
    con = get_db()
    cur = con.cursor()
    cur.execute("UPDATE izinler SET durum='Onaylandı' WHERE id=?", (izin_id,))
    con.commit()
    con.close()
    return redirect(url_for('yonetici_paneli'))

@app.route('/izin_reddet/<int:izin_id>')
def izin_reddet(izin_id):
    con = get_db()
    cur = con.cursor()
    cur.execute("UPDATE izinler SET durum='Reddedildi' WHERE id=?", (izin_id,))
    con.commit()
    con.close()
    return redirect(url_for('yonetici_paneli'))

@app.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('giris'))

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-this')

def get_db_connection():
    conn = sqlite3.connect('izin_sistemi.db')
    conn.row_factory = sqlite3.Row
    return conn

# -------------------
# Giriş ve çıkış
# -------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect('/yonetici_panel')
            else:
                return redirect('/personel_panel')
        else:
            flash('Hatalı giriş!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------------------
# Yönetici Paneli
# -------------------
@app.route('/yonetici_panel')
def yonetici_panel():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    persons = conn.execute('SELECT * FROM users WHERE role = "personel"').fetchall()
    leaves = conn.execute('SELECT * FROM leaves').fetchall()
    conn.close()

    # Chart.js için veri hazırlama
    dates = []
    persons_chart = []

    # tüm izin tarihlerini al
    for leave in leaves:
        start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
        end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
        delta = (end - start).days + 1
        for i in range(delta):
            day = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            if day not in dates:
                dates.append(day)
    dates.sort()

    import random
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

    for person in persons:
        data = []
        for date in dates:
            total = 0
            for leave in leaves:
                if leave['user_id'] == person['id']:
                    start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
                    end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
                    if start <= datetime.strptime(date, '%Y-%m-%d') <= end:
                        total = 1
            data.append(total)
        persons_chart.append({
            'name': person['name'],
            'leaves': data,
            'color': random.choice(colors)
        })

    return render_template('yonetici_panel.html', persons=persons_chart, dates=dates)

# -------------------
# Personel Ekleme
# -------------------
@app.route('/yonetici_ekle', methods=['GET', 'POST'])
def yonetici_ekle():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        total_leave = int(request.form['total_leave'])
        conn = get_db_connection()
        conn.execute('INSERT INTO users (name, email, password, role, total_leave) VALUES (?, ?, ?, ?, ?)',
                     (name, email, password, 'personel', total_leave))
        conn.commit()
        conn.close()
        flash('Personel eklendi!')
        return redirect('/yonetici_panel')
    return render_template('yonetici_ekle.html')

# -------------------
# Personel Paneli
# -------------------
@app.route('/personel_panel')
def personel_panel():
    if session.get('role') != 'personel':
        return redirect('/login')
    user_id = session.get('user_id')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    leaves = conn.execute('SELECT * FROM leaves WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    remaining_leave = user['total_leave'] - user['used_leave']
    return render_template('personel_panel.html', user=user, leaves=leaves, remaining_leave=remaining_leave)

if __name__ == '__main__':
    app.run(debug=True)



@app.route('/add_personnel', methods=['GET', 'POST'])
def add_personnel():
    if 'kullanici_id' not in session or session['rol'] != 'yonetici':
        return redirect(url_for('giris'))
    if request.method == 'POST':
        ad = request.form.get('ad','').strip()
        email = request.form.get('email','').strip()
        sifre = request.form.get('sifre','').strip()
        tur = request.form.get('tur','İdari').strip()
        if not email or not sifre:
            flash('E-posta ve şifre gerekli.', 'danger')
            return render_template('add_personnel.html')
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM kullanicilar WHERE email=?", (email,))
        existing = cur.fetchone()
        if existing:
            con.close()
            flash('❌ Bu e-posta zaten kayıtlı!', 'danger')
            return render_template('add_personnel.html')
        hashed = generate_password_hash(sifre)
        cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?, ?, ?, ?, ?)", (ad if ad else email.split('@')[0], email, hashed, 'personel', tur))
        con.commit()
        con.close()
        flash('✅ Yeni personel eklendi.', 'success')
        return redirect(url_for('yonetici_paneli'))
    return render_template('add_personnel.html')
