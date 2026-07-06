# admin.py

import streamlit as st
import sqlite3
import datetime
from tariffs import TARIFFS

def admin_panel():
    st.title("🛠️ Администрирование")
    if st.session_state.get('role') != 'admin':
        st.error("⛔ Доступ запрещён")
        return

    st.subheader("👥 Список пользователей")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT email, full_name, tariff, daily_generations, last_gen_date, confirmed FROM users")
    users = c.fetchall()
    conn.close()

    for user in users:
        with st.expander(f"{user[1]} ({user[0]})"):
            st.write(f"📊 Тариф: **{user[2]}**")
            st.write(f"📈 Генераций сегодня: **{user[3]}**")
            st.write(f"📅 Последняя генерация: **{user[4] or 'никогда'}**")
            st.write(f"✅ Подтверждён: **{'Да' if user[5] else 'Нет'}**")

            col1, col2 = st.columns(2)
            with col1:
                new_tariff = st.selectbox(
                    "Изменить тариф",
                    options=list(TARIFFS.keys()),
                    key=f"tariff_{user[0]}"
                )
                if st.button("Обновить тариф", key=f"upd_{user[0]}"):
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute("UPDATE users SET tariff = ? WHERE email = ?", (new_tariff, user[0]))
                    conn.commit()
                    conn.close()
                    st.success("✅ Тариф обновлён!")
                    st.rerun()
            with col2:
                if st.button("Сбросить лимит", key=f"reset_{user[0]}"):
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute("UPDATE users SET daily_generations = 0, last_gen_date = ? WHERE email = ?",
                              (datetime.date.today().isoformat(), user[0]))
                    conn.commit()
                    conn.close()
                    st.success("✅ Лимит сброшен!")
                    st.rerun()