import hashlib
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

TEMP = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = str(Path(TEMP.name) / "nested" / "test.db")
os.environ["ENV"] = "test"

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, select
from app.main import app
from app.core.db import engine, ensure_schema
from app.core.security import hash_password, verify_password
from app.models import Meal, SavedDay, User
from app.services.meal_history import get_meal_history


class AppTests(unittest.TestCase):
    def setUp(self):
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        ensure_schema()
        self.client = TestClient(app)
        self.client.post("/register", data={"email": "a@example.com", "password": "test-password"})

    def test_passwords(self):
        hashed = hash_password("secret")
        self.assertTrue(verify_password("secret", hashed))
        self.assertFalse(verify_password("bad", hashed))
        legacy = "salt:" + hashlib.sha256(b"saltsecret").hexdigest()
        self.assertTrue(verify_password("secret", legacy))
        self.assertFalse(verify_password("secret", "malformed"))

    def test_category_copy_and_fresh_autocomplete(self):
        self.client.post("/meals/add", data={"name": "Owsianka", "kcal": 350, "category": "Breakfast"})
        page = self.client.get("/meals")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["meal_kcal_modes"], {"owsianka": 350})
        self.assertLess(len(self.client.cookies.get("session")), 500)
        with Session(engine) as session:
            meal = session.exec(select(Meal)).one()
            meal_id = meal.id
        self.client.post(f"/meals/copy/{meal_id}")
        self.client.post("/meals/save-day")
        page = self.client.get("/meals/history")
        self.assertEqual(page.context["days"][0]["total_kcal"], 700)
        self.assertEqual(page.context["days"][0]["meals"][1].category, "Breakfast")
        self.client.post(f"/meals/edit/{meal_id}", data={"name": "Owsianka", "kcal": 300})
        self.assertEqual(self.client.get("/meals").context["meal_kcal_modes"], {"owsianka": 300})

    def test_stats_validation_and_modes(self):
        self.client.post("/meals/add", data={"name": "Meal", "kcal": 250, "category": "Lunch"})
        for params in ({"sort_by": "invalid"}, {"from_date": "bad"}, {"top_n": -1}, {"chart_type": "bad"}):
            self.assertEqual(self.client.get("/meals/stats", params=params).status_code, 422)
        for grouping in ("name", "category", "category_name"):
            for chart in ("bar", "pie", "box"):
                page = self.client.get("/meals/stats", params={"agg_by": grouping, "chart_type": chart, "view_mode": "graph"})
                self.assertEqual(page.status_code, 200)
        page = self.client.get("/meals/stats", params={"agg_func": "invalid"})
        self.assertEqual(len(page.context["chart_data"]["header"]), 2)

    def test_ownership(self):
        self.client.post("/meals/add", data={"name": "Private", "kcal": 250})
        self.client.post("/logout")
        self.client.post("/register", data={"email": "b@example.com", "password": "test-password"})
        self.client.post("/meals/edit/1", data={"name": "Stolen", "kcal": 1})
        self.client.post("/meals/delete/1")
        self.client.post("/meals/copy/1")
        with Session(engine) as session:
            self.assertEqual(session.exec(select(Meal)).one().name, "Private")
        self.assertEqual(self.client.get("/meals").context["meal_kcal_modes"], {})

    def test_history_query_count_and_isolation(self):
        with Session(engine) as session:
            for day in range(1, 21):
                session.add(SavedDay(date=date(2026, 1, day), user_id=1))
                session.add(Meal(date=date(2026, 1, day), user_id=1, name="A", kcal=10))
                session.add(Meal(date=date(2026, 1, day), user_id=2, name="A", kcal=999))
            session.commit()
            queries = []
            def capture(*args):
                queries.append(args[2])
            event.listen(engine, "before_cursor_execute", capture)
            try:
                days = get_meal_history(session, 1)
            finally:
                event.remove(engine, "before_cursor_execute", capture)
            self.assertEqual(len(queries), 2)
            self.assertEqual(len(days), 20)
            self.assertTrue(all(day["total_kcal"] == 10 for day in days))
            self.assertEqual(len(get_meal_history(session, 1, from_date="2026-01-19")), 2)

    def test_anonymous_plots(self):
        self.client.post("/logout")
        for route in ("/plot-top-meals-freq", "/plot-top-meals-avg-kcal", "/plot-meal-analysis", "/plot-meals-daily", "/plot-meals-hist"):
            self.assertEqual(self.client.get(route).status_code, 403)

    def test_migration_from_main(self):
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP TABLE meal")
            conn.exec_driver_sql("CREATE TABLE meal (id INTEGER PRIMARY KEY, date DATE, name TEXT, kcal INTEGER, user_id INTEGER)")
            conn.exec_driver_sql("INSERT INTO meal VALUES (1, '2026-01-01', 'Old', 100, 1)")
        ensure_schema()
        ensure_schema()
        with Session(engine) as session:
            meal = session.exec(select(Meal)).one()
            self.assertEqual(meal.name, "Old")
            self.assertIsNone(meal.category)


if __name__ == "__main__":
    unittest.main()
