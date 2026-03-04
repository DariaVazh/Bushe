# queries.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, text  # ДОБАВЬ text СЮДА
from datetime import datetime, timedelta
from .models import User, KnowledgeItem, Interaction, Review
import pandas as pd
from typing import Dict, Any, List


class AnalyticsQueries:

    @staticmethod
    def get_user_learning_curve(db: Session, user_id: int) -> pd.DataFrame:
        """Кривая обучения пользователя (успешность по времени)"""
        query = text(f"""
            SELECT 
                DATE(timestamp) as date,
                AVG(outcome) as daily_success_rate,
                COUNT(*) as interactions_count,
                AVG(response_time) as avg_response_time
            FROM interactions
            WHERE user_id = {user_id}
            GROUP BY DATE(timestamp)
            ORDER BY date
        """)
        return pd.read_sql(query, db.bind)

    @staticmethod
    def get_item_difficulty_analysis(db: Session) -> pd.DataFrame:
        """Анализ сложности элементов знаний"""
        query = text("""
            SELECT 
                ki.item_id,
                COUNT(i.interaction_id) as total_attempts,
                AVG(i.outcome) as success_rate,
                AVG(i.response_time) as avg_response_time,
                COUNT(DISTINCT i.user_id) as unique_users
            FROM knowledge_items ki
            LEFT JOIN interactions i ON ki.item_id = i.item_id
            GROUP BY ki.item_id
            HAVING COUNT(i.interaction_id) > 10
            ORDER BY success_rate
        """)
        return pd.read_sql(query, db.bind)

    @staticmethod
    def get_spaced_repetition_effectiveness(db: Session) -> pd.DataFrame:
        """Эффективность интервальных повторений"""
        query = text("""
            SELECT 
                CASE 
                    WHEN delta_days < 1 THEN 'same_day'
                    WHEN delta_days < 3 THEN '1-3_days'
                    WHEN delta_days < 7 THEN '3-7_days'
                    WHEN delta_days < 14 THEN '7-14_days'
                    ELSE '14+_days'
                END as interval_group,
                AVG(outcome) as success_rate,
                COUNT(*) as sample_size
            FROM interactions
            WHERE delta_days > 0
            GROUP BY interval_group
            ORDER BY 
                CASE interval_group
                    WHEN 'same_day' THEN 1
                    WHEN '1-3_days' THEN 2
                    WHEN '3-7_days' THEN 3
                    WHEN '7-14_days' THEN 4
                    ELSE 5
                END
        """)
        return pd.read_sql(query, db.bind)

    @staticmethod
    def get_ml_training_data(db: Session, min_interactions: int = 10) -> pd.DataFrame:
        """Подготовка данных для ML модели (предсказание успешности)"""
        query = text(f"""
            WITH user_stats AS (
                SELECT 
                    user_id,
                    AVG(outcome) as user_avg_success,
                    AVG(response_time) as user_avg_response_time
                FROM interactions
                GROUP BY user_id
                HAVING COUNT(*) > {min_interactions}
            ),
            item_stats AS (
                SELECT 
                    item_id,
                    AVG(outcome) as item_avg_success,
                    AVG(response_time) as item_avg_response_time
                FROM interactions
                GROUP BY item_id
            )
            SELECT 
                i.user_id,
                i.item_id,
                i.history_step,
                i.outcome as target,
                i.response_time,
                i.delta_days,
                us.user_avg_success,
                us.user_avg_response_time,
                is2.item_avg_success,
                is2.item_avg_response_time,
                r.review_count,
                r.success_rate as user_item_success_rate,
                EXTRACT(DOW FROM i.timestamp) as day_of_week,
                EXTRACT(HOUR FROM i.timestamp) as hour_of_day
            FROM interactions i
            JOIN user_stats us ON i.user_id = us.user_id
            JOIN item_stats is2 ON i.item_id = is2.item_id
            LEFT JOIN reviews r ON i.user_id = r.user_id AND i.item_id = r.item_id
            WHERE i.user_id IN (SELECT user_id FROM user_stats)
            ORDER BY i.timestamp
        """)
        return pd.read_sql(query, db.bind)

    # learning_platform_db/queries.py (добавить в класс AnalyticsQueries)

    @staticmethod
    def get_all_users(db: Session) -> List[Dict[str, Any]]:
        """Возвращает список всех пользователей с базовой информацией"""
        users = db.query(User).all()

        result = []
        for user in users:
            # Считаем баллы пользователя
            correct_count = db.query(Interaction).filter(
                Interaction.user_id == user.user_id,
                Interaction.outcome == 1
            ).count()

            total_count = db.query(Interaction).filter(
                Interaction.user_id == user.user_id
            ).count()

            # Баллы: 10 за каждый правильный ответ
            score = correct_count * 10

            result.append({
                'user_id': user.user_id,
                'name': f"{user.user_name} {user.user_surname}",
                'role': user.user_role,
                'score': score,
                'correct': correct_count,
                'total': total_count,
                'accuracy': round(correct_count / total_count * 100, 1) if total_count > 0 else 0
            })

        # Сортируем по баллам (убывание)
        result.sort(key=lambda x: x['score'], reverse=True)
        return result

    @staticmethod
    def get_user_details(db: Session, user_id: int) -> Dict[str, Any]:
        """Возвращает детальную информацию о пользователе"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {}

        # Статистика по interactions
        interactions = db.query(Interaction).filter(Interaction.user_id == user_id).all()

        correct = sum(1 for i in interactions if i.outcome == 1)
        total = len(interactions)

        # Статистика по дням
        from sqlalchemy import func
        days_active = db.query(func.count(func.distinct(Interaction.timestamp))) \
                          .filter(Interaction.user_id == user_id).scalar() or 0

        # Последняя активность
        last_active = db.query(Interaction.timestamp) \
            .filter(Interaction.user_id == user_id) \
            .order_by(Interaction.timestamp.desc()) \
            .first()

        # Прогресс по темам (из reviews)
        reviews = db.query(Review).filter(Review.user_id == user_id).all()
        topics_progress = [
            {
                'item_id': r.item_id,
                'success_rate': round(r.success_rate * 100, 1) if r.success_rate else 0,
                'review_count': r.review_count
            }
            for r in reviews[:5]  # топ-5 тем
        ]

        return {
            'user_id': user.user_id,
            'name': f"{user.user_name} {user.user_surname}",
            'role': user.user_role,
            'phone': user.user_phone_number or 'Не указан',
            'created': user.created_at.strftime('%d.%m.%Y') if user.created_at else 'Неизвестно',
            'last_active': last_active[0].strftime('%d.%m.%Y %H:%M') if last_active else 'Нет активности',
            'stats': {
                'correct': correct,
                'total': total,
                'accuracy': round(correct / total * 100, 1) if total > 0 else 0,
                'score': correct * 10,
                'days_active': days_active
            },
            'topics': topics_progress
        }

class ReviewQueries:

    @staticmethod
    def get_items_for_review(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить элементы для повторения (SMART алгоритм)"""
        query = """
            SELECT 
                r.item_id,
                r.review_count,
                r.success_rate,
                r.avg_response_time,
                EXTRACT(DAY FROM NOW() - r.last_review) as days_since_review,
                -- Чем ниже success_rate и чем больше дней прошло, тем выше приоритет
                (1 - COALESCE(r.success_rate, 0)) * 
                EXTRACT(DAY FROM NOW() - COALESCE(r.last_review, '1970-01-01')) as priority_score
            FROM reviews r
            WHERE r.user_id = :user_id
            ORDER BY priority_score DESC
            LIMIT :limit
        """

        # Правильный способ получения результатов
        result = db.execute(
            text(query),
            {"user_id": user_id, "limit": limit}
        )

        # Исправляем преобразование в словарь
        reviews = []
        for row in result:
            reviews.append({
                'item_id': row[0],
                'review_count': row[1],
                'success_rate': row[2],
                'avg_response_time': row[3],
                'days_since_review': row[4],
                'priority_score': row[5]
            })
        return reviews

    @staticmethod
    def bulk_update_reviews(db: Session, reviews_data: List[Dict]):
        """Массовое обновление ревью (для ETL процессов)"""
        from sqlalchemy.dialects.postgresql import insert

        stmt = insert(Review).values(reviews_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'item_id'],
            set_={
                'review_count': stmt.excluded.review_count,
                'last_review': stmt.excluded.last_review,
                'avg_response_time': stmt.excluded.avg_response_time,
                'success_rate': stmt.excluded.success_rate,
                'history_json': stmt.excluded.history_json,
                'updated_at': datetime.utcnow()
            }
        )
        db.execute(stmt)
        db.commit()