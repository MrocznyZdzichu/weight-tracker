from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    daily_kcal_goal: int = Field(default=2000)

class Measurement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    weight_kg: float
    user_id: Optional[int] = Field(default=None)

class Meal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    name: str
    kcal: int
    user_id: Optional[int] = Field(default=None)
