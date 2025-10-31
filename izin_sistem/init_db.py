import sqlite3
from werkzeug.security import generate_password_hash

DB = "izinler.db"

def veritabani_olustur():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        sifre TEXT NOT NULL,
        rol TEXT NOT NULL,
        tur TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS izinler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_id INTEGER NOT NULL,
        izin_turu TEXT NOT NULL,
        sure INTEGER NOT NULL,
        baslangic TEXT NOT NULL,
        bitis TEXT NOT NULL,
        durum TEXT DEFAULT 'Bekliyor',
        FOREIGN KEY(kullanici_id) REFERENCES kullanicilar(id)
    )
    """)

    try:
        cur.execute("SELECT id FROM kullanicilar WHERE email = ?", ("admin@example.com",))
        if not cur.fetchone():
            cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?, ?, ?, ?, ?)",
                        ("Yönetici", "admin@example.com", generate_password_hash("galatasaray"), "yonetici", "İdari"))

        cur.execute("SELECT id FROM kullanicilar WHERE email = ?", ("deniz@example.com",))
        if not cur.fetchone():
            cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?, ?, ?, ?, ?)",
                        ("Deniz", "deniz@example.com", generate_password_hash("deniz123"), "personel", "Akademik"))

        conn.commit()
        print("✅ Veritabanı oluşturuldu ve örnek kullanıcılar eklendi.")
    except Exception as e:
        print('Hata:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    veritabani_olustur()

import sqlite3
from werkzeug.security import generate_password_hash

DB = "izinler.db"

def veritabani_olustur():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        sifre TEXT NOT NULL,
        rol TEXT NOT NULL,
        tur TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS izinler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_id INTEGER NOT NULL,
        izin_turu TEXT NOT NULL,
        sure INTEGER NOT NULL,
        baslangic TEXT NOT NULL,
        bitis TEXT NOT NULL,
        durum TEXT DEFAULT 'Bekliyor',
        FOREIGN KEY(kullanici_id) REFERENCES kullanicilar(id)
    )
    """)

    try:
        cur.execute("SELECT id FROM kullanicilar WHERE email = ?", ("admin@example.com",))
        if not cur.fetchone():
            cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?, ?, ?, ?, ?)",
                        ("Yönetici", "admin@example.com", generate_password_hash("galatasaray"), "yonetici", "İdari"))

        cur.execute("SELECT id FROM kullanicilar WHERE email = ?", ("deniz@example.com",))
        if not cur.fetchone():
            cur.execute("INSERT INTO kullanicilar (ad, email, sifre, rol, tur) VALUES (?, ?, ?, ?, ?)",
                        ("Deniz", "deniz@example.com", generate_password_hash("deniz123"), "personel", "Akademik"))

        conn.commit()
        print("✅ Veritabanı oluşturuldu ve örnek kullanıcılar eklendi.")
    except Exception as e:
        print('Hata:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    veritabani_olustur()

import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('izin_sistemi.db')
c = conn.cursor()

# users tablosu
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'admin' veya 'personel'
    total_leave INTEGER DEFAULT 14,
    used_leave INTEGER DEFAULT 0
)
''')

# leaves tablosu
c.execute('''
CREATE TABLE IF NOT EXISTS leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days INTEGER NOT NULL,
    status TEXT DEFAULT 'beklemede',
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# Örnek admin hesabı
c.execute("SELECT * FROM users WHERE email = 'admin@firma.com'")
if not c.fetchone():
    c.execute("INSERT INTO users (name, email, password, role, total_leave) VALUES (?, ?, ?, ?, ?)",
              ('Admin', 'admin@firma.com', generate_password_hash('admin123'), 'admin', 999))

conn.commit()
conn.close()
print("Veritabanı ve tablolar hazır!")
