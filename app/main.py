from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from app.core.config import SESSION_SECRET
from app.core.db import ensure_schema
from app.routes import auth, base, plots, tips, recipes, kcal, meals

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory="app/static") if os.path.exists("app/static") else StaticFiles(directory="app/templates"), name="static")
ensure_schema()
app.include_router(base.router)
app.include_router(plots.router)
app.include_router(tips.router)
app.include_router(recipes.router)
app.include_router(kcal.router)
app.include_router(meals.router)
app.include_router(auth.router)
