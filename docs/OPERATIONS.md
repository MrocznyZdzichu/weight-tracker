# Uruchamianie i wydania

## Lokalnie
Python 3.11: python -m venv .venv, aktywuj ?rodowisko, pip install -r requirements-dev.txt. Ustaw DB_PATH na baz? dewelopersk? i SESSION_SECRET na losowy sekret. Uruchom uvicorn app.main:app --port 8201. Testy: python -m unittest discover -s tests -v; same ustawiaj? tymczasow? baz? przed importem aplikacji.

## Docker
Produkcja: docker compose up -d --build tracker (8200). DEV: docker compose up -d --build tracker-test (8201). Zawsze wskazuj us?ug?, aby nie uruchomi? obu ?rodowisk przypadkiem. ENV=test nie kopiuje ju? bazy produkcyjnej; testowa baza startuje pusta. Skrypty rebuild*.bat zatrzymuj? wdro?enie po b??dzie budowania.

Dane montowane s? z ./data. Obraz nie zawiera bazy. Ustaw SESSION_SECRET w ?rodowisku us?ugi; dotychczasowy fallback dev-secret wymaga wymiany przed udost?pnieniem aplikacji publicznie. Obecna konfiguracja jest lokalna, HTTP; HTTPS wymaga reverse proxy i konfiguracji secure cookie.

## Wdro?enie i rollback
1. Przejrzyj PR do main obejmuj?cy funkcje DEV, testy i dokumentacj?. Zweryfikuj CI i testy obrazu.
2. Zapisz identyfikator aktualnego obrazu i otaguj go jako tracker:rollback. Zr?b sp?jny backup SQLite przez sqlite3.Connection.backup (nie kopiuj aktywnego pliku zwyk?ym copy).
3. Zbuduj nowy obraz, uruchom wy??cznie tracker, sprawd? GET /, /login oraz zalogowany scenariusz kategorii, kopiowania i podpowiedzi. Nie zmieniaj danych istniej?cych u?ytkownik?w w smoke testach.
4. W razie awarii przywr?? poprzedni obraz i odtw?rz us?ug? z --no-build. Migracje tego wydania s? addytywne; nie odtwarzaj backupu po nowych zapisach bez analizy utraty danych.

Nie u?ywaj docker compose down -v. Nie wypisuj sekret?w przez docker inspect lub compose config do log?w.
