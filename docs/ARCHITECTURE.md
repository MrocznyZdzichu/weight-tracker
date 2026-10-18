# Architektura

Aplikacja serwerowa FastAPI: app/main.py montuje trasy i middleware sesji. HTML renderuje Jinja2 przez app/core/templates.py; formularze po zapisie przekierowuj? kodem 303. Brak oddzielnego frontendu i bundlera.

app/models.py opisuje User, Measurement, Meal i SavedDay. SQLite znajduje si? pod DB_PATH. core/db.py tworzy tabele i wykonuje idempotentne migracje addytywne oraz indeksy (user_id, date). Stare pomiary bez user_id nie s? automatycznie przypisywane do kont.

Sesja zawiera uid. Has?a nowe i migrowane przy logowaniu u?ywaj? scrypt; wcze?niejsze SHA-256 pozostaj? czytelne do pierwszego poprawnego logowania. SESSION_SECRET musi pozosta? sta?y mi?dzy restartami, inaczej sesje wygasn?.

meal_modes.py normalizuje bia?e znaki i wielko?? liter, wybiera najcz?stsz? warto?? kcal (remis: mniejsza warto??). Podpowiedzi oblicza strona /meals na podstawie bie??cych danych u?ytkownika. meal_history.py pobiera zapisane dni i posi?ki w dw?ch zapytaniach. SavedDay oznacza dzie? zapisany; historia liczy sumy z aktualnych posi?k?w, nie ze snapshotu total_kcal.

Statystyki posi?k?w agreguje pandas; Plotly renderuje wykresy interaktywne, matplotlib pozosta?e PNG. Zewn?trzne wyszukiwanie kalorii i przepis?w u?ywa requests i scrapingu; odpowiedzi us?ug nie s? gwarantowane.
