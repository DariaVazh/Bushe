# hr_learning_dashboards/ml/predictor.py
import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к БД
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.models import User, KnowledgeItem, Interaction, Review
from sqlalchemy import func, text
import joblib


class RecallPredictor:
    def __init__(self, model_path=None):
        """Инициализация предиктора"""
        self.model = None
        self.feature_names = None

        # Если передан путь к сохранённой модели - загружаем
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def load_model(self, model_path):
        """Загружает обученную модель из файла"""
        import joblib
        self.model = joblib.load(model_path)
        print(f"✅ Модель загружена из {model_path}")

    def save_model(self, model_path='ml/recall_model.pkl'):
        """Сохраняет модель в файл"""
        import joblib
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        print(f"✅ Модель сохранена в {model_path}")

    def prepare_user_features(self, db, user_id, item_id):
        """
        Подготавливает фичи для конкретного пользователя и факта
        """
        # Получаем статистику пользователя
        user_stats = db.query(
            func.avg(Interaction.outcome).label('user_avg_success')
        ).filter(Interaction.user_id == user_id).first()

        # Получаем статистику факта
        item_stats = db.query(
            func.avg(Interaction.outcome).label('item_avg_success')
        ).filter(Interaction.item_id == item_id).first()

        # Получаем последнее взаимодействие с этим фактом
        last_interaction = db.query(Interaction).filter(
            Interaction.user_id == user_id,
            Interaction.item_id == item_id
        ).order_by(Interaction.timestamp.desc()).first()

        # Получаем ревью (агрегированную историю)
        review = db.query(Review).filter(
            Review.user_id == user_id,
            Review.item_id == item_id
        ).first()

        # Базовые фичи
        now = datetime.now()

        # Если факт вообще не изучался
        if not last_interaction:
            return {
                'history_step': 0,
                'delta_days': 0,
                'log_delta': 0,
                'prev_response_time': 0,
                'prev_delta': 0,
                'user_avg_success': user_stats.user_avg_success or 0.5,
                'item_avg_success': item_stats.item_avg_success or 0.5,
                'hour_sin': np.sin(2 * np.pi * now.hour / 24),
                'hour_cos': np.cos(2 * np.pi * now.hour / 24),
                'is_morning': 1 if 6 <= now.hour <= 11 else 0,
                'is_afternoon': 1 if 12 <= now.hour <= 17 else 0,
                'is_evening': 1 if 18 <= now.hour <= 23 else 0,
                'is_night': 1 if 0 <= now.hour <= 5 else 0
            }

        # Если факт уже изучался
        delta_days = (now - last_interaction.timestamp).total_seconds() / 86400

        # Предыдущее время ответа (из последнего взаимодействия)
        prev_response_time = last_interaction.response_time

        # Предыдущий интервал
        prev_delta = last_interaction.delta_days or 7

        features = {
            'history_step': review.review_count if review else 1,
            'delta_days': delta_days,
            'log_delta': np.log1p(delta_days),
            'prev_response_time': prev_response_time,
            'prev_delta': prev_delta,
            'user_avg_success': user_stats.user_avg_success or 0.5,
            'item_avg_success': item_stats.item_avg_success or 0.5,
            'hour_sin': np.sin(2 * np.pi * now.hour / 24),
            'hour_cos': np.cos(2 * np.pi * now.hour / 24),
            'is_morning': 1 if 6 <= now.hour <= 11 else 0,
            'is_afternoon': 1 if 12 <= now.hour <= 17 else 0,
            'is_evening': 1 if 18 <= now.hour <= 23 else 0,
            'is_night': 1 if 0 <= now.hour <= 5 else 0
        }

        return features

    def predict_recall(self, db, user_id, item_id):
        """
        Предсказывает вероятность recall для конкретного пользователя и факта
        """
        if self.model is None:
            raise ValueError("Модель не загружена! Сначала вызови load_model()")

        # Получаем фичи
        features = self.prepare_user_features(db, user_id, item_id)

        # Преобразуем в массив в правильном порядке
        # ВАЖНО: порядок должен совпадать с обучением!
        feature_order = [
            'history_step',
            'delta_days',
            'log_delta',
            'prev_response_time',
            'prev_delta',
            'user_avg_success',
            'item_avg_success',
            'hour_sin',
            'hour_cos',
            'is_morning',
            'is_afternoon',
            'is_evening',
            'is_night'
        ]

        X = np.array([[features[f] for f in feature_order]])

        # Предсказываем вероятность
        probability = self.model.predict_proba(X)[0, 1]

        return probability

    def predict_for_user(self, db, user_id, limit=20):
        """
        Предсказывает recall для всех фактов пользователя
        Возвращает список фактов с вероятностью вспоминания
        """
        # Получаем все факты, которые пользователь когда-либо изучал
        reviewed_items = db.query(Review.item_id).filter(
            Review.user_id == user_id
        ).all()

        results = []
        for (item_id,) in reviewed_items:
            prob = self.predict_recall(db, user_id, item_id)
            results.append({
                'item_id': item_id,
                'recall_probability': prob,
                'needs_review': prob < 0.7  # порог для повторения
            })

        # Сортируем по вероятности (самые забытые - первые)
        results.sort(key=lambda x: x['recall_probability'])

        return results[:limit]

    def days_until_review(self, db, user_id, item_id, threshold=0.7, max_days=30):
        """
        Определяет, через сколько дней вероятность упадёт ниже порога
        """
        # Текущая вероятность
        current_prob = self.predict_recall(db, user_id, item_id)

        if current_prob < threshold:
            return 0  # уже нужно повторять

        # Получаем фичи для текущего состояния
        features = self.prepare_user_features(db, user_id, item_id)

        # Симулируем увеличение интервала
        for days in range(1, max_days + 1):
            test_features = features.copy()
            test_features['delta_days'] = days
            test_features['log_delta'] = np.log1p(days)

            # Формируем массив
            feature_order = [
                'history_step', 'delta_days', 'log_delta',
                'prev_response_time', 'prev_delta',
                'user_avg_success', 'item_avg_success',
                'hour_sin', 'hour_cos',
                'is_morning', 'is_afternoon', 'is_evening', 'is_night'
            ]

            X_test = np.array([[test_features[f] for f in feature_order]])
            prob = self.model.predict_proba(X_test)[0, 1]

            if prob < threshold:
                return days

        return max_days  # если держится дольше месяца

    def get_review_schedule(self, db, user_id):
        """
        Возвращает расписание повторений для пользователя
        """
        results = self.predict_for_user(db, user_id, limit=50)

        schedule = []
        for item in results:
            if item['recall_probability'] < 0.7:
                days = 0  # повторить сегодня
            else:
                days = self.days_until_review(db, user_id, item['item_id'])

            schedule.append({
                'item_id': item['item_id'],
                'current_probability': round(item['recall_probability'], 3),
                'days_until_review': days,
                'review_date': datetime.now() + timedelta(days=days)
            })

        return schedule

    def get_user_mastery(self, db, user_id, threshold=0.7):
        """
        Рассчитывает общее усвоение материала для конкретного сотрудника
        threshold - порог усвоения (можно менять)
        """
        reviews = db.query(Review).filter(Review.user_id == user_id).all()

        if not reviews:
            return {
                'total_items': 0,
                'mastered_items': 0,
                'mastery_percentage': 0,
                'average_probability': 0,
                'distribution': {},
                'status': 'Нет данных'
            }

        # Получаем все вероятности
        probabilities = []
        for review in reviews:
            prob = self.predict_recall(db, user_id, review.item_id)
            probabilities.append(prob)

        # Считаем статистику
        probabilities = np.array(probabilities)

        # Распределение по зонам
        low = sum(p < 0.3 for p in probabilities)  # критично (<30%)
        medium_low = sum(0.3 <= p < 0.5 for p in probabilities)  # слабо (30-50%)
        medium = sum(0.5 <= p < 0.7 for p in probabilities)  # средне (50-70%)
        high = sum(p >= 0.7 for p in probabilities)  # усвоено (>=70%)

        mastery_pct = (high / len(reviews)) * 100

        # Определяем статус
        if mastery_pct >= 70:
            status = "🔥 Отлично"
        elif mastery_pct >= 50:
            status = "👍 Хорошо"
        elif mastery_pct >= 30:
            status = "👌 Средне"
        elif mastery_pct >= 10:
            status = "⚠️ Слабо"
        else:
            status = "🔴 Критично"

        return {
            'total_items': len(reviews),
            'mastered_items': high,
            'mastery_percentage': round(mastery_pct, 1),
            'average_probability': round(np.mean(probabilities), 3),
            'median_probability': round(np.median(probabilities), 3),
            'distribution': {
                '🔴 Критично (<30%)': low,
                '🟠 Слабо (30-50%)': medium_low,
                '🟡 Средне (50-70%)': medium,
                '🟢 Усвоено (>70%)': high
            },
            'status': status
        }

    def get_company_mastery(self, db):
        """
        Рассчитывает общее усвоение по всей компании
        """
        # Получаем всех пользователей (кроме админа)
        users = db.query(User).filter(User.user_name != 'admin').all()

        all_masteries = []
        total_items = 0
        total_mastered = 0

        for user in users:
            mastery = self.get_user_mastery(db, user.user_id)
            all_masteries.append(mastery['mastery_percentage'])
            total_items += mastery['total_items']
            total_mastered += mastery['mastered_items']

        # Избегаем деления на ноль
        company_mastery = (total_mastered / total_items * 100) if total_items > 0 else 0

        # Распределение сотрудников по уровням
        distribution = {
            '🔥 Отлично (>80%)': sum(1 for m in all_masteries if m >= 80),
            '👍 Хорошо (60-80%)': sum(1 for m in all_masteries if 60 <= m < 80),
            '👌 Средне (40-60%)': sum(1 for m in all_masteries if 40 <= m < 60),
            '⚠️ Слабо (20-40%)': sum(1 for m in all_masteries if 20 <= m < 40),
            '🔴 Критично (<20%)': sum(1 for m in all_masteries if m < 20)
        }

        # Топ-5 сотрудников
        users_with_mastery = [(user.user_name, mastery['mastery_percentage'])
                              for user, mastery in zip(users, [self.get_user_mastery(db, u.user_id) for u in users])]
        users_with_mastery.sort(key=lambda x: x[1], reverse=True)

        top_5 = [{'user': u[0], 'mastery': u[1]} for u in users_with_mastery[:5]]
        bottom_5 = [{'user': u[0], 'mastery': u[1]} for u in users_with_mastery[-5:]]

        return {
            'total_employees': len(users),
            'total_items_studied': total_items,
            'total_items_mastered': total_mastered,
            'company_mastery': round(company_mastery, 1),
            'average_employee_mastery': round(np.mean(all_masteries), 1) if all_masteries else 0,
            'distribution': distribution,
            'top_5': top_5,
            'bottom_5': bottom_5
        }


