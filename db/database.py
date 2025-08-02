from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base
from core.config import DATABASE_URL
import logging
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    logging.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logging.info("Database initialized successfully.")
