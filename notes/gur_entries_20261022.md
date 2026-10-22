# ГУР entries: where they stand and what comes next (22.10.2026)

Picks up the ГУР work of 05.10-06.10.2026 (commit 6cba9cc: Ukrainian dates and
decrees read from the GUR pages; ffeda7c: ИП Коровкин's name-only hits closed).
Counts are from `entities.json` / `people.json` on main at 1a41ee0. Nothing here
is a new fact: section 1 is a set of review closures drafted from the screen's
stored match record, sections 2-4 are reading tasks.

## State

- **14 entities carry a Ukraine `sanctions[]` entry read off their own GUR page**
  (6cba9cc and earlier): five with a decree read on zakon.rada.gov.ua (415/2025,
  447/2026, 472/2025, 473/2025, 554/2025), the rest with the portal's own date and
  the decree not identified. In every case the NSDC decision's annex was not read
  (president.gov.ua refused scripted requests), so the naming rests on the portal.
- **`ooo-aero-khit-servis`**: page read 04.10, it says «The country has not yet
  applied sanctions»; closed as `linked_not_designated`. Lesson kept: the long
  jurisdiction panel on a GUR page is site boilerplate, not a listing.
- **53 entities have only name-matched GUR hits.** 44 had a `sanctions_review`
  or a sanctions entry; 9 still raised the board's `screen_hits_unreviewed`
  flag. Section 1 closes those 9.

## 1. Drafted on branch `claude/project-thread-qtsqtj`, not committed

`sanctions_review` `{as_of: 2026-10-22, outcome: closed}` on nine records, in
`corrections_entities.json` (`add_entities`) and `entities.json`, same wording as
the Коровкин closure. No GUR hit on any of them prints this record's ИНН or ОГРН;
each shares only a surname, a first name and patronymic, or a generic word.

| Record | Hits | What matched |
|---|---|---|
| ИП Габитов Р. А. | 1 | surname (Gabitov Marat Khanbalevich, other ИНН) |
| ИП Попов А. С. | 5 | surname or name+patronymic, other ИНН or none |
| ООО «Аркодим-Про» | 1 | «Pro» (ООО «Laggar Pro», ИНН 5250070144) |
| Ассоциация технологического бизнеса | 1 | «association» (South Urals UAV cluster, ИНН 7451471189) |
| Фонд развития промышленности Тульской области | 1 | «development» (Digital Development Agency, ИНН 5190091997) |
| ИП Маврин О. В. | 5 | surname (Mavrin Sergei Petrovich, no ИНН) or name+patronymic |
| ИП Карпушин А. А. | 5 | surname (Karpushin Oleg Vyacheslavovich, ИНН 772783693278) or name+patronymic |
| ИП Пинимасов А. В. | 5 | name+patronymic only |
| ИП Артемьева В. М. | 5 | first name only |

After this the only record left with the flag is `ooo-as-kam`, an OpenSanctions
hit, not ГУР. `check_registry.py --no-local-files`: 0 errors. `test_status_board`
and `test_relationship_graph` pass. `board.json` was not regenerated here; the
pre-commit hook does that on the Mac.

## 2. Five ID-confirmed GUR pages already saved on the Mac, Ukraine field unread

Each page prints this record's own ИНН and ОГРН. Read the «Date of entry and
reference to the document» field and record what it says: a dated Ukraine entry
(decree read where linked, as in 6cba9cc), or `linked_not_designated` if it
says the country has not applied sanctions.

| Record | Page | Saved copy |
|---|---|---|
| `ovod` ООО «РЛВТ» | uav/companies/14059 | s6141 (05.09) |
| `ooo-vozdushnyy-traktat` | uav/companies/14072 | s6142 (05.09) |
| `ao-ekolibri` | uav/companies/14291 | s6144 (05.09) |
| `ooo-gaskar-integratsiya` | uav/companies/15561 | s6146 (05.09) |
| `ooo-gruppa-promavto` | uav/companies/13126 | s9338 (08.10) |

`ao-ekolibri` and `ooo-gaskar-integratsiya` have no other `sanctions[]` entry
than the aggregator one, so this read decides whether they carry any designation
read on an official source.

## 3. Ukraine claims resting on OpenSanctions, where it names a GUR page we never saved

Fifteen pages, one request each. The cloud cannot reach war-sanctions.gur.gov.ua,
so this runs on the Mac (single lookups; the script's browser User-Agent is needed,
a bare request gets 403):

```bash
cd ~/Downloads/roymarket-investigation
D=$(date +%Y%m%d); UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
while read slug inn path; do
  f="data/sources/GUR_${inn}_${D}_${slug}.html"
  [ -e "$f" ] && { echo "exists: $f"; continue; }
  curl -sS -A "$UA" -o "$f" "https://war-sanctions.gur.gov.ua/en/$path" && echo "saved $f"; sleep 3
done <<'EOF'
pao-bank-psb 7744000912 sanctions/companies/32
ao-pk-azimut 7701583410 sanctions/companies/155
ooo-atlant-aero 6154165878 sanctions/companies/15599
ao-kotlin-novator 7811075899 uav/companies/10214
ooo-kleverkopter 5257183517 sanctions/companies/16050
ooo-trimiks 7802942873 sanctions/companies/12685
ao-tekhnodinamika 7719265496 components/companies/4664
ooo-aeromaks 7725347482 sanctions/companies/1534
ano-npts-ushkuynik 5300010714 sanctions/companies/14954
npp-radar-mms 7814027653 sanctions/companies/3333
ao-nii-vektor 7813491943 sanctions/companies/428
npts-elvis 7735582816 sanctions/companies/336
gk-rostekh 7704274402 sanctions/companies/16
ooo-rt-razvitie-biznesa 7704861136 sanctions/companies/5973
ao-nii-stt 6730046954 uav/companies/8229
EOF
python3 scripts/inventory_sources.py && python3 scripts/extract_registry.py && python3 scripts/check_registry.py
```

Then, per page: check the printed ИНН/ОГРН against the record first (a page that
prints another company's identifiers is not ours), then read the Ukraine field as
in section 2. `ooo-trimiks` (3mx), `ooo-kleverkopter`, `ano-npts-ushkuynik` and
`ooo-atlant-aero` are ЦБСТ-tied at t-doc and matter most to the packets.

## 4. Ukraine claims with no GUR page named anywhere

Aggregator or NSDC-tagged claims with no portal page to read: `fond-nasha-pravda`,
`ano-platforma-nti`, `ooo-dsg`, `ano-tsentr-razvitiya-transportnykh-tekhnologiy`,
`assotsiatsiya-vzaimopomoshch`, `ooo-arkhangel-tsentr`, `ooo-arkhangel-melitopol-2`,
`ooo-uk-komaks`, `ooo-npo-programmnye-kompleksy-realnogo-vremeni`, `ao-kbp-shipunova`.
Next step is a GUR site search by ИНН for each (the name search in
`screen_gur.py` found nothing for them), then the NSDC State Register. Fond «Наша
Правда» first: it is cbst-core and its Ukraine claim rests on one aggregator source
(s0575).

People: 13 records carry a Ukraine claim; only Алейник and Богатиков have a
dated entry citing a ГУР source (s9164, s9165), the rest rest on aggregators or NSDC tags. People have no
`gur_matches` field because `screen_gur.py` screens entities only.
