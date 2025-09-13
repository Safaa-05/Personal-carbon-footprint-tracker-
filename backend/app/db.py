from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./carbon_tracker.db")
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    from app import models  # ensure models imported to register tables
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
