
"""Initialize database for production (Postgres) or local SQLite fallback.
Run: python init_db_render.py
"""
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Date, Text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    sqlite_path = os.path.join(os.getcwd(), 'izinler.db')
    engine = create_engine(f"sqlite:///{sqlite_path}")

meta = MetaData()

kullanicilar = Table(
    'kullanicilar', meta,
    Column('id', Integer, primary_key=True),
    Column('ad', String, nullable=True),
    Column('email', String, unique=True, nullable=False),
    Column('sifre', String, nullable=False),
    Column('rol', String, nullable=False),
    Column('tur', String, nullable=True)
)

izinler = Table(
    'izinler', meta,
    Column('id', Integer, primary_key=True),
    Column('kullanici_id', Integer, nullable=False),
    Column('izin_turu', String, nullable=True),
    Column('sure', Integer, nullable=True),
    Column('baslangic', String, nullable=True),
    Column('bitis', String, nullable=True),
    Column('durum', String, nullable=True)
)

try:
    meta.create_all(engine)
    print('Database initialized.')
except OperationalError as e:
    print('Database error:', e)
