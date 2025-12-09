import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.base import Base


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./gigaschool.db"
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    session = SessionLocal()
    try:
        return session
    finally:
        pass


def init_db():
    Base.metadata.create_all(bind=engine)