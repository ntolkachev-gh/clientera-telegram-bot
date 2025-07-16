from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from .models import Base

# Исправляем URL для совместимости с Heroku
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Создание таблиц в базе данных"""
    Base.metadata.create_all(bind=engine) 