from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from datetime import date
from sqlmodel import Session, select
from app.core.db import engine
from app.core.templates import templates
from app.models import Meal, User

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
