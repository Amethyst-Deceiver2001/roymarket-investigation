# Evidence packets: claim-verifier run, 03.10.2026 (issue #20, item 1)

Six packets in `notes/packets/`, one `claim-verifier` agent each (read-only), about 330 claims checked in all. Nothing in a packet or the registry was edited. The verifier's output is a list of leads; items marked **checked** I confirmed myself against the document on 03.10.2026. A correction goes through `corrections_*.json` after a person has read the document.

## By packet, most serious first

### ООО «Гаскар» (9710112989): the packet conflates two companies
- **Checked.** The EU (Decision 2026/509, designated 23.04.2026, EU.14160.3) and the Swiss list (listed 21.05.2026) name «Гаскар Групп» with ИНН 7734436058, ОГРН 1207700279797, КПП 773101001, Skolkovo. The ЕГРЮЛ extract of 03.10.2026 shows that ИНН and ОГРН as ООО «СТИМС» (renamed 19.11.2024); the extract never mentions Гаскар. Neither list has an entry for 9710112989 or 1237700273744.
- The packet says ООО «Гаскар» is "EU-sanctioned" and grades the ЦБСТ tie "Documented" (post 2095 names «Гаскар Групп», no ИНН). Its own §2 says "EU: no ID match". The registry's own note calls the referent of «Групп» open; the packet drops it.
- The registry's Ukraine/Canada lead (s0809, OpenSanctions record under the name "EVR", alias «Гаскар», datasets ua_war_sanctions, ca_dfatd_sema_sanctions) is an aggregator record not read against the primary lists; the packet says "Ukraine: nothing" and "registry: listed" without that caveat. No Canadian list text is local.
- ООО «СТИМС» is not in the registry. Its owners per the extract: ООО «Аметист Кэпитал» 60%, Мингалимов Ленар Нуриахметович 20% (general director), Саитов Ренат Фаритович 20% (07.07.2026). Саитов is already in the registry as general director of ООО «Гаскар Интеграция» (s1548).
- Smaller: two sentences cut off mid-word; registration date 12.04.2023 omitted.

### ООО НПО «Киловатт» (Шестопалов), 4800016776
- **Dealer, checked.** E3 (image-only PDF, read from the page) certifies «ИП Пинимасов Александр Вячеславович ИНН 583680188519», signed Шестопалов С.А., № 2106/2024. The packet and the registry name ИП Пинимасова Елена Александровна (ИНН 583713716580, Пензенская обл.). The certificate is also titled as a conformity document.
- **Founder, checked.** The packet says Хальзев Сергей Юрьевич "founded" the company; the ЕГРЮЛ enters him on 31.03.2026 (40%, ₽400,000); the company was created 22.07.2024.
- **Trademark 1086620 and design RU145992** are attributed to this entity; the FIPS capture gives the Lipetsk address of the sister ООО НПО «Киловатт» (4800013729), and the registry and CLAUDE.md already say the sister holds the mark. The image cannot tell them apart.
- Ukraine row says "nothing"; the archived Aleph/OpenSanctions file (s0592) lists "Ukraine NSDC State Register of Sanctions", and `people.json` carries an NSDC sanction for Шестопалов. Aggregator records, unconfirmed.
- The sister-entity row cites E7, which never mentions the sister. E6 (post 369) names Капюшон in a batch; it names neither Киловатт nor a legal entity. "ШТУРМ-К" alias is not on E11. Sole-founder 2024 name is on neither cited exhibit.

### ООО «Гагаринг» (2312321660)
- **Ownership.** The ЕГРЮЛ (s0455, s6776; **checked**) shows Александров 49.5% (₽4,950) and Барашков 50.5% (₽5,050), both entries ГРН 2262300538091 (15.04.2026). The FY2025 audit report (s5333, OCR, signed 04.06.2026 by ООО «БСК аудит», a corrected version of a report signed 31.03.2026) says 50/50 and Александров a participant "с декабря 2023г". The register entry is earlier than the audit report, and the report was not reconciled with it. The register is the primary record; the conflict is not explained.
- The owners row "04.09.2023 Барашков 50.5% / Александров 49.5%" is wrong: Александров's record first dates from 22.12.2023.
- ООО «Интел Дрон»: packet says 50% (audit note); the ЕГРЮЛ (s6815) says 40%.
- FY2024 profit printed as ₽20.9m; the FY2025 filing and the audit report restate it as ₽15.4m.
- "Member of the association": the audit report lists it as a related party; the association's own extract lists Гагаринг as a participant/founder (01.03.2024). "Member" is not stated.
- "Two live hh.ru postings": one exhibit (s5420); the second (s5419) is not cited.
- Titles: s5333 is "Fedresurs register record" but is the auditor's report; s5420 and s5419 are hh.ru vacancies titled "Press article"; s7361 is an aggregator page titled "Archived document".
- Not checked: personal ИНН, E10, E15-E24, E26, E29-E31, the quotes. This packet is only partly verified.

