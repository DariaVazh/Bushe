# example_usage.py
from learning_platform_db import (
    SessionLocal,
    create_tables,
    UserCRUD,
    InteractionCRUD,
    AnalyticsQueries,
    ReviewQueries,
    KnowledgeItem  # Добавьте этот импорт!
)


def main():
    print("🚀 Создаем таблицы...")
    create_tables()

    db = SessionLocal()

    try:
        print("👤 Создаем пользователя...")
        user = UserCRUD.create(
            db,
            user_name="Тестовый пользователь",
            user_surname="ТестоваяФамилия",  # Добавь реальную фамилию
            user_phone_number="+71234567890",  # По желанию
            user_password_cash="секретный_пароль",  # По желанию
            user_role="student"  # По желанию
        )
        print(f"   ✅ Создан пользователь с ID: {user.user_id}, имя: {user.user_name}")

        # ✅ ДОБАВЛЯЕМ ТЕСТОВЫЕ ЭЛЕМЕНТЫ ЗНАНИЙ
        print("📚 Создаем тестовые элементы знаний...")
        for item_id in [1, 2, 3]:
            # Проверяем, есть ли уже такой элемент
            item = db.query(KnowledgeItem).filter(KnowledgeItem.item_id == item_id).first()
            if not item:
                item = KnowledgeItem(
                    item_id=item_id,
                    difficulty=0.5,  # средняя сложность
                    domain="math" if item_id % 2 else "physics"
                )
                db.add(item)
                print(f"   ✅ Создан элемент знаний с ID: {item_id}")
        db.commit()

        # Теперь добавляем взаимодействия
        print("📝 Добавляем тестовые взаимодействия...")
        interactions_data = [
            (1, 1, 5.2),  # item 1, успех, 5.2 сек
            (1, 1, 2.1),  # item 1, успех, 2.1 сек
            (2, 0, 8.4),  # item 2, неудача, 8.4 сек
            (1, 1, 1.8),  # item 1, успех, 1.8 сек
            (2, 1, 4.2),  # item 2, успех, 4.2 сек
        ]

        for item_id, outcome, response_time in interactions_data:
            interaction = InteractionCRUD.create(
                db,
                user_id=user.user_id,
                item_id=item_id,
                outcome=outcome,
                response_time=response_time
            )
            print(f"   + Взаимодействие #{interaction.history_step}: "
                  f"item={item_id} outcome={outcome}")
        # 3. Получаем статистику для ML
        print("\n📊 Данные для ML:")
        ml_data = AnalyticsQueries.get_ml_training_data(db, min_interactions=3)
        print(ml_data.head())

        # 4. Что повторять сегодня?
        print("\n📚 Элементы для повторения:")
        to_review = ReviewQueries.get_items_for_review(db, user.user_id)
        for item in to_review:
            print(f"  Item {item['item_id']}: приоритет {item['priority_score']:.2f}")

        # 5. Анализ кривой обучения
        print("\n📈 Кривая обучения:")
        learning_curve = AnalyticsQueries.get_user_learning_curve(db, user.user_id)
        print(learning_curve)


    except Exception as e:

        print(f"❌ Ошибка: {e}")

        import traceback

        traceback.print_exc()


    finally:

        db.close()

        print("\n✨ Готово!")


if __name__ == "__main__":
    main()