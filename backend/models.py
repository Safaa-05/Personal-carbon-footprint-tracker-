# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    emissions = relationship("Emission", back_populates="owner")

class Emission(Base):
    __tablename__ = "emissions"
    id = Column(Integer, primary_key=True, index=True)
    transport_km = Column(Float)
    mode = Column(String)
    energy_kwh = Column(Float)
    days = Column(Integer)
    food_type = Column(String)
    waste_kg = Column(Float)
    total_emission = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="emissions")
