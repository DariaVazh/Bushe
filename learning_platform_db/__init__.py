# learning_platform_db/__init__.py
from .database import Base, engine, SessionLocal, create_tables  # create_tables уже есть?
from .models import User, KnowledgeItem, Interaction, Review
from .crud import UserCRUD, InteractionCRUD, ReviewCRUD
from .queries import AnalyticsQueries, ReviewQueries

__all__ = [
    'Base', 'engine', 'SessionLocal', 'create_tables',  # <- проверьте, что create_tables здесь есть
    'User', 'KnowledgeItem', 'Interaction', 'Review',
    'UserCRUD', 'InteractionCRUD', 'ReviewCRUD',
    'AnalyticsQueries', 'ReviewQueries',
]