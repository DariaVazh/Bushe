# models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, JSON, Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, nullable=False)

    user_name = Column(String, nullable=False)
    user_surname = Column(String, nullable=False)
    user_phone_number = Column(String)
    user_password_cash = Column(String)
    user_role = Column(String)

    # Дополнительные полезные поля
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    interactions = relationship("Interaction", back_populates="user")
    reviews = relationship("Review", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name='{self.user_name}')>"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    item_id = Column(Integer, primary_key=True, index=True)

    # Метаданные элемента знаний
    difficulty = Column(Float, nullable=True)  # Сложность (0-1)
    domain = Column(String(100), nullable=True)  # Предметная область
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    interactions = relationship("Interaction", back_populates="item")
    reviews = relationship("Review", back_populates="item", uselist=False)

    def __repr__(self):
        return f"<KnowledgeItem {self.item_id}>"


class Interaction(Base):
    __tablename__ = "interactions"
    __table_args__ = (
        # Составной индекс для быстрых запросов по пользователю и времени
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        # Индекс для анализа по элементам
        Index('idx_item_timestamp', 'item_id', 'timestamp'),
        # Уникальность не требуется, но если нужно:
        # UniqueConstraint('user_id', 'item_id', 'timestamp', name='unique_interaction'),
    )

    interaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    item_id = Column(Integer, ForeignKey('knowledge_items.item_id'), nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    history_step = Column(Integer, nullable=False)  # Порядковый номер взаимодействия

    outcome = Column(Integer, nullable=False)  # 0 или 1
    response_time = Column(Float, nullable=False)  # в секундах
    delta_days = Column(Float, nullable=False)  # дней с предыдущего взаимодействия

    # Связи
    user = relationship("User", back_populates="interactions")
    item = relationship("KnowledgeItem", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction user={self.user_id} item={self.item_id} outcome={self.outcome}>"


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index('idx_review_user_item', 'user_id', 'item_id'),
    )

    # Используем составной primary key
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    item_id = Column(Integer, ForeignKey('knowledge_items.item_id', ondelete='CASCADE'), primary_key=True)

    # Агрегированные данные
    review_count = Column(Integer, default=0, nullable=False)
    last_review = Column(DateTime, nullable=True)
    avg_response_time = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)  # Процент успешных ответов

    # История для ML моделей
    history_json = Column(JSON, default=list)  # Храним последние N результатов

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="reviews")
    item = relationship("KnowledgeItem", back_populates="reviews")

    def __repr__(self):
        return f"<Review user={self.user_id} item={self.item_id} count={self.review_count}>"

    def update_from_interaction(self, interaction: Interaction):
        """Обновляет агрегированные данные на основе нового взаимодействия"""
        # Добавляем проверку на None для всех полей
        if self.review_count is None:
            self.review_count = 0
        self.review_count += 1

        self.last_review = interaction.timestamp

        # Обновляем среднее время ответа
        if self.avg_response_time is None:
            self.avg_response_time = interaction.response_time
        else:
            self.avg_response_time = (
                    (self.avg_response_time * (self.review_count - 1) +
                     interaction.response_time) / self.review_count
            )

        # Обновляем успешность
        if self.success_rate is None:
            self.success_rate = float(interaction.outcome)
        else:
            self.success_rate = (
                    (self.success_rate * (self.review_count - 1) +
                     interaction.outcome) / self.review_count
            )

        # Обновляем историю
        if self.history_json is None:
            self.history_json = []

        self.history_json.append({
            'timestamp': interaction.timestamp.isoformat(),
            'outcome': interaction.outcome,
            'response_time': interaction.response_time,
            'delta_days': interaction.delta_days
        })

        # Оставляем только последние 10 записей
        if len(self.history_json) > 10:
            self.history_json = self.history_json[-10:]