# Recording registry facts without the archive Mac (protocol, 25.10.2026)

Set up at the user's request when the archive Mac may not come back. Tool: `scripts/local_sources.py`. First use: «Квадросим» (ООО «НИНСАР»), see `notes/kvadrosim_and_archangel_diplomas_20261024.md`.

## The problem

A registry record has to cite a source id, and `check_registry.py` rejects an id that `sources.json` does not hold. The sNNNN ids come from `inventory_sources.py` on the archive Mac, so a machine without it could not record a new fact with a source of its own. The workaround so far was to leave the fact in a note.

## The rule

1. **Write the file the usual way.** A saved page or document goes into `data/sources/` through `source_files.write_new()` with the usual `<TYPE>_<INN-or-OGRN>_<YYYYMMDD>_<slug>.<ext>` name; a Telegram post from the scraped database goes through `scripts/archive_tg_posts.py`. Nothing in `data/sources/` is overwritten.
2. **Give it a local id.** `python3 scripts/local_sources.py add data/sources/<file> [--url URL] [--inn INN]` adds a record to `sources.json` with an id **`L0001`, `L0002`, …**, flagged `"_local": true` and `"_origin": "local-mac"`. The id cannot collide with an s-id. `add` is idempotent (same sha256, same id) and takes title and public link from `source_citation.py`; a file it cannot read needs `--title` and `--public-url`.
3. **Record the fact as usual.** A new entity or person goes through `corrections_entities.json` (`add_entities`) or `corrections_people.json` (`people_add_entities`), with a `why` that names the L-ids, **and** is mirrored into `entities.json` / `people.json` (CLAUDE.md: a generated file edited by hand here is mirrored in corrections). Cite the L-id wherever an s-id goes. A source that already has an s-id (for example a post the archive already holds) keeps it.
4. **Check as usual.** `build_relationship_graph.py`, then `check_registry.py --no-local-files` (0 errors). The checker prints how many local sources are pending.
5. **Pages are fine.** A reader page built from a record that cites an L-id shows the source's plain title and public link like any other; the id is never printed.

## When the archive Mac is back (or a new archive machine exists)

On that machine, in this order:

1. `git pull`.
2. Copy the files `python3 scripts/local_sources.py list` names from this Mac's `data/sources/` to the same paths there. (They are not in git. The list gives each file's sha256 prefix; `merge` re-checks the full hash.)
3. `python3 scripts/inventory_sources.py`: assigns each copied file its s-id in `_source_ids.json`.
4. `python3 scripts/local_sources.py merge` (dry run), then `merge --apply`: rewrites every quoted `"L0001"` in `data/registry/*.json` to the s-id of the same path, after checking the file's sha256, and drops the L records. Anything waiting on a file or an id is reported and left alone.
5. `python3 scripts/extract_registry.py`, `build_relationship_graph.py`, `check_registry.py` (0 errors, no pending local sources), then commit.
6. `notes/*.md` that cite an L-id are listed by `merge`; edit them by hand.

If there is never an archive Mac: nothing breaks. The L-ids simply stay, and `check_registry.py` keeps reporting them as pending, not as errors.

## What a local record must still honour

All the usual rules apply: facts only from a document read in full; an identity only by identifier or a matching named person; time-variant facts as dated history entries; a `cbst_tie` with a `confidence` from `{t-doc, t-open, press}`; screening fields (`sanctions[]`, `gur_matches`…) are never invented, and an unscreened record says so in `open_questions`.

## Records made this way so far

| Record | Local sources | Waiting for |
|---|---|---|
| `ooo-ninsar` («Квадросим») and `sechinskiy-egor-valerevich` | L0001 ЕГРЮЛ extract; L0002 riamo.ru capture; L0003, L0004 ЦБСТ posts 1524, 1584; L0005, L0006 projectArchangel posts 9709, 10550; L0007 Archangel_Forum post 175293; L0008 ЕГРЮЛ search result | s-ids; screening on the archive machine |
| 251 files that had no id by path or hash on 25.10.2026 (L0009–L0259): 3 ЕГРЮЛ extracts (ИНН 6685221143, 7702330228, 7704278421; their entities already exist), press and web captures (Вот Так, Ukrainska Pravda, CIR, HRW, UN, fondsvo.ru, the Wayback captures of the supplier page), 7 Telegram post texts, 49 Telegram pictures/videos, the ФБК «Он вам не Димон» page text and its 174 images | L0009–L0259 | s-ids. Registered as sources only: **no new entity or fact was entered from them**; each document still has to be read in full before a fact is recorded. Titles are from `source_citation.py` or the file name; `public_url` is empty where the capture has none |
