# Běh 4 – Sonnet 5.5 (úsilí medium): daně – účty, modely, data (bez výpočtu)

```
Přečti CLAUDE.md, předávku běhu 3 a v docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md jen „Přednosti“, oddíl 1 (D1–D14),
9.2 C0 a C1, 9.3 C1 a C2, a z oddílu 8 jen G1 (role a účty FVOCI).
Větev ukol/ZJ-07-dane-a-tridy. Schváleno; návrhy nespuštěné – převezmi, uprav, otestuj, odchylky do Výsledku ZJ-07.
ROZSAH: (1) šablona a migrace investra_chart_fund: všechny nové účty z 9.3 C1 (ty, které už založil běh 3, jen zkontroluj) a z G1;
nové role revaluation_reserve a revaluation_reserve_tax v investra_entity; mapování ČNB rolí podle G1 (OVĚŘ docs/cnb).
(2) Modely z 9.3 C2: investra.tax.rule, investra.tax.rule.version, investra.fund.tax.exception (včetně pravidla D10: rozvahový účet
smí mít i splatné pravidlo), pole fondu (tax_rule_id, nosič tax_fee_rule_id, tax_base_step, action_add_common_tax_exceptions vč. D11),
tax_rule_id na opravě (investra.valuation.external), data pravidel (Daň 21 %, Daň ZIF 5 %, Samostatný základ 15 %, Mimo základ daně,
Odložená FVOCI 21 % a 5 %), oprávnění, kontroly z 9.2 C1. Nabídku Nastavení › Daně › Daňová pravidla založ jako menuitem + akci
s výchozími pohledy (bez vlastních formulářů – ty dělá Copilot).
NEDĚLEJ: výpočet daně (engine, _tax_item, _book_tax), migraci sazeb investra_nav (C5), FVOCI ocenění – to je běh 5 (Opus).
Testy modelů (kontroly, unikátnost, D10, tlačítko běžných výjimek) v investra_nav/tests/test_tax_rules_models.py; testy investra_entity+,
investra_chart_fund+, investra_nav+, investra_cnb+; snímek 35/39 = beze změny (výpočet se ještě nemění). Commit, push,
předávka …-davka-beh-4.md se seznamem modelů a polí pro Copilota. Na konci relace mi napiš krátce za běhy 2–4: commity, odchylky, testy, snímek.
```
