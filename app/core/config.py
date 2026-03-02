import os

APP_PORT = int(os.environ.get("APP_PORT", 8200))
DB_PATH = os.environ.get("DB_PATH", "data/measurements.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret")
