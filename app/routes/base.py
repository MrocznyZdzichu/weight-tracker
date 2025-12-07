from fastapi import APIRouter, Request, Form, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
import io
from datetime import date, datetime
from sqlmodel import Session
from app.core.db import engine
from app.core.templates import templates
from app.models import Measurement
from app.services.measurements import get_all_measurements, compute_weekly_changes, filter_by_periods

router = APIRouter()

@router.get("/")
def index(request: Request):
    uid = request.session.get("uid")
    measurements = get_all_measurements(uid) if uid else []
    weekly = compute_weekly_changes(measurements)
    if weekly:
        last_change = round(float(weekly[-1]["kg_per_week"]), 3)
        avg_weekly = round(float(sum(w["kg_per_week"] for w in weekly) / len(weekly)), 3)
    else:
        last_change = None
        avg_weekly = None
    return templates.TemplateResponse("index.html", {"request": request, "measurements": measurements, "last_change": last_change, "avg_weekly": avg_weekly})

@router.get("/add")
def add_form(request: Request):
    if not request.session.get("uid"):
        return RedirectResponse("/login", status_code=303)
    today = date.today().isoformat()
    return templates.TemplateResponse("add.html", {"request": request, "today": today})

@router.post("/add")
def add_measurement(request: Request, date_str: str = Form(...), weight: float = Form(...)):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    weight = round(weight, 1)
    with Session(engine) as session:
        m = Measurement(date=dt, weight_kg=weight, user_id=uid)
        session.add(m)
        session.commit()
    return RedirectResponse("/", status_code=303)

@router.get("/history")
def history(request: Request, filters: str | None = None):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    measurements = get_all_measurements(uid)
    filtered = filter_by_periods(measurements, filters)
    return templates.TemplateResponse("history.html", {"request": request, "measurements": filtered, "filters": filters or ""})

@router.get("/stats")
def stats(request: Request, filters: str | None = None, trend: str | None = None):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    measurements = get_all_measurements(uid)
    measurements = filter_by_periods(measurements, filters)
    if len(measurements) < 2:
        return templates.TemplateResponse("stats.html", {"request": request, "weekly": [], "last_change": None, "avg_weekly": None, "filters": filters or "", "trend": trend in ("1","true","yes","on")})
    weekly = compute_weekly_changes(measurements)
    if not weekly:
        return templates.TemplateResponse("stats.html", {"request": request, "weekly": [], "last_change": None, "avg_weekly": None, "filters": filters or "", "trend": trend in ("1","true","yes","on")})
    last_change = round(float(weekly[-1]["kg_per_week"]), 3)
    avg_weekly = round(float(sum(w["kg_per_week"] for w in weekly) / len(weekly)), 3)
    return templates.TemplateResponse("stats.html", {"request": request, "weekly": weekly, "last_change": last_change, "avg_weekly": avg_weekly, "filters": filters or "", "trend": trend in ("1","true","yes","on")})

@router.get("/export")
def export_csv(request: Request):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    measurements = get_all_measurements(uid)
    rows = []
    for m in measurements:
        d = m.date.strftime("%d/%m/%Y")
        rows.append(f"{d},{m.weight_kg}")
    content = "\n".join(rows)
    return StreamingResponse(io.BytesIO(content.encode("utf-8")), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=measurements.csv"})

@router.get("/import")
def import_form(request: Request):
    if not request.session.get("uid"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("import.html", {"request": request})

@router.post("/import")
async def import_csv(request: Request, file: UploadFile):
    data = await file.read()
    text = data.decode("utf-8").strip().splitlines()
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    with Session(engine) as session:
        for line in text:
            parts = line.strip().split(",")
            if len(parts) != 2:
                continue
            dstr, wstr = parts
            try:
                dt = datetime.strptime(dstr, "%d/%m/%Y").date()
                w = round(float(wstr), 1)
            except:
                continue
            m = Measurement(date=dt, weight_kg=w, user_id=uid)
            session.add(m)
        session.commit()
    return RedirectResponse("/history", status_code=303)

@router.get("/edit/{measurement_id}")
def edit_form(request: Request, measurement_id: int):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    with Session(engine) as session:
        m = session.get(Measurement, measurement_id)
        if not m or m.user_id != uid:
            return RedirectResponse("/history", status_code=303)
        return templates.TemplateResponse("edit.html", {"request": request, "m": m})

@router.post("/edit/{measurement_id}")
def edit_measurement(request: Request, measurement_id: int, date_str: str = Form(...), weight: float = Form(...)):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    weight = round(weight, 1)
    with Session(engine) as session:
        m = session.get(Measurement, measurement_id)
        if m and m.user_id == uid:
            m.date = dt
            m.weight_kg = weight
            session.add(m)
            session.commit()
    return RedirectResponse("/history", status_code=303)

@router.post("/delete/{measurement_id}")
def delete_measurement(request: Request, measurement_id: int):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=303)
    with Session(engine) as session:
        m = session.get(Measurement, measurement_id)
        if m and m.user_id == uid:
            session.delete(m)
            session.commit()
    return RedirectResponse("/history", status_code=303)
