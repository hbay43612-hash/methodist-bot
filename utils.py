import os
import json
import re
import random
import logging
from io import BytesIO

import openai
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# ============================================================
# 1. ЗАГРУЗКА JSON
# ============================================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

# ============================================================
# 2. КОНФИГУРАЦИЯ YANDEX GPT
# ============================================================
def get_openai_client():
    try:
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

client = get_openai_client()

# ============================================================
# 3. ПАРСИНГ КЛАССА И КЛЮЧИ ФАЙЛОВ (из main.py)
# ============================================================
def parse_grade_choice(choice):
    subject = "soc" if "обществозн" in choice.lower() else "hist"
    m = re.search(r'(\d+)', choice)
    num = m.group(1) if m else ""
    level = ""
    if "база" in choice.lower():
        level = "base"
    elif "профиль" in choice.lower():
        level = "prof"
    return subject, num, level

def grade_file_key(choice):
    subject, num, level = parse_grade_choice(choice)
    key = num if subject == "hist" else f"soc_{num}"
    if level:
        key = f"{key}_{level}"
    return key

def textbook_keys(choice):
    subject, num, level = parse_grade_choice(choice)
    base = num if subject == "hist" else f"soc_{num}"
    if level:
        return [f"{base}_{level}", base]
    return [base]

# ============================================================
# 4. ЗАГРУЗКА ДАННЫХ
# ============================================================
TYPES_DATA = load_json("types.json")
PROMPTS_DATA = load_json("prompts.json")
SOCIAL_PROMPTS_DATA = load_json("prompts_social.json")

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (из main.py)
# ============================================================
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

# ============================================================
# 6. ВАРИАТИВНОСТЬ ПРИЁМОВ
# ============================================================
_SERVICE_PROMPTS = {"Функциональная грамотность (PISA)", "Формирующее оценивание (Промпт №2)"}

def _technique_short(value):
    if isinstance(value, dict):
        return value.get("суть") or value.get("инструкция", "")
    return value

def _technique_full(value):
    if isinstance(value, dict):
        return value.get("инструкция") or value.get("суть", "")
    return value

def get_technique_bank(subject):
    if subject == "soc":
        return {name: _technique_short(desc) for name, desc in SOCIAL_PROMPTS_DATA.items()
                if name not in _SERVICE_PROMPTS}
    else:
        return {name: _technique_short(desc) for name, desc in PROMPTS_DATA.items()
                if name not in _SERVICE_PROMPTS}

def pick_techniques(subject, n=4):
    bank = get_technique_bank(subject)
    if not bank:
        return []
    names = list(bank.keys())
    random.shuffle(names)
    chosen = names[:n]
    return [(name, bank[name]) for name in chosen]

_VARIATIVE_KEYWORDS = (
    "актуализац", "усвоен", "закреплен", "применен",
    "домашн", "рефлекс", "обобщен", "систематизац", "творческ",
)

def is_variative_stage(stage_name):
    low = stage_name.lower()
    return any(kw in low for kw in _VARIATIVE_KEYWORDS)

