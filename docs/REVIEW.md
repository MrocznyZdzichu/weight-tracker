# Review 2026-10-18

Zakres: kod Python, szablony i konfiguracja wydania; baza DEV 934863d wzgl?dem main 77b576b. Wydanie obejmuje r?wnie? kategorie i przebudowane statystyki obecne na DEV.

## Naprawione
- Podpowiedzi w sesji mog?y przekroczy? limit ciasteczka i pozostawa?y nieaktualne. Dane s? pobierane na stronie posi?k?w; sesja zawiera wy??cznie to?samo??.
- Historia i dwa wykresy powiela?y zapytania na ka?dy dzie?. Wsp?lny serwis wykonuje dwa zapytania, filtruje dni w SQL i zachowuje izolacj? u?ytkownik?w.
- Nieznany sort_by powodowa? KeyError; daty i warianty wykres?w mog?y ko?czy? si? 500. Parametry statystyk waliduje FastAPI, Top N ograniczono do 100, agregacje maj? poprawny fallback.
- Brak importu Response powodowa? 500 przy anonimowych ??daniach wykres?w. Naprawiono import i ochron? wykres?w historii.
- Katalog DB_PATH nie by? tworzony, migracje nie mia?y jawnej transakcji. Dodano obs?ug? katalogu, transakcj? i indeksy user/date.
- Docker kopiowa? dane u?ytkownik?w do warstw obrazu. Usuni?to kopiowanie, dodano .dockerignore.
- ENV=test kopiowa?o produkcyjn? baz? bez jawnej zgody. Testowe ?rodowisko startuje puste.
- Has?a u?ywa?y szybkiego SHA-256. Nowe has?a u?ywaj? scrypt; poprawne logowanie migruje stary hash, por?wnanie jest sta?oczasowe.
- Import CSV odczytywa? plik przed uwierzytelnieniem i bez limitu. Autoryzacja poprzedza odczyt; limit 2 MiB.

## Dalsze prace
- Pe?na ochrona CSRF formularzy, ograniczanie pr?b logowania i unikalny indeks email z obs?ug? istniej?cych duplikat?w.
- Zast?pienie domy?lnego sekretu sesji konfiguracj? produkcyjn?, secure cookie po wdro?eniu HTTPS.
- Aktualizacja starych zale?no?ci wraz z testami kompatybilno?ci; nie wykonano audytu CVE.
- Paginacja du?ych historii, bud?et czasu i ograniczenia pobierania w scraperach, pe?na walidacja pomiar?w (warto?ci dodatnie i sko?czone).

Review i testy regresji nie stanowi? pe?nego audytu bezpiecze?stwa ani testu obci??eniowego.
