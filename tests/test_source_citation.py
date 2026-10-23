#!/usr/bin/env python3
"""Fixtures for scripts/source_citation.py (B4 reader citations).

No pytest dependency - plain assertions, run directly:
    python3 tests/test_source_citation.py

Locks down the rules a reader sees in every footnote: a Telegram post resolves to its public
link whichever header format the capture used, a Wayback capture links the archived copy, a
procurement record links its registry card, and no title carries a file name or a source id.
"""
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import source_citation as C  # noqa: E402


def rec(name, **kw):
    return {"id": "s0001", "path": f"data/sources/{name}", **kw}


def facts_of(name, text):
    d = Path(tempfile.mkdtemp())
    p = d / name
    p.write_text(text, encoding="utf-8")
    return C.facts(p)


def test_telegram_headers():
    for head in ("t.me/asidyakin (own channel), channel_id 1, msg_id 618, 2025-12-15",
                 "Channel: t.me/asidyakin (id 1)\nMessage id: 618\n",
                 "Channel: @asidyakin (channel_id 1) | Msg ID: 618 | Date: 2025-12-15"):
        f = facts_of("TGPOST_20251215_x.txt", head)
        t, u = C.cite(rec("TGPOST_20251215_x.txt", as_of="2025-12-15"), f)
        assert u == "https://t.me/asidyakin/618", (head, u)
        assert t == "Telegram, @asidyakin, post 618, 15.12.2025", t


def test_private_chat_has_no_link():
    f = facts_of("TGPOST_20240925_y.txt", "private Telegram chat «Академия» msg_id 5")
    t, u = C.cite(rec("TGPOST_20240925_y.txt"), f)
    assert u is None and "closed chat «Академия»" in t, t


def test_wayback_links_the_capture():
    html = '<title>Оферта</title><script>__wm.wombat("https://roimarket.ru/legal/supplier-offer","20260822091340"</script>'
    f = facts_of("WAYBACK_20260822_offer.html", html)
    t, u = C.cite(rec("WAYBACK_20260822_offer.html"), f)
    assert u == "https://web.archive.org/web/20260822091340/https://roimarket.ru/legal/supplier-offer", u
    assert t.startswith("«Оферта», web page archived by the Internet Archive, 22.08.2026"), t


def test_procurement_and_trademark_links():
    t, u = C.cite(rec("ZAKUPKI_CONTRACT_1463204748024000101_20260829.html"), {})
    assert "reestrNumber=1463204748024000101" in u and "no. 1463204748024000101" in t
    t, u = C.cite(rec("TRADEMARK_RU1125967_20250625_ooo-trimiks.html"), {})
    assert u.endswith("DocNumber=1125967") and "1125967" in t


def test_court_case_number():
    t, u = C.cite(rec("A40-211563-2022_20221109_Opredelenie.pdf"), {})
    assert t == "Arbitration court ruling (определение), case А40-211563/2022, 09.11.2022", t


def test_no_internal_notation():
    names = ["EGRUL_7802942873_20260907_ooo-trimiks.pdf", "BFO_7802942873_2023_ооо-тримикс.pdf",
             "TGMEDIA_9705196180_20250211_nashapravdafond-post393-1.jpg", "ARTIFACT_20260826_brief.html",
             "bf074f6f-b83d-402b-a413-77c124e18ab0.pdf"]
    for n in names:
        t, _ = C.cite(rec(n, captured_date="2026-09-07"), {})
        assert not re.search(r"\.(pdf|html?|jpe?g)\b|\bs\d{4}\b|ooo-|_", t), t
        assert t[:1].isupper(), t



def test_relative_canonical_is_resolved_or_dropped():
    tg = ('<link rel="canonical" href="/s/readovkanews?before=65390">'
          '<a href="https://t.me/readovkanews/65389">')
    assert facts_of("PRESS_20230903_x.html", tg)["url"] == "https://t.me/s/readovkanews?before=65390"
    wp = ('<link rel="canonical" href="/fond-sarmat/">'
          '<link rel="https://api.w.org/" href="https://barssarmat.ru/wp-json/">')
    assert facts_of("SITE_6154168283_20260919_x.html", wp)["url"] == "https://barssarmat.ru/fond-sarmat/"
    og = '<link rel="canonical" href="/"><meta property="og:url" content="https://wheelies.ru/">'
    assert facts_of("WEB_9200026034_20261001_x.html", og)["url"] == "https://wheelies.ru/"
    # No host on the page: no public link rather than a broken one.
    assert "url" not in facts_of("SITE_x_20260919_y.html", '<link rel="canonical" href="/nashi/">')
    assert facts_of("WEB_x_20261001_y.html", '<link rel="canonical" href="https://a.ru/b">')["url"] == "https://a.ru/b"

