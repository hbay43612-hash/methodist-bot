# send_email.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def send_confirmation_email(to_email, token):
    """Отправляет письмо с ссылкой на подтверждение."""
    if not SENDGRID_API_KEY or not FROM_EMAIL:
        return False
    subject = "Подтверждение регистрации"
    # Ссылка для подтверждения (потом заменишь на свой домен)
    link = f"https://your-app.streamlit.app/confirm?token={token}"
    html = f"""
    <html>
        <body>
            <h2>Подтверждение регистрации</h2>
            <p>Перейдите по ссылке для подтверждения:</p>
            <a href="{link}">Подтвердить</a>
        </body>
    </html>
    """
    data = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}]
    }
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post("https://api.sendgrid.com/v3/mail/send", json=data, headers=headers)
        return response.status_code == 202
    except:
        return False