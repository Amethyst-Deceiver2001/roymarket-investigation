# Delivery-signal scan of the archive (2026-10-02)

`python3 scripts/delivery_signal_scan.py --out <file>` finds posts where a delivery verb (передали, привезли, вручили, доставили, отправили, поставили...) sits within 220 characters of a recipient (бойцам, парням, бригада, полк, батальон, группировка «Центр», на передовую, СВО...) and the post names a product. Local, read-only, 22 seconds. A hit is a lead to read; nothing below was recorded without the post being read in full.

## Coverage and limits

- 302,614 of the 503,714 posts were scanned: the rest have no text or 40 characters or fewer (photo-only posts and captions). A handover shown only in a picture is invisible to this scan.
- 5,877 posts carry a signal; 5,192 distinct texts after grouping reposts by normalised text.
- **Class A (200 texts):** the post also names a registry product (`products[]`, `products.json` or an accessory) or a maker brand. **Class B (4,992):** only a category word (дрон, детектор, РЭБ, антенна...). Class B is the long tail; it was not read.
- Donor brands are reported separately from products and generic nouns («Ретранслятор», «Передатчик», «Приемник») are not treated as products. Before that filter, «Архангел» alone made 1,225 of 1,682 class A texts.
- Precision is unmeasured. Of the class A texts read, the main false-positive types are a product name that is also a word («Сокол», «Титан», «Буран», «Прометей»), a verb that is not a handover (an award ceremony, a transfer of a command) and a product named in an unrelated sentence of a long digest.
- Recall is also unmeasured: a handover phrased without one of the verbs, or naming the unit before the item in a long post, can miss.
- Donor classes among all 5,192 texts: «Архангел» 532, «Наша Правда» 274, «Единая Россия» 174 + 88, «ЦБСТ» 131, «Народный фронт» 29. Years: 2023 1,128; 2024 1,896; 2025 1,373; 2026 715.

## What it shows

1. **One donor chain dominates the institutional handovers:** Фонд «Наша Правда» with «Единая Россия» and, from 2025, ЦБСТ named as co-donor. Posts name the unit or direction (a brigade, a regiment, a group, a front direction) and the shipment value.
2. **«Булат» (Тримикс/3mx) is in that chain.** 44 distinct texts name it with a delivery signal. Sixteen are the fund's own reports between 2025-02-11 and 2026-05-19 and are recorded as deliveries on `products.json` («Булат»); the credibility is single (the donor's own post) and no version is ever stated. Others are volunteer groups (Архангел Спецназа 2023, «Судоплатов» 2024, a volunteer fund in Kursk 2024, individuals), the maker's own reports (3mx and Покров to Kursk fighters 28.04.2025; 3mx to Э. Запашный 30.10.2025) and handovers by chats of buyers. Not recorded: see the open question on the product record.
3. **A stronger ЦБСТ statement for the maker.** On 09.04.2025 the ЦИК head of «Единая Россия» Сидякин, delivering to the 132nd brigade, says the party brought «оборудование резидентов ЦБСТ – средства радиоэлектронной разведки “Перехват” и “Булат”» (`@evgeniy_lisitsyn` 15603, s8895). The fund's own post of the same trip (nashapravdafond 422, s8896) names ЦБСТ as co-donor. Added to the `cbst_tie` evidence of ООО «Тримикс»; the grade stays t-doc and a formal residency document is still not shown.
4. **Delivery reports are routine donor content.** The fund's reports include «Перехват» (АО «НПП») and «Талисман» prototypes next to «Булат». The same method on those products would give a delivery list for each ЦБСТ-resident product; it was run on «Булат» only.
5. **The «Булат» deliveries span 15 months and six directions or groups** (Красноармейское, Донецкое, Покровское, Сватовское, Курская область, ЛНР/группировки «Юг» и «Центр»), against the maker's own statement that its goods are sold only on 3mx.ru and through dealers (s8860): a donor purchase route is not shown in these posts.

## Not recorded (decisions still open)

Volunteer-group and individual handovers (about 20 more «Булат» texts), the 3mx-own handovers, and any town-level location. Whether named volunteers and unit-level detail may be recorded, and whether volunteer reports are graded as self-reports by default, are the user's decisions. The recorded deliveries carry the donor's own wording of the recipient only at unit, region or direction level.

## Next

- Run the same recording for other resident products (Перехват, Капюшон, Скворец) once the privacy decisions are made.
- Read a sample of class B (it holds the volunteer chains).
- Find the donor purchase route: invoices or tenders for «Булат» bought by Фонд «Наша Правда» (not in the posts).
- Capture the two WB brand-store listings.
