"""Shared history for HTML and plots; two queries regardless of day count."""
from collections import defaultdict
from datetime import date

from sqlmodel import Session, select
from app.models import Meal, SavedDay


def parse_optional_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def get_meal_history(session: Session, user_id: int, date_str=None,
                     from_date=None, to_date=None, product=None) -> list[dict]:
    exact, start, end = map(parse_optional_date, (date_str, from_date, to_date))
    days = select(SavedDay.date).where(SavedDay.user_id == user_id)
    if exact:
        days = days.where(SavedDay.date == exact)
    if start:
        days = days.where(SavedDay.date >= start)
    if end:
        days = days.where(SavedDay.date <= end)
    dates = session.exec(days.distinct().order_by(SavedDay.date.desc())).all()
    if not dates:
        return []
    # A subquery avoids SQLite's bind-parameter limit for long histories.
    meals = session.exec(select(Meal).where(
        Meal.user_id == user_id, Meal.date.in_(days)
    ).order_by(Meal.id)).all()
    by_date = defaultdict(list)
    query = (product or "").strip().lower()
    for meal in meals:
        if query in meal.name.lower():
            by_date[meal.date].append(meal)
    return [{"date": day, "meals": by_date[day],
             "total_kcal": sum(m.kcal for m in by_date[day])} for day in dates]
