# Referenční model společného dopočtu (ZJ-12, příloha A)

Nezávislý model společného dopočtu úplat, odměny a daně, ověřený 18. 11. 2026: 12 013 kontrol prošlo, 0 selhalo.
Spuštění: `powershell -NoProfile -ExecutionPolicy Bypass -File testy.ps1`; na macOS přes `pwsh`, nebo rovnou převést do Pythonu (krok 1 ZJ-12).
Zjednodušení: jedno období, měřítko kapitál třídy, bez příjemců úplat. F1 = úplata fondu, F2 = úplata třídy A, P = odměna třídy A, T = daň.
Ve zdrojovém kódu jsou stavy S0–S3 = kroky 1–4.

## Výstup posledního běhu

```
Oprav s pevnou částkou ověřeno: 1152 (2 scénáře × 144 kombinací × 4 pravidla)
Kombinací: 720 (5 scénářů × 4 × 4 × 3 × 3), ze shody s dnešním pořadím ověřeno: 40
Nejvíc kroků dopočtu: 33
Největší relativní zbytek po dopočtu: 3.30546048008715E-13
Kontrol prošlo: 12013, selhalo: 0
```

## Očekávané hodnoty

| Případ | Nastavení | Očekávané |
|---|---|---|
| C1 | jedna třída 1 000 000, úplaty 1 % a 0,1 %, obě po kroku 2 | 9 891,1968 a 989,1197 |
| C2 | totéž, 1 % po kroku 1, 0,1 % po kroku 2 | 10 000 a 989,011 |
| C3 | třída 1 000, výsledek 100, HWM 1 000, odměna 20 % po kroku 4, daň 5 % po kroku 3 | odměna 19,1919, daň 4,0404 |
| C4 | jedna třída 1 000 000, výsledek 100 000, úplata 1 % po kroku 4, daň 5 % po kroku 2 | úplata 10 846,9539, daň 4 457,6523 |
| C5 | A, B po 1 000 000, výsledek 100 000, odměna A 20 % nad HWM 1 000 000 po kroku 1, daň 5 % po kroku 3 | odměna 10 000, daň 4 500, kapitál A 1 038 000, B 1 047 500 |
| C6 | A, B, výsledek −50 000 | daň 0, daň třídy A 0 |
| C7 | A, B, výsledek 5 000, úplata A 1 % po kroku 1, daň 5 % po kroku 2 | úplata 10 025, daň 0, daň třídy A −125, B +125 |
| C8 | jedna třída 1 000 000, úplata 1 % po kroku 2, oprava −100 | vypočteno 9 900,9901, výsledek 9 800,9901, FK 990 199,0099 |
