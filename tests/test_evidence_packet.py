#!/usr/bin/env python3
"""Fixtures for exhibits/build_evidence_packet.py, against the real registry.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_evidence_packet.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "exhibits"))
import build_evidence_packet as bp  # noqa: E402


def main():
    text = bp.build("ooo-gagaring", False, bp.GAP_CSV, bp.GAP_AS_OF)
    assert text.splitlines()[2].startswith("**DRAFT"), "every packet opens with the draft warning"
    assert "ИНН 2312321660, ОГРН 1232300051235" in text
    # Every exhibit number cited in the body has a row in the exhibit list, and no row is unused.
    body, exhibits = text.split("## Exhibits", 1)
    cited = set(re.findall(r"\[E(\d+)\]", body))
    rows = set(re.findall(r"^\| E(\d+) \|", exhibits, re.M))
    assert cited == rows and cited, (cited ^ rows)
    # Researcher notes stay out of the body; open questions only in the internal appendix.
    assert "_corrected" not in text and "Appendix (internal" in text
    # The statement of reasons leaves the conclusion to the submitter.
    assert "[Conclusion and criterion: for the submitter.]" in text

    ext = bp.build("ooo-gagaring", True, bp.GAP_CSV, bp.GAP_AS_OF)
    assert not re.search(r"\bs\d{4}\b", ext), "external packet carries no internal source ids"
    assert "Appendix (internal" not in ext

    assert bp.rub_m(-514000.0) == "−₽0.5m" and bp.rub_m(None) == "—"
    top = bp.top_unlisted(bp.GAP_CSV, 3)
    assert len(top) == 3 and "ooo-smart-teknolodzhis" in top, top
    print("ok: evidence packet fixtures pass")


if __name__ == "__main__":
    main()
