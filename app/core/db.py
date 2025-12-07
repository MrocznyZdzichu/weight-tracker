import os
from sqlmodel import SQLModel, create_engine
from app import models
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

if not os.path.exists("data"):
    os.makedirs("data")

SQLModel.metadata.create_all(engine)

def ensure_schema():
    with engine.connect() as conn:
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('measurement')").fetchall()]
        if "user_id" not in cols:
            conn.exec_driver_sql("ALTER TABLE measurement ADD COLUMN user_id INTEGER")
