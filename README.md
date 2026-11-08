# Maty Agent

Agent pro zpracování rezervací z Bookio notifikací doručených do Seznam Emailu.

## 🚀 Rychlé spuštění (Windows)

1. Nainstaluj Python 3.10 nebo novější.
2. Stáhni repozitář a otevři PowerShell v jeho složce.
3. Vytvoř lokální konfigurační soubor:

```powershell
Copy-Item .env.example .env
```

4. Otevři `.env` a doplň přihlašovací údaje k e-mailové schránce. Výchozí nastavení používá IMAP/SMTP Seznamu. Pokud poskytovatel vyžaduje aplikační heslo, použij ho místo běžného hesla.
5. Spusť agenta:

```powershell
python -m app.main
```

Jeden průchod schránkou bez čekání na další cyklus:

```powershell
python -m app.main --once
```

Projekt používá standardní knihovnu Pythonu; nejsou potřeba externí balíčky ani `pip install`. Pokud příkaz `python` ve Windows nefunguje, zkus `py -3`.

## Co agent dělá

- připojí se k e-mailu přes IMAP,
- vyhledá Bookio notifikace,
- rozpozná novou, změněnou a zrušenou rezervaci,
- uloží události do lokální SQLite databáze,
- deduplikuje zprávy podle Message-ID,
- každých 48 hodin vytvoří report,
- volitelně odešle report přes SMTP na zvolený e-mail.

Reporty se ukládají do složky `reports/`; databáze je ve výchozím nastavení `data/maty_agent.db`.

## Konfigurace

Všechny hodnoty se nastavují v lokálním souboru `.env`. Výchozí proměnné a jejich popis najdeš v [`.env.example`](.env.example). Mezi důležité patří:

- `EMAIL_USER`, `EMAIL_PASSWORD` — přístup k e-mailové schránce,
- `IMAP_HOST`, `IMAP_PORT` — příjem zpráv,
- `SMTP_HOST`, `SMTP_PORT` — odesílání reportů,
- `REPORT_SEND_EMAIL` — zapnutí nebo vypnutí e-mailového reportu,
- `REPORT_TO_EMAIL` — volitelný příjemce reportu,
- `POLL_SECONDS` — interval kontroly schránky.

## Bezpečnost

Přihlašovací údaje patří pouze do lokálního `.env`. Tento soubor nesmí být commitnutý do Gitu. Doporučené je použít samostatné aplikační heslo, pokud ho poskytovatel účtu podporuje. Před zapnutím automatického odesílání ověř adresu příjemce reportů.

## Report

Report obsahuje počet nových rezervací, změn a zrušení a dostupné údaje o zákazníkovi, službě, datu/času a kontaktu. Přesnost parseru závisí na podobě skutečných Bookio e-mailových šablon.

## Vývoj a testy

```powershell
python -m pytest -q
```
