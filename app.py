# app.py

import streamlit as st
import os
import docx
from utils import (
    get_available_agents,
    generate_lesson,
    get_openai_client,
    get_lesson_themes,
    get_lesson_types,
    get_textbook_content,
    AGENTS,
    parse_grade_choice
)

st.set_page_config(
    page_title="Робот-методист",
    page_icon="📚",
    layout="wide"
)

client = get_openai_client()
if not client:
    st.sidebar.warning("⚠️ Yandex GPT не настроен. Проверьте ключи в секретах.")

def find_paragraph_in_textbook(theme, textbook_path):
    """Ищет в docx-файле параграф с заголовком, совпадающим с темой."""
    try:
        doc = docx.Document(textbook_path)
        current_heading = None
        paragraphs = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if text and (p.style.name.lower().startswith('heading') or p.style.name.lower().startswith('заголовок')):
                if current_heading and current_heading.lower() == theme.lower():
                    return '\n'.join(paragraphs)
                current_heading = text
                paragraphs = []
            elif current_heading:
                paragraphs.append(text)
        # Если не нашли точное совпадение, ищем по вхождению
        for p in doc.paragraphs:
            if theme.lower() in p.text.lower():
                return p.text
        return ""
    except:
        return ""

def main_app():
    st.title("📚 Робот-методист")

    st.header("📝 Генерация конспекта урока")

    grade = st.selectbox(
        "Класс",
        ["История 5", "История 6", "История 7", "История 8", "История 9",
         "История 10 (база)", "История 10 (профиль)",
         "История 11 (база)", "История 11 (профиль)",
         "Обществознание 9",
         "Обществознание 10 (база)", "Обществознание 10 (профиль)",
         "Обществознание 11 (база)", "Обществознание 11 (профиль)"],
        key="grade_selector"
    )

    themes = get_lesson_themes(grade)
    if not themes:
        st.warning("⚠️ Нет тем для выбранного класса. Проверьте файлы lessons_*.json в корневой папке.")
    theme = st.selectbox("Тема урока", themes if themes else ["Нет тем"], key="theme_selector")

    lesson_type = st.selectbox("Тип урока", get_lesson_types() or ["Нет типов"], key="lesson_type_selector")

    # Автоматический выбор учебника по классу
    subject, num, level = parse_grade_choice(grade)
    key = num if subject == "hist" else f"soc_{num}"
    if level:
        key = f"{key}_{level}"
    textbook_path = os.path.join("textbooks", f"textbook_{key}.docx")
    if not os.path.exists(textbook_path):
        # пробуем без уровня (общий)
        textbook_path = os.path.join("textbooks", f"textbook_{num}.docx")

    # Проверка на наличие учебника
    if os.path.exists(textbook_path):
        st.info(f"📖 Учебник: {os.path.basename(textbook_path)}")
    else:
        st.warning(f"⚠️ Учебник для {grade} не найден. Добавьте файл textbook_{key}.docx в папку textbooks.")

    # Модели ИИ (все доступны)
    agents = get_available_agents()
    if agents:
        agent = st.selectbox("Модель ИИ", agents, key="agent_selector")
    else:
        st.error("Нет доступных моделей.")
        agent = None

    if st.button("🚀 Сгенерировать конспект", type="primary"):
        if not client:
            st.error("❌ Yandex GPT не настроен. Проверьте ключи в секретах.")
        elif not theme or theme == "Нет тем":
            st.warning("⚠️ Выберите тему")
        elif not agent:
            st.warning("⚠️ Выберите модель ИИ")
        elif not os.path.exists(textbook_path):
            st.warning("⚠️ Учебник не найден. Загрузите файл в папку textbooks.")
        else:
            # Ищем параграф в учебнике по теме
            textbook_text = find_paragraph_in_textbook(theme, textbook_path)
            if not textbook_text:
                st.warning(f"Параграф '{theme}' не найден в учебнике. Будет использован весь текст.")
                textbook_text = get_textbook_content(textbook_path)

            with st.spinner("⏳ Генерация конспекта..."):
                try:
                    result = generate_lesson(
                        theme=theme,
                        lesson_type=lesson_type,
                        agent_id=AGENTS.get(agent),
                        grade=grade,
                        textbook_text=textbook_text[:3000]  # ограничим для экономии токенов
                    )
                    st.success("✅ Конспект готов!")
                    st.markdown("### 📄 Результат:")
                    st.text_area("Конспект", result, height=400, key="result_area")
                    st.download_button(
                        label="📥 Скачать конспект (DOCX)",
                        data=result,
                        file_name=f"Техкарта_{theme}.docx",
                        mime="text/plain",
                        key="download_btn"
                    )
                except Exception as e:
                    st.error(f"❌ Ошибка генерации: {str(e)}")

def main():
    main_app()

if __name__ == "__main__":
    main()
