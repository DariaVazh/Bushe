# clean_db.py
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import SessionLocal, engine, Base
from Bushe.learning_platform_db.models import User, KnowledgeItem, Interaction, Review
from sqlalchemy import text


def clean_database():
    """Полностью очищает все таблицы и сбрасывает последовательности"""
    print("🧹 Очистка базы данных...")

    db = SessionLocal()
    try:
        # Удаляем все данные в правильном порядке (из-за внешних ключей)
        db.execute(text("DELETE FROM reviews"))
        db.execute(text("DELETE FROM interactions"))
        db.execute(text("DELETE FROM knowledge_items"))
        db.execute(text("DELETE FROM users"))

        # Сбрасываем последовательности ID
        db.execute(text("ALTER SEQUENCE users_user_id_seq RESTART WITH 1"))
        db.execute(text("ALTER SEQUENCE knowledge_items_item_id_seq RESTART WITH 1"))
        db.execute(text("ALTER SEQUENCE interactions_interaction_id_seq RESTART WITH 1"))

        db.commit()
        print("✅ База данных очищена")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    clean_database()