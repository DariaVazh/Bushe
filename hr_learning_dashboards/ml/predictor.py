# hr_learning_dashboards/ml/predictor.py
import numpy as np
import pandas as pd
import pickle
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(current_dir)
learning_platform_path = os.path.join(parent_dir, "learning_platform_db")
if learning_platform_path not in sys.path:
    sys.path.insert(0, learning_platform_path)

from Bushe.learning_platform_db.database import get_db
from Bushe.learning_platform_db.models import User, KnowledgeItem, Interaction, Review
from sqlalchemy import func, text
import joblib
#EAFFDA

class RecallPredictor:
    def __init__(self, model_path=None):
        self.model = None
        self.feature_names = None

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def load_model(self, model_path):
        import joblib
        self.model = joblib.load(model_path)
        print(f"Модель загружена из {model_path}")

    def save_model(self, model_path='ml/recall_model.pkl'):
        """Сохраняет модель в файл"""
        import joblib
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        print(f"Модель сохранена в {model_path}")

    def prepare_user_features(self, db, user_id, item_id):

        user_stats = db.query(
            func.avg(Interaction.outcome).label('user_avg_success')
        ).filter(Interaction.user_id == user_id).first()

        item_stats = db.query(
            func.avg(Interaction.outcome).label('item_avg_success')
        ).filter(Interaction.item_id == item_id).first()

        last_interaction = db.query(Interaction).filter(
            Interaction.user_id == user_id,
            Interaction.item_id == item_id
        ).order_by(Interaction.timestamp.desc()).first()

        review = db.query(Review).filter(
            Review.user_id == user_id,
            Review.item_id == item_id
        ).first()

        now = datetime.now()

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

        delta_days = (now - last_interaction.timestamp).total_seconds() / 86400

        prev_response_time = last_interaction.response_time

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
        if self.model is None:
            raise ValueError("Модель не загружена! Сначала вызови load_model()")

        features = self.prepare_user_features(db, user_id, item_id)

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

        probability = self.model.predict_proba(X)[0, 1]

        return probability

    def predict_for_user(self, db, user_id, limit=20):

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

        results.sort(key=lambda x: x['recall_probability'])

        return results[:limit]

    def days_until_review(self, db, user_id, item_id, threshold=0.7, max_days=30):

        current_prob = self.predict_recall(db, user_id, item_id)

        if current_prob < threshold:
            return 0  # уже нужно повторять

        features = self.prepare_user_features(db, user_id, item_id)

        for days in range(1, max_days + 1):
            test_features = features.copy()
            test_features['delta_days'] = days
            test_features['log_delta'] = np.log1p(days)

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

        probabilities = []
        for review in reviews:
            prob = self.predict_recall(db, user_id, review.item_id)
            probabilities.append(prob)

        probabilities = np.array(probabilities)

        low = sum(p < 0.3 for p in probabilities)  # критично (<30%)
        medium_low = sum(0.3 <= p < 0.5 for p in probabilities)  # слабо (30-50%)
        medium = sum(0.5 <= p < 0.7 for p in probabilities)  # средне (50-70%)
        high = sum(p >= 0.7 for p in probabilities)  # усвоено (>=70%)

        mastery_pct = (high / len(reviews)) * 100

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

        users = db.query(User).filter(User.user_name != 'admin').all()

        all_masteries = []
        total_items = 0
        total_mastered = 0

        for user in users:
            mastery = self.get_user_mastery(db, user.user_id)
            all_masteries.append(mastery['mastery_percentage'])
            total_items += mastery['total_items']
            total_mastered += mastery['mastered_items']

        company_mastery = (total_mastered / total_items * 100) if total_items > 0 else 0

        distribution = {
            '🔥 Отлично (>80%)': sum(1 for m in all_masteries if m >= 80),
            '👍 Хорошо (60-80%)': sum(1 for m in all_masteries if 60 <= m < 80),
            '👌 Средне (40-60%)': sum(1 for m in all_masteries if 40 <= m < 60),
            '⚠️ Слабо (20-40%)': sum(1 for m in all_masteries if 20 <= m < 40),
            '🔴 Критично (<20%)': sum(1 for m in all_masteries if m < 20)
        }

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
    print(f"\n{'=' * 70}")
    print(f"👤 АНАЛИЗ ПОЛЬЗОВАТЕЛЯ: {user.user_name.upper()}")
    print('=' * 70)

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
    print("ЗАПУСК ML-АНАЛИЗА И ПРЕДСКАЗАНИЙ")
    print("=" * 70)

    print("\nОбучение модели...")
    analyzer = RecallAnalyzer()
    analyzer.train()

    print("\nСохранение модели...")
    predictor = RecallPredictor()
    predictor.model = analyzer.model
    predictor.save_model('ml/recall_model.pkl')

    db_gen = get_db()
    db = next(db_gen)

    # Кэш для результатов
    cache_file = 'ml/user_cache.pkl'
    user_results = []

    # Загружаем кэш если есть
    if os.path.exists(cache_file):
        print("\nагрузка кэша...")
        with open(cache_file, 'rb') as f:
            user_results = pickle.load(f)
        print(f"Загружены данные для {len(user_results)} пользователей")

    # Интерактивный режим
    while True:
        print("\n" + "=" * 70)
        print("ИНТЕРАКТИВНЫЙ АНАЛИЗ")
        print("=" * 70)
        print("1. Показать всех пользователей")
        print("2. Анализ конкретного пользователя")
        print("3. Топ-10 лучших")
        print("4. Топ-10 худших")
        print("5. Статистика по компании")
        print("6. Обновить кэш (пересчитать всех)")
        print("0. Выход")

        choice = input("\nВыберите опцию: ").strip()

        if choice == '0':
            break

        elif choice == '6':  # Обновить кэш
            print("\nПересчитываем всех пользователей...")
            users = db.query(User).filter(User.user_name != 'admin').all()
            user_results = []

            for i, u in enumerate(users):
                print(f"\r   Обработка: {i + 1}/{len(users)}", end="")
                mastery = predictor.get_user_mastery(db, u.user_id)
                user_results.append({
                    'name': u.user_name,
                    'role': u.user_role,
                    'mastery': mastery['mastery_percentage'],
                    'total_items': mastery['total_items'],
                    'mastered': mastery['mastered_items'],
                    'avg_prob': mastery['average_probability']
                })

            with open(cache_file, 'wb') as f:
                pickle.dump(user_results, f)

            print(f"\n✅ Кэш обновлён! Данные для {len(user_results)} пользователей")
            input("\nНажмите Enter для продолжения...")

        elif choice == '1':
            # Показать всех пользователей
            if not user_results:
                print("⚠️ Сначала выполните опцию 6 для загрузки данных")
            else:
                print("\n📋 СПИСОК ПОЛЬЗОВАТЕЛЕЙ:")
                print("-" * 60)
                print(f"{'№':<3} {'Имя':<15} {'Роль':<12} {'Усвоение':<8} {'Фактов'}")
                print("-" * 60)
                for i, u in enumerate(sorted(user_results, key=lambda x: x['name']), 1):
                    print(f"{i:<3} {u['name']:<15} {u['role']:<12} {u['mastery']:6.1f}%   {u['total_items']}")
            input("\nНажмите Enter для продолжения...")

        elif choice == '2':
            name = input("Введите имя пользователя: ").strip()
            user = db.query(User).filter(
                User.user_name == name,
                User.user_name != 'admin'
            ).first()

            if user:
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
            # Топ-10 лучших (из кэша)
            if not user_results:
                print("⚠️ Сначала выполните опцию 6 для загрузки данных")
            else:
                sorted_results = sorted(user_results, key=lambda x: x['mastery'], reverse=True)

                print("\n🔥 ТОП-10 ЛУЧШИХ СОТРУДНИКОВ:")
                print("-" * 60)
                print(f"{'№':<3} {'Имя':<15} {'Усвоение':<8} {'Фактов'}")
                print("-" * 60)

                for i, u in enumerate(sorted_results[:10], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
                    status = "🔥" if u['mastery'] >= 50 else "👍" if u['mastery'] >= 30 else "👌"
                    print(f"{medal} {i:<2} {u['name']:<15} {u['mastery']:6.1f}%   {u['total_items']}  {status}")

            input("\nНажмите Enter для продолжения...")

        elif choice == '4':
            # Топ-10 худших (из кэша)
            if not user_results:
                print("⚠️ Сначала выполните опцию 6 для загрузки данных")
            else:
                sorted_results = sorted(user_results, key=lambda x: x['mastery'])

                print("\n⚠️ ТОП-10 ХУДШИХ (НУЖДАЮТСЯ В ПОМОЩИ):")
                print("-" * 60)
                print(f"{'№':<3} {'Имя':<15} {'Усвоение':<8} {'Фактов'}")
                print("-" * 60)

                for i, u in enumerate(sorted_results[:10], 1):
                    status = "🔴" if u['mastery'] < 10 else "🟠" if u['mastery'] < 20 else "🟡"
                    print(f"  {i:<2} {u['name']:<15} {u['mastery']:6.1f}%   {u['total_items']}  {status}")

            input("\nНажмите Enter для продолжения...")

        elif choice == '5':
            if not user_results:
                print("⚠️ Сначала выполните опцию 6 для загрузки данных")
            else:
                masteries = [u['mastery'] for u in user_results]

                distribution = {
                    '🔥 Отлично (>50%)': sum(1 for m in masteries if m >= 50),
                    '👍 Хорошо (30-50%)': sum(1 for m in masteries if 30 <= m < 50),
                    '👌 Средне (10-30%)': sum(1 for m in masteries if 10 <= m < 30),
                    '🔴 Критично (<10%)': sum(1 for m in masteries if m < 10)
                }

                print("\n" + "=" * 70)
                print("🏢 СТАТИСТИКА ПО КОМПАНИИ")
                print("=" * 70)
                print(f"""
👥  Всего сотрудников: {len(user_results)}
📊  Среднее усвоение: {np.mean(masteries):.1f}%
📈  Медиана: {np.median(masteries):.1f}%
📉  Минимум: {min(masteries):.1f}%
📈  Максимум: {max(masteries):.1f}%

📊 РАСПРЕДЕЛЕНИЕ ПО УРОВНЯМ:
{'-' * 50}""")

                for level, count in distribution.items():
                    if count > 0:
                        percentage = (count / len(user_results)) * 100
                        bar = "█" * int(percentage / 2)
                        print(f"{level:20} : {count:2} чел. ({percentage:4.1f}%) {bar}")

            input("\n\nНажмите Enter для продолжения...")

    db.close()
    print("\n✅ Анализ завершён!")
