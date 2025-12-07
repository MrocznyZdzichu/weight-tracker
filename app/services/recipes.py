from urllib.parse import urljoin, urlparse, parse_qs, unquote
import re
import random

def search_recipe_links(query: str, limit: int = 20) -> list[str]:
    import requests
    from bs4 import BeautifulSoup
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    r = requests.get(url, params=params, timeout=8, headers={"User-Agent": "WeightTracker/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    links: list[str] = []
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
        if len(links) >= limit:
            break
    random.shuffle(links)
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
        m = re.search(r"kalorie\s*(\d{2,4})", text)
    if not m:
        m = re.search(r"calories\s*(\d{2,4})", text)
    if m:
        try:
            kcal = int(m.group(1))
        except Exception:
            kcal = None
    return {"title": title, "url": url, "kcal": kcal, "text": text}

def find_recipes(ingredients: list[str], max_results: int = 5) -> list[dict]:
    queries = [
        "przepis " + " ".join(ingredients),
        "przepis na " + " ".join(ingredients),
        "recipe " + " ".join(ingredients),
        "danie " + " ".join(ingredients),
    ]
    seen = set()
    links: list[str] = []
    for q in queries:
        for l in search_recipe_links(q, limit=20):
            if l not in seen:
                seen.add(l)
                links.append(l)
    random.shuffle(links)
    results: list[dict] = []
    for link in links:
        try:
            d = fetch_recipe_details(link)
        except Exception:
            continue
        ok = True
        for ing in ingredients:
            token = ing.strip().lower()
            if token and token not in d["text"]:
                ok = False
                break
        if ok:
            titles = {r["title"] for r in results}
            if d["title"] in titles:
                continue
            results.append(d)
            if len(results) >= max_results:
                break
    return results
