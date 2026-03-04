# show_users.py
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import SessionLocal
from Bushe.learning_platform_db.models import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print("\n📋 Таблица users в базе данных learning_db")
    print("=" * 60)
    print(f"{'ID':<5} {'Логин':<15} {'Пароль':<15} {'Роль':<10} {'Имя':<15}")
    print("-" * 60)

    for user in users:
        print(
            f"{user.user_id:<5} {user.user_name:<15} {user.user_password_cash:<15} {user.user_role:<10} {user.user_surname:<15}")

    print("=" * 60)
    print(f"Всего пользователей: {len(users)}")

finally:
    db.close()