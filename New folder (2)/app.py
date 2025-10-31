
import os
import sqlite3
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-this-secret')

DATABASE_URL = os.environ.get('DATABASE_URL')
DB_PATH = os.path.join(os.getcwd(), 'izinler.db')

def get_db():
    if hasattr(g, 'db') and g.db:
        return g.db
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = False
        g.db = conn
        return conn
    else:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        g.db = con
        return con

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        try:
            db.close()
        except:
            pass

def row_to_dict(row, cur=None, pg=False):
    if not row:
        return None
    if pg:
        # psycopg2 returns tuples unless RealDictCursor used; try to map via cursor.description
        if isinstance(row, dict):
            return row
        if cur is not None and hasattr(cur, 'description'):
            desc = [d[0] for d in cur.description]
            return {desc[i]: row[i] for i in range(len(row))}
        return row
    else:
        return dict(row)

def rows_to_list(cur, pg=False):
    rows = cur.fetchall()
    if pg:
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return rows
        desc = [d[0] for d in cur.description] if hasattr(cur, 'description') else []
        result = []
        for r in rows:
            result.append({desc[i]: r[i] for i in range(len(r))})
        return result
    else:
        return [dict(r) for r in rows]

# --------------------------
# Login
# --------------------------
@app.route('/', methods=['GET','POST'])
def giris():
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        sifre = request.form.get('sifre','').strip()
        con = get_db()
        cur = con.cursor()
        pg = bool(DATABASE_URL)
        if pg:
            cur.execute("SELECT * FROM kullanicilar WHERE email = %s", (email,))
            user = cur.fetchone()
            user = row_to_dict(user, cur, pg=True)
        else:
            cur.execute("SELECT * FROM kullanicilar WHERE email = ?", (email,))
            user = cur.fetchone()
            user = row_to_dict(user, cur, pg=False)
        if user and check_password_hash(user.get('sifre'), sifre):
            session['kullanici_id'] = user.get('id')
            session['ad'] = user.get('ad')
            session['rol'] = user.get('rol')
            if user.get('rol') == 'yonetici':
                return redirect(url_for('yonetici_paneli'))
            return redirect(url_for('personel_paneli'))
        flash('Hatalı e-posta veya parola.', 'danger')
    return render_template('login.html')

# --------------------------
# Personel panel
# --------------------------
@app.route('/personel')
def personel_paneli():
    if 'kullanici_id' not in session or session.get('rol') != 'personel':
        return redirect(url_for('giris'))
    con = get_db()
    cur = con.cursor()
    pg = bool(DATABASE_URL)
    if pg:
        cur.execute("SELECT * FROM izinler WHERE kullanici_id = %s", (session['kullanici_id'],))
    else:
        cur.execute("SELECT * FROM izinler WHERE kullanici_id = ?", (session['kullanici_id'],))
    izinler = rows_to_list(cur, pg)
    if pg:
        cur.execute("SELECT tur FROM kullanicilar WHERE id = %s", (session['kullanici_id'],))
        row = cur.fetchone()
        row = row_to_dict(row, cur, pg=True)
    else:
        cur.execute("SELECT tur FROM kullanicilar WHERE id = ?", (session['kullanici_id'],))
        row = cur.fetchone()
        row = row_to_dict(row, cur, pg=False)
    toplam = 30 if row and row.get('tur') and row.get('tur').lower() == 'akademik' else 20
    kullanilan = sum([i.get('sure',0) for i in izinler if i.get('durum') == 'Onaylandı'])
    kalan = max(toplam - kullanilan, 0)
    return render_template('personel_panel.html', ad=session.get('ad'), izinler=izinler, toplam=toplam, kullanilan=kullanilan, kalan=kalan)

# --------------------------
# İzin talebi (personel)
# --------------------------
@app.route('/izin_talebi', methods=['GET','POST'])
def izin_talebi():
    if 'kullanici_id' not in session:
        return redirect(url_for('giris'))
    if request.method == 'POST':
        izin_turu = request.form.get('izin_turu','Yıllık')
        try:
            sure = int(request.form.get('sure','1'))
        except:
            sure = 1
        baslangic = request.form.get('baslangic', date.today().isoformat())
        bas_t = date.fromisoformat(baslangic)
        bitis = (bas_t + timedelta(days=sure-1)).isoformat()
        con = get_db()
        cur = con.cursor()
        pg = bool(DATABASE_URL)
        if pg:
            cur.execute("INSERT INTO izinler (kullanici_id, izin_turu, sure, baslangic, bitis, durum) VALUES (%s,%s,%s,%s,%s,%s)",
                        (session['kullanici_id'], izin_turu, sure, baslangic, bitis, 'Bekliyor'))
        else:
            cur.execute("INSERT INTO izinler (kullanici_id, izin_turu, sure, baslangic, bitis, durum) VALUES (?,?,?,?,?,?)",
                        (session['kullanici_id'], izin_turu, sure, baslangic, bitis, 'Bekliyor'))
        con.commit()
        flash('İzin talebin yöneticinin onayına gönderildi.', 'success')
        return redirect(url_for('personel_paneli'))
    return render_template('izin_talep.html')

