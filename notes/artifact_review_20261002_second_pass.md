# Artifact review, second pass (2026-10-02)

The first pass (`notes/brief_leftovers_20261002.md`) retired six artifacts. This pass covers the eleven that were unreviewed. Local copies are in `data/sources/ARTIFACT_*.html` (ids s8951–s8960).

## Disposition

| Artifact | Outcome | Reason |
|---|---|---|
| Five Residents (21 Sep) | retired | Same five cases as the generated `docs/cases/*.html`. Hand-copied; legal form of Тримикс wrong («АО», registry says ООО); omits Покров's Ukrainian sanction. s8955. |
| Coverage Audit & Cutoff Plan (19 Sep) | retired | Dated snapshot (235 entities, 1,124 nodes) that duplicated `notes/rebuild_plan.md`. Its open tasks are carried below. s8952. |
| Demand-Side Icon Set (21 Sep) | retired | Proposal. Government-customer nodes shipped; the fund glyph was never built; the «financial / training buyer» rejection predates the programme model. s8954. |
| Supply-Demand Cycle (14 Sep) | retired | Concept canvas, superseded by the Ecosystem Model artifact. s8951. |
| Data-to-Ink Rules (21 Sep) | retired | The rule now lives in `STYLE_GUIDE.md` §5.6. s8953. |
| Roymarket design system (21 Sep) | retired at user direction ("i'd redo the design system") | Tokens, README and `bundle.css` saved in `data/sources/ARTIFACT_20260921_roymarket-design-system/` (s8957–s8960). A redo should add the v11 kinds: programme / event / group / storefront nodes and the sale, partner and membership edge colours. |
| From ЦБСТ to the Front (21 Sep) | **kept for now** | `docs/story.html` (committed, public) links it as its call to action; deleting it breaks a live page. Decision needed: repoint the link at the explorer and retire, or correct and keep. s8956 is the local copy. |
| Multi-Role Individuals | kept | `scripts/build_affiliation_matrix.py` regenerates it. Not refreshed in this pass. |
| Архангел: Claimed Components | kept | Not confirmed that the project's own stills are archived locally; the artifact embeds them. |
| Slides ×2 | kept | Both are empty decks (no slide files, no `slides` store documents). Nothing to audit. |

## Errors in "From ЦБСТ to the Front" (still published)

- ИНН 7100027464 is labelled «ООО «Овод»». The registry has it as ООО «Русская лаборатория воздушного транспорта» (`ovod`, brand Овод).
- Chain 3 says both shells are «sanctioned (EU/US)». The registry has EU entries on `ovod`; `ooo-vozdushnyy-traktat` carries US and Ukraine entries.
- The $3M howitzer claim (Овод, `s5446`, post of 05.08.2026) is a press-style claim by a named reservist unit; the artifact grades its edge «Doc».
- Тримикс is labelled «ООО» correctly there, but the node counts in the footer (1,141 nodes, 50 ties) are stale (now 1,258 nodes, 74 tie edges).

## Corrections to my own first-pass report

I said the battlefield chains were missing from the graph and that 26 military units were off it. That is deliberate: `scripts/graph_contract.py` records a 2026-09-15 peer audit that scoped `military_units.json` to the Наша Правда delivery channel and ruled that units named only in manufacturer posts must not be added. Only 1 of 17 `battlefield_evidence` items has a `unit_slug` (АО «Росс», группировка «Центр»). No change made.

## cbst_tie backfill: 32 resident-worded ties without a membership

Read in full: ЦБСТ posts 2095, 2109, 1509, 2184, 2198, 2379 (all archived).

**Wired (6, `cbst-residency`, basis doc, via `corrections_entities.json`):**
- `ooo-gagaring` (post 2109, s5440); `npo-kaysant` (post 1509, s7597).
- `ooo-skb-piranya`, `ooo-atlant-aero`, `ao-tekhnodron`, `ooo-arkhangel-tsentr` (post 2095, s7588). The note on each carries the limit: the headline and closing paragraph say «резиденты», the body says «входящие в контур», and the post names no legal entity. Identity per entity is stated in its note (EU act link for Архангел-Центр; exact-ИНН EU match for Атлант Аэро and Технодрон).
- `resident_of` edges: 30 → 36.

