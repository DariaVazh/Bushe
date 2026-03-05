# hr_learning_dashboards/generate_realistic_data.py
import sys
import os
import random
import numpy as np
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import SessionLocal
from Bushe.learning_platform_db.models import User, KnowledgeItem, Interaction, Review
from Bushe.learning_platform_db.crud import UserCRUD, InteractionCRUD
from sqlalchemy import text


class RealisticDataGenerator:
    def __init__(self):
        self.db = SessionLocal()

        # Параметры
        self.num_users = 200
        self.num_items = 500
        self.days_back = 60

        # Реалистичное распределение типов пользователей
        self.user_types = {
            'отличник': {'weight': 15, 'base_success': 0.85, 'forgetting_rate': 0.3},
            'хорошист': {'weight': 25, 'base_success': 0.75, 'forgetting_rate': 0.4},
            'середняк': {'weight': 30, 'base_success': 0.65, 'forgetting_rate': 0.5},
            'слабый': {'weight': 20, 'base_success': 0.50, 'forgetting_rate': 0.6},
            'новенький': {'weight': 10, 'base_success': 0.60, 'forgetting_rate': 0.45}
        }

        # Категории знаний
        self.categories = [
            "Хлеб", "Кондитерка", "СанПиН", "Касса",
            "Охрана труда", "Напитки", "Фастфуд", "Сыры"
        ]

    def clean_all(self):
        """Очищает все таблицы, кроме админа"""
        print("🧹 Очистка данных...")
        self.db.execute(text("DELETE FROM reviews"))
        self.db.execute(text("DELETE FROM interactions"))
        self.db.execute(text("DELETE FROM knowledge_items"))
        self.db.execute(text("DELETE FROM users WHERE user_name != 'admin'"))
        self.db.commit()
        print("✅ Данные очищены")

    def create_knowledge_items(self):
        """Создаёт элементы знаний с разной сложностью"""
        print(f"📚 Создание {self.num_items} элементов знаний...")

        items = []
        for i in range(1, self.num_items + 1):
            category = random.choice(self.categories)
            # Сложность распределена нормально
            difficulty = min(0.95, max(0.1, random.gauss(0.5, 0.15)))

            item = KnowledgeItem(
                item_id=i,
                difficulty=round(difficulty, 2),
                domain=category
            )
            self.db.add(item)
            items.append(item)

        self.db.commit()
        print(f"✅ Создано {len(items)} элементов")
        return items

    def create_users(self):
        """Создаёт пользователей с реалистичными именами"""
        print(f"👥 Создание {self.num_users} пользователей...")

        names = ["иван", "петр", "сергей", "анна", "елена", "дмитрий",
                 "ольга", "михаил", "татьяна", "алексей", "наталья",
                 "андрей", "юлия", "николай", "екатерина", "владимир"]

        roles = ["пекарь", "бариста", "кассир", "повар", "продавец"]

        users = []
        for i in range(self.num_users):
            name = random.choice(names)
            role = random.choice(roles)

            # Определяем тип пользователя по весам
            user_type = random.choices(
                list(self.user_types.keys()),
                weights=[t['weight'] for t in self.user_types.values()]
            )[0]

            user = UserCRUD.create(
                self.db,
                user_name=f"{name}{i + 1}",
                user_surname=random.choice(["Иванов", "Петров", "Сидоров"]),
                user_role=f"{role}_{user_type}",
                user_phone_number=f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}",
                user_password_cash=f"pass{i + 123}"
            )
            users.append((user, user_type))

        self.db.commit()
        print(f"✅ Создано {len(users)} пользователей")
        return users

    def forgetting_curve(self, days, base_retention=0.8, forgetting_rate=0.5):
        """Кривая забывания Эббингауза"""
        return base_retention * np.exp(-forgetting_rate * days / 10)

    def generate_interactions(self, users_items):
        """Генерирует взаимодействия с реалистичными паттернами"""
        users, items = users_items
        print("📝 Генерация взаимодействий...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)

        total_interactions = 0

        for user, user_type in users:
            user_config = self.user_types[user_type]
            base_success = user_config['base_success']
            forgetting_rate = user_config['forgetting_rate']

            # Определяем предпочтительное время для пользователя
            preferred_hour = random.choice([9, 10, 11, 14, 15, 16, 19, 20])

            user_interactions = 0
            current_date = start_date

            # История повторений для каждого факта
            item_history = {}

            while current_date <= end_date:
                # Количество взаимодействий в день зависит от типа
                if user_type == 'отличник':
                    daily_target = random.randint(8, 15)
                elif user_type == 'хорошист':
                    daily_target = random.randint(5, 10)
                elif user_type == 'середняк':
                    daily_target = random.randint(3, 7)
                else:
                    daily_target = random.randint(1, 4)

                # Выходные меньше учатся
                if current_date.weekday() >= 5:  # суббота, воскресенье
                    daily_target = int(daily_target * 0.5)

                interactions_today = 0
                for _ in range(daily_target):
                    if total_interactions > 200000:  # лимит
                        break

                    item = random.choice(items)

                    # Проверяем, когда в последний раз видел этот факт
                    last_seen = item_history.get(item.item_id)

                    if last_seen:
                        days_ago = (current_date - last_seen).days
                        # Вероятность вспомнить зависит от кривой забывания
                        recall_prob = self.forgetting_curve(
                            days_ago,
                            base_retention=base_success,
                            forgetting_rate=forgetting_rate
                        )
                        # Добавляем случайность
                        success_prob = min(0.95, max(0.1, recall_prob + random.gauss(0, 0.1)))
                    else:
                        # Первый раз - высокая вероятность правильно
                        success_prob = base_success + random.gauss(0, 0.1)

                    outcome = 1 if random.random() < success_prob else 0

                    # Время ответа
                    if outcome == 1:
                        response_time = random.gauss(2.5, 1.0)
                    else:
                        response_time = random.gauss(6.0, 2.0)

                    response_time = max(0.5, min(15, response_time))

                    try:
                        # Создаём взаимодействие с нужным временем
                        interaction = InteractionCRUD.create(
                            self.db,
                            user_id=user.user_id,
                            item_id=item.item_id,
                            outcome=outcome,
                            response_time=round(response_time, 2)
                        )

                        # Меняем timestamp
                        hour = preferred_hour + random.randint(-3, 3)
                        hour = max(8, min(22, hour))

                        interaction.timestamp = current_date.replace(
                            hour=hour,
                            minute=random.randint(0, 59)
                        )
                        self.db.add(interaction)

                        # Обновляем историю
                        item_history[item.item_id] = interaction.timestamp

                        interactions_today += 1
                        total_interactions += 1

                    except Exception as e:
                        print(f"Ошибка: {e}")

                    if total_interactions % 10000 == 0:
                        print(f"   ... создано {total_interactions} взаимодействий")
                        self.db.commit()

                user_interactions += interactions_today
                current_date += timedelta(days=1)

            print(f"   {user.user_name} ({user_type}): {user_interactions} взаим.")

        self.db.commit()
        print(f"✅ Всего создано {total_interactions} взаимодействий")

    def run(self):
        """Запускает генерацию"""
        print("=" * 60)
        print("🚀 ГЕНЕРАЦИЯ РЕАЛИСТИЧНЫХ ДАННЫХ")
        print("=" * 60)

        self.clean_all()
        items = self.create_knowledge_items()
        users = self.create_users()
        self.generate_interactions((users, items))

        print("\n✅ Генерация завершена!")
        print(f"   Пользователей: {len(users)}")
        print(f"   Элементов: {len(items)}")

        self.db.close()


if __name__ == "__main__":
    generator = RealisticDataGenerator()
    generator.run()