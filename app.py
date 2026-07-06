# app.py

import streamlit as st
import os
from utils import (
    get_available_agents,
    generate_lesson,
    get_openai_client,
    get_lesson_themes,
    get_lesson_types,
    get_textbook_content,
    AGENTS
)

st.set_page_config(
    page_title="Робот-методист",
    page_icon="📚",
    layout="wide"
)

client = get_openai_client()
if not client:
    st.sidebar.warning("⚠️ Yandex GPT не настроен. Проверьте ключи в секретах.")

def main_app():
    st.title("📚 Робот-методист")

    st.header("📝 Генерация конспекта урока")

    # Выбор класса
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

    # Получаем темы для выбранного класса
    themes = get_lesson_themes(grade)
    if not themes:
        st.warning("⚠️ Нет тем для выбранного класса. Проверьте файлы lessons_*.json в корневой папке.")
    theme = st.selectbox("Тема урока", themes if themes else ["Нет тем"], key="theme_selector")

    lesson_type = st.selectbox("Тип урока", get_lesson_types() or ["Нет типов"], key="lesson_type_selector")

    # Выбор учебника (из папки textbooks)
    textbook_files = []
    if os.path.exists("textbooks"):
        textbook_files = [f for f in os.listdir("textbooks") if f.endswith(".docx")]
    textbook_choice = None
    if textbook_files:
        textbook_choice = st.selectbox("Учебник", textbook_files, key="textbook_selector")
    else:
        st.warning("📁 Нет загруженных учебников. Положите файлы .docx в папку textbooks.")

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
        elif not textbook_choice:
            st.warning("⚠️ Выберите учебник")
        else:
            with st.spinner("⏳ Генерация конспекта..."):
                textbook_path = os.path.join("textbooks", textbook_choice)
                textbook_text = get_textbook_content(textbook_path)

                result = generate_lesson(
                    theme=theme,
                    lesson_type=lesson_type,
                    agent_id=AGENTS.get(agent),
                    grade=grade,
                    textbook_text=textbook_text
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

def main():
    main_app()

if __name__ == "__main__":
    main()
