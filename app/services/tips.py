import random
import re

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
            "Wybieraj produkty z wysoką zawartością błonnika.",
        ]
    return random.choice(tips)

def translate_to_pl(text: str) -> str:
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target="pl").translate(text)
    except Exception:
        return text
