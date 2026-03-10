# Weight Tracker

Lekka aplikacja FastAPI do śledzenia masy ciała i kalorii, z zaawansowanymi statystykami, importem/eksportem danych, wyszukiwarką przepisów i ciekawostkami o zdrowym odżywianiu.

## Główne Funkcjonalności

- **Uwierzytelnianie**: Rejestracja i logowanie użytkowników z systemem sesji.
- **Pomiary Masy Ciała**:
  - Dodawanie, edycja i usuwanie pomiarów.
  - Historia pomiarów z filtrowaniem (rok, kwartał, miesiąc).
  - Import i eksport danych w formacie CSV.
- **Śledzenie Posiłków i Kalorii**:
  - Rejestrowanie dziennych posiłków z nazwą i kalorycznością.
  - Ustawianie i śledzenie dziennego celu kalorycznego.
  - Historia spożytych posiłków z opcją wyszukiwania.
- **Zaawansowane Statystyki**:
  - **Pomiary Masy**: Wykres trendu, histogram tygodniowych zmian.
  - **Posiłki**: Interaktywna analiza posiłków z widokiem tabelarycznym i graficznym (wykresy słupkowe, kołowe, pudełkowe).
    - Filtrowanie po zakresie dat.
    - Dowolne kombinacje funkcji agregacji (średnia, mediana, suma, liczba, min, max, odchylenie std.).
    - Sortowanie wyników wg wybranego kryterium.
    - Wybór Top N posiłków do analizy.
- **Narzędzia Dodatkowe**:
  - **Wyszukiwarka Kalorii**: Znajdowanie informacji o kaloryczności produktów (korzysta z OpenFoodFacts API).
  - **Wyszukiwarka Przepisów**: Wyszukiwanie przepisów w internecie na podstawie podanych składników.
  - **Porady**: Wyświetlanie losowych ciekawostek o zdrowym odżywianiu.

## Deployment

### Środowisko Produkcyjne

- Budowanie i uruchomienie kontenera Docker:
  ```bash
  docker compose build
  docker compose up -d
  ```
- Alternatywnie, skrypt `rebuild.bat` (dla Windows) automatyzuje ten proces.
- **Port**: Aplikacja jest dostępna na porcie `8200` (zgodnie z `docker-compose.yml`).
- **Dane**: Katalog `data/` jest montowany jako wolumen, przechowując bazę danych SQLite.

### Środowisko Testowe

- Aby uruchomić aplikację w trybie testowym, należy ustawić zmienną środowiskową `ENV=test`.
- W trybie testowym, jeśli testowa baza danych nie istnieje, aplikacja automatycznie skopiuje produkcyjną bazę danych, aby zapewnić spójność danych do testów.
  ```bash
  # Przykład uruchomienia w trybie testowym
  ENV=test docker compose up
  ```

## Struktura Projektu

- `app/core` — Konfiguracja, połączenie z bazą danych, obsługa szablonów i bezpieczeństwo.
- `app/services` — Logika biznesowa (obliczenia statystyczne, web scraping, operacje na danych).
- `app/routes` — Endpointy API i logika żądań/odpowiedzi FastAPI.
- `app.templates` — Szablony HTML (Jinja2).
- `data/` — Katalog na dane runtime (np. baza SQLite). Tworzony automatycznie, ignorowany przez Git.

## Licencja

Projekt na użytek wewnętrzny. Można dowolnie modyfikować i rozwijać.
