import sqlite3
import bcrypt
import secrets
import datetime
import os

def init_db():
    """Создаёт таблицы и гарантирует наличие пользователя-админа."""
    # Удаляем старую БД, чтобы пересоздать с правильными данными (только для отладки!)
    # Раскомментируй следующую строку, если нужно сбросить БД:
    # if os.path.exists('users.db'): os.remove('users.db')
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
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
    
    # --- ГАРАНТИРУЕМ НАЛИЧИЕ АДМИНА С ПРАВИЛЬНЫМ ПАРОЛЕМ ---
    admin_email = "dr.drozdov2016@yandex.ru"
    admin_password = "Qq12131415"
    hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
    
    # Проверяем, есть ли пользователь
    c.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    if c.fetchone():
        # Обновляем пароль и подтверждение
        c.execute("UPDATE users SET password = ?, confirmed = 1, tariff = 'pro' WHERE email = ?", (hashed, admin_email))
    else:
        # Создаём нового пользователя-админа
        c.execute(
            "INSERT INTO users (email, password, full_name, confirmed, tariff) VALUES (?, ?, ?, 1, 'pro')",
            (admin_email, hashed, "Дроздов Денис Олегович")
        )
    
    # Добавляем в админы
    c.execute("INSERT OR IGNORE INTO admins (email) VALUES (?)", (admin_email,))
    
    conn.commit()
    conn.close()

def add_user(email, password, full_name):
    """Добавляет нового пользователя (сразу подтверждён)."""
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

def get_user(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row

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

# Инициализируем БД при первом импорте
init_db()
