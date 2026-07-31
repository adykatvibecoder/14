from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DB_PATH = os.path.join(DATA_DIR, "esbrawlelite.db")

engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    from database.models import User
    Base.metadata.create_all(engine)
