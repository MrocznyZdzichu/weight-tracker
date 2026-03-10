from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from datetime import date, datetime
from sqlmodel import Session, select
import statistics
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
  
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

@router.get("/meals/stats")
def meals_stats(
    request: Request,
    from_date: str | None = None,
    to_date: str | None = None,
    view_mode: str = 'table',
    agg_func: list[str] = Query(default=['mean']),
    chart_type: str = 'bar',
    top_n: int = 10,
    sort_by: str = 'mean',
):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)

    d_from = pd.to_datetime(from_date) if from_date else None
    d_to = pd.to_datetime(to_date) if to_date else None

    with Session(engine) as session:
        stmt = select(Meal).where(Meal.user_id == uid)
        meals = session.exec(stmt).all()

    if not meals:
        return templates.TemplateResponse("meal_stats.html", {
            "request": request, 
            "chart_data": None,
            "from_date": from_date,
            "to_date": to_date,
            "view_mode": view_mode,
            "agg_func": agg_func,
            "chart_type": chart_type,
            "top_n": top_n,
            "sort_by": sort_by,
        })

    df = pd.DataFrame([m.dict() for m in meals])
    df['date'] = pd.to_datetime(df['date'])

    if d_from:
        df = df[df['date'] >= d_from]
    if d_to:
        df = df[df['date'] <= d_to]

    if df.empty:
        return templates.TemplateResponse("meal_stats.html", {
            "request": request, 
            "chart_data": None,
            "from_date": from_date,
            "to_date": to_date,
            "view_mode": view_mode,
            "agg_func": agg_func,
            "chart_type": chart_type,
            "top_n": top_n,
            "sort_by": sort_by,
        })

    agg_map = {
        'mean': 'mean',
        'median': 'median',
        'sum': 'sum',
        'count': 'count',
        'min': 'min',
        'max': 'max',
        'std': 'std'
    }
    
    friendly_names = {
        'mean': 'Średnia',
        'median': 'Mediana',
        'sum': 'Suma',
        'count': 'Liczba',
        'min': 'Min',
        'max': 'Max',
        'std': 'Odchylenie'
    }
    
    valid_aggs = [agg for agg in agg_func if agg in agg_map]
    if not valid_aggs:
        valid_aggs = ['mean']
    
    if view_mode == 'graph' and sort_by not in valid_aggs:
        valid_aggs.append(sort_by)
    
    agg_df = df.groupby('name')['kcal'].agg([agg_map[a] for a in valid_aggs]).reset_index()
    agg_df.rename(columns={'name': 'Posiłek'}, inplace=True)
    
    cols_to_rename = {agg_map[a]: friendly_names[a] for a in valid_aggs}
    agg_df.rename(columns=cols_to_rename, inplace=True)
    
    sort_col = friendly_names.get(sort_by)
    
    if sort_col not in agg_df.columns:
        if sort_by in agg_map:
            temp_agg = df.groupby('name')['kcal'].agg(agg_map[sort_by]).reset_index()
            temp_agg.columns = ['Posiłek', sort_col]
            agg_df = pd.merge(agg_df, temp_agg, on='Posiłek')
        else:
            sort_col = agg_df.columns[1]
    
    agg_df = agg_df.sort_values(by=sort_col, ascending=False)
    agg_df = agg_df.astype(object).replace(np.nan, None)

    requested_aggs_friendly = [friendly_names[a] for a in agg_func if a in friendly_names]
    if not requested_aggs_friendly:
        requested_aggs_friendly = [friendly_names.get('mean', 'Średnia')]

    chart_data = None
    if view_mode == 'graph':
        plot_df = agg_df.head(top_n).copy().reset_index(drop=True)
        
        y_cols = requested_aggs_friendly
        
        if len(y_cols) == 1:
            chart_title = f'{y_cols[0]} - Top {top_n} posiłków (sortowanie: {sort_col})'
        else:
            chart_title = f'Statystyki - Top {top_n} posiłków (sortowanie: {sort_col})'

        if chart_type == 'bar':
            fig = go.Figure()

            for col in y_cols:
                fig.add_trace(go.Bar(
                    x=plot_df['Posiłek'].tolist(),
                    y=plot_df[col].tolist(),
                    name=col
                ))
            
            fig.update_layout(
                barmode='group',
                title=chart_title,
                template="plotly_dark"
            )
            fig.update_xaxes(categoryorder='array', categoryarray=plot_df['Posiłek'].tolist())
        
        elif chart_type == 'pie':
            fig = go.Figure(data=[go.Pie(
                labels=plot_df['Posiłek'].tolist(),
                values=plot_df[y_cols[0]].tolist(),
                hole=.3
            )])
            fig.update_layout(
                title_text=chart_title,
                template="plotly_dark"
            )
        elif chart_type == 'box':
            top_names = plot_df['Posiłek'].tolist()
            box_df = df[df['name'].isin(top_names)]
            
            fig = go.Figure()
            for name in top_names:
                fig.add_trace(go.Box(
                    y=box_df[box_df['name'] == name]['kcal'].tolist(),
                    name=name
                ))
            fig.update_layout(
                title_text=f'Rozkład kcal dla Top {top_n} posiłków',
                template="plotly_dark",
                xaxis_title="Posiłek",
                yaxis_title="kcal"
            )
        
        if chart_type in ['bar', 'box']:
            fig.update_layout(
                xaxis={'type': 'category'}
            )
            if chart_type == 'bar':
                fig.update_xaxes(categoryorder='array', categoryarray=plot_df['Posiłek'].tolist())

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        chart_data = json.loads(fig.to_json())

    else:
        requested_friendly_names = [friendly_names[a] for a in agg_func if a in friendly_names]
        table_cols = ['Posiłek'] + requested_friendly_names
        display_df = agg_df[[c for c in table_cols if c in agg_df.columns]]
        
        chart_data = {
            "header": display_df.columns.tolist(),
            "rows": display_df.values.tolist()
        }

    return templates.TemplateResponse(
        "meal_stats.html",
        {
            "request": request,
            "from_date": from_date,
            "to_date": to_date,
            "view_mode": view_mode,
            "agg_func": agg_func,
            "chart_type": chart_type,
            "top_n": top_n,
            "sort_by": sort_by,
            "chart_data": chart_data,
        },
    )

@router.post("/meals/copy/{meal_id}")
def copy_meal(request: Request, meal_id: int):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    with Session(engine) as session:
        m = session.get(Meal, meal_id)
        if m and m.user_id == uid:
            new_meal = Meal(
                date=date.today(),
                name=m.name,
                kcal=m.kcal,
                user_id=uid
            )
            session.add(new_meal)
            session.commit()
    return RedirectResponse("/meals", status_code=303)
