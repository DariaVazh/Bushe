from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base  # ИСПРАВЛЕНО: новый импорт
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

Base = declarative_base() 

DATABASE_URL = ###


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

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
