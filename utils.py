# utils.py

import datetime
import sqlite3
import json
import re
import os
import tempfile
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
    if not YANDEX_CLOUD_API_KEY or not YANDEX_CLOUD_FOLDER:
        return None
    return openai.OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url="https://ai.api.cloud.yandex.net/v1",
        project=YANDEX_CLOUD_FOLDER,
        timeout=60.0,
    )

client = get_openai_client()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (из main.py) ---
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

# --- ГЕНЕРАЦИЯ КОНСПЕКТА ---
def generate_lesson(theme, lesson_type, agent_id, grade, textbook_text=""):
    """Генерирует технологическую карту урока (возвращает текст и DOCX)."""
    # Заглушка — замени на реальный код позже
    # Пока возвращаем тестовый текст
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