# Maty Agent

Agent pro zpracování rezervací z Bookio notifikací doručených do Seznam Emailu.

## Co dělá

- připojí se k e-mailu přes IMAP,
- vyhledá Bookio notifikace,
- rozpozná novou, změněnou a zrušenou rezervaci,
- uloží události do lokální SQLite databáze,
- nespolehne se na stav přečteno/nepřečteno a zprávy deduplikuje podle Message-ID,
- každých 48 hodin vytvoří report,
- volitelně odešle report přes SMTP na zvolený e-mail.

## Rychlý start

1. Zkopíruj `.env.example` jako `.env`.
2. Doplň e-mail a heslo pro IMAP/SMTP.
3. Spusť:

```powershell
python -m app.main
```

Jednorázové načtení bez nekonečné smyčky:

```powershell
python -m app.main --once
```

## Bezpečnost

Přihlašovací údaje patří pouze do lokálního `.env`. Soubor je ignorovaný Gitem. Doporučené je použít samostatné heslo pro aplikaci, pokud ho poskytovatel účtu podporuje.

## Report

Report obsahuje:

- počet nových rezervací,
- počet změn,
- počet zrušení,
- seznam zpracovaných Bookio událostí,
- zákazníka, službu, datum/čas a kontakt, pokud je lze ze zprávy spolehlivě vyčíst.

Přesný parser lze doladit podle reálné Bookio šablony bez změny zbytku architektury.
