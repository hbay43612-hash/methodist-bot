# send_email.py

import requests
import streamlit as st

def send_confirmation_email(to_email, token):
    """Отправляет письмо с подтверждением через Unisender API."""
    api_key = st.secrets.get("UNISENDER_API_KEY")
    from_email = st.secrets.get("FROM_EMAIL")
    from_name = st.secrets.get("FROM_NAME", "Робот-методист")
    
    if not api_key or not from_email:
        return False
    
    # Ссылка для подтверждения
    link = f"https://methodist-bot-hbay43612-hash.streamlit.app/confirm?token={token}"
    
    # Текст письма
    subject = "Подтверждение регистрации"
    html = f"""
    <html>
        <body>
            <h2>Подтверждение регистрации</h2>
            <p>Перейдите по ссылке для подтверждения:</p>
            <a href="{link}">Подтвердить</a>
        </body>
    </html>
    """
    
    # API Unisender (v2)
    url = "https://api.unisender.com/ru/api/sendEmail"
    params = {
        "format": "json",
        "api_key": api_key,
        "email": to_email,
        "sender_email": from_email,
        "sender_name": from_name,
        "subject": subject,
        "body": html,
        "list_id": 1  # если у тебя есть список, иначе можно убрать
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        result = response.json()
        # Если статус "success" — письмо отправлено
        if result.get("status") == "success":
            return True
        else:
            # Логируем ошибку, но не прерываем регистрацию
            print(f"Unisender error: {result}")
            return False
    except Exception as e:
        print(f"Unisender exception: {e}")
        return False
