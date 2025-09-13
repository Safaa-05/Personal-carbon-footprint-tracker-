from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    reports: List["Report"] = Relationship(back_populates="user")

class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    month: date  # use first day of month to indicate the month (e.g., 2025-09-01)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # store breakdown and total as JSON strings (pydantic / JSON)
    electricity: float
    cooking: float
    transport: float
    food: float
    waste: float
    total: float

    raw_input: Optional[str] = None  # original input JSON string for reproducibility

    user: Optional[User] = Relationship(back_populates="reports")
