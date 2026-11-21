# Dávka ZJ-24 bod 15 · ZJ-25 Ocenění · ZJ-27 Zařazení z obchodu · ZJ-26 Vzhled – přehled (2026-11-20)

Cíl: celé provést **Sonnet 5.5, úsilí medium, v jedné relaci**, s co nejmenším počtem zásahů Martina.
Návrh udělal poradce předem (technické plány níže), agent jen programuje, testuje a hlásí.
Pořadí: ZJ-27 před ZJ-26, aby se vzhled dělal jen jednou, na konečných polích.

## Interakce Martina
0. **Schválení plánů** (s poradcem, před spuštěním): `plan-ZJ-25-technicky.md` (schváleno 2026-11-20), K6 (schváleno),
   `plan-ZJ-27-technicky.md` (do hlavičky „Schválil Martin RRRR-MM-DD“).
1. **Příprava:** soubory dávky (8 souborů složky bez promptů + zadání + prompt-pokracovani.md) přilož do chatu spolu s promptem; agent je uloží
   do `docs/ukoly/podklady/davka-ZJ-24-27/`.
2. **Spusť** relaci Sonnet (medium) s promptem z `prompt-jedna-relace.md`. Agent udělá části 1–2, pak napíše, ať přepneš
   úsilí na **high** – přepni v aplikaci a napiš „pokračuj“; části 3–4 doběhnou samy.
3. Po zprávě agenta: zkontroluj v prohlížeči podle jeho seznamu (případně poradce zkontroluje diff), napiš **„slučuj“**.

## Části (větve na sebe navazují, nic se neslučuje do konce)
| Část | Co | Větev (z) | Podklad |
|---|---|---|---|
| 1 | povýšení a testy ZJ-24, bod 15, hláška nulového kapitálu | `ukol/ZJ-24-bod-15` (z `ukol/ZJ-24-hlasky-a-sazby`) | `plan-ZJ-24-bod-15.md` |
| 2 | ZJ-25 rozpad tříd, kontroly, balíček, texty, Portfolio | `ukol/ZJ-25-oceneni-kontroly-rozpad` (z části 1) | `plan-ZJ-25-technicky.md`, `podklad-katalog-kontrol.md` |
| 3 | ZJ-27 zařazení z obchodu, způsob ocenění na nástroji, role z profilů, cena v %, místo obchodu | `ukol/ZJ-27-zarazeni-z-obchodu` (z části 2) | `plan-ZJ-27-technicky.md`, `podklad-zj27-fakta.md` |
| 4 | ZJ-26 jednotný vzhled (podle polí po ZJ-27) | `ukol/ZJ-26-vzhled` (z části 3) | `podklad-zj26-obrazovky.md` |
| slučuj | merge všech větví do main | main | – |

## Kdy agent zastaví (jinak pokračuje sám)
Testy neprojdou a oprava není zřejmá do 2 pokusů; snímek 35/39 se změní; kontrola `class_split` nesedí na referenčních scénářích;
kód odporuje plánu ve výpočtu nebo účtování. Pak napíše, co zjistil – jen tehdy přepni relaci na úsilí high nebo předej poradci.

## Záloha
Když relace dojde nebo se zasekne: nová relace s `prompt-pokracovani.md` (čte jen poslední předávku).