# --------------------------
# Yönetici panel
# --------------------------
@app.route('/yonetici')
def yonetici_paneli():
    if 'kullanici_id' not in session or session.get('rol') != 'yonetici':
        return redirect(url_for('giris'))
    con = get_db()
    cur = con.cursor()
    pg = bool(DATABASE_URL)
    cur.execute(\"\"\"
        SELECT izinler.id, kullanicilar.ad, kullanicilar.tur, izinler.izin_turu, izinler.sure,
               izinler.baslangic, izinler.bitis, izinler.durum
        FROM izinler
        JOIN kullanicilar ON izinler.kullanici_id = kullanicilar.id
        ORDER BY izinler.id ASC
    \"\"\")
    izinler = rows_to_list(cur, pg)
    # Pasta grafik verisi (onaylanan toplam gün personel bazında)
    cur.execute(\"\"\"
        SELECT k.ad, COALESCE(SUM(i.sure),0) AS toplam_sure
        FROM kullanicilar k
        LEFT JOIN izinler i ON i.kullanici_id = k.id AND i.durum = 'Onaylandı'
        GROUP BY k.ad
        ORDER BY k.ad
    \"\"\")
    grafik = rows_to_list(cur, pg)
    isimler = [r.get('ad') for r in grafik]
    izin_sureleri = [r.get('toplam_sure',0) for r in grafik]
    return render_template('yonetici_panel.html', izinler=izinler, isimler=isimler, izin_sureleri=izin_sureleri)

# --------------------------
# Yeni personel ekleme
# --------------------------
@app.route('/add_personnel', methods=['GET','POST'])
def add_personnel():
    if 'kullanici_id' not in session or session.get('rol') != 'yonetici':
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
        pg = bool(DATABASE_URL)
        if pg:
            cur.execute("SELECT * FROM kullanicilar WHERE email = %s", (email,))
            exists = cur.fetchone()
        else:
            cur.execute("SELECT * FROM kullanicilar WHERE email = ?", (email,))
            exists = cur.fetchone()
        if exists:
            flash('Bu e-posta zaten kayıtlı!', 'danger')
            return render_template('add_personnel.html')
        hashed = generate_password_hash(sifre)
        if pg:
            cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (%s,%s,%s,%s,%s)",
                        (ad if ad else email.split('@')[0], email, hashed, 'personel', tur))
        else:
            cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?,?,?,?,?)",
                        (ad if ad else email.split('@')[0], email, hashed, 'personel', tur))
        con.commit()
        flash('Yeni personel eklendi.', 'success')
        return redirect(url_for('yonetici_paneli'))
    return render_template('add_personnel.html')

# --------------------------
# Onay / reddet
# --------------------------
@app.route('/izin_onayla/<int:izin_id>')
def izin_onayla(izin_id):
    if 'kullanici_id' not in session or session.get('rol') != 'yonetici':
        return redirect(url_for('giris'))
    con = get_db()
    cur = con.cursor()
    pg = bool(DATABASE_URL)
    if pg:
        cur.execute("UPDATE izinler SET durum = 'Onaylandı' WHERE id = %s", (izin_id,))
    else:
        cur.execute("UPDATE izinler SET durum = 'Onaylandı' WHERE id = ?", (izin_id,))
    con.commit()
    flash('İzin onaylandı.', 'success')
    return redirect(url_for('yonetici_paneli'))

@app.route('/izin_reddet/<int:izin_id>')
def izin_reddet(izin_id):
    if 'kullanici_id' not in session or session.get('rol') != 'yonetici':
        return redirect(url_for('giris'))
    con = get_db()
    cur = con.cursor()
    pg = bool(DATABASE_URL)
    if pg:
        cur.execute("UPDATE izinler SET durum = 'Reddedildi' WHERE id = %s", (izin_id,))
    else:
        cur.execute("UPDATE izinler SET durum = 'Reddedildi' WHERE id = ?", (izin_id,))
    con.commit()
    flash('İzin reddedildi.', 'warning')
    return redirect(url_for('yonetici_paneli'))

@app.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('giris'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)
