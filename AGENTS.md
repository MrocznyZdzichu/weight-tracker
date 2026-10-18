# Praca agent?w w repozytorium

Czytaj README.md, docs/ARCHITECTURE.md i docs/HANDOFF.md przed zmianami. Sprawd? git status i zachowuj zastane zmiany u?ytkownika. Nie dodawaj data/, sekret?w ani baz do Git lub obrazu Docker.

## Implementacja
- Python 3.11, FastAPI, SQLModel 0.0.8 (Pydantic v1), Jinja2. Nie stosuj API Pydantic v2 bez migracji zale?no?ci.
- Trasy obs?uguj? HTTP; wsp??dzielon? logik? umieszczaj w app/services. Zapytania zawsze ograniczaj przez user_id z sesji; nigdy z formularza.
- Waliduj parametry przed agregacj? i renderowaniem. Zachowuj kategorie przy kopiowaniu posi?k?w i deterministyczny remis autouzupe?niania (mniejsze kcal).
- Nie przechowuj historii ani podpowiedzi w podpisanym ciasteczku sesji. Ciasteczko nie jest szyfrowane.
- Unikaj zapyta? w p?tli. Dla historii u?ywaj meal_history.py; zachowaj zgodno?? filtrowania z wykresami.
- Migracje SQLite musz? by? idempotentne i zachowywa? dane. Testuj baz? z maina, nie tylko pust?.
- Wykresy matplotlib generuj pod PLOT_LOCK i zamykaj przez render_png.
- Testy u?ywaj? wy??cznie tymczasowej bazy. Nie montuj produkcyjnego data/ do test?w.

## Weryfikacja i przekazanie
Uruchom python -m unittest discover -s tests -v po instalacji requirements-dev.txt na Pythonie 3.11. Zbuduj obraz Docker, sprawd? git diff --check. Nowe zachowania sprawdzaj testami regresji, bez testowania szczeg???w implementacji poza istotnymi gwarancjami wydajno?ci.

Przed PR uaktualnij docs/HANDOFF.md: zakres, wyniki test?w, ryzyka, nast?pny krok. Opis PR podaje problem, efekt i walidacj?. Nie deklaruj wykonanych test?w lub wdro?enia bez dowod?w. Produkcj? wdra?aj tylko w autoryzowanym zakresie, po backupie SQLite i z obrazem do rollbacku; patrz docs/OPERATIONS.md.
