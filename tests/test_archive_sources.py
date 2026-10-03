#!/usr/bin/env python3
"""Fixtures for scripts/archive_sources.py (offline: planning and tiering only).

No pytest dependency - plain assertions, run directly:
    python3 tests/test_archive_sources.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import archive_sources as A  # noqa: E402


def test_classify():
    assert A.classify("https://t.me/ano_cbst/2041") == "telegram"
    assert A.classify("https://zakupki.gov.ru/epz/contract/x") == "procurement"
    assert A.classify("https://new.fips.ru/registers-doc-view/x") == "trademark"
    assert A.classify("https://web.archive.org/web/20230327050156/https://x.ru/") == "archived"
    assert A.classify("https://3mx.ru/") == "web"
    # Relative canonical links from a capture cannot be archived as given.
    assert A.classify("/s/aviaru_uav?before=1227") is None
    assert A.classify("/fond-sarmat/") is None


def test_telegram_variants():
    assert A.telegram_variants("https://t.me/s/ano_cbst/2041") == [
        "https://t.me/ano_cbst/2041", "https://t.me/ano_cbst/2041?embed=1&mode=tme"]
    assert A.telegram_variants("https://t.me/ano_cbst") == ["https://t.me/ano_cbst"]


def test_telegram_key_and_channel_hits():
    assert A.telegram_key("https://t.me/ANO_CBST/5") == ("ano_cbst", "5", False)
    assert A.telegram_key("https://t.me/s/ano_cbst/5?embed=1&mode=tme") == ("ano_cbst", "5", True)
    assert A.telegram_key("https://t.me/ano_cbst") is None
    rows = [["20260301000000", "https://t.me/Ano_Cbst/5", "A"],
            ["20251101000000", "https://t.me/ano_cbst/5", "B"],
            ["20251001000000", "https://t.me/ano_cbst/5?single", "C"],
            ["20260101000000", "https://t.me/ano_cbst/5?embed=1&mode=tme", "D"],
            ["20260101000000", "https://t.me/ano_cbst/6?comment=3", "E"]]
    h = A.channel_hits(rows)
    assert h[("ano_cbst", "5", False)]["wayback_sha1"] == "B", "earliest bare-page capture, case folded"
    assert h[("ano_cbst", "5", True)]["wayback_sha1"] == "D"
    assert ("ano_cbst", "6", False) not in h, "a comment view is not the post"


def test_preview_pages():
    assert A.preview_url("ano_cbst", 2041) == "https://t.me/s/ano_cbst?before=2042"
    html = b'<div data-post="ANO_CBST/2041"></div><div data-post="ano_cbst/2039"></div><div data-post="other/7">'
    assert A.posts_on_page(html, "ano_cbst") == {2041, 2039}
    import gzip
    assert A.posts_on_page(gzip.compress(html), "ano_cbst") == {2041, 2039}, "id_ bytes may be gzipped"


def test_telegram_capture_never_stale_and_variant_follows_base():
    today = date(2026, 10, 3)
    old = [{"timestamp": "20200101000000", "method": "existing"}]
    assert A.is_current({"kind": "telegram", "captures": old}, today)
    assert not A.is_current({"kind": "web", "captures": old}, today)
    data = {"urls": {
        "https://t.me/a/1": {"tier": 1, "kind": "telegram", "captures": old},
        "https://t.me/a/1?embed=1&mode=tme": {"tier": 1, "kind": "telegram", "captures": [],
                                              "variant_of": "https://t.me/a/1"},
        "https://t.me/a/2?embed=1&mode=tme": {"tier": 1, "kind": "telegram", "captures": [],
                                              "variant_of": "https://t.me/a/2"},
        "https://t.me/a/2": {"tier": 1, "kind": "telegram", "captures": []}}}
    assert A.pending(data, {1}, today)[0] == "https://t.me/a/2"
    # a captured post whose saved text is unavailable keeps its embed view (cannot rule out truncation)
    assert "https://t.me/a/1?embed=1&mode=tme" in A.pending(data, {1}, today)


def test_tiers():
    assert A.tier_of("telegram", True) == 1
    assert A.tier_of("web", True) == 1
    assert A.tier_of("procurement", True) == 2
    assert A.tier_of("trademark", True) == 2
    assert A.tier_of("web", False) == 3


def test_plan_merges_and_keeps_captures():
    sources = [
        {"id": "s0001", "public_url": "https://t.me/ano_cbst/1"},
        {"id": "s0002", "public_url": "https://t.me/ano_cbst/1"},   # duplicate capture
        {"id": "s0003", "public_url": "https://zakupki.gov.ru/x"},
        {"id": "s0004", "public_url": "/relative"},
        {"id": "s0005", "public_url": None},
    ]
    cap = {"service": "wayback", "timestamp": "20261001000000", "method": "saved"}
    prev = {"urls": {
        "https://t.me/ano_cbst/1": {"captures": [cap]},
        "https://gone.example/": {"captures": [cap], "kind": "web", "tier": 1},
    }}
    data, unusable = A.build_plan(sources, {"s0001"}, prev)
    u = data["urls"]
    assert unusable == [{"source_id": "s0004", "public_url": "/relative"}]
    post = u["https://t.me/ano_cbst/1"]
    assert post["source_ids"] == ["s0001", "s0002"] and post["tier"] == 1
    assert post["captures"] == [cap], "a recorded capture survives a re-plan"
    assert u["https://t.me/ano_cbst/1?embed=1&mode=tme"]["variant_of"] == "https://t.me/ano_cbst/1"
    assert u["https://zakupki.gov.ru/x"]["tier"] == 3, "uncited registry page is tier 3"
    assert u["https://gone.example/"]["dropped"] is True, "uncited URL keeps its history"


def test_pending_skips_fresh_and_dropped():
    today = date(2026, 10, 2)
    data = {"urls": {
        "a": {"tier": 1, "kind": "web", "captures": [{"timestamp": "20260901000000"}]},
        "b": {"tier": 1, "kind": "web", "captures": [{"timestamp": "20200101000000"}]},
        "c": {"tier": 1, "kind": "telegram", "captures": []},
        "d": {"tier": 1, "kind": "web", "captures": [], "dropped": True},
        "e": {"tier": 3, "kind": "web", "captures": []},
        "f": {"tier": 2, "kind": "archived", "captures": [{"method": "cited"}]},
    }}
    assert A.pending(data, {1, 2}, today) == ["c", "b"], "telegram first, stale capture re-saved"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
