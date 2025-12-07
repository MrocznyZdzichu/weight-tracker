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

def get_all_measurements(user_id: int | None = None):
    with Session(engine) as session:
        stmt = select(Measurement).order_by(Measurement.date)
        if user_id is not None:
            stmt = stmt.where(Measurement.user_id == user_id)
        results = session.exec(stmt).all()
        return results

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{h}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, h = password_hash.split(":", 1)
    except ValueError:
        return False
    calc = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return calc == h

def compute_weekly_changes(measurements):
    if not measurements or len(measurements) < 2:
        return []
    df = pd.DataFrame([{"date": m.date, "weight": m.weight_kg} for m in measurements])
    df = df.sort_values("date")
    df["date"] = pd.to_datetime(df["date"])
    df["delta_days"] = df["date"].diff().dt.days
    df["delta_weight"] = df["weight"].diff()
    df = df.dropna()
    df = df[df["delta_days"] > 0]
    df["kg_per_week"] = df["delta_weight"] / df["delta_days"] * 7
    weekly = df[["date", "kg_per_week"]].copy()
    weekly["kg_per_week"] = weekly["kg_per_week"].round(3)
    return weekly.to_dict(orient="records")

def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Response(buf.read(), media_type="image/png")

def filter_by_periods(measurements, filters_str: str | None):
    if not filters_str:
        return measurements
    tokens = [t.strip() for t in filters_str.split(",") if t.strip()]
    if not tokens:
        return measurements
    res = []
    for m in measurements:
        d = m.date
        ok = False
        for t in tokens:
            if len(t) == 4 and t.isdigit():
                if d.year == int(t):
                    ok = True
            elif len(t) == 7 and t[4] == "-" and t[:4].isdigit() and t[5:7].isdigit():
                y = int(t[:4])
                mo = int(t[5:7])
                if d.year == y and d.month == mo:
                    ok = True
            elif len(t) == 6 and t[:4].isdigit() and t[4] == "Q" and t[5] in "1234":
                y = int(t[:4])
                q = int(t[5])
                start = (q - 1) * 3 + 1
                end = start + 2
                if d.year == y and start <= d.month <= end:
                    ok = True
            elif len(t) == 6 and t[:4].isdigit() and t[4] == "H" and t[5] in "12":
                y = int(t[:4])
                h = int(t[5])
                start = 1 if h == 1 else 7
                end = 6 if h == 1 else 12
                if d.year == y and start <= d.month <= end:
                    ok = True
            if ok:
                break
        if ok:
            res.append(m)
    return res

def is_truthy(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "on")

def fetch_health_fact() -> str:
    import requests
    from bs4 import BeautifulSoup
    sources = [
        "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
        "https://www.nhs.uk/live-well/eat-well/",
        "https://www.cdc.gov/healthyweight/healthy_eating/index.html",
        "https://www.hsph.harvard.edu/nutritionsource/healthy-eating-plate/",
        "https://www.who.int/news-room/articles-detail/healthy-diet",
    ]
    tips = []
    for url in sources:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "WeightTracker/1.0"})
            html = r.text
            soup = BeautifulSoup(html, "html.parser")
            items = [el.get_text(" ", strip=True) for el in soup.select("p, li")]
            for t in items:
                t = re.sub(r"\s+", " ", t)
                if len(t) < 40:
                    continue
                sentences = re.split(r"(?<=[.!?])\s+", t)
                for s in sentences:
                    s = s.strip()
                    if not s or len(s) < 60 or len(s) > 240:
                        continue
                    wc = len(s.split())
                    if wc < 12 or wc > 40:
                        continue
                    if ":" in s or "•" in s or "|" in s:
                        continue
                    if not s[-1] in ".!?":
                        continue
                    sl = s.lower()
                    kw = [
                        "diet","healthy","vegetable","fruit","whole","grain","fiber","salt","sugar",
                        "protein","fat","water","hydrate","portion","calorie","nuts","seeds","legumes"
                    ]
                    if not any(k in sl for k in kw):
                        continue
                    tips.append(s)
            if tips:
                break
        except Exception:
            continue
    if not tips:
        tips = [
            "Jedz dużo warzyw, owoców i pełnoziarnistych produktów.",
            "Wybieraj chude źródła białka i zdrowe tłuszcze.",
            "Ogranicz cukry dodane i wysoko przetworzone produkty.",
            "Pij wodę i jedz regularnie, dbając o porcje.",
            "Włącz do diety strączki, orzechy i nasiona.",
            "Zmniejsz spożycie soli; zamieniaj ją na zioła i przyprawy.",
            "Wybieraj produkty z wysoką zawartością błonnika dla sytości.",
            "Planuj posiłki z wyprzedzeniem, aby jeść bardziej świadomie.",
            "Uważne jedzenie pomaga kontrolować porcje i kalorie.",
            "Zadbaj o nawodnienie — woda przed posiłkiem może zmniejszyć łaknienie.",
        ]
    return random.choice(tips)

def translate_to_pl(text: str) -> str:
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target="pl").translate(text)
    except Exception:
        return text

 

 

 

 

 

 

 

 

def search_recipe_links(query: str) -> list[str]:
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, urlparse, parse_qs, unquote
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    r = requests.get(url, params=params, timeout=8, headers={"User-Agent": "WeightTracker/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    def normalize(href: str | None) -> str | None:
        if not href:
            return None
        if href.startswith("//"):
            href = "https:" + href
        if href.startswith("/"):
            href = urljoin("https://duckduckgo.com", href)
        try:
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            if "uddg" in qs and qs["uddg"]:
                return unquote(qs["uddg"][0])
        except Exception:
            pass
        return href
    for a in soup.select("a.result__a"):
        href = normalize(a.get("href"))
        if href:
            links.append(href)
        if len(links) >= 10:
            break
    return links

def fetch_recipe_details(url: str) -> dict:
    import requests
    from bs4 import BeautifulSoup
    r = requests.get(url, timeout=8, headers={"User-Agent": "WeightTracker/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else url
    text = soup.get_text(" ", strip=True).lower()
    kcal = None
    m = re.search(r"(\d{2,4})\s?kcal", text)
    if not m:
        m = re.search(r"calories\s*(\d{2,4})", text)
    if m:
        try:
            kcal = int(m.group(1))
        except Exception:
            kcal = None
    return {"title": title, "url": url, "kcal": kcal, "text": text}

def pick_recipe(ingredients: list[str]) -> dict | None:
    q = "przepis " + " ".join(ingredients)
    links = search_recipe_links(q)
    for link in links:
        d = fetch_recipe_details(link)
        ok = True
        for ing in ingredients:
            token = ing.strip().lower()
            if token and token not in d["text"]:
                ok = False
                break
        if ok:
            return d
    return None

 

 


 


 

 


 


 

 

