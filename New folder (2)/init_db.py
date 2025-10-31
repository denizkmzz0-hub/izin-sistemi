
import sqlite3, os
from werkzeug.security import generate_password_hash
DB = os.path.join(os.getcwd(), 'izinler.db')
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT,
        email TEXT UNIQUE,
        sifre TEXT,
        rol TEXT,
        tur TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS izinler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_id INTEGER,
        izin_turu TEXT,
        sure INTEGER,
        baslangic TEXT,
        bitis TEXT,
        durum TEXT
    )
    ''')
    cur.execute("SELECT * FROM kullanicilar WHERE email = ?", ('admin@local',))
    if not cur.fetchone():
        cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?, ?, ?, ?, ?)", ('Admin', 'admin@local', generate_password_hash('galatasaray'), 'yonetici', 'İdari'))
    con.commit()
    con.close()
    print('DB hazır:', DB)
if __name__ == '__main__':
    init_db()
