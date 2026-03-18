#!/usr/bin/env python3
"""
Сброс пароля пользователя по email.
Запуск: python reset_user_password.py <email> <новый_пароль>

Пример: python reset_user_password.py ya.serj.s.a@gmail.com MyNewPass123
"""
import sys
from passlib.context import CryptContext
from database import SessionLocal
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    if len(sys.argv) != 3:
        print("Использование: python reset_user_password.py <email> <новый_пароль>")
        print("Пароль должен быть не менее 8 символов.")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    new_password = sys.argv[2]

    if len(new_password) < 8:
        print("Ошибка: пароль должен быть не менее 8 символов.")
        sys.exit(1)

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"Пользователь с email {email} не найден.")
            sys.exit(1)

        user.password_hash = pwd_context.hash(new_password)
        session.commit()
        print(f"Пароль для {user.last_name} {user.first_name} ({email}) успешно изменён.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
