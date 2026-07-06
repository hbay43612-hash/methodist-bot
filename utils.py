# utils.py

import datetime
import sqlite3
import json
import re
import os
import logging
import random
from io import BytesIO

import openai
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dotenv import load_dotenv

from tariffs import TARIFFS, AGENTS

load_dotenv()

# --- КОНФИГУРАЦИЯ YANDEX GPT ---
YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")
YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")

def get_openai_client():
    # Сначала пробуем получить из st.secrets (для Streamlit Cloud)
    try:
        import streamlit as st
        api_key = st.secrets.get("YANDEX_CLOUD_API_KEY")
        folder = st.secrets.get("YANDEX_CLOUD_FOLDER")
        if api_key and folder:
            return openai.OpenAI(
                api_key=api_key,
                base_url="https://ai.api.cloud.yandex.net/v1",
                project=folder,
                timeout=60.0,
            )
    except:
        pass
    # Если нет — пробуем из .env (для локальной разработки)
    if YANDEX_CLOUD_API_KEY and YANDEX_CLOUD_FOLDER:
        return openai.OpenAI(
            api_key=YANDEX_CLOUD_API_KEY,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=YANDEX_CLOUD_FOLDER,
            timeout=60.0,
        )
    return None

client = get_openai_client()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def _strip_cite_marks(obj):
    if isinstance(obj, str):
        return re.sub(r'\s*\[cite[^\]]*\]', '', obj)
    if isinstance(obj, dict):
        return {k: _strip_cite_marks(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_cite_marks(v) for v in obj]
    return obj

def _extract_json(text):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    chunk = text[start:end+1]
    try:
        return json.loads(chunk)
    except:
        return None

def ask_json(agent_id, instruction, expected_keys):
    """Отправляет запрос в Yandex GPT и возвращает JSON-ответ."""
    if not client:
        raise Exception("Yandex GPT не настроен")
    keys_desc = ", ".join(f'"{k}"' for k in expected_keys)
    full_prompt = (
        instruction
        + "\n\nВЕРНИ ОТВЕТ СТРОГО В ФОРМАТЕ JSON, без пояснений, без markdown, "
        + "без обратных кавычек. Только один JSON-объект со следующими ключами: "
        + keys_desc + ". "
        + "Значение каждого ключа — готовый текст на русском языке для этого поля "
        + "технологической карты. Не добавляй других ключей."
    )
    raw = client.responses.create(prompt={"id": agent_id}, input=full_prompt).output_text
    data = _extract_json(raw)
    if data is None:
        logging.warning("Модель вернула не-JSON, использую сырой текст. Ответ: %s", raw[:500])
        data = {expected_keys[0]: raw.strip()}
    return {k: str(data.get(k, "") or "").strip() for k in expected_keys}

# --- ГЕНЕРАЦИЯ КОНСПЕКТА (пока заглушка) ---
def generate_lesson(theme, lesson_type, agent_id, grade, textbook_text=""):
    """Генерирует технологическую карту урока (возвращает текст)."""
    return f"""Технологическая карта урока.

Класс: {grade}
Тема: {theme}
Тип урока: {lesson_type}

**Цель урока:** Сформировать у учащихся представление о ...

**Задачи:**
Образовательные: ...
Развивающие: ...
Воспитательные: ...

**Ход урока:**
... (здесь будет полный конспект)
"""

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ ---
def check_generation_limit(email):
    """Проверяет, не превышен ли дневной лимит."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("SELECT tariff, daily_generations, last_gen_date FROM users WHERE email=?", (email,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    tariff, gen_count, last_date = row
    if last_date != today:
        gen_count = 0
        c.execute("UPDATE users SET daily_generations = 0, last_gen_date = ? WHERE email=?", (today, email))
        conn.commit()
    limit = TARIFFS[tariff]["generations_per_day"]
    if gen_count >= limit:
        conn.close()
        return False
    c.execute("UPDATE users SET daily_generations = ? WHERE email=?", (gen_count+1, email))
    conn.commit()
    conn.close()
    return True

def get_available_agents(email):
    """Возвращает список доступных моделей для пользователя."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT tariff FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        tariff = row[0]
        return TARIFFS[tariff]["available_agents"]
    return []

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С УЧЕБНИКАМИ И КТП ---
def get_lesson_themes(grade):
    """Возвращает список тем для выбранного класса (из lessons_*.json)."""
    subject, num, level = parse_grade_choice(grade)
    key = num if subject == "hist" else f"soc_{num}"
    if level:
        key = f"{key}_{level}"
    filename = f"lessons_{key}.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return list(data.keys())
    return []

def get_lesson_types():
    """Возвращает список типов уроков из types.json."""
    if os.path.exists("types.json"):
        with open("types.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return list(data.keys())
    return []

def get_textbook_content(filepath):
    """Читает текст из DOCX-файла."""
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except:
        return ""

def parse_grade_choice(choice):
    """Разбирает строку класса на (subject, num, level)."""
    subject = "soc" if "обществозн" in choice.lower() else "hist"
    m = re.search(r'(\d+)', choice)
    num = m.group(1) if m else ""
    level = ""
    if "база" in choice.lower():
        level = "base"
    elif "профиль" in choice.lower():
        level = "prof"
    return subject, num, level
