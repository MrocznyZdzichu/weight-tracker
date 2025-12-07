from typing import List, Optional
from datetime import date
import pandas as pd
from sqlmodel import Session, select
from app.core.db import engine
from app.models import Measurement

def get_all_measurements(user_id: Optional[int] = None) -> List[Measurement]:
    with Session(engine) as session:
        stmt = select(Measurement).order_by(Measurement.date)
        if user_id is not None:
            stmt = stmt.where(Measurement.user_id == user_id)
        return session.exec(stmt).all()

def compute_weekly_changes(measurements: List[Measurement]):
    if not measurements or len(measurements) < 2:
        return []
    df = pd.DataFrame([{"date": m.date, "weight": m.weight_kg} for m in measurements])
    df = df.sort_values("date")
    df["date"] = pd.to_datetime(df["date"])
    df["delta_days"] = df["date"].diff().dt.days
    df["delta_weight"] = df["weight"].diff()
    df = df.dropna()
    df = df[df["delta_days"] > 0]
    df["kg_per_week"] = df["delta_weight"] / df["delta_days"] * 7
    weekly = df[["date", "kg_per_week"]].copy()
    weekly["kg_per_week"] = weekly["kg_per_week"].round(3)
    return weekly.to_dict(orient="records")

def filter_by_periods(measurements: List[Measurement], filters_str: str | None):
    if not filters_str:
        return measurements
    tokens = [t.strip() for t in filters_str.split(",") if t.strip()]
    if not tokens:
        return measurements
    res = []
    for m in measurements:
        d = m.date
        ok = False
        for t in tokens:
            if len(t) == 4 and t.isdigit():
                if d.year == int(t):
                    ok = True
            elif len(t) == 7 and t[4] == "-" and t[:4].isdigit() and t[5:7].isdigit():
                y = int(t[:4])
                mo = int(t[5:7])
                if d.year == y and d.month == mo:
                    ok = True
            elif len(t) == 6 and t[:4].isdigit() and t[4] == "Q" and t[5] in "1234":
                y = int(t[:4])
                q = int(t[5])
                start = (q - 1) * 3 + 1
                end = start + 2
                if d.year == y and start <= d.month <= end:
                    ok = True
            elif len(t) == 6 and t[:4].isdigit() and t[4] == "H" and t[5] in "12":
                y = int(t[:4])
                h = int(t[5])
                start = 1 if h == 1 else 7
                end = 6 if h == 1 else 12
                if d.year == y and start <= d.month <= end:
                    ok = True
            if ok:
                break
        if ok:
            res.append(m)
    return res

def is_truthy(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "on")
