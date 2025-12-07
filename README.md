# Weight Tracker

Lekka aplikacja FastAPI do śledzenia masy ciała, statystyk, importu/eksportu CSV, ciekawostek o zdrowym odżywianiu oraz wyszukiwania przepisów po składnikach.

## Funkcje
- Rejestracja i logowanie użytkowników
- Dodawanie, edycja i usuwanie pomiarów
- Historia i statystyki (wykres trendu, histogram tygodniowych zmian)
- Import/Export CSV
- Porady: jedna losowa ciekawostka (z automatycznym tłumaczeniem na polski)
- Przepisy: wyszukiwanie po składnikach, wiele losowych wyników, link i kcal

## Docker
- Budowanie i uruchomienie:
  - `docker compose build`
  - `docker compose up -d`
- Alternatywnie: `rebuild.bat` (Windows) uruchamia sekwencję build + up
- Port: `8200` (mapowany w `docker-compose.yml`)
- Dane: katalog `data/` montowany do kontenera (`volumes`)

## Struktura katalogów
- `app/core` — konfiguracja, baza danych, sesje, bezpieczeństwo
- `app/services` — logika domenowa (pomiar, wykresy, porady, przepisy)
- `app/routes` — endpointy FastAPI
- `app/templates` — szablony Jinja2
- `data/` — dane runtime (baza SQLite). Tworzony automatycznie, ignorowany przez Git

## Import/Export CSV
- Export: `GET /export` — pobiera plik CSV (`dd/mm/YYYY,weight`)
- Import: `GET /import` + formularz upload — akceptuje CSV o tym samym formacie

## Przepisy (losowe, wielokrotne)
- `GET /recipes` — formularz składników i liczby wyników
- `POST /recipes` — parametry:
  - `ingredients`: np. `ziemniaki, cebula, kurczak`
  - `count`: liczba wyników (1–10, domyślnie 5)
- Zwraca listę przepisów z tytułem, linkiem i (jeśli dostępne) liczbą kcal

## Wykresy
- `GET /plot` — przebieg masy (z opcjonalnym trendem: `?trend=1`)
- `GET /plot-weekly-changes` — histogram tygodniowych zmian

## Licencja
- Wewnętrzny projekt; dostosuj wg potrzeb.