def interactive_mode(predictor, db):
    """Интерактивный режим для анализа пользователей"""

    while True:
        print("\n" + "=" * 70)
        print("🔍 ИНТЕРАКТИВНЫЙ АНАЛИЗ")
        print("=" * 70)
        print("1. Показать всех пользователей")
        print("2. Анализ конкретного пользователя")
        print("3. Топ-10 лучших")
        print("4. Топ-10 худших")
        print("5. Статистика по компании")
        print("0. Выход")

        choice = input("\nВыберите опцию: ").strip()

        if choice == '0':
            break

        elif choice == '1':
            users = db.query(User).filter(User.user_name != 'admin').all()
            print("\n📋 СПИСОК ПОЛЬЗОВАТЕЛЕЙ:")
            print("-" * 50)
            for i, u in enumerate(users, 1):
                print(f"{i:2}. {u.user_name:15} (роль: {u.user_role})")

        elif choice == '2':
            name = input("Введите имя пользователя: ").strip()
            user = db.query(User).filter(
                User.user_name == name,
                User.user_name != 'admin'
            ).first()

            if user:
                analyze_single_user(predictor, db, user)
            else:
                print("❌ Пользователь не найден!")

        elif choice == '3':
            users = db.query(User).filter(User.user_name != 'admin').all()
            results = []
            for u in users:
                mastery = predictor.get_user_mastery(db, u.user_id)
                results.append((u.user_name, mastery['mastery_percentage']))

            results.sort(key=lambda x: x[1], reverse=True)

            print("\n🔥 ТОП-10 ЛУЧШИХ:")
            print("-" * 50)
            for i, (name, mastery) in enumerate(results[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
                print(f"{medal} {i:2}. {name:15} {mastery:6.1f}%")

        elif choice == '4':
            users = db.query(User).filter(User.user_name != 'admin').all()
            results = []
            for u in users:
                mastery = predictor.get_user_mastery(db, u.user_id)
                results.append((u.user_name, mastery['mastery_percentage']))

            results.sort(key=lambda x: x[1])

            print("\n⚠️ ТОП-10 ХУДШИХ (нуждаются в помощи):")
            print("-" * 50)
            for i, (name, mastery) in enumerate(results[:10], 1):
                print(f"  {i:2}. {name:15} {mastery:6.1f}% 🔴")

        elif choice == '5':
            company = predictor.get_company_mastery(db)
            print("\n🏢 СТАТИСТИКА КОМПАНИИ:")
            print("-" * 50)
            print(f"👥 Всего сотрудников: {company['total_employees']}")
            print(f"📊 Общее усвоение: {company['company_mastery']}%")
            print(f"📈 Среднее по сотрудникам: {company['average_employee_mastery']}%")
            print(f"\n📊 Распределение:")
            for level, count in company['distribution'].items():
                if count > 0:
                    print(f"  {level}: {count} чел.")


def analyze_single_user(predictor, db, user):
    """Анализ одного пользователя (весь твой существующий код)"""
    print(f"\n{'=' * 70}")
    print(f"👤 АНАЛИЗ ПОЛЬЗОВАТЕЛЯ: {user.user_name.upper()}")
    print('=' * 70)

    # Предсказания
    predictions = predictor.predict_for_user(db, user.user_id, limit=10)

    print("\n📊 ТОП-10 ФАКТОВ, КОТОРЫЕ СКОРО ЗАБУДЕТ:")
    print("-" * 70)
    print(f"{'№':<3} {'Факт ID':<8} {'Вероятность':<12} {'Статус':<15} {'Рекомендация'}")
    print("-" * 70)

    for i, p in enumerate(predictions[:10], 1):
        prob = p['recall_probability']
        if prob < 0.3:
            status = "🔴 КРИТИЧНО"
            rec = "Повторить СЕГОДНЯ"
        elif prob < 0.5:
            status = "🟠 СРОЧНО"
            rec = "Повторить завтра"
        elif prob < 0.7:
            status = "🟡 СКОРО"
            rec = "Запланировать"
        else:
            status = "🟢 НОРМА"
            rec = "Не трогать"

        print(f"{i:<3} {p['item_id']:<8} {prob:.1%}       {status:<15} {rec}")

    # Усвоение
    mastery = predictor.get_user_mastery(db, user.user_id)

    print(f"""
    📊 УСВОЕНИЕ МАТЕРИАЛА
    {'-' * 50}
    Статус: {mastery['status']}
    Всего фактов: {mastery['total_items']}
    Средняя вероятность: {mastery['average_probability']:.1%}
    Медианная вероятность: {mastery['median_probability']:.1%}

    Распределение:
      🟢 Усвоено (>70%): {mastery['distribution']['🟢 Усвоено (>70%)']} фактов
      🟡 Средне (50-70%): {mastery['distribution']['🟡 Средне (50-70%)']} фактов
      🟠 Слабо (30-50%): {mastery['distribution']['🟠 Слабо (30-50%)']} фактов
      🔴 Критично (<30%): {mastery['distribution']['🔴 Критично (<30%)']} фактов

    Итог: усвоено {mastery['mastery_percentage']}% материала
    """)


if __name__ == "__main__":
    from recall_analyzer import RecallAnalyzer

    print("=" * 70)
    print("🚀 ЗАПУСК ML-АНАЛИЗА И ПРЕДСКАЗАНИЙ")
    print("=" * 70)

    # Обучение модели
    print("\n📥 Обучение модели...")
    analyzer = RecallAnalyzer()
    analyzer.train()

    print("\n💾 Сохранение модели...")
    predictor = RecallPredictor()
    predictor.model = analyzer.model
    predictor.save_model('ml/recall_model.pkl')


    db_gen = get_db()
    db = next(db_gen)

    # Интерактивный режим
    while True:
        print("\n" + "=" * 70)
        print("🔍 ИНТЕРАКТИВНЫЙ АНАЛИЗ")
        print("=" * 70)
        print("1. Показать всех пользователей")
        print("2. Анализ конкретного пользователя")
        print("3. Топ-10 лучших")
        print("4. Топ-10 худших")
        print("5. Статистика по компании")
        print("0. Выход")

        choice = input("\nВыберите опцию: ").strip()

        if choice == '0':
            break

        elif choice == '1':
            # Показать всех пользователей
            users = db.query(User).filter(User.user_name != 'admin').all()
            print("\n📋 СПИСОК ПОЛЬЗОВАТЕЛЕЙ:")
            print("-" * 50)
            for i, u in enumerate(users, 1):
                print(f"{i:2}. {u.user_name:15} (роль: {u.user_role})")
            input("\nНажмите Enter для продолжения...")

        elif choice == '2':
            # Анализ конкретного пользователя
            name = input("Введите имя пользователя: ").strip()
            user = db.query(User).filter(
                User.user_name == name,
                User.user_name != 'admin'
            ).first()

            if user:
                # Получаем предсказания
                predictions = predictor.predict_for_user(db, user.user_id, limit=10)

                print(f"\n{'=' * 70}")
                print(f"👤 АНАЛИЗ ПОЛЬЗОВАТЕЛЯ: {user.user_name.upper()}")
                print('=' * 70)

                print("\n📊 ТОП-10 ФАКТОВ, КОТОРЫЕ СКОРО ЗАБУДЕТ:")
                print("-" * 70)
                print(f"{'№':<3} {'Факт ID':<8} {'Вероятность':<12} {'Статус':<15} {'Рекомендация'}")
                print("-" * 70)

                for i, p in enumerate(predictions[:10], 1):
                    prob = p['recall_probability']
                    if prob < 0.3:
                        status = "🔴 КРИТИЧНО"
                        rec = "Повторить СЕГОДНЯ"
                    elif prob < 0.5:
                        status = "🟠 СРОЧНО"
                        rec = "Повторить завтра"
                    elif prob < 0.7:
                        status = "🟡 СКОРО"
                        rec = "Запланировать"
                    else:
                        status = "🟢 НОРМА"
                        rec = "Не трогать"

                    print(f"{i:<3} {p['item_id']:<8} {prob:.1%}       {status:<15} {rec}")

                # Усвоение материала
                mastery = predictor.get_user_mastery(db, user.user_id)

                print("\n" + "=" * 70)
                print("📊 УСВОЕНИЕ МАТЕРИАЛА")
                print("=" * 70)

                status_icon = "🟢" if mastery['mastery_percentage'] >= 70 else "🟡" if mastery[
                                                                                         'mastery_percentage'] >= 40 else "🔴"
                print(f"""
{status_icon}  Статус: {mastery['status']}
📚  Всего изучал: {mastery['total_items']} фактов
✅  Усвоил: {mastery['mastered_items']} фактов
📊  Процент усвоения: {mastery['mastery_percentage']}%
🎯  Средняя вероятность: {mastery['average_probability']:.1%}
                """)
            else:
                print("❌ Пользователь не найден!")
            input("\nНажмите Enter для продолжения...")

        elif choice == '3':
            # Топ-10 лучших
            users = db.query(User).filter(User.user_name != 'admin').all()
            results = []

            print("\n📊 Собираем данные...")
            for i, u in enumerate(users):
                print(f"\r   Обработка: {i + 1}/{len(users)}", end="")
                mastery = predictor.get_user_mastery(db, u.user_id)
                results.append((u.user_name, mastery['mastery_percentage']))

            results.sort(key=lambda x: x[1], reverse=True)

            print("\n\n🔥 ТОП-10 ЛУЧШИХ СОТРУДНИКОВ:")
            print("-" * 50)
            print(f"{'№':<3} {'Имя':<15} {'Усвоение':<10} {'Статус'}")
            print("-" * 50)

            for i, (name, mastery) in enumerate(results[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
                status = "🔥" if mastery >= 80 else "👍" if mastery >= 60 else "👌"
                print(f"{medal} {i:<2} {name:<15} {mastery:6.1f}%     {status}")

            input("\n\nНажмите Enter для продолжения...")

        elif choice == '4':
            # Топ-10 худших
            users = db.query(User).filter(User.user_name != 'admin').all()
            results = []

            print("\n📊 Собираем данные...")
            for i, u in enumerate(users):
                print(f"\r   Обработка: {i + 1}/{len(users)}", end="")
                mastery = predictor.get_user_mastery(db, u.user_id)
                results.append((u.user_name, mastery['mastery_percentage']))

            results.sort(key=lambda x: x[1])

            print("\n\n⚠️ ТОП-10 ХУДШИХ (НУЖДАЮТСЯ В ПОМОЩИ):")
            print("-" * 50)
            print(f"{'№':<3} {'Имя':<15} {'Усвоение':<10} {'Статус'}")
            print("-" * 50)

            for i, (name, mastery) in enumerate(results[:10], 1):
                status = "🔴" if mastery < 20 else "🟠" if mastery < 40 else "🟡"
                print(f"  {i:<2} {name:<15} {mastery:6.1f}%     {status}")

            input("\n\nНажмите Enter для продолжения...")

        elif choice == '5':
            # Статистика по компании
            users = db.query(User).filter(User.user_name != 'admin').all()

            if not users:
                print("❌ Нет пользователей для анализа")
                continue

            all_masteries = []
            distribution = {
                '🔥 Отлично (>80%)': 0,
                '👍 Хорошо (60-80%)': 0,
                '👌 Средне (40-60%)': 0,
                '⚠️ Слабо (20-40%)': 0,
                '🔴 Критично (<20%)': 0
            }

            print("\n📊 Собираем статистику...")
            for i, u in enumerate(users):
                print(f"\r   Обработка: {i + 1}/{len(users)}", end="")
                mastery = predictor.get_user_mastery(db, u.user_id)
                m_pct = mastery['mastery_percentage']
                all_masteries.append(m_pct)

                if m_pct >= 80:
                    distribution['🔥 Отлично (>80%)'] += 1
                elif m_pct >= 60:
                    distribution['👍 Хорошо (60-80%)'] += 1
                elif m_pct >= 40:
                    distribution['👌 Средне (40-60%)'] += 1
                elif m_pct >= 20:
                    distribution['⚠️ Слабо (20-40%)'] += 1
                else:
                    distribution['🔴 Критично (<20%)'] += 1

            avg_mastery = np.mean(all_masteries) if all_masteries else 0

            print("\n\n" + "=" * 70)
            print("🏢 СТАТИСТИКА ПО КОМПАНИИ")
            print("=" * 70)
            print(f"""
👥  Всего сотрудников: {len(users)}
📊  Среднее усвоение: {avg_mastery:.1f}%
📈  Медиана: {np.median(all_masteries):.1f}%
📉  Минимум: {min(all_masteries):.1f}%
📈  Максимум: {max(all_masteries):.1f}%

📊 РАСПРЕДЕЛЕНИЕ ПО УРОВНЯМ:
{'-' * 50}""")

            for level, count in distribution.items():
                if count > 0:
                    percentage = (count / len(users)) * 100
                    bar = "█" * int(percentage / 2)
                    print(f"{level:20} : {count:2} чел. ({percentage:4.1f}%) {bar}")

            input("\n\nНажмите Enter для продолжения...")

    db.close()
    print("\n✅ Анализ завершён!")