# ОЗ ВС РФ workbook: what it is and how we use it (internal, 06.10.2026)

`~/Downloads/ОЗ ВС РФ.xlsx` is an **internal finder only**. Per the user's rule (05.10.2026) it is never cited, never catalogued in `data/sources/`, and never copied into the repo. This note records its shape and what it showed. It reproduces none of its rows. Nothing here is a fact about a unit: a parent, a в/ч or a marking from the workbook is a lead until a document we may cite states it.

## What it is

A compilation of Russian army **identification markings** («ОЗ», опознавательные знаки: the symbols painted on vehicles) and the unit hierarchy they belong to. Three sheets:

- **Лист1, markings catalogue (260 rows).** Columns: status, an analyst comment (in English), regiment, brigade or division, army, military district, a drawn sample, up to three markings with a text description each, and a source link. 122 rows are marked «внесен» (entered) and 137 «в работе» (in progress). 550 embedded drawings. The unit chain is only partly filled: the brigade or division on 155 rows, the army on 136, the regiment on 68; the district is unknown («?») on 56. 154 rows carry a source link, mostly Telegram posts (106), then VK (18) and X/Twitter (22). The descriptions are plain geometry («точка в квадрате», «7 в квадрате», «ромб»): 115 distinct phrasings.
- **Лист2, hierarchy with markings (244 rows).** District or branch → army → division or brigade → regiment → battalion, with the marking of each level. 25 armies, 132 divisions and brigades, 111 distinct regiments, 7 districts or branches (Western 86 rows, Southern 59, Central 39, Eastern 31, airborne and others). Markings are filled for 14 armies, 70 divisions or brigades and 55 regiments; battalions are nearly empty (6). 198 drawings.
- **полезные ссылки (22 rows).** The compiler's own tools: warspotting, OWL maps, a Telegram feed, the Defence Ministry's multimedia site.

## How reliable it is

A hand-built crowd compilation: unknown compiler, sources that are mostly Telegram posts, half the catalogue still «in progress», and the compiler's own comments flag decorative or non-tactical marks. It covers about 240 numbered units, a small share of the army. Use it to find a lead and to check a collision; never as the statement of a fact.

## What it showed about our units (06.10.2026)

Of the 20 numbered records in `military_units.json`, the workbook lists at least one entry with the same number for 15; the two 237th regiments, the 76th division, the 91st control brigade and the 114th brigade are all there.

- **The two 237ths are separate in the workbook too** (a tank regiment in a motor-rifle division of the 20th army; an air-assault regiment in an airborne division). That agrees with the registry and with what the user said; the parents stay `lead` until a citable document states them.
- **Numbers shared by two or more units are common: 46 numbers, out of about 240.** That is the evidence for the registry rule that a number alone never identifies a unit.
- **Collisions to watch in our records** (same number, other types or parents): **114** has a motor-rifle regiment in another division and army besides the brigade, so the two 114 records need their parent and type stated by a document before either is resolved by a bare mention; **9** has an artillery brigade, a control brigade and a motor-rifle brigade; **18**, **20** and **2** each have several. **76** and **91** have no collision in the workbook.
- The workbook has **no 114th reconnaissance regiment**, the type of one of our records. That is a prompt to re-check that record's type against its source, not a finding.

## How to use it

1. When a post names a unit by number, look it up in `unit_lookup.py` first; consult the workbook only to see what other units share the number, then find a citable source (a decree, a letter, the post's own wording) for the parent.
2. A marking seen in a photo (a vehicle in a handover or field picture) can be looked up in the workbook as a lead for which unit it might be. The lead goes into a media record's note as «unverified», never into `shows`, and a face or a marking is never used to name a unit without a source.
3. Do not add it to `data/sources/`, `MANIFEST.md`, `sources.json` or any citation. Do not paste its rows or drawings into notes, exhibits or packets.
