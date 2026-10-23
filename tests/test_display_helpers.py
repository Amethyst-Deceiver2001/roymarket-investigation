#!/usr/bin/env python3
"""Fixtures for English-first reader rendering helpers."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from display_helpers import caption_html, figure_html, quote_html  # noqa: E402


def test_caption_translation_keeps_original_under_ru():
    out = caption_html("Первая партия из 50 дронов", "cap-m0004", "First batch of 50 drones")
    assert "First batch of 50 drones" in out
    assert 'popovertarget="nm-cap-m0004"' in out
    assert 'lang="ru" class="rm-nm-v">Первая партия из 50 дронов</span>' in out
    assert "Pervaya partiya" not in out


def test_caption_without_translation_fails_instead_of_transliterating():
    try:
        caption_html("Первая партия", "cap-missing")
    except ValueError as exc:
        assert "needs an English translation" in str(exc)
    else:
        raise AssertionError("Russian captions without a translation must not render as transliteration")


def test_english_caption_rejects_cyrillic_fallback():
    try:
        caption_html("Русская подпись", "cap-bad", "Russkaya подпись")
    except ValueError as exc:
        assert "must not contain Cyrillic" in str(exc)
    else:
        raise AssertionError("English captions must not include Cyrillic text")


def test_english_caption_needs_no_popover():
    assert caption_html("Product photo from the official site") == "Product photo from the official site"


def test_quote_translation_transliterates_names_and_preserves_original():
    out = quote_html("ЦБСТ сообщает «Булат»", "ЦБСТ сообщает «Булат»", key="q-test")
    assert "TsBST soobshchaet" in out
    assert "«Bulat»" in out
    assert 'lang="ru" class="rm-nm-v">ЦБСТ сообщает «Булат»</span>' in out


def test_figure_uses_english_translation_for_caption_and_alt():
    out = figure_html(
        {"id": "m0004", "shows": "Первая партия", "shows_en": "First batch", "asserted_by": "self"},
        "image.jpg",
        "the publisher",
        "",
    )
    assert 'alt="First batch"' in out
    assert "First batch" in out
    assert "Pervaya" not in out


def test_publishable_registry_captions_have_english_translations():
    media = json.loads((ROOT / "data" / "registry" / "media.json").read_text(encoding="utf-8"))
    for item in media:
        if item.get("publish") not in ("ok", "excerpt") or not re.search(r"[А-Яа-яЁё]", item.get("shows") or ""):
            continue
        assert item.get("shows_en"), item["id"]
        assert not re.search(r"[А-Яа-яЁё]", item["shows_en"]), item["id"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
