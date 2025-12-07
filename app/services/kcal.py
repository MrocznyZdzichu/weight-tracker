from typing import List, Dict
import re

def _parse_grams(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"(\d+(?:[\.,]\d+)?)\s*g", s.lower())
    if not m:
        return None
    try:
        val = m.group(1).replace(",", ".")
        return float(val)
    except Exception:
        return None

def _kcal_from_kj(kj: float | None) -> float | None:
    if kj is None:
        return None
    try:
        return round(float(kj) / 4.184, 1)
    except Exception:
        return None

def _extract_kcal(text: str) -> Dict:
    t = text.lower()
    kcal_100g = None
    kcal_serv = None
    serving_size = None
    p1 = re.search(r"(?:per|na)\s*100\s*g[^\n]{0,40}?(\d{2,4})\s*kcal", t)
    if not p1:
        p1 = re.search(r"(\d{2,4})\s*kcal[^\n]{0,40}?(?:per|na)\s*100\s*g", t)
    if p1:
        try:
            kcal_100g = float(p1.group(1))
        except Exception:
            kcal_100g = None
    p2 = re.search(r"(\d{2,4})\s*kcal[^\n]{0,40}?(?:per|na)\s*(serving|porcja|sztuka|piece)", t)
    if p2:
        try:
            kcal_serv = float(p2.group(1))
            serving_size = p2.group(2)
        except Exception:
            kcal_serv = None
    if kcal_serv is None:
        mgs = re.search(r"(porcja|serving|sztuka|baton|piece)[^\n]{0,30}?(\d+(?:[\.,]\d+)?)\s*g", t)
        if mgs and kcal_100g is not None:
            try:
                grams = float(mgs.group(2).replace(",", "."))
                kcal_serv = round(kcal_100g * grams / 100.0, 1)
                serving_size = f"{grams} g"
            except Exception:
                pass
    return {"kcal_100g": kcal_100g, "kcal_serv": kcal_serv, "serving_size": serving_size}

def _fallback_search_kcal(query: str, max_results: int) -> List[Dict]:
    import requests
    from bs4 import BeautifulSoup
    from app.services.recipes import search_recipe_links
    results: List[Dict] = []
    queries = [
        f"kcal {query}",
        f"kalorie {query}",
        f"{query} kalorie 100 g",
        f"{query} calories 100 g",
        f"{query} kcal per serving",
    ]
    seen = set()
    links: List[str] = []
    for q in queries:
        for l in search_recipe_links(q, limit=20):
            if l not in seen:
                seen.add(l)
                links.append(l)
    for url in links:
        if len(results) >= max_results:
            break
        try:
            r = requests.get(url, timeout=6, headers={"User-Agent": "WeightTracker/1.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else url
            text = soup.get_text(" ", strip=True)
            ex = _extract_kcal(text)
            if ex["kcal_100g"] is not None or ex["kcal_serv"] is not None:
                results.append({
                    "name": title,
                    "kcal_100g": ex["kcal_100g"],
                    "kcal_per_piece": ex["kcal_serv"],
                    "serving_size": ex["serving_size"],
                    "source": url,
                })
        except Exception:
            continue
    return results

def find_kcal_info(query: str, max_results: int = 5) -> List[Dict]:
    import requests
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": max_results,
    }
    results: List[Dict] = []
    try:
        r = requests.get(url, params=params, timeout=5, headers={"User-Agent": "WeightTracker/1.0"})
        data = r.json()
        products = data.get("products") or []
        for p in products:
            name = p.get("product_name") or p.get("product_name_pl") or p.get("brands") or "Produkt"
            nutr = p.get("nutriments") or {}
            kcal_100g = nutr.get("energy-kcal_100g")
            if kcal_100g is None:
                kcal_100g = _kcal_from_kj(nutr.get("energy_100g"))
            kcal_serv = nutr.get("energy-kcal_serving")
            if kcal_serv is None:
                grams = _parse_grams(p.get("serving_size"))
                if grams and kcal_100g is not None:
                    kcal_serv = round(kcal_100g * grams / 100.0, 1)
            item = {
                "name": name,
                "kcal_100g": kcal_100g,
                "kcal_per_piece": kcal_serv,
                "serving_size": p.get("serving_size"),
                "source": p.get("url") or p.get("id") or "",
            }
            if item["kcal_100g"] is not None or item["kcal_per_piece"] is not None:
                results.append(item)
            if len(results) >= max_results:
                break
    except Exception:
        results = []
    if results:
        return results
    return _fallback_search_kcal(query, max_results)
