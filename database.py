from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base  # ИСПРАВЛЕНО: новый импорт
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Базовый класс для всех моделей
Base = declarative_base()  # Теперь предупреждения не будет

# Настройки подключения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/learning_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()