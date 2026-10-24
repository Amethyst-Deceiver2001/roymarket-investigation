# РОЙ.МАРКЕТ supplier page: «двойного назначения» became «специального назначения» (24.10.2026)

Pages read in full in Russian (text extracted from the HTML; original bytes saved through `write_new`): `https://xn--80akkfikneu.xn--p1ai/` (роймаркет.рф), «Начать продавать на РОЙ.МАРКЕТ», the supplier questionnaire page. Wayback copies are the raw `id_` captures. **A page's own wording at a date; no registry fact until catalogued.**

## The line
| Capture | Sentence |
|---|---|
| Wayback 22.08.2026 09:13:46 (also 22.08 21:18:18, 24.08 21:49:03) | «РОЙ.МАРКЕТ - защищённый канал продаж товаров **двойного назначения**. Здесь ваш ассортимент получает доступ к спросу профессиональных заказчиков.» |
| Wayback 03.10.2026 03:11:35; 12.10.2026 12:50:49; 12.10.2026 12:58:16 | same, «двойного назначения» |
| **Live, fetched 24.10.2026** | «РОЙ.МАРКЕТ - защищённый канал продаж товаров **специального назначения**. …» |
So the phrase was changed **after 12.10.2026 12:58 UTC and before our fetch on 24.10.2026**; Wayback has no capture between, so the exact date is unknown. Headline above it is unchanged: «Ваши товары могут продаваться не только на Wildberries и Ozon».

## What else changed on the page
- The form was **extended between 24.08 and 03.10.2026**: new field «**Являетесь ли вы резидентом АНО «ЦБСТ»?** Да / Нет»; new «Продажи на маркетплейсах» block (Wildberries / Ozon yes-no); new categories «Системы связи» and «**Комплектующие НРТК**» (ground robotic complexes). «Антенны» was in the August form and is gone. The August form has no ЦБСТ-resident question.
- The phrase change is separate and later: «двойного» held through the 03.10 and 12.10 captures that already carried the ЦБСТ question.
- Meta description and keywords («компоненты для дронов, запчасти для БПЛА, маркетплейс беспилотных систем») are the same in August and now; the OG description reads «Маркетплейс компонентов, оборудования и материалов для беспилотных систем.»

## What the public site never says
The main site `roimarket.ru` (login page; «Закрытая платформа инженерного снабжения») and its public pages (`/about`, `/contacts`, `/delivery`, `/legal`, `/legal/buyer-offer`, `/payment`, `/privacy`, `/returns`, `/warranty`) were fetched 24.10.2026: **none uses «двойного назначения», «специального назначения», «военн-» or «гражданск-»** (regex check on the extracted text). The term appears **only on the supplier-recruitment page**. This answers the open point from the previous turn: the platform's own terms do not claim dual-use; the claim was a recruiting line aimed at sellers.

## Reading (for the story; attribute, do not conclude)
- РОЙ.МАРКЕТ recruited suppliers in August to October 2026 as a channel for «товаров двойного назначения», then changed the line to «специального назначения» in the 12–24 October window. The list of categories (drone batteries and components, DJI/AUTEL, video, communications, ground-robot components) is for unmanned systems, and the form asks if the seller is a ЦБСТ resident.
- «Special-purpose» is the Russian trade-regulation word for goods for state defence and security buyers; we do not define it here, and a reader can see for themselves that the label moved away from civilian-use wording. **No statement about why, or about legal consequence, is made.** The timing coincides with 13.10 (ЦБСТ post on Interdron joining) and 20.10 (the Гагарин strike post) in our scrape; no source links the change to either.
- Pairs with the Kherson series: the channel uses «двойного назначения» for ambulances and funeral vehicles (`notes/osvedomitell_alex_scan_20261024.md` §5).

## To do
- The supplier page changes again: re-fetch by hand when asked; a Wayback capture is a lead only until we hold it ourselves (captures above are ours).
- The Wayback gap 12.10 to 24.10: ask the archive Mac / `archive_sources.py` whether Wayback holds a later copy.
- Catalogue the four captures on the archive Mac.