def test_packet_exhibit_titles():
    """Titles the 03.10.2026 packet check found naming the wrong kind of document."""
    t, _ = C.cite(rec("FEDRESURS_939B297414FA48A4A4B3497315AF3659_20260903_gagaring-audit-report-2025fy-full.pdf",
                      captured_date="2026-09-03"), {})
    assert t == "Auditor's report on the annual accounts, as published on Fedresurs, FY 2025, 03.09.2026", t
    t, _ = C.cite(rec("FEDRESURS_ABC_20260903_notice.pdf", captured_date="2026-09-03"), {})
    assert t.startswith("Fedresurs register record"), t
    for name, want in (("OFAC_7300024069_20261005_ooo-skb-piranya-sdn-49943.xml", "US Treasury (OFAC) Specially Designated Nationals list, entry, 05.10.2026"),
                       ("SECO_7300024069_20261005_ooo-skb-piranya-105178.xml", "Swiss SECO sanctions list, entry, 05.10.2026"),
                       ("EU_7300024069_20261005_ooo-skb-piranya-fsf-EU.14019.43.xml", "EU consolidated financial sanctions list, entry, 05.10.2026"),
                       ("UKSL_7300024069_20261005_x-RUS1402.xml", "UK Sanctions List (FCDO), entry, 05.10.2026")):
        t, _ = C.cite(rec(name, captured_date="2026-10-05"), {})
        assert t == want, (name, t)
    t, _ = C.cite(rec("EGRUL_780223272953_20261006_inn-780223272953.pdf", captured_date="2026-10-06"), {})
    assert t == "Sole-trader register extract (EGRIP, Federal Tax Service) for INN 780223272953, 06.10.2026", t
    t, u = C.cite(rec("UKAZ_415-2025_20250620_president-decree-nsdc-sanctions.html", captured_date="2026-10-05"), {})
    assert t.startswith("Decree of the President of Ukraine no. 415/2025") and u == "https://zakon.rada.gov.ua/laws/show/415/2025", (t, u)
    t, _ = C.cite(rec("OFAC_20240823_recent-action-russia-related-designations.html", captured_date="2026-10-05"), {})
    assert t.startswith("US Treasury (OFAC) recent actions notice"), t
    t, _ = C.cite(rec("HHRU_2312321660_20260904_gagaring-vacancy-lawyer-goz.txt", captured_date="2026-08-07"), {})
    assert t == "Job vacancy posted on hh.ru, 07.08.2026", t
    t, _ = C.cite(rec("CERT_4800016776_20260823_kilovatt-official-dealer-2106-2024.pdf", captured_date="2026-08-23"), {})
    assert t.startswith("Official dealer certificate"), t
    t, _ = C.cite(rec("CERT_1_20260101_conformity.pdf", captured_date="2026-01-01"), {})
    assert t.startswith("Certificate or declaration of conformity"), t
    f = facts_of("TGPOST_20250512_ano_cbst-706-cbst-tie-evidence.txt", "t.me/ano_cbst (own channel), channel_id 1, msg_id 706, 2025-05-12")
    t, u = C.cite(rec("TGPOST_20250512_ano_cbst-706-cbst-tie-evidence.txt", as_of="2025-05-12"), f)
    assert t.endswith("(transcript of the database text, not a capture of the page)") and u == "https://t.me/ano_cbst/706", (t, u)


def test_registry_prefixes_have_titles():
    cases = {
        "RNP_6165205064_20260907_debarment.html": "Register of unscrupulous suppliers (RNP) record, 07.09.2026",
        "WHOIS_proekt-arhangel-ru_20260905.txt": "Domain registration (WHOIS) record, 05.09.2026",
        "SANCTIONSLISTS_20261004_canada-sema/SANCTIONS_CA_20261004.xml": "Canadian (SEMA) sanctions list, full download, 04.10.2026",
        "ATR_20260825_reestr-potentsialnykh-ispolniteley-bas-components.pdf": "ATR register of potential UAV-component executors, 25.08.2026",
    }
    for name, want in cases.items():
        iso = None
        for part in name.replace("/", "_").split("_"):
            if len(part) >= 8 and part[:8].isdigit() and part.startswith("2026"):
                iso = f"{part[:4]}-{part[4:6]}-{part[6:8]}"
        t, _ = C.cite(rec(name, captured_date=iso), {})
        assert t == want, (t, want)
        assert not t.startswith("Archived document"), t


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
