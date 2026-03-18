#!/usr/bin/env python3
"""
Проверка пользователей для входа на веб-портал.
Показывает: email, email_verified, has_password, is_blocked — чтобы найти несостыковки.

Запуск из корня проекта: python check_users_login.py
"""
from database import SessionLocal
from models import User


def main():
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.last_name, User.first_name).all()
        print(f"{'user_id':<10} {'email':<35} {'verified':<8} {'password':<8} {'blocked':<8} {'name'}")
        print("-" * 95)
        for u in users:
            email = (u.email or "-")[:33]
            verified = "да" if getattr(u, "email_verified", False) else "нет"
            has_pwd = "да" if getattr(u, "password_hash", None) else "нет"
            blocked = "да" if getattr(u, "is_blocked", False) else "нет"
            name = f"{u.last_name} {u.first_name}"[:25]
            print(f"{u.user_id:<10} {email:<35} {verified:<8} {has_pwd:<8} {blocked:<8} {name}")

        # Проблемные случаи
        no_email = [u for u in users if not u.email]
        email_not_verified = [u for u in users if u.email and not getattr(u, "email_verified", False)]
        no_password = [u for u in users if u.email and getattr(u, "email_verified", False) and not getattr(u, "password_hash", None)]

        print("\n--- Потенциальные проблемы ---")
        if no_email:
            print(f"Без email ({len(no_email)}): user_id={[u.user_id for u in no_email[:10]]}{'...' if len(no_email) > 10 else ''}")
        if email_not_verified:
            print(f"Email не верифицирован ({len(email_not_verified)}): {[u.email for u in email_not_verified[:5]]}{'...' if len(email_not_verified) > 5 else ''}")
        if no_password:
            print(f"Верифицирован, но пароль не задан — войти по паролю нельзя ({len(no_password)}): {[u.email for u in no_password[:5]]}{'...' if len(no_password) > 5 else ''}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
