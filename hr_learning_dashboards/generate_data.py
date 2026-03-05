# generate_data.py
import sys
import os
import random
from datetime import datetime, timedelta
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import SessionLocal
from Bushe.learning_platform_db.models import User, KnowledgeItem, Interaction, Review
from Bushe.learning_platform_db.crud import UserCRUD, InteractionCRUD
from Bushe.learning_platform_db.queries import  AnalyticsQueries
from sqlalchemy import text


class MLDataGenerator:
    def __init__(self):
        self.db = SessionLocal()

        # Параметры генерации
        self.num_users = 200
        self.num_items = 500
        self.num_interactions = 100000  # ← 100 тысяч

        self.categories = [
            "Хлеб", "Кондитерка", "СанПиН",
            "Касса", "Охрана труда", "Напитки",
            "Фастфуд", "Сыры", "Стандарты"
        ]

    def clean_all(self):
        """Очищает все таблицы"""
        print("🧹 Очистка таблиц...")
        self.db.execute(text("DELETE FROM reviews"))
        self.db.execute(text("DELETE FROM interactions"))
        self.db.execute(text("DELETE FROM knowledge_items"))
        self.db.execute(text("DELETE FROM users WHERE user_name != 'admin'"))
        self.db.commit()
        print("✅ Таблицы очищены")

    def create_admin(self):
        """Проверяет, что админ есть"""
        admin = self.db.query(User).filter(User.user_name == "admin").first()
        if not admin:
            admin = UserCRUD.create(
                self.db,
                user_name="admin",
                user_surname="Администратор",
                user_role="admin",
                user_phone_number="+79990000000",
                user_password_cash="admin123"
            )
            print("✅ Админ создан")
        else:
            print("✅ Админ уже существует")
        return admin

    def create_knowledge_items(self):
        """Создает элементы знаний с разной сложностью"""
        print(f"📚 Создание {self.num_items} элементов знаний...")

        items = []
        for i in range(1, self.num_items + 1):
            category = random.choice(self.categories)
            difficulty = round(random.uniform(0.1, 0.95), 2)

            item = KnowledgeItem(
                item_id=i,
                difficulty=difficulty,
                domain=category
            )
            self.db.add(item)
            items.append(item)

        self.db.commit()
        print(f"✅ Создано {len(items)} элементов")
        return items

    def create_users(self):
        """Создает пользователей с разными паттернами обучения"""
        print(f"👥 Создание {self.num_users} пользователей...")

        names = ["Иван", "Петр", "Сергей", "Анна", "Елена", "Дмитрий",
                 "Ольга", "Михаил", "Татьяна", "Алексей", "Наталья"]
        surnames = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов",
                    "Попова", "Васильева", "Соколова"]
        roles = ["пекарь", "бариста", "кассир", "повар", "продавец"]

        users = []
        for i in range(self.num_users):
            name = random.choice(names)
            surname = random.choice(surnames)
            role = random.choice(roles)

            # У каждого пользователя свой "профиль обучения"
            user_type = random.choices(
                ["отличник", "хорошист", "середняк", "отстающий", "непостоянный"],
                weights=[15, 30, 30, 15, 10],
                k=1
            )[0]

            user = UserCRUD.create(
                self.db,
                user_name=f"{name.lower()}{i + 10}",
                user_surname=surname,
                user_role=role,
                user_phone_number=f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}",
                user_password_cash=f"pass{i + 123}"
            )

            # Сохраняем тип пользователя (временное поле, потом удалим)
            user.user_role = f"{role}_{user_type}"  # хак, чтобы не создавать новое поле
            self.db.add(user)
            users.append(user)

        self.db.commit()
        print(f"✅ Создано {len(users)} пользователей")
        return users

    def generate_interactions(self, users, items):
        """
        Генерирует взаимодействия с реалистичными паттернами
        """
        print(f"📝 Генерация {self.num_interactions} взаимодействий...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)

        interactions_created = 0
        batch_size = 1000

        for user in users:
            # Определяем тип пользователя по роли (наш хак)
            if "отличник" in user.user_role:
                base_success = random.uniform(0.85, 0.98)
                daily_intensity = random.uniform(8, 15)
                response_base = random.uniform(1.5, 3.0)
            elif "хорошист" in user.user_role:
                base_success = random.uniform(0.7, 0.85)
                daily_intensity = random.uniform(5, 10)
                response_base = random.uniform(2.5, 4.5)
            elif "середняк" in user.user_role:
                base_success = random.uniform(0.5, 0.7)
                daily_intensity = random.uniform(3, 7)
                response_base = random.uniform(4.0, 6.0)
            elif "отстающий" in user.user_role:
                base_success = random.uniform(0.3, 0.5)
                daily_intensity = random.uniform(1, 4)
                response_base = random.uniform(6.0, 9.0)
            else:  # непостоянный
                base_success = random.uniform(0.4, 0.8)
                daily_intensity = random.uniform(2, 8)
                response_base = random.uniform(3.0, 7.0)
                # Непостоянные имеют "провалы" в активности
                active_days = random.sample(range(60), random.randint(20, 40))
            current_date = start_date
            user_interactions = 0

            while current_date <= end_date and interactions_created < self.num_interactions:
                # Для непостоянных - активность только в выбранные дни
                if "непостоянный" in user.user_role:
                    day_num = (current_date - start_date).days
                    if day_num not in active_days:
                        current_date += timedelta(days=1)
                        continue

                # Количество взаимодействий в день (распределение Пуассона)
                daily_count = max(0, int(np.random.poisson(daily_intensity)))

                for _ in range(min(daily_count, 20)):  # не больше 20 в день
                    item = random.choice(items)

                    # Добавляем зависимости:
                    # - Сложность элемента влияет на успех
                    # - Утром успешность выше
                    hour = random.randint(8, 23)
                    time_factor = 1.0 if hour < 12 else 0.95 if hour < 18 else 0.9

                    # Сложность элемента
                    difficulty_factor = 1.0 - (item.difficulty * 0.3)

                    # Итоговая вероятность успеха
                    success_prob = base_success * time_factor * difficulty_factor
                    success_prob = min(0.99, max(0.1, success_prob))

                    outcome = 1 if random.random() < success_prob else 0

                    # Время ответа зависит от:
                    # - правильности (правильные быстрее)
                    # - сложности (сложные медленнее)
                    if outcome == 1:
                        response_time = response_base * random.uniform(0.6, 1.2) * (1 + item.difficulty * 0.3)
                    else:
                        response_time = response_base * random.uniform(1.3, 2.5) * (1 + item.difficulty * 0.5)

                    try:
                        InteractionCRUD.create(
                            self.db,
                            user_id=user.user_id,
                            item_id=item.item_id,
                            outcome=outcome,
                            response_time=round(response_time, 2)
                        )

                        user_interactions += 1
                        interactions_created += 1

                        if interactions_created % batch_size == 0:
                            print(f"   ... создано {interactions_created} взаимодействий")
                            self.db.commit()

                    except Exception as e:
                        print(f"Ошибка: {e}")

                    if interactions_created >= self.num_interactions:
                        break

                current_date += timedelta(days=1)
                if interactions_created >= self.num_interactions:
                    break

            print(f"   Пользователь {user.user_name}: {user_interactions} взаимодействий")

        self.db.commit()
        print(f"✅ Всего создано {interactions_created} взаимодействий")

    def run(self):
        """Запускает генерацию"""
        print("=" * 60)
        print("🚀 ГЕНЕРАЦИЯ ДАННЫХ ДЛЯ ML")
        print("=" * 60)
        print(f"Параметры:")
        print(f"  - Пользователей: {self.num_users}")
        print(f"  - Элементов знаний: {self.num_items}")
        print(f"  - Взаимодействий: {self.num_interactions}")
        print("=" * 60)

        self.clean_all()
        admin = self.create_admin()
        items = self.create_knowledge_items()
        users = self.create_users()
        self.generate_interactions(users, items)

        # Проверка
        df = AnalyticsQueries.get_ml_training_data(self.db)
        print("\n📊 Итоговая статистика:")
        print(f"  - Записей для ML: {len(df)}")
        print(f"  - Пользователей в данных: {df['user_id'].nunique()}")
        print(f"  - Элементов знаний: {df['item_id'].nunique()}")
        print("=" * 60)

        self.db.close()


if __name__ == "__main__":
    generator = MLDataGenerator()
    generator.run()