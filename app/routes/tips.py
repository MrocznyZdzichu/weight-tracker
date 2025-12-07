from fastapi import APIRouter, Request
from app.core.templates import templates
from app.services.tips import fetch_health_fact, translate_to_pl

router = APIRouter()

@router.get("/tips")
def tips(request: Request):
    fact = fetch_health_fact()
    fact_pl = translate_to_pl(fact)
    return templates.TemplateResponse("tips.html", {"request": request, "fact": fact_pl})
