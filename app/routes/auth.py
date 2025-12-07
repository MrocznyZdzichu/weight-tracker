from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.core.db import engine
from app.core.security import hash_password, verify_password
from app.core.templates import templates
from app.models import User

router = APIRouter()

@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            return templates.TemplateResponse("register.html", {"request": request, "error": "Email już istnieje"})
        ph = hash_password(password)
        u = User(email=email, password_hash=ph)
        session.add(u)
        session.commit()
        session.refresh(u)
        request.session["uid"] = u.id
    return RedirectResponse("/", status_code=303)

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    with Session(engine) as session:
        u = session.exec(select(User).where(User.email == email)).first()
        if not u or not verify_password(password, u.password_hash):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Nieprawidłowy login lub hasło"})
        request.session["uid"] = u.id
    return RedirectResponse("/", status_code=303)

@router.post("/logout")
def logout(request: Request):
    request.session.pop("uid", None)
    return RedirectResponse("/", status_code=303)
