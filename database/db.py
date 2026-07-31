from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine("sqlite:///esbrawlelite.db")
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    from database.models import User
    Base.metadata.create_all(engine)