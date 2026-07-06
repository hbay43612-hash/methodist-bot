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

# --- КОНФИГУРАЦИЯ YANDEX GPT ---
load_dotenv()

def get_openai_client():
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
    # Для локальной разработки
    api_key = os.getenv("YANDEX_CLOUD_API_KEY")
    folder = os.getenv("YANDEX_CLOUD_FOLDER")
    if api_key and folder:
        return openai.OpenAI(
            api_key=api_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=folder,
            timeout=60.0,
        )
    return None

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

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С УЧЕБНИКАМИ И КТП ---
def get_lesson_themes(grade):
    """Возвращает список тем для выбранного класса (из lessons_*.json)."""
    subject, num, level = parse_grade_choice(grade)
    key = num if subject == "hist" else f"soc_{num}"
    if level:
        key = f"{key}_{level}"
    filename = f"lessons_{key}.json"
    # Пытаемся найти файл в корневой папке
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(data.keys())
        except:
            return []
    return []

def get_lesson_types():
    """Возвращает список типов уроков из types.json."""
    if os.path.exists("types.json"):
        try:
            with open("types.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(data.keys())
        except:
            return []
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

# --- МОДЕЛИ И ТАРИФЫ (все доступны) ---
AGENTS = {
    "⚡ Быстрый (YandexGPT 5 Lite)": "fvtp590q2aec9sirbfd4",
    "⚖️ Стандарт (YandexGPT 5 Pro)": "fvtan6sh64v0qptovitu",
    "🧠 Умный (YandexGPT 5.1 Pro)": "fvttfdflmeapltgq6q3c",
}

def get_available_agents():
    """Возвращает все модели (без ограничений)."""
    return list(AGENTS.keys())

def check_generation_limit():
    """Всегда разрешает генерацию (без лимитов)."""
    return True
