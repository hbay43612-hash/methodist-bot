import streamlit as st
import os
from utils import (
    get_available_agents,
    generate_lesson,
    get_openai_client,
    get_lesson_themes,
    get_lesson_types,
    get_textbook_content,
    get_paragraphs_from_docx,
    get_textbook_paragraph_content,
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
        st.warning("⚠️ Нет тем для выбранного класса. Проверьте файлы lessons_*.json.")
        themes = ["Нет тем"]

    theme = st.selectbox("Тема урока", themes, key="theme_selector")

    lesson_types = get_lesson_types()
    if not lesson_types:
        st.warning("⚠️ Файл types.json не найден.")
        lesson_types = ["Нет типов"]

    lesson_type = st.selectbox("Тип урока", lesson_types, key="lesson_type_selector")

    # --- УЧЕБНИК И ПАРАГРАФЫ ---
    textbook_files = []
    if os.path.exists("textbooks"):
        textbook_files = [f for f in os.listdir("textbooks") if f.endswith(".docx")]

    if textbook_files:
        textbook_choice = st.selectbox("Учебник", textbook_files, key="textbook_selector")

        # Парсим параграфы из выбранного учебника
        textbook_path = os.path.join("textbooks", textbook_choice)
        paragraphs = get_paragraphs_from_docx(textbook_path)

        if paragraphs:
            selected_paragraph = st.selectbox("Параграф (раздел)", paragraphs, key="paragraph_selector")
            # Получаем текст выбранного параграфа
            textbook_text = get_textbook_paragraph_content(textbook_path, selected_paragraph)
        else:
            st.warning("⚠️ В учебнике не найдены разделы. Будет использован весь текст.")
            selected_paragraph = None
            textbook_text = get_textbook_content(textbook_path)
    else:
        st.warning("📁 Нет загруженных учебников. Положите файлы .docx в папку textbooks.")
        textbook_choice = None
        textbook_text = ""

    # --- МОДЕЛИ ---
    agents = get_available_agents()
    if agents:
        agent = st.selectbox("Модель ИИ", agents, key="agent_selector")
    else:
        st.error("Нет доступных моделей.")
        agent = None

    if st.button("🚀 Сгенерировать конспект", type="primary"):
        if not client:
            st.error("❌ Yandex GPT не настроен.")
        elif not theme or theme == "Нет тем":
            st.warning("⚠️ Выберите тему")
        elif not agent:
            st.warning("⚠️ Выберите модель")
        elif not textbook_choice:
            st.warning("⚠️ Выберите учебник")
        else:
            with st.spinner("⏳ Генерация..."):
                try:
                    result = generate_lesson(
                        theme=theme,
                        lesson_type=lesson_type,
                        agent_id=AGENTS.get(agent),
                        grade=grade,
                        textbook_text=textbook_text
                    )
                    st.success("✅ Конспект готов!")
                    st.markdown("### 📄 Результат:")
                    st.text_area("Конспект", result, height=500, key="result_area")
                    st.download_button(
                        label="📥 Скачать конспект (DOCX)",
                        data=result,
                        file_name=f"Техкарта_{theme[:30]}.docx",
                        mime="text/plain",
                        key="download_btn"
                    )
                except Exception as e:
                    st.error(f"❌ Ошибка генерации: {e}")

def main():
    main_app()

if __name__ == "__main__":
    main()
