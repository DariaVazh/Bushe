# hr_learning_dashboards/add_admin.py
import sys
import os

# Добавляем путь к learning_platform_db
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import SessionLocal
from Bushe.learning_platform_db.models import User
from Bushe.learning_platform_db.crud import UserCRUD
from sqlalchemy import text


def add_admin_user():
    """Добавляет тестового администратора в БД"""
    db = SessionLocal()

    try:
        # Проверяем, есть ли уже админ
        existing = db.query(User).filter(User.user_name == "admin").first()

        if existing:
            print(f"✅ Админ уже существует: {existing.user_name} (ID: {existing.user_id})")
            print(f"   Пароль: {existing.user_password_cash}")
            return

        # Создаем админа через CRUD
        admin = UserCRUD.create(
            db,
            user_name="admin",
            user_surname="Администраторов",
            user_role="admin",
            user_phone_number="+79991234567",
            user_password_cash="admin123"  # В реальном проекте нужно хешировать!
        )

        print(f"✅ Админ успешно создан:")
        print(f"   ID: {admin.user_id}")
        print(f"   Имя: {admin.user_name}")
        print(f"   Пароль: admin123")
        print(f"   Роль: {admin.user_role}")

        # Добавим еще пару тестовых пользователей
        test_users = [
            ("hr_specialist", "HR", "hr123"),
            ("manager", "Управляющий", "manager123"),
            ("trainer", "Тренер", "trainer123"),
        ]

        for username, surname, pwd in test_users:
            if not db.query(User).filter(User.user_name == username).first():
                UserCRUD.create(
                    db,
                    user_name=username,
                    user_surname=surname,
                    user_role="user",
                    user_phone_number="",
                    user_password_cash=pwd
                )
                print(f"✅ Создан тестовый пользователь: {username} / {pwd}")

        # Проверим, сколько всего пользователей
        count = db.query(User).count()
        print(f"\n📊 Всего пользователей в БД: {count}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def update_existing_admin_password():
    """Обновляет пароль существующего админа (если нужно)"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.user_name == "admin").first()
        if admin:
            admin.user_password_cash = "admin123"
            db.commit()
            print(f"✅ Пароль админа обновлен на: admin123")
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
    finally:
        db.close()


def list_all_users():
    """Показывает всех пользователей в БД"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("\n📋 Список пользователей:")
        print("-" * 50)
        for user in users:
            print(
                f"ID: {user.user_id} | Логин: {user.user_name} | Пароль: {user.user_password_cash} | Роль: {user.user_role}")
        print("-" * 50)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Утилита управления пользователями")
    print("=" * 50)

    # Добавляем админа
    add_admin_user()

    # Показываем всех пользователей
    list_all_users()

    # Если нужно обновить пароль:
    # update_existing_admin_password()