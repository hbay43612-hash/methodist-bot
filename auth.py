import streamlit as st
from database import get_user, add_user, confirm_user, is_admin

def login_page():
    st.title("🔐 Вход в систему (временно без пароля)")
    if st.button("Войти в программу", type="primary"):
        st.session_state['authenticated'] = True
        st.session_state['user'] = "admin@temp.ru"
        st.session_state['role'] = "admin"
        st.session_state['tariff'] = "pro"
        st.rerun()

def register_page():
    st.title("📝 Регистрация (отключена)")
    st.info("Регистрация временно отключена. Нажмите 'Войти в программу' на вкладке 'Вход'.")

def logout():
    for key in ['authenticated', 'user', 'role', 'tariff']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
