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

    # The core packet: one file, one exhibit list, the centre printed as a non-profit and not as its own resident.
    core = bp.build_core(False, bp.GAP_CSV, bp.GAP_AS_OF)
    body, exhibits = core.split("## Exhibits", 1)
    cited = set(re.findall(r"\[E(\d+)\]", body))
    rows = set(re.findall(r"^\| E(\d+) \|", exhibits, re.M))
    assert cited == rows and cited, (cited ^ rows)
    for inn in ("9702064851", "9703232234", "9703244871", "4632306583", "9714068459", "9705196180", "7744000912"):
        assert f"| {inn} |" in core, inn
    part1 = body.split("## Part 1:", 1)[1].split("## Part 2:", 1)[0]
    assert "This record is ЦБСТ itself." in part1 and "**Documented**" not in part1, "no inbound ties listed as the hub's own"
    assert "is a non-profit organisation registered in Russia" in part1
    assert "Its recorded participants are Фонд «Наша Правда»" in part1, "both founders, not only the last row"
    # Non-profit money is funds received/used, one row per year however many copies of the filing are on file.
    assert "| 2024 | ₽269.8m | ₽98.0m |" in part1 and part1.count("| 2024 |") == 1
    assert "| Year | Revenue |" not in part1
    # The Tula namesake is named only to keep it apart, never as a member.
    assert "7100032961" in core.split("## Members", 1)[0] and "| ООО «Центр беспилотных систем» |" not in core
    # Closed register sections are said as such, with the last readable value.
    assert "Its participants' section is closed («Доступ к сведениям ограничен»)" in core
    assert "Its general director is — (EGRUL-restricted)" not in core
    assert "Registry entry: None" not in core
    ext = bp.build_core(True, bp.GAP_CSV, bp.GAP_AS_OF)
    assert not re.search(r"\bs\d{4}\b", ext) and "Appendix (internal" not in ext
    print("ok: evidence packet fixtures pass")


if __name__ == "__main__":
    main()
