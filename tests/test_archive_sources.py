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
