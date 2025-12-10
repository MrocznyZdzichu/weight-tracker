from fastapi import APIRouter, Request
import matplotlib.pyplot as plt
from app.services.measurements import get_all_measurements, compute_weekly_changes, filter_by_periods, is_truthy
from app.services.plotting import PLOT_LOCK, render_png
from datetime import datetime, date
from sqlmodel import Session, select
from app.core.db import engine
from app.models import Meal, SavedDay

router = APIRouter()

@router.get("/plot")
def plot_history(request: Request, filters: str | None = None, trend: str | None = None):
    uid = request.session.get("uid")
    measurements = get_all_measurements(uid) if uid else []
    measurements = filter_by_periods(measurements, filters)
    with PLOT_LOCK:
        if not measurements:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "Brak danych", ha="center", va="center", fontsize=20)
            ax.axis("off")
            return render_png(fig)
        dates = [m.date for m in measurements]
        values = [m.weight_kg for m in measurements]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, values, marker="o", linewidth=2)
        if is_truthy(trend):
            import pandas as pd
            s = pd.Series(values)
            sm = s.rolling(window=5, center=True).mean().tolist()
            d2 = [d for d, v in zip(dates, sm) if v is not None]
            v2 = [v for v in sm if v is not None]
            if d2 and v2:
                ax.plot(d2, v2, color="orange", linewidth=3)
        ax.grid(True)
        ax.set_title("Przebieg masy ciała", fontsize=18)
        ax.set_xlabel("Data", fontsize=14)
        ax.set_ylabel("Masa (kg)", fontsize=14)
        fig.tight_layout()
        return render_png(fig)

@router.get("/plot-weekly-changes")
def plot_weekly_changes(request: Request, filters: str | None = None):
    uid = request.session.get("uid")
    measurements = get_all_measurements(uid) if uid else []
    measurements = filter_by_periods(measurements, filters)
    weekly = compute_weekly_changes(measurements)
    with PLOT_LOCK:
        if not weekly:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "Brak danych do histogramu", ha="center", va="center", fontsize=20)
            ax.axis("off")
            return render_png(fig)
        values = [float(w["kg_per_week"]) for w in weekly]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(values, bins=16, edgecolor="black")
        ax.grid(True)
        ax.set_title("Histogram tygodniowych zmian masy", fontsize=18)
        ax.set_xlabel("Zmiana masy (kg/tydzień)", fontsize=14)
        ax.set_ylabel("Liczba tygodni", fontsize=14)
        fig.tight_layout()
        return render_png(fig)

@router.get("/plot-meals-daily")
def plot_meals_daily(request: Request, date_str: str | None = None, from_date: str | None = None, to_date: str | None = None, product: str | None = None):
    uid = request.session.get("uid")
    q_product = (product or "").strip().lower()
    d_exact: date | None = None
    d_from: date | None = None
    d_to: date | None = None
    try:
        if date_str:
            d_exact = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        d_exact = None
    try:
        if from_date:
            d_from = datetime.strptime(from_date, "%Y-%m-%d").date()
    except Exception:
        d_from = None
    try:
        if to_date:
            d_to = datetime.strptime(to_date, "%Y-%m-%d").date()
    except Exception:
        d_to = None
    with Session(engine) as session:
        stmt = select(SavedDay).where(SavedDay.user_id == uid).order_by(SavedDay.date)
        days = session.exec(stmt).all()
        points = []
        for sd in days:
            if d_exact and sd.date != d_exact:
                continue
            if d_from and sd.date < d_from:
                continue
            if d_to and sd.date > d_to:
                continue
            meals = session.exec(
                select(Meal).where(Meal.user_id == uid, Meal.date == sd.date).order_by(Meal.id)
            ).all()
            if q_product:
                meals = [m for m in meals if q_product in (m.name or "").lower()]
            total = sum(int(m.kcal) for m in meals) if meals else 0
            points.append((sd.date, total))
    with PLOT_LOCK:
        fig, ax = plt.subplots(figsize=(10, 5))
        if not points:
            ax.text(0.5, 0.5, "Brak danych", ha="center", va="center", fontsize=20)
            ax.axis("off")
            return render_png(fig)
        dates = [p[0] for p in points]
        totals = [p[1] for p in points]
        ax.plot(dates, totals, marker="o", linewidth=2)
        ax.grid(True)
        ax.set_title("Historia dziennych kalorii", fontsize=18)
        ax.set_xlabel("Data", fontsize=14)
        ax.set_ylabel("Kalorie (kcal)", fontsize=14)
        fig.tight_layout()
        return render_png(fig)

@router.get("/plot-meals-hist")
def plot_meals_hist(request: Request, date_str: str | None = None, from_date: str | None = None, to_date: str | None = None, product: str | None = None):
    uid = request.session.get("uid")
    q_product = (product or "").strip().lower()
    d_exact: date | None = None
    d_from: date | None = None
    d_to: date | None = None
    try:
        if date_str:
            d_exact = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        d_exact = None
    try:
        if from_date:
            d_from = datetime.strptime(from_date, "%Y-%m-%d").date()
    except Exception:
        d_from = None
    try:
        if to_date:
            d_to = datetime.strptime(to_date, "%Y-%m-%d").date()
    except Exception:
        d_to = None
    with Session(engine) as session:
        stmt = select(SavedDay).where(SavedDay.user_id == uid).order_by(SavedDay.date)
        days = session.exec(stmt).all()
        totals = []
        for sd in days:
            if d_exact and sd.date != d_exact:
                continue
            if d_from and sd.date < d_from:
                continue
            if d_to and sd.date > d_to:
                continue
            meals = session.exec(
                select(Meal).where(Meal.user_id == uid, Meal.date == sd.date).order_by(Meal.id)
            ).all()
            if q_product:
                meals = [m for m in meals if q_product in (m.name or "").lower()]
            total = sum(int(m.kcal) for m in meals) if meals else 0
            totals.append(total)
    with PLOT_LOCK:
        fig, ax = plt.subplots(figsize=(10, 5))
        if not totals:
            ax.text(0.5, 0.5, "Brak danych do histogramu", ha="center", va="center", fontsize=20)
            ax.axis("off")
            return render_png(fig)
        ax.hist(totals, bins=16, edgecolor="black")
        ax.grid(True)
        ax.set_title("Histogram dziennych kalorii", fontsize=18)
        ax.set_xlabel("Kalorie (kcal)", fontsize=14)
        ax.set_ylabel("Liczba dni", fontsize=14)
        fig.tight_layout()
        return render_png(fig)
