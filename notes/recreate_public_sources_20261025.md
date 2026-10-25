# Recreating the sources behind the public draft (25.10.2026)

`data/sources/` was lost with the archive Mac (1 of 9,229 registered files was on the working Mac). The public landing draft describes **168 distinct sources** (103 notes after merging duplicates; 98 have a public link). Counts below are by file-name prefix of those 168. The registered `sha256` of every source is kept in `sources.json`, so a re-created file is checked by hash where it can be.

| Group | Cited | How | Status 25.10.2026 |
|---|---|---|---|
| TGPOST (Telegram post text) | 43 | `archive_tg_posts.py` from the rebuilt `roymarket.db` | **32 reproduced byte-identical to the registered hash**; 4 exist in the database but the text differs (post edited since, or channel title changed): `s5440, s6915, s8841, s8994`; 4 are not in the database (`s8860` private chat `chat1651823792` post 42146; `s8990, s8991, s8992` nashapravdafond 302/310/311, before 24.10.2024), 3 do not match the naming pattern. Across **all 364** registered TGPOST files, 119 were rewritten byte-identical (same path, same hash). |
| TGMEDIA (pictures, videos) | 48 | user-run `tg_media_pull.py download` | 4 commands below (29 messages); 13 files cannot be fetched from this database (ru3mxchat 8, archangelforum 4, tulaovod 1). The authenticated download gives the full photo, which may not be byte-equal to the preview image that was registered. |
| Registers (РЕСУРС/БФО 16, ZAKUPKI 5, ЕГРЮЛ and ul 6, trademark 1, …) | about 30 | `egrul_batch_pull.py`, `bfo_pull.py`, `zakupki_batch_pull.py` (user-run, by ИНН) | not started; files will carry today's date, so each becomes a re-capture, not the original bytes |
| Screening (OPENSANCTIONS 5, SANCTIONS 4, EU 4, SECO 3, OFAC 2, GUR 2, NSDC 1) | 21 | `sanctions_watch.py` by hand | the 05.10 snapshot cannot be reproduced; a fresh run gives a new as_of |
| Web (WEBCAPTURE 6, SITE 5, WEB 2, PRESS 2, SCREENSHOT 2, WAYBACK 1, shop pages, catalogue, certificate, PDFs, TRANSCRIPT) | about 25 | live fetch or Wayback (442 captures exist) | pages that have changed are lost unless Wayback holds them |

## TGMEDIA commands (user-run; message ids include album neighbours)

```
scripts/run scripts/tg_media_pull.py download --channel nashapravdafond --msg-ids 393,394,398,399,400,408,409,422,444,448,473,487,493,494,519,593,594,608,609,615 --label nashapravdafond
scripts/run scripts/tg_media_pull.py download --channel projectarchangel --msg-ids 10619,10782,10796 --label projectarchangel
scripts/run scripts/tg_media_pull.py download --channel tulaovod --msg-ids 845,896 --label tulaovod
scripts/run scripts/tg_media_pull.py download --channel piranhafpv --msg-ids 360,384,432,433 --label piranhafpv
```

Ten of the nashapravdafond videos in the first command (393, 399, 409, 448, 473, 487, 493, 494, 519, 608) are already downloaded (local ids L0308–L0317).

## Rule for a re-created file

Same path and name where the original name is known, never over an existing file; if the content differs from the registered `sha256`, write it as `-r2` and mark the old source `superseded_by`. A fact is re-checked against the new file before the draft relies on it.
