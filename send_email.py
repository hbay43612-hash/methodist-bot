# send_email.py

import requests
import streamlit as st

def send_confirmation_email(to_email, token):
    """Отправляет письмо с подтверждением через Unisender API."""
    api_key = st.secrets.get("UNISENDER_API_KEY")
    from_email = st.secrets.get("FROM_EMAIL")
    from_name = st.secrets.get("FROM_NAME", "Робот-методист")
    
    if not api_key or not from_email:
        print("Ошибка: отсутствуют UNISENDER_API_KEY или FROM_EMAIL")
        return False
    
    # Ссылка для подтверждения
    link = f"https://methodist-bot-hbay43612-hash.streamlit.app/confirm?token={token}"
    
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
    
    url = "https://api.unisender.com/ru/api/sendEmail"
    params = {
        "format": "json",
        "api_key": api_key,
        "email": to_email,
        "sender_email": from_email,
        "sender_name": from_name,
        "subject": subject,
        "body": html,
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        result = response.json()
        if result.get("status") == "success":
            print(f"Письмо отправлено на {to_email}")
            return True
        else:
            print(f"Unisender ошибка: {result}")
            return False
    except Exception as e:
        print(f"Исключение при отправке: {e}")
        return False
