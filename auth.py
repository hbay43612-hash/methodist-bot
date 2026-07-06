import streamlit as st
from database import get_user, add_user, confirm_user, is_admin
from send_email import send_confirmation_email

def login_page():
    st.title("🔐 Вход в систему")
    email = st.text_input("Email", key="login_email_field")
    password = st.text_input("Пароль", type="password", key="login_password_field")
    if st.button("Войти", type="primary", key="login_submit_btn"):
        user = get_user(email)
        if user:
            if password == user[1]:
                st.session_state['authenticated'] = True
                st.session_state['user'] = email
                st.session_state['role'] = 'admin' if is_admin(email) else 'user'
                st.session_state['tariff'] = user[4]
                st.rerun()
            else:
                st.error("❌ Неверный пароль")
        else:
            st.error("❌ Пользователь не найден. Зарегистрируйтесь.")

def register_page():
    st.title("📝 Регистрация")
    full_name = st.text_input("ФИО", key="register_fullname_field")
    email = st.text_input("Email", key="register_email_field")
    password = st.text_input("Пароль", type="password", key="register_password_field_1")
    password2 = st.text_input("Повторите пароль", type="password", key="register_password_field_2")
    agree = st.checkbox("Я принимаю условия пользовательского соглашения", key="register_agree_check")
    if st.button("Зарегистрироваться", type="primary", key="register_submit_btn"):
        if not agree:
            st.warning("⚠️ Необходимо принять соглашение")
            return
        if password != password2:
            st.error("❌ Пароли не совпадают")
            return
        if len(password) < 6:
            st.error("❌ Пароль должен быть не менее 6 символов")
            return
        token = add_user(email, password, full_name)
        if token is None:
            st.error("❌ Пользователь с таким email уже существует")
        else:
            st.success("✅ Регистрация завершена! Теперь вы можете войти.")

def logout():
    for key in ['authenticated', 'user', 'role', 'tariff']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