### ООО «Метаскан» (1660349248)
- Address **checked**: ул. Меридианная, д. 26А, Казань (ГРН 2231601071744, 28.09.2023); the packet says "no dated source" and lists only the superseded April 2023 address.
- Two participants **checked**: Поспехов 50% and ООО «Централизованная юридическая служба» (1215226708) 50%. The registry's founders list omits the company; two registry notes say "sole founder".
- ЦБСТ post 706 is in the database and on file (s7594, a transcript of the database text, not a capture). It names «Арена 5М» (ООО «Метаскан») among goods handed to sappers and speaks of "техника резидентов ЦБСТ" generally; it does not say Метаскан is a resident. The registry's "not archived" note is stale.
- "As of 09.07.2025" for the director is the date of the share records; the director's entry is 15.02.2024.

### ООО «Смарт Текнолоджис» (7715934509)
- **Checked.** Registered 07.09.2012 by the Moscow inspectorate No. 46, address in Moscow; the packet's §7 says "registered in Penza" ("Penza" is press wording only).
- "резидент ЦБСТ" is printed as a quotation; the post (487) says «Резидент Центра беспилотных систем и технологий (ЦБСТ)». The quote comes from the registry's tie note.
- Trademark entries print `«»` with no mark name, and their exhibit hashes differ from the files on disk; nothing ties either mark to the product.
- Address drops «стр. 1, пом. XXV, ком. 1Ж», and is dated 03.09.2018 in the extract.
- Open question: a leader-id self-report and a press quote name two other people as director; the ЕГРЮЛ (11.11.2025) names Кот Олег Петрович.

### ООО ОПКБ «Экспломет» (1215235283): mostly sound
- No wrong figure, owner, director or identifier. Gaps: ЦБСТ-tie text cut off, and the registry's "direct, first-degree institutional tie" and "joint development" go beyond the post («предполагает»); address drops the street and says undated (ЕГРЮЛ dates it 03.11.2023); Минпромторг conclusion numbers and dates (E9, E13) are not in the PDF text layers; E17 title date 01.04.2021 does not match the 2023 charter cited; patents are held by Фоминых Алексей Михайлович personally; 2023 profit restated in the FY2024 filing (₽55.7m, not ₽54.4m).

## Patterns across the packets (generator and rules, not facts)
1. **Truncated strings** ("agr...", "per ЦБСТ's own ...", "1...") in five packets: a length cut in `exhibits/build_evidence_packet.py`.
2. **"[no dated source on file]" for the address** is wrong in four packets: the extracts date the entry; the registry's `address_history` carries no source.
3. **Ukraine/Canada rows say "nothing"** where the registry holds an unread aggregator lead (Гаскар, Киловатт). The row should say "aggregator record, not read".
4. **Exhibit titles** that name the wrong kind of document (`s5333`, `s5420`, `s5419`, the dealer certificate, transcripts titled as Telegram captures): rules in `scripts/source_citation.py` with fixtures.
5. **Quotation marks around paraphrase** (the «резидент ЦБСТ» string in the registry's tie notes).
6. **Restatements not carried** (Гагаринг 2024, Экспломет 2023).
7. **Strong wording from a party's own post** ("direct, first-degree tie", "Documented") where the post names a brand or a batch.

## Not done, and what each needs
- **Registry corrections** (read the document first, then `corrections_*.json`): record ООО «СТИМС» with the EU and Swiss `sanctions[]` entries and the Саитов link, after reading both full entries and the regulation; correct the Киловатт dealer, the Хальзев role and the trademark holder; add the second Метаскан participant; correct the Гагаринг owners row; fix the quoted «резидент ЦБСТ». The Пинимасов ИНН needs its own ЕГРИП extract before a record is made.
- **Гагаринг conflict:** needs the later audit PDF and the ЕГРЮЛ side by side; a person decides which stands, as of what date.
- **Generator fixes** as in the patterns above, then regenerate each packet with `python3 exhibits/build_evidence_packet.py <slug>`.
- **Not verified at all:** the personal ИНН checksums for Гагаринг, the 02.10 sanctions tables, date and place of birth (none printed), and the Canadian list.
