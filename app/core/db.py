import os
import shutil
from sqlmodel import SQLModel, create_engine
from app import models
from .config import DATABASE_URL, DB_PATH

if os.environ.get("ENV") == "test":
    prod_db = "data/measurements.db"
    test_db = DB_PATH
    if not os.path.exists(test_db) and os.path.exists(prod_db):
        print(f"Copying production database {prod_db} to {test_db}...")
        shutil.copy2(prod_db, test_db)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

if not os.path.exists("data"):
    os.makedirs("data")

SQLModel.metadata.create_all(engine)

def ensure_schema():
    with engine.connect() as conn:
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('measurement')").fetchall()]
        if "user_id" not in cols:
            conn.exec_driver_sql("ALTER TABLE measurement ADD COLUMN user_id INTEGER")
        ucols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('user')").fetchall()]
        if "daily_kcal_goal" not in ucols:
            conn.exec_driver_sql("ALTER TABLE user ADD COLUMN daily_kcal_goal INTEGER DEFAULT 2000")