**Claim corrected:** `ooo-aeromaks` cbst_tie rewritten and downgraded t-doc → t-open. Post 2095 lists «Аэромакс» among «ряд других отечественных разработчиков дронов», not among the residents; the old wording rested on a paraphrase in the dossier draft.

**Held, with reason:**
- Овод / Воздушный трактат: two entities carry the brand; your decision on which holds the residency is still open.
- `ooo-gaskar`: the post says «Гаскар Групп»; the sister entities are not told apart.
- `ao-npp-bat`, `ao-npp-real` (АО «НПП»): short name only, entity by registry inference.
- `ooo-npo-rustekhdron`, `ao-tekhnodron`'s «Скворец» reading: brand-level names in post 1074.
- `ooo-aeroplatformy` (post 2184: «Резидент ЦБСТ… компания «Аэроплатформы»»): no site, no ИНН printed; entity matched by name only.
- `ooo-tsentr-dinarus` (finalist of stream II, post 2198) and `va-technologies` (stream III participant, post 2379): the posts link the companies' sites, but the sites print no ИНН; `va-technologies` is matched through the founder's name. Accelerator participation, not residency.
- `ooo-ti-es-dzhi-grupp`: residency stated by KurskCity (press) and by ЦБСТ under the Latin name «TSG Group»; identity link rests on the press page.
- `ao-shkola-bpla-oktagon`, `ooo-boevye-tekhnologii`: «Резидент ЦБСТ, гендиректор …» is grammatically the person.
- `ooo-trimiks`, `ooo-npo-kilovatt-shestopalov`: product-level statements; `ooo-eyartek`, `ooo-orient-sistems`: no «резидент» applied; `ooo-pekhtra`: prize winner, not a resident; `ooo-tskbr`: names only a person; `ano-platforma-nti`: a board seat; `ano-dpo-obrazovatelny-tsentr-gagaring`, `npts-ushkuynik`, `krams-brand-unresolved`: derived from or duplicating an entity already wired; `proekt-kb-arkhangel`: user of a resident's product.

**Open question added to `gk-logos`:** the «Логос» resident is not identified by an identifier. The membership recorded earlier on `gk-logos` rests on post 878 plus the entity's own site; `ooo-gk-logos` (ИНН 3435149330, whose legal name is literally «Группа компаний «Логос»») claims the same post. The two records also disagree on gk-logos's ИНН (7839303129 vs 1001294845).

## Tasks carried from the Coverage Audit (19 Sep); status not re-verified today

1. Confirm regime and date of each sanction against OFAC / EU / UK / GUR primary pages (GUR returned 403 from this machine). 2. Decide the three unsourced sanctions entries (Лысогорский, Скорятин, ЦКБР). 3. Resolve duplicate pairs (Стратим, Аэромакс, «Архангел» ×4). 4. Four missing dates of birth (Елисеев, Корчагина, Гаврилов, Пинимасова) via rupep or ЕГРЮЛ. 5. Weaker tie types for seven detached sanctioned entities (ГЭС-2, Элиарс, Интек Беспилотные Системы, Титан-Северо-Запад, Радиофид Системы, Архангел-Центр, Архангел-Мелитополь-2); Архангел-Центр has since gained a tie. 6. Re-test Росаккредитация. 7. reveng.ee key; NAZK War & Sanctions. 8. ФССП and arbitration checks on the top ~20 entities; Филиппов criminal-record flag; PII line for any deck. 9–10. Screen АО «Кронштадт»; find its owner. 11. Aleph-era ГК Аэромакс ↔ ООО «Аэромакс» cross-holding. 12. Review the zakupki re-mine output. 14. Hand screening of the 18 entities added 19 Sep. 15. Pull owners not yet on file (АО «НПО «Высокоточные комплексы» 7704721192 and six organisation stubs).
