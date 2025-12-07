import os

DB_PATH = "data/measurements.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret")