# ============================================================
# 7. ГЕНЕРАЦИЯ КОНСПЕКТА (ПОЛНОСТЬЮ ИЗ main.py)
# ============================================================
def generate_lesson(theme, lesson_type, agent_id, grade, textbook_text=""):
    if not client:
        raise Exception("Yandex GPT не настроен")

    subject, _, _ = parse_grade_choice(grade)
    if subject == "soc":
        teacher_label = "обществознания"
        meta_fields = "основные термины, нормативные акты, социальные институты и процессы"
    else:
        teacher_label = "истории"
        meta_fields = "основные понятия и даты; список исторических личностей темы"

    stages = TYPES_DATA.get(lesson_type, {})
    if not stages:
        return f"Ошибка: тип урока «{lesson_type}» не найден в types.json."

    table_data = []
    lesson_meta = {}
    ctx = f"Учебник: {textbook_text[:3000]}"

    # --- ШАПКА ---
    try:
        m_instruction = (
            f"Ты опытный учитель {teacher_label}. Класс: {grade}. "
            f"Тема урока: {theme}. Тип урока: {lesson_type}.\n\n"
            f"ВОТ МАТЕРИАЛ УРОКА (учебник), на который ты "
            f"ОБЯЗАН опираться:\n«««\n{ctx}\n»»»\n\n"
            f"Сформулируй для технологической карты урока: "
            f"общую цель урока; образовательную задачу; развивающую задачу; "
            f"воспитательную задачу; {meta_fields}.\n\n"
            f"ТРЕБОВАНИЯ: используй КОНКРЕТНЫЕ факты, термины, нормативные акты, "
            f"экономические показатели ИМЕННО из приведённого выше материала. "
            f"Запрещены обтекаемые формулировки, подходящие к любому уроку."
        )
        lesson_meta = ask_json(agent_id, m_instruction,
                               ['goal', 't_edu', 't_dev', 't_vosp', 'concepts', 'persons'])
    except Exception as e:
        lesson_meta = {}
        logging.exception("Ошибка генерации шапки")

    # --- ЭТАПЫ ---
    stage_keys = ['task', 'forms', 'teacher', 'student', 'result', 'diagnostics']
    extra_note_soc = ""
    if subject == "soc":
        extra_note_soc = (
            "\nУЧТИ: в заданиях и диагностике используй ссылки на нормативные акты, "
            "расчёты, социальные процессы. Не ограничивайся только фактами."
        )

    for idx, (s_n, s_p) in enumerate(stages.items()):
        technique_block = ""
        if is_variative_stage(s_n):
            techs = pick_techniques(subject, 4)
            if techs:
                listed = "\n".join(f"  • {name}: {desc.split(chr(10))[0]}" for name, desc in techs)
                technique_block = (
                    f"\n\n⚠ ВАРИАТИВНОСТЬ ПРИЁМА (важно для этого этапа):\n"
                    f"Методический сценарий выше может называть конкретный приём. "
                    f"НЕ используй его автоматически — вместо него ВЫБЕРИ один "
                    f"подходящий приём из списка ниже:\n{listed}\n"
                )

        if is_variative_stage(s_n):
            scenario_rule = (
                "МЕТОДИЧЕСКАЯ ЦЕЛЬ И ЛОГИКА ЭТОГО ЭТАПА (сохрани её суть, но "
                "конкретный приём можешь заменить):"
            )
        else:
            scenario_rule = (
                "МЕТОДИЧЕСКИЙ СЦЕНАРИЙ ЭТОГО ЭТАПА (его нужно ТОЧНО воплотить):"
            )

        u_instruction = (
            f"Ты опытный учитель {teacher_label}, заполняешь технологическую карту урока.\n"
            f"Класс: {grade}. Тема: {theme}. Тип урока: {lesson_type}.\n"
            f"Этап урока: «{s_n}».\n\n"
            f"ГЛАВНОЕ — {scenario_rule}\n"
            f"►►► {s_p} ◄◄◄"
            f"{technique_block}\n\n"
            f"ВОТ МАТЕРИАЛ УРОКА (учебник):\n«««\n{ctx}\n»»»\n\n"
            f"Распиши реализацию сценария по шести полям технологической карты:\n"
            f'"task" — задача этапа;\n'
            f'"forms" — формы организации;\n'
            f'"teacher" — действия учителя (конкретные вопросы, задания);\n'
            f'"student" — действия учащихся (конкретные, НЕ «слушают»);\n'
            f'"result" — что ученик теперь знает/умеет;\n'
            f'"diagnostics" — конкретный вопрос/задание для проверки.\n\n'
            f"ЗАПРЕЩЕНО: общие фразы, вода, пересказ сценария."
            + extra_note_soc
        )

        try:
            fields = ask_json(agent_id, u_instruction, stage_keys)
            row = {'stage': s_n}
            row.update(fields)
            table_data.append(row)
        except Exception as e:
            logging.exception("Ошибка генерации этапа «%s»", s_n)
            row = {'stage': s_n, '_error': str(e)}
            for k in stage_keys:
                row[k] = ""
            table_data.append(row)

    # Формируем результат
    result = f"""Технологическая карта урока.

Класс: {grade}
Тема: {theme}
Тип урока: {lesson_type}

**Цель урока:** {lesson_meta.get('goal', '')}
**Образовательные:** {lesson_meta.get('t_edu', '')}
**Развивающие:** {lesson_meta.get('t_dev', '')}
**Воспитательные:** {lesson_meta.get('t_vosp', '')}

**Ход урока:**
"""
    for i, row in enumerate(table_data, 1):
        result += f"\n{i}. {row.get('stage', '')}\n"
        result += f"   Задача: {row.get('task', '')}\n"
        result += f"   Формы: {row.get('forms', '')}\n"
        result += f"   Учитель: {row.get('teacher', '')}\n"
        result += f"   Ученики: {row.get('student', '')}\n"
        result += f"   Результат: {row.get('result', '')}\n"
        result += f"   Диагностика: {row.get('diagnostics', '')}\n"

    return result

# ============================================================
# 8. ФУНКЦИИ ДЛЯ ИНТЕРФЕЙСА (ТЕМЫ, ТИПЫ УРОКОВ, УЧЕБНИКИ)
# ============================================================
def get_lesson_themes(grade):
    key = grade_file_key(grade)
    filename = f"lessons_{key}.json"
    data = load_json(filename)
    if not data and key == "5":
        data = load_json("lessons.json")
    return list(data.keys()) if data else []

def get_lesson_types():
    return list(TYPES_DATA.keys()) if TYPES_DATA else []

def get_textbook_content(filepath):
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except:
        return ""

# ============================================================
# 9. МОДЕЛИ И ТАРИФЫ
# ============================================================
AGENTS = {
    "⚡ Быстрый (YandexGPT 5 Lite)": "fvtp590q2aec9sirbfd4",
    "⚖️ Стандарт (YandexGPT 5 Pro)": "fvtan6sh64v0qptovitu",
    "🧠 Умный (YandexGPT 5.1 Pro)": "fvttfdflmeapltgq6q3c",
}

def get_available_agents():
    return list(AGENTS.keys())

def check_generation_limit():
    return True
