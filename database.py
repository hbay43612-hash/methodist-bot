import sqlite3
import bcrypt
import secrets
import datetime
import os

def init_db():
    if os.path.exists('users.db'):
        os.remove('users.db')
        print("Старая БД удалена, создаётся новая.")
    
    conn = sqlite3.connect('users.db')
    # Включаем поддержку BLOB
    conn.execute('PRAGMA encoding="UTF-8"')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password BLOB,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            tariff TEXT DEFAULT 'free',
            daily_generations INTEGER DEFAULT 0,
            last_gen_date TEXT,
            confirmed BOOLEAN DEFAULT 1,
            confirm_token TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE
        )
    ''')
    
    admins = [
        ("dr.drozdov2016@yandex.ru", "Qq12131415", "Дроздов Денис Олегович"),
        ("test@test.ru", "Qq12131415", "Тест Тестович")
    ]
    
    for email, password, full_name in admins:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            c.execute("UPDATE users SET password = ?, confirmed = 1, tariff = 'pro' WHERE email = ?", (hashed, email))
        else:
            c.execute(
                "INSERT INTO users (email, password, full_name, confirmed, tariff) VALUES (?, ?, ?, 1, 'pro')",
                (email, hashed, full_name)
            )
        c.execute("INSERT OR IGNORE INTO admins (email) VALUES (?)", (email,))
    
    conn.commit()
    conn.close()
    print("База данных инициализирована, админы созданы.")

def get_user(email):
    conn = sqlite3.connect('users.db')
    # КЛЮЧЕВОЕ: заставляем SQLite возвращать BLOB как bytes
    conn.text_factory = bytes
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row

def add_user(email, password, full_name):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    confirm_token = secrets.token_urlsafe(32)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (email, password, full_name, confirm_token, confirmed) VALUES (?, ?, ?, ?, 1)",
            (email, hashed, full_name, confirm_token)
        )
        conn.commit()
        return confirm_token
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def confirm_user(token):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET confirmed = 1 WHERE confirm_token = ?", (token,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def is_admin(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row is not None

def add_admin(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()

init_db()
