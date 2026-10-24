#!/usr/bin/env python3
"""Fixtures for scripts/media_triage.py: repeats fold before download, near-duplicates fold before a look,
a first-pass label never overwrites the main session's, and sheets map cells back to posts.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_media_triage.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import media_triage as mt  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def picture(path: Path, size=(400, 300), shift=0):
    im = Image.new("RGB", size, (230, 230, 230))
    d = ImageDraw.Draw(im)
    d.rectangle([40 + shift, 60, 200 + shift, 220], fill=(20, 60, 140))
    d.ellipse([240, 40, 380, 180], fill=(180, 40, 30))
    im.save(path)
    return path


def main():
    # Telegram's own id folds forwards of one file
    assert mt.media_key('{"kind": "photo", "photo_id": 7, "size": 1}') == "p7"
    assert mt.media_key('{"kind": "video", "document_id": 9}') == "d9"
    assert mt.media_key(None) is None and mt.media_key("not json") is None

    assert mt.kind_of("photo", None) == "photo"
    assert mt.kind_of("document", '{"mime_type": "image/png"}') == "image"
    assert mt.kind_of("document", '{"mime_type": "application/pdf"}') is None, "a PDF is read, not looked at"
    assert mt.kind_of("other", "{}") is None

    # an album is one channel's posts in the same second; the caption is whichever member has text
    rows = [(1, 10, "2026-10-01T13:31:26", ""), (1, 11, "2026-10-01T13:31:26", "Передали «Булат»"),
            (1, 12, "2026-10-01T13:31:26", ""), (1, 13, "2026-10-01T14:00:00", ""), (2, 10, "2026-10-01T13:31:26", "x")]
    cap = mt.group_albums(rows)
    assert cap[(1, "2026-10-01T13:31:26")] == "Передали «Булат»"
    assert cap[(1, "2026-10-01T14:00:00")] == "" and cap[(2, "2026-10-01T13:31:26")] == "x"

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        a = picture(d / "a.jpg")
        Image.open(a).resize((160, 120)).save(d / "a_small.jpg", quality=40)   # re-encoded, resized copy
        picture(d / "b.jpg", shift=150)                                          # a different picture
        h = {n: mt.dhash(d / n) for n in ("a.jpg", "a_small.jpg", "b.jpg")}
        assert mt.hamming(h["a.jpg"], h["a_small.jpg"]) <= mt.NEAR_DUP_BITS, "a resized copy is the same picture"
        assert mt.hamming(h["a.jpg"], h["b.jpg"]) > mt.NEAR_DUP_BITS, "a different picture is not"
        dup = mt.cluster_near_dups(h)
        assert dup == {"a_small.jpg": "a.jpg"}, dup

        # sheets skip labelled items and every near-duplicate after the first
        items = [{"key": "p1", "file": "a.jpg"}, {"key": "p2", "file": "a_small.jpg"},
                 {"key": "p3", "file": "b.jpg"}, {"key": "p4", "file": "missing.jpg"}]
        processed = {"a.jpg": {}, "a_small.jpg": {"near_dup_of": "a.jpg"}, "b.jpg": {}}
        assert [i["key"] for i in mt.sheet_candidates(items, processed, {})] == ["p1", "p3"]
        assert [i["key"] for i in mt.sheet_candidates(items, processed, {"p1": {}})] == ["p3"], \
            "a labelled picture's near-duplicate is skipped with it"

        out = d / "sheet.jpg"
        mt.draw_sheet([(a, "ANO_CBST/2601", "Передали «Булат»", True), (d / "nope.jpg", "x/1", "", False)], out)
        with Image.open(out) as s:
            assert s.size == (mt.GRID * mt.CELL, mt.GRID * (mt.CELL + 34))

    # labels: vocabulary checked; a first pass never overwrites a full-size look
    assert mt.validate_labels({"1": {"label": "handover", "keep": True}}) == []
    assert mt.validate_labels({"1": {"label": "handover", "keep": True, "mission": "ties"}}) == []
    assert len(mt.validate_labels({"1": {"label": "handover", "keep": True, "mission": "maybe"}})) == 1

    # the caption outranks the picture: a handover caption with a registry hit beats a bare one
    assert mt.text_score("Передали бойцам груз", {"registry": "Булат", "delivery": "B/strong"}) > \
        mt.text_score("Выставка дронов", {"registry": "Булат"}) >= mt.text_score("", {}) == 0
    assert mt.text_score("Выставка дронов", {"registry": "Булат"}) == 0, "a bare registry hit is not a handover"
    assert mt.text_score("Передали бойцам", {"registry": "Булат"}) > mt.text_score("Передали бойцам", {})
    assert mt.text_score("Добровольцы награждены медалью", {}) < mt.text_score("Передали бойцам партию", {}), "ceremonies are not handovers"
    base = {"file": "a.jpg", "key": "k", "channel": "x", "reasons": {}}
    assert mt.ignored({**base, "channel": "rostecru"}) and mt.ignored({**base, "reasons": {"registry": "ростех"}})
    assert not mt.ignored({**base, "reasons": {"registry": "ростех, булат"}}) and not mt.ignored(base)
    assert mt.ignored({**base, "caption": "Главное за неделю: лента новостей от АНО «ЦБСТ»"}) and not mt.ignored({**base, "caption": "Передали бойцам"})
    assert mt.ignored({**base, "channel": "ANO_CBST", "caption": "Израиль передал армии лазерный перехватчик"})
    assert not mt.ignored({**base, "channel": "ANO_CBST", "caption": "ЦБСТ совместно с фондом «Наша Правда» передали бригаде"})
    assert not mt.ignored({**base, "channel": "ANO_CBST", "caption": ""}), "an uncaptioned album stays"
    h = mt.registry_matcher()
    assert h("в секторе") == [] and h("площадью 5 га") == [] and h("Новый дрон-перехватчик") == [], "ordinary words are not hits"
    assert h("«Набат» отгружен") == ["набат"] and h("детектор Булат") == ["булат"]
    # an album: two cells at most, none once one of its pictures is labelled; recorded posts go last
    its = [{"key": f"p{i}", "file": f"f{i}.jpg", "channel": "c", "msg_id": 10 + i, "album": "1:t", "reasons": {}} for i in range(4)]
    pr = {f"f{i}.jpg": {"dhash": "x"} for i in range(4)}
    assert [i["key"] for i in mt.sheet_candidates(its, pr, {})] == ["p0", "p1"]
    assert mt.sheet_candidates(its, pr, {"p0": {"post": "c/10"}}) == [], "a labelled picture takes its album with it"
    assert [i["key"] for i in mt.sheet_candidates(its, pr, {}, {("c", 10)})] == ["p1", "p0"], "a recorded post goes last"
    assert mt.post_url("nashapravdafond", 615) == "https://t.me/nashapravdafond/615" and mt.post_url("123", 5) == ""
    assert mt.origin_of([("2026-10-02", "b/2"), ("2026-10-01", "a/1")]) == ("2026-10-01", "a/1")

    assert len(mt.validate_labels({"1": {"label": "tank", "keep": "yes"}})) == 2
    sheet = {"sheet": "20261003-001", "cells": {"1": {"key": "p1", "channel": "ANO_CBST", "msg_id": 5},
                                                   "2": {"key": "p2", "channel": "ANO_CBST", "msg_id": 6}}}
    ledger = {"p1": {"label": "logo", "keep": False, "by": "main"}}
    n = mt.apply_labels(ledger, sheet, {"1": {"label": "handover", "keep": True},
                                        "2": {"label": "equipment", "keep": True, "note": "two drones"}},
                        "haiku", "2026-10-03")
    assert n == 1 and ledger["p1"]["label"] == "logo", "main's label stands"
    mt.apply_labels(ledger, sheet, {"2": {"label": "handover", "keep": True, "mission": "none"}}, "main", "2026-10-04")
    assert ledger["p2"]["mission"] == "none"
    mt.apply_labels(ledger, sheet, {"2": {"label": "equipment", "keep": True, "note": "two drones"}}, "haiku", "2026-10-03")
    ledger["p2"] = {"label": "equipment", "keep": True, "note": "two drones", "by": "haiku",
                    "as_of": "2026-10-03", "sheet": "20261003-001", "post": "ANO_CBST/6"}
    assert ledger["p2"] == {"label": "equipment", "keep": True, "note": "two drones", "by": "haiku",
                            "as_of": "2026-10-03", "sheet": "20261003-001", "post": "ANO_CBST/6"}

    # CLIP evidence score: posing-only ranks below a handover; an unranked picture sits in the middle
    posing = {"p": {"people": 0.9, "handover": 0.1}}
    handover = {"p": {"handover": 0.8, "equipment": 0.15, "people": 0.05}}
    assert mt.evidence_score(posing) < mt.evidence_score(None) < mt.evidence_score(handover)

    # text inside a picture surfaces as a hit
    assert mt.id_hits("Командиру в/ч 12345, ИНН 9702064851") == ["ИНН 9702064851", "в/ч 12345"]
    hits = mt.registry_matcher()
    assert any("булат" in x for x in hits("Бойцам передали комплексы «Булат»")), "positive control: a registry product"
    assert hits("") == []

    # a same-size, different-content re-download (a retried pull landing a corrupted/different
    # payload of coincidentally equal length) must still count as changed, not be skipped forever
    # on a size-only check
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        f = d / "same-size.bin"
        f.write_bytes(b"\x01" * 100)
        prior = {"size": 100, "sha256": mt.sha256(f)}
        assert mt._changed_since_processed(f, prior) is False, "identical bytes: not changed"
        f.write_bytes(b"\x02" * 100)  # same size, different content
        assert mt._changed_since_processed(f, prior) is True, "same size but different bytes must still re-process"
        assert mt._changed_since_processed(f, {}) is True, "never-seen file is changed"

    print("test_media_triage: ok")


if __name__ == "__main__":
    main()
