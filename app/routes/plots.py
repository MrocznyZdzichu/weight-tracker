from fastapi import APIRouter, Request
import matplotlib.pyplot as plt
from app.services.measurements import get_all_measurements, compute_weekly_changes, filter_by_periods, is_truthy
from app.services.plotting import PLOT_LOCK, render_png

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
