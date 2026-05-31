from collections import Counter, defaultdict
import re

from sqlmodel import Session, select

from app.models import Meal


def normalize_meal_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip().lower())


def build_user_meal_kcal_modes(session: Session, user_id: int) -> dict[str, int]:
    meals = session.exec(select(Meal).where(Meal.user_id == user_id)).all()
    counts_by_name: dict[str, Counter[int]] = defaultdict(Counter)

    for meal in meals:
        name = normalize_meal_name(meal.name)
        if not name or meal.kcal is None:
            continue
        counts_by_name[name][int(meal.kcal)] += 1

    modes: dict[str, int] = {}
    for name, kcal_counts in counts_by_name.items():
        if not kcal_counts:
            continue
        modes[name] = sorted(kcal_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return modes
