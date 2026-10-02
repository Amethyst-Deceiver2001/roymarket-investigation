# Media backfill, 02.10.2026 (track V, steps 1–2)

`data/registry/media.json` now holds 58 records. They came from 63 `entities.images[]` entries and the 2 `battlefield_evidence[]` entries that have an image; each record keeps its origin in `migrated_from`. Every picture whose genre can contain people was opened and looked at before `redact` was set. `shows` is the existing caption, which was written by whoever captured the image.

## Classification

| Genre | Records | Notes |
|---|---|---|
| logo | 20 | `graphic`, self, publishable |
| marketing | 11 | product photos, banners, one CGI render, the Покров «Булат» v.4 card; publishable as excerpts only |
| event | 10 | exhibition booths (Пиранья, Дронница-2025), the Покров concert, an NTV frame |
| training / production / recruitment | 10 | «Архангел» and Гагаринг video stills |
| facility | 4 | GoDrone showroom and storefront (two of them customer uploads, `third_party`) |
| interview | 2 | the «Андрей Иванов» stills; also linked to Черезов |
| other | 1 each | handover (Овод shipment), combat (Пиранья operator, `graphic: false`), portrait (Барашков), document (Барило letter to Замятин) |

## Faces

Three records showed the face of someone without a person record: m0037 (a bystander behind Барашков), m0045 (a Гагаринг graduate's eyes above the buff) and m0052 («Радистка»). The `docs/images/` copies were blurred on 02.10.2026, and the unblurred originals stay in `data/sources/`. The Барашков original had no archived copy, so it was saved first as `TGMEDIA_20260803_my-el-lab-post4210-barashkov-portrait.jpg`; it still needs `inventory_sources.py`.

## Gaps: images in `docs/images/` with no archived original

These images were not migrated, because a media record needs the source the picture came from:

| Image | Entity | Missing |
|---|---|---|
| `gagaring_hq_krasnodar_residential.jpg` | ooo-gagaring | Any source. Probably a street-level view of ул. Фадеева 429/3; provider and date unknown. |
| `gagaring_school_kunikova_annex.jpg` | ooo-gagaring | The picture's own source (s5385 is the licence that gives the address, not the image). |
| `uas_murommash_satellite.jpg` | ooo-npts-basirtk | Any source, the imagery provider and date, and the basis for the coordinates. |
| `uas_kovrovets_106_division.jpg` | ooo-npts-basirtk | The channel post it came from. |
| `uas_stupor_antidrone.jpg` | ooo-npts-basirtk | The post of 16.10.2024. |
| `uas_kindyakov_speech.jpg` | ooo-npts-basirtk | Any source (the caption says an unrelated public event). |
| `uas_barilo_letter_sukhonenkova.jpg` | ooo-npts-basirtk | The post or document; the first letter is s0232. |

**Decision (user, 02.10.2026):** these images come from the original manual discovery. Keep them in `docs/images/` as they are, and source them later. Re-capturing them is the fix. For the two facility views, use the screenshot rule decided 02.10.2026: Google Earth or Yandex Maps, with the provider and imagery date recorded.

## Open

- 13 stills have no frame timestamp. Record `frame.t` when the source video is next opened.
- 76 Telegram media files in `data/sources/` are not linked to any record (step 2, part 2).
- `entities.images[]` and `battlefield_evidence[].image_path` are still in place. New builders read `media.json`, and the old fields are retired once nothing reads them.
