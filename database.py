import sqlite3
import bcrypt
import secrets
import datetime

def init_db():
    """Создаёт таблицы, если их нет."""
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
            confirmed BOOLEAN DEFAULT 1,   -- сразу подтверждён
            confirm_token TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE
        )
    ''')
    # Добавляем тебя в админы (если ещё не добавлен)
    c.execute("INSERT OR IGNORE INTO admins (email) VALUES ('dr.drozdov2016@yandex.ru')")
    conn.commit()
    conn.close()

def add_user(email, password, full_name):
    """Добавляет нового пользователя (пароль хэшируется)."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    confirm_token = secrets.token_urlsafe(32)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        # Вставляем с confirmed = 1 (сразу подтверждён)
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
    """Возвращает данные пользователя по email."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row

def confirm_user(token):
    """Подтверждает пользователя по токену (если нужно)."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET confirmed = 1 WHERE confirm_token = ?", (token,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def is_admin(email):
    """Проверяет, является ли пользователь админом."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row is not None

def add_admin(email):
    """Добавляет админа (можно вызвать дополнительно)."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()

# Инициализируем БД при первом импорте
init_db()
