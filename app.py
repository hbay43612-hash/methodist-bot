# app.py (обновлённая версия с уникальными ключами)

import streamlit as st
from auth import login_page, register_page, logout
from admin import admin_panel
from utils import check_generation_limit, get_available_agents, generate_lesson, get_openai_client
from tariffs import TARIFFS, AGENTS
from database import confirm_user

st.set_page_config(
    page_title="Робот-методист",
    page_icon="📚",
    layout="wide"
)

client = get_openai_client()
if not client:
    st.sidebar.warning("⚠️ Yandex GPT не настроен. Проверьте ключи в .env")

def main_app():
    st.title("📚 Робот-методист")
    st.write(f"👋 Добро пожаловать, **{st.session_state['user']}**!")
    st.write(f"💰 Тариф: **{st.session_state['tariff']}**")

    if st.sidebar.button("🚪 Выйти"):
        logout()

    if st.session_state.get('role') == 'admin':
        admin_panel()
        st.divider()

    st.header("📝 Генерация конспекта урока")
    with st.form("generation_form_main"):
        col1, col2 = st.columns(2)
        with col1:
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
            theme = st.text_input("Тема урока", placeholder="Например: Урок 5. Европа в IX—XI вв.", key="theme_text_input")
            lesson_type = st.selectbox(
                "Тип урока",
                ["Урок изучения нового материала (ФГОС + ФГ + ФО)",
                 "Урок изучения нового материала",
                 "Урок закрепления (первоначальных навыков)",
                 "Урок повторения (актуализации)",
                 "Урок обобщения и систематизации",
                 "Контрольный урок",
                 "Коррекционный урок",
                 "Комбинированный урок",
                 "Урок применения метапредметных знаний",
                 "Интегрированный урок",
                 "Нетрадиционные уроки (экскурсия и др.)",
                 "Урок проектных задач"],
                key="lesson_type_selector"
            )
        with col2:
            available_agents = get_available_agents(st.session_state['user'])
            if available_agents:
                agent = st.selectbox("Модель ИИ", available_agents, key="agent_selector")
            else:
                st.error("Нет доступных моделей. Повысьте тариф.")
                agent = None
            textbook_file = st.file_uploader("Загрузить учебник (DOCX)", type=['docx'], key="textbook_uploader_main")

        submitted = st.form_submit_button("🚀 Сгенерировать конспект")

    if submitted:
        if not client:
            st.error("❌ Yandex GPT не настроен. Проверьте ключи в .env")
        elif not theme:
            st.warning("⚠️ Введите тему урока")
        elif not agent:
            st.warning("⚠️ Выберите модель ИИ")
        else:
            if not check_generation_limit(st.session_state['user']):
                st.error("⛔ Дневной лимит генераций исчерпан. Повысьте тариф.")
            else:
                with st.spinner("⏳ Генерация конспекта..."):
                    result = generate_lesson(
                        theme=theme,
                        lesson_type=lesson_type,
                        agent_id=AGENTS.get(agent),
                        grade=grade,
                        textbook_text="Текст учебника (пока заглушка)"
                    )
                    st.success("✅ Конспект готов!")
                    st.markdown("### 📄 Результат:")
                    st.text_area("Конспект", result, height=400, key="result_text_area")
                    st.download_button(
                        label="📥 Скачать конспект (DOCX)",
                        data="Пока просто текст",
                        file_name=f"Конспект_{theme}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_btn_main"
                    )

def main():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if "token" in st.query_params:
        token = st.query_params["token"]
        if confirm_user(token):
            st.success("✅ Почта подтверждена! Теперь вы можете войти.")
            st.query_params.clear()
        else:
            st.error("❌ Неверный или истёкший токен.")
            st.query_params.clear()

    if st.session_state['authenticated']:
        main_app()
    else:
        tab1, tab2 = st.tabs(["🔐 Вход", "📝 Регистрация"])
        with tab1:
            login_page()
        with tab2:
            register_page()

if __name__ == "__main__":
    main()