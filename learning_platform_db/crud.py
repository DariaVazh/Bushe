# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .models import User, KnowledgeItem, Interaction, Review
import json
from .database import SessionLocal

class UserCRUD:
    @staticmethod
    def create(db: Session, user_name: str, user_phone_number: Optional[str] = None, user_password_cash: Optional[str] = None) -> User:
        """Создает нового пользователя с обязательным именем"""
        user = User(
            user_name=user_name,
            user_phone_number=user_phone_number,
            user_password_cash=user_password_cash
            # created_at и last_active заполнятся автоматически
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False


class InteractionCRUD:
    @staticmethod
    def create(
            db: Session,
            user_id: int,
            item_id: int,
            outcome: int,
            response_time: float,
            history_step: Optional[int] = None
    ) -> Interaction:
        # Получаем последнее взаимодействие для расчета delta_days
        last_interaction = db.query(Interaction) \
            .filter(
            Interaction.user_id == user_id,
            Interaction.item_id == item_id
        ) \
            .order_by(Interaction.timestamp.desc()) \
            .first()

        now = datetime.utcnow()

        # Рассчитываем delta_days
        if last_interaction:
            delta = (now - last_interaction.timestamp).total_seconds() / 86400  # в днях
        else:
            delta = 0.0

        # Определяем history_step
        if history_step is None:
            max_step = db.query(func.max(Interaction.history_step)) \
                           .filter(Interaction.user_id == user_id) \
                           .scalar() or 0
            history_step = max_step + 1

        # Создаем взаимодействие
        interaction = Interaction(
            user_id=user_id,
            item_id=item_id,
            timestamp=now,
            history_step=history_step,
            outcome=outcome,
            response_time=response_time,
            delta_days=delta
        )

        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        # Обновляем или создаем Review
        InteractionCRUD._update_review(db, user_id, item_id, interaction)

        return interaction

    @staticmethod
    def _update_review(db: Session, user_id: int, item_id: int, interaction: Interaction):
        review = db.query(Review).filter(
            Review.user_id == user_id,
            Review.item_id == item_id
        ).first()

        if not review:
            review = Review(
                user_id=user_id,
                item_id=item_id
            )
            db.add(review)

        review.update_from_interaction(interaction)
        db.commit()

    @staticmethod
    def get_user_interactions(
            db: Session,
            user_id: int,
            limit: int = 100
    ) -> List[Interaction]:
        return db.query(Interaction) \
            .filter(Interaction.user_id == user_id) \
            .order_by(Interaction.timestamp.desc()) \
            .limit(limit) \
            .all()


class ReviewCRUD:
    @staticmethod
    def get_for_ml(
            db: Session,
            min_reviews: int = 5,
            limit: int = 1000
    ) -> List[Review]:
        """Получить данные для ML модели"""
        return db.query(Review) \
            .filter(Review.review_count >= min_reviews) \
            .limit(limit) \
            .all()

    @staticmethod
    def get_user_reviews(db: Session, user_id: int) -> List[Review]:
        return db.query(Review) \
            .filter(Review.user_id == user_id) \
            .all()