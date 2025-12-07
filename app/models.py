from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Measurement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    weight_kg: float
    user_id: Optional[int] = Field(default=None)
