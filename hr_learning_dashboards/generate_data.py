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
from sqlalchemy import text


class DataGenerator:
    def __init__(self):
        self.db = SessionLocal()

        # Категории знаний (для разнообразия)
        self.categories = [
            "Хлеб", "Кондитерка", "СанПиН",
            "Касса", "Охрана труда", "Напитки",
            "Фастфуд", "Сыры", "Стандарты"
        ]

        # Имена и фамилии для генерации
        self.first_names = [
            "Иван", "Петр", "Сергей", "Анна", "Елена", "Дмитрий",
            "Ольга", "Михаил", "Татьяна", "Алексей", "Наталья",
            "Андрей", "Юлия", "Николай", "Екатерина", "Владимир"
        ]

        self.last_names = [
            "Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов",
            "Попова", "Васильева", "Соколова", "Михайлова", "Новикова",
            "Федоров", "Морозов", "Волков", "Алексеев", "Лебедев"
        ]

        # Роли
        self.roles = ["пекарь", "бариста", "кассир", "повар", "администратор", "продавец"]

    def clean_all(self):
        """Очищает все таблицы"""
        print("🧹 Очистка таблиц...")
        self.db.execute(text("DELETE FROM reviews"))
        self.db.execute(text("DELETE FROM interactions"))
        self.db.execute(text("DELETE FROM knowledge_items"))
        self.db.execute(text("DELETE FROM users"))
        self.db.commit()
        print("✅ Таблицы очищены")

    def create_admin(self):
        """Создает админа с нулевыми показателями"""
        print("👤 Создание администратора...")
        admin = UserCRUD.create(
            self.db,
            user_name="admin",
            user_surname="Администратор",
            user_role="admin",
            user_phone_number="+79990000000",
            user_password_cash="admin123"
        )
        print(f"✅ Админ создан (ID: {admin.user_id})")
        return admin

    def create_knowledge_items(self, count=500):
        """Создает элементы знаний с разной сложностью"""
        print(f"📚 Создание {count} элементов знаний...")

        items = []
        for i in range(1, count + 1):
            category = random.choice(self.categories)

            # Сложность от 0.1 до 0.9
            difficulty = round(random.uniform(0.2, 0.9), 2)

            item = KnowledgeItem(
                item_id=i,
                difficulty=difficulty,
                domain=category
            )
            self.db.add(item)
            items.append(item)

        self.db.commit()
        print(f"✅ Создано {count} элементов знаний")
        return items

    def create_users(self, count=200):
        """Создает обычных пользователей с разной успешностью"""
        print(f"👥 Создание {count} пользователей...")

        users = []
        for i in range(count):
            name = random.choice(self.first_names)
            surname = random.choice(self.last_names)
            role = random.choice(self.roles)

            # Генерируем телефон
            phone = f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}"

            # Пароль простой для тестов
            password = f"user{i + 123}"

            user = UserCRUD.create(
                self.db,
                user_name=name.lower() + str(random.randint(1, 99)),
                user_surname=surname,
                user_role=role,
                user_phone_number=phone,
                user_password_cash=password
            )
            users.append(user)

            if (i + 1) % 5 == 0:
                print(f"   ... создано {i + 1} пользователей")

        print(f"✅ Создано {count} пользователей")
        return users

    def generate_interactions(self, users, items, days_back=60):
        """
        Генерирует взаимодействия с разной успешностью для каждого пользователя

        Категории успешности:
        - Отличники: успешность 85-100%
        - Хорошисты: успешность 70-85%
        - Середняки: успешность 50-70%
        - Отстающие: успешность 30-50%
        - Новенькие: мало взаимодействий
        """
        print(f"📝 Генерация взаимодействий за последние {days_back} дней...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        total_interactions = 0

        for user in users:
            # Пропускаем админа (у него 0 взаимодействий)
            if user.user_name == "admin":
                continue

            # Определяем профиль успешности пользователя
            user_type = random.choices(
                ["отличник", "хорошист", "середняк", "отстающий", "новенький"],
                weights=[15, 25, 30, 20, 10],  # распределение
                k=1
            )[0]

            # Настраиваем параметры в зависимости от типа
            if user_type == "отличник":
                base_success = random.uniform(0.85, 1.0)
                interactions_per_day = random.randint(8, 15)
                response_time_base = random.uniform(1.5, 3.0)
                print(f"   🏆 {user.user_name} - отличник (усп-ть: {base_success:.0%})")

            elif user_type == "хорошист":
                base_success = random.uniform(0.7, 0.85)
                interactions_per_day = random.randint(5, 10)
                response_time_base = random.uniform(2.5, 4.5)
                print(f"   👍 {user.user_name} - хорошист (усп-ть: {base_success:.0%})")

            elif user_type == "середняк":
                base_success = random.uniform(0.5, 0.7)
                interactions_per_day = random.randint(3, 7)
                response_time_base = random.uniform(4.0, 6.0)
                print(f"   👤 {user.user_name} - середняк (усп-ть: {base_success:.0%})")

            elif user_type == "отстающий":
                base_success = random.uniform(0.3, 0.5)
                interactions_per_day = random.randint(1, 4)
                response_time_base = random.uniform(6.0, 10.0)
                print(f"   ⚠️ {user.user_name} - отстающий (усп-ть: {base_success:.0%})")

            else:  # новенький
                base_success = random.uniform(0.4, 0.7)
                interactions_per_day = random.randint(1, 3)
                response_time_base = random.uniform(5.0, 8.0)
                # Новенькие активны только последние N дней
                user_start_date = end_date - timedelta(days=random.randint(5, 15))
                print(f"   🆕 {user.user_name} - новенький (с {user_start_date.strftime('%d.%m')})")

            # Генерируем взаимодействия по дням
            current_date = start_date
            user_interactions = 0

            while current_date <= end_date:
                # Для новеньких начинаем позже
                if user_type == "новенький" and current_date < user_start_date:
                    current_date += timedelta(days=1)
                    continue

                # Количество взаимодействий в этот день (с вариацией)
                daily_count = max(0, int(np.random.poisson(interactions_per_day)))

                for _ in range(daily_count):
                    # Выбираем случайный элемент знаний
                    item = random.choice(items)

                    # Успешность с небольшими отклонениями
                    success_variation = random.uniform(-0.15, 0.15)
                    success_prob = min(1.0, max(0.0, base_success + success_variation))
                    outcome = 1 if random.random() < success_prob else 0

                    # Время ответа
                    if outcome == 1:
                        # Правильные ответы быстрее
                        response_time = response_time_base * random.uniform(0.7, 1.3)
                    else:
                        # Неправильные медленнее
                        response_time = response_time_base * random.uniform(1.3, 2.5)

                    # Создаем взаимодействие с нужной датой
                    try:
                        interaction = InteractionCRUD.create(
                            self.db,
                            user_id=user.user_id,
                            item_id=item.item_id,
                            outcome=outcome,
                            response_time=round(response_time, 2)
                        )

                        # Хак: меняем timestamp на нужную дату
                        interaction.timestamp = current_date + timedelta(
                            hours=random.randint(8, 22),
                            minutes=random.randint(0, 59)
                        )
                        self.db.add(interaction)
                        user_interactions += 1

                    except Exception as e:
                        print(f"      Ошибка создания: {e}")

                current_date += timedelta(days=1)

            total_interactions += user_interactions
            print(f"      Итого: {user_interactions} взаимодействий")

        self.db.commit()
        print(f"✅ Всего создано {total_interactions} взаимодействий")

    def update_reviews(self):
        """Обновляет агрегированные данные в reviews"""
        print("🔄 Обновление агрегированных данных...")

        # Reviews обновляются автоматически через trigger в InteractionCRUD
        # Просто убедимся, что все данные посчитаны
        self.db.execute(text("""
            INSERT INTO reviews (user_id, item_id, review_count, last_review, avg_response_time, success_rate, history_json)
            SELECT 
                user_id,
                item_id,
                COUNT(*) as review_count,
                MAX(timestamp) as last_review,
                AVG(response_time) as avg_response_time,
                AVG(outcome) as success_rate,
                '[]'::json as history_json
            FROM interactions
            GROUP BY user_id, item_id
            ON CONFLICT (user_id, item_id) DO UPDATE
            SET 
                review_count = EXCLUDED.review_count,
                last_review = EXCLUDED.last_review,
                avg_response_time = EXCLUDED.avg_response_time,
                success_rate = EXCLUDED.success_rate
        """))

        self.db.commit()
        print("✅ Агрегированные данные обновлены")

    def run(self):
        """Запускает полную генерацию данных"""
        print("=" * 50)
        print("🚀 ГЕНЕРАЦИЯ СИНТЕТИЧЕСКИХ ДАННЫХ")
        print("=" * 50)

        # 1. Очистка
        self.clean_all()

        # 2. Создание админа
        admin = self.create_admin()

        # 3. Создание элементов знаний
        items = self.create_knowledge_items(50)

        # 4. Создание обычных пользователей
        users = self.create_users(25)  # 25 обычных + админ = 26 всего

        # 5. Генерация взаимодействий
        self.generate_interactions(users + [admin], items, days_back=45)

        # 6. Обновление агрегированных данных
        self.update_reviews()

        print("=" * 50)
        print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА")
        print("=" * 50)
        print(f"👤 Админ: admin / admin123")
        print(f"👥 Обычных пользователей: {len(users)}")
        print(f"📚 Элементов знаний: {len(items)}")
        print("\nПримеры логинов/паролей:")
        for i, user in enumerate(users[:5]):
            print(f"   {user.user_name} / user{i + 123}")


if __name__ == "__main__":
    generator = DataGenerator()
    generator.run()