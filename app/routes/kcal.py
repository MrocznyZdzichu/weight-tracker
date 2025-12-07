from fastapi import APIRouter, Request, Form
from app.core.templates import templates
from app.services.kcal import find_kcal_info

router = APIRouter()

@router.get("/kcal")
def kcal_form(request: Request):
    return templates.TemplateResponse("kcal.html", {"request": request})

@router.post("/kcal")
def kcal_search(request: Request, product: str = Form(...)):
    q = product.strip()
    results = find_kcal_info(q, max_results=8) if q else []
    if not results:
        return templates.TemplateResponse("kcal.html", {"request": request, "product": product, "error": "Nie znaleziono danych kaloryczności."})
    return templates.TemplateResponse("kcal.html", {"request": request, "product": product, "results": results})

