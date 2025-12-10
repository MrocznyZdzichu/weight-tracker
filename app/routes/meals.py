from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from datetime import date, datetime
from sqlmodel import Session, select
from app.core.db import engine
from app.core.templates import templates
from app.models import Meal, User, SavedDay

router = APIRouter()

@router.get("/meals")
def meals_today(request: Request):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    today = date.today()
    with Session(engine) as session:
        meals = session.exec(
            select(Meal).where(Meal.user_id == uid, Meal.date == today).order_by(Meal.id)
        ).all()
        total = sum(int(m.kcal) for m in meals) if meals else 0
        user = session.exec(select(User).where(User.id == uid)).first()
        goal = user.daily_kcal_goal if user and user.daily_kcal_goal else 2000
        remaining = goal - total
    return templates.TemplateResponse(
        "meals.html",
        {
            "request": request,
            "today": today,
            "meals": meals,
            "total": total,
            "goal": goal,
            "remaining": remaining,
        },
    )

@router.post("/meals/add")
def add_meal(request: Request, name: str = Form(...), kcal: int = Form(...)):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    name = name.strip()
    kcal = int(kcal)
    if not name or kcal <= 0:
        return RedirectResponse("/meals", status_code=303)
    with Session(engine) as session:
        m = Meal(date=date.today(), name=name, kcal=kcal, user_id=uid)
        session.add(m)
        session.commit()
    return RedirectResponse("/meals", status_code=303)

@router.post("/meals/goal")
def set_goal(request: Request, goal: int = Form(...)):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    g = int(goal)
    if g < 800:
        g = 800
    if g > 10000:
        g = 10000
    with Session(engine) as session:
        u = session.get(User, uid)
        if u:
            u.daily_kcal_goal = g
            session.add(u)
            session.commit()
    return RedirectResponse("/meals", status_code=303)

@router.post("/meals/edit/{meal_id}")
def edit_meal(request: Request, meal_id: int, name: str = Form(...), kcal: int = Form(...)):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    name = name.strip()
    kcal = int(kcal)
    if not name or kcal <= 0:
        return RedirectResponse("/meals", status_code=303)
    with Session(engine) as session:
        m = session.get(Meal, meal_id)
        if m and m.user_id == uid:
            m.name = name
            m.kcal = kcal
            session.add(m)
            session.commit()
    return RedirectResponse("/meals", status_code=303)

@router.post("/meals/save-day")
def save_day(request: Request):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    today = date.today()
    with Session(engine) as session:
        meals = session.exec(
            select(Meal).where(Meal.user_id == uid, Meal.date == today)
        ).all()
        if not meals:
            return RedirectResponse("/meals", status_code=303)
        total = sum(int(m.kcal) for m in meals)
        existing = session.exec(
            select(SavedDay).where(SavedDay.user_id == uid, SavedDay.date == today)
        ).first()
        if existing:
            existing.total_kcal = total
            existing.saved_at = datetime.utcnow()
            session.add(existing)
        else:
            sd = SavedDay(date=today, user_id=uid, total_kcal=total)
            session.add(sd)
        session.commit()
    return RedirectResponse("/meals/history", status_code=303)

@router.get("/meals/history")
def meals_history(request: Request, date_str: str | None = None, from_date: str | None = None, to_date: str | None = None, product: str | None = None):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
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
        stmt = select(SavedDay).where(SavedDay.user_id == uid).order_by(SavedDay.date.desc())
        days = session.exec(stmt).all()
        filtered_days = []
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
            filtered_days.append({
                "date": sd.date,
                "meals": meals,
                "total_kcal": total,
            })
    return templates.TemplateResponse(
        "meals_history.html",
        {
            "request": request,
            "days": filtered_days,
            "date_str": date_str or "",
            "from_date": from_date or "",
            "to_date": to_date or "",
            "product": product or "",
            "today": date.today().isoformat(),
        },
    )

@router.post("/meals/delete/{meal_id}")
def delete_meal(request: Request, meal_id: int):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    with Session(engine) as session:
        m = session.get(Meal, meal_id)
        if m and m.user_id == uid:
            session.delete(m)
            session.commit()
    return RedirectResponse("/meals", status_code=303)
