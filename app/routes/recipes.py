from fastapi import APIRouter, Request, Form
from app.core.templates import templates
from app.services.recipes import find_recipes

router = APIRouter()

@router.get("/recipes")
def recipes_form(request: Request):
    return templates.TemplateResponse("recipes.html", {"request": request})

@router.post("/recipes")
def recipes_search(request: Request, ingredients: str = Form(...), count: int = Form(5)):
    parts = [p.strip() for p in ingredients.split(",") if p.strip()]
    count = max(1, min(10, count))
    results = find_recipes(parts, max_results=count)
    if not results:
        return templates.TemplateResponse("recipes.html", {"request": request, "ingredients": ingredients, "count": count, "error": "Nie znaleziono przepisu zawierającego wszystkie składniki."})
    return templates.TemplateResponse("recipes.html", {"request": request, "ingredients": ingredients, "count": count, "recipes": results})
