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
    t = text.lower().replace(",", ".")
    kcal_100g = None
    m100 = (
        re.search(r"(?:na|per|/)\s*100\s*g[^\n]*?[:=]?\s*(\d+(?:\.\d+)?)\s*kcal", t)
        or re.search(r"100\s*g[^\n]*?(?:kcal|kilocalories)[^\n]*?[:=]?\s*(\d+(?:\.\d+)?)", t)
        or re.search(r"kcal\s*/\s*100\s*g\s*[:=]?\s*(\d+(?:\.\d+)?)", t)
    )
    if m100:
        try:
            kcal_100g = float(m100.group(1))
        except Exception:
            kcal_100g = None
    return {"kcal_100g": kcal_100g}

def _fallback_search_kcal(query: str, max_results: int) -> List[Dict]:
    import requests
    from bs4 import BeautifulSoup
    from app.services.recipes import search_recipe_links
    results: List[Dict] = []
    queries = [
        f"kcal {query} 100 g",
        f"kalorie {query} 100 g",
        f"{query} kalorie na 100 g",
        f"{query} calories per 100 g",
        f"{query} kcal / 100 g",
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
            if ex["kcal_100g"] is not None:
                results.append({
                    "name": title,
                    "kcal_100g": ex["kcal_100g"],
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
            item = {
                "name": name,
                "kcal_100g": kcal_100g,
                "source": p.get("url") or p.get("id") or "",
            }
            if item["kcal_100g"] is not None:
                results.append(item)
            if len(results) >= max_results:
                break
    except Exception:
        results = []
    if results:
        return results
    return _fallback_search_kcal(query, max_results)
