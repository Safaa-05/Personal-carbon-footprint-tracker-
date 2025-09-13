from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from datetime import datetime
from app.database.session import Base

class CarbonReport(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    period = Column(String)
    electricity = Column(Float)
    cooking = Column(Float)
    transport = Column(Float)
    food = Column(Float)
    waste = Column(Float)
    total = Column(Float)
    data_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
