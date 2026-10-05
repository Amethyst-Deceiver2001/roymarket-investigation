"""Reader-facing citations for data/sources/ files (plan B4).

Two steps, so files are read once:
- facts(path)  reads what a citation needs from the file itself (a Telegram header, a page's canonical URL
  and title, a Wayback capture's original URL) and returns a small dict. inventory_sources.py caches it per
  file under "cite" (with CITE_VERSION, so a rule change re-reads every file).
- cite(source, facts)  turns a sources.json record plus those facts into (title, public_url).
  extract_registry.py writes both onto the record; page builders print them and never decide on their own.

A title is plain words for a reader: what the document is, who published it, its number and date. It never
holds a source id, a file name or a slug (STYLE_GUIDE §3.4–3.5). Bare identifiers (ИНН, case numbers,
registration numbers) are allowed: they let a specialist find the document. public_url is set only where the
file itself, or a stable registry number, gives one; otherwise it is None.
Local file processing only.
"""
import html
import re
from pathlib import Path

CITE_VERSION = 6
REPO = Path(__file__).resolve().parent.parent


def _ru(d):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", d or "")
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else (d or "")


def _read(path: Path, n: int) -> str:
    try:
        with open(path, "rb") as f:
            return f.read(n).decode("utf-8", errors="ignore")
    except OSError:
        return ""


def _page_facts(head: str) -> dict:
    out = {}
    m = (re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', head)
         or re.search(r'<link[^>]*href="([^"]+)"[^>]*rel="canonical"', head)
         or re.search(r'property="og:url"[^>]*content="([^"]+)"', head))
    if m:
        url = _absolute(html.unescape(m.group(1)), head)
        if url:
            out["url"] = url.replace("http://", "https://", 1)
    t = re.search(r"<title>([^<]+)", head) or re.search(r'property="og:title"[^>]*content="([^"]+)"', head)
    if t:
        title = re.sub(r"\s+", " ", html.unescape(t.group(1))).strip()
        if title and not re.search(r"\.(xml|html?)$|^Telegram Widget$", title):
            out["page_title"] = title[:160]
    return out


def _absolute(url: str, head: str) -> str | None:
    """A canonical link as an absolute URL, or None when the page does not say which site it is on.

    Some captures carry a relative canonical: Telegram's web preview writes "/s/<channel>?before=N", and
    WordPress sites can write "/page/". It is resolved only against the page's own host, read from an
    absolute og:url, <base href> or a rel=shortlink/alternate/EditURI/api.w.org link; never guessed.
    """
    if re.match(r"https?://", url):
        return url
    if not url.startswith("/") or url.startswith("//"):
        return ("https:" + url) if url.startswith("//") else None
    if url.startswith("/s/") and re.search(r"https?://(t\.me|telegram\.org)/", head):
        return "https://t.me" + url
    for pat in (r'property="og:url"[^>]*content="(https?://[^/"]+)',
                r'<base[^>]*href="(https?://[^/"]+)',
                r'<link[^>]*rel="(?:shortlink|alternate|EditURI|https://api\.w\.org/)"[^>]*href="(https?://[^/"]+)',
                r'<link[^>]*href="(https?://[^/"]+)[^"]*"[^>]*rel="(?:shortlink|alternate|EditURI|https://api\.w\.org/)"'):
        m = re.search(pat, head)
        if m:
            return m.group(1) + url
    return None


_WATCH = None


def _watchlist() -> set:
    global _WATCH
    if _WATCH is None:
        p = REPO / "config" / "channels.txt"
        lines = p.read_text().splitlines() if p.exists() else []
        _WATCH = {re.sub(r"^(@|https?://)?(t\.me/)?", "", x.strip()).lower() for x in lines if x.strip() and not x.startswith("#")}
    return _WATCH


def facts(path: Path) -> dict:
    """What the file itself says about where it came from. Cheap: reads a header, not the whole file."""
    name = path.name
    prefix = name.split("_", 1)[0]
    f = {"v": CITE_VERSION}
    if prefix == "TGPOST":
        head = _read(path, 800)
        chat = re.search(r"private Telegram chat «([^»]+)»", head)
        ch = re.search(r"t\.me/([A-Za-z0-9_]{4,})|Channel: @([A-Za-z0-9_]{4,})|\(@([A-Za-z0-9_]{4,})\)", head)
        msg = re.search(r"msg_id (\d+)|Message id: (\d+)|Msg ID: (\d+)|Telegram post \d+:(\d+)|t\.me/[A-Za-z0-9_]+/(\d+)", head)
        multi = name.startswith("TGPOST_multi_")
        if chat:
            f["tg_chat"] = chat.group(1).strip()
        elif ch:
            f["tg_channel"] = next(g for g in ch.groups() if g)
        else:
            # No header: the filename's channel is used only when it is a channel on the watchlist.
            m = re.match(r"TGPOST_\d{8}_([A-Za-z0-9_]+?)-(\d+)(?:-|\.)", name)
            if m and m.group(1).lower() in _watchlist():
                f["tg_channel"], f["tg_msg"] = m.group(1), m.group(2)
        if msg and not multi and "tg_msg" not in f:
            f["tg_msg"] = next(g for g in msg.groups() if g)
        if multi:
            f["tg_multi"] = True
    elif prefix == "TGWEB":
        head = _read(path, 400000)
        m = re.match(r"TGWEB_\d{8}_([A-Za-z0-9_]+?)-(\d+)(?:-|\.)", name)
        if m and f"t.me/{m.group(1)}/{m.group(2)}".lower() in head.lower():
            f["tg_channel"], f["tg_msg"] = m.group(1), m.group(2)
        else:
            c = re.match(r"TGWEB_\d{8}_([A-Za-z0-9_]+?)-(?:s-|channel)", name)
            if c and f"t.me/{c.group(1)}".lower() in head.lower():
                f["tg_channel"] = c.group(1)
    elif prefix == "WAYBACK":
        head = _read(path, 400000)
        m = re.search(r'__wm\.wombat\("([^"]+)","(\d{14})"', head)
        if m:
            f["orig_url"], f["wayback_ts"] = m.group(1), m.group(2)
        f.update({k: v for k, v in _page_facts(head).items() if k == "page_title"})
    elif path.suffix.lower() in (".html", ".htm"):
        f.update(_page_facts(_read(path, 300000)))
    return f


# --- formatting ------------------------------------------------------------------------------------------------

COURT_DOC = {"Opredelenie": "ruling (определение)", "Reshenija_i_postanovlenija": "decision",
             "Postanovlenie_apelljacionnoj_instancii": "appeal court resolution", "Prochie_sudebnye_dokumenty": "court document",
             "Reshenie_v_vide_rezoljutivnoj_chasti": "decision (operative part)"}
SIMPLE = {  # prefix -> title stem; the date is appended
    "EGRULAPI": "Company register open lookup (ЕГРЮЛ, Federal Tax Service)",
    "EGRIP": "Sole-trader register extract (ЕГРИП, Federal Tax Service)",
    "UD": "Founding documents filed with the company register (Federal Tax Service)",
    "OPENSANCTIONS": "Sanctions-list entries compiled by OpenSanctions, checked",
    "ALEPH": "OCCRP Aleph search record, checked",
    "FNS": "Federal Tax Service «Прозрачный бизнес» record, checked",
    "RUPEP": "RuPEP politically exposed persons database",
    "PEP": "RuPEP politically exposed persons database",
    "PROVERKI": "Federal register of state inspections (ЕРКНМ)",
    "FEDRESURS": "Fedresurs register record",
    "NALETAY": "Налетай marketplace page, archived",
    "NSPD": "National spatial data system (НСПД) cadastral record",
    "RKN": "Roskomnadzor register search",
    "MCHS": "МЧС fire-safety licence register search",
    "FSA": "Rosakkreditatsiya conformity register record",
    "ROM": "Federal register of securing measures (Fedresurs)",
    "GISP": "State industry information system (ГИСП) data",
    "AERONEXT": "АЭРОНЕКСТ association member record",
    "NSDC": "Extract from Ukraine's State Register of Sanctions",
    "OFAC": "US Treasury (OFAC) Specially Designated Nationals list, entry",
    "SECO": "Swiss SECO sanctions list, entry",
    "UKSL": "UK Sanctions List (FCDO), entry",
    "RUSPROFILE": "Rusprofile company page, archived",
    "OZON": "Ozon marketplace page, archived",
    "WILDBERRIES": "Wildberries seller page, archived",
    "CATALOG": "Online shop page, archived",
    "CERT": "Certificate or declaration of conformity",
    "TRANSCRIPT": "Transcript",
    "FUNDNTI": "Fund for National Technology Initiative (Фонд НТИ) document",
    "MINPROMTORG": "Ministry of Industry and Trade document",
    "DATASET": "Open government dataset",
    "COURT": "Court filing",
    "YOUTUBE": "YouTube video capture",
    "IMG": "Photograph",
    "TGFILE": "File posted on Telegram",
    "TG": "Telegram channel page, archived",
}


def cite(s: dict, f: dict | None) -> tuple[str, str | None]:
    """(title, public_url) for one sources.json record."""
    title, url = _cite(s, f)
    name = Path(s["path"]).name
    if name.startswith("TGPOST_") and "tie-evidence" in name:  # our transcript of the database text, not a page capture
        title += " (transcript of the database text, not a capture of the page)"
    return title[:1].upper() + title[1:], url


def _cite(s: dict, f: dict | None) -> tuple[str, str | None]:
    f = f or {}
    path = Path(s["path"])
    name = path.name
    prefix = name.split("_", 1)[0]
    date = _ru(s.get("as_of") or s.get("captured_date"))
    dated = f", {date}" if date else ""
    url = f.get("url")
    typ = s.get("type")

    if prefix == "ARTIFACT":
        return "Internal working document (not a source for publication)", None
    if prefix in ("TGPOST", "TGWEB"):
        if f.get("tg_chat"):
            return f"Telegram, closed chat «{f['tg_chat']}»{', message ' + f['tg_msg'] if f.get('tg_msg') else ''}{dated}", None
        if f.get("tg_channel") and f.get("tg_msg"):
            return (f"Telegram, @{f['tg_channel']}, post {f['tg_msg']}{dated}",
                    f"https://t.me/{f['tg_channel']}/{f['tg_msg']}")
        if f.get("tg_channel") and f.get("tg_multi"):
            return f"Telegram, @{f['tg_channel']}, posts read together{dated}", f"https://t.me/{f['tg_channel']}"
        if f.get("tg_channel"):
            return f"Telegram channel @{f['tg_channel']}, page archived{dated}", f"https://t.me/{f['tg_channel']}"
        return f"Telegram post{dated}", None
    if prefix == "TGMEDIA":
        m = re.match(r"TGMEDIA_(?:\d{10,12}_)?\d{8}_([A-Za-z0-9_]+)-post(\d+)", name)
        if m:
            link = f"https://t.me/{m.group(1)}/{m.group(2)}" if m.group(1).lower() in _watchlist() else None
            return f"Picture posted on Telegram, @{m.group(1)}, message {m.group(2)}{dated}", link
        return f"Picture posted on Telegram{dated}", None
    if prefix == "ZAKUPKI":
        m = re.search(r"(\d{19})", name)
        if m:
            return (f"State procurement record no. {m.group(1)}, zakupki.gov.ru",
                    f"https://zakupki.gov.ru/epz/contract/contractCard/common-info.html?reestrNumber={m.group(1)}")
        m = re.match(r"ZAKUPKI_(\d{10,12})_\d{8}_supplier-search", name)
        if m:
            return (f"State procurement search for supplier ИНН {m.group(1)}, zakupki.gov.ru{dated}",
                    f"https://zakupki.gov.ru/epz/contract/search/results.html?supplierTitle={m.group(1)}")
        return f"State procurement record, zakupki.gov.ru{dated}", None
    if prefix == "FEDRESURS" and "audit-report" in name:
        m = re.search(r"(\d{4})fy", name)
        return f"Auditor's report on the annual accounts, as published on Fedresurs{', FY ' + m.group(1) if m else ''}{dated}", None
    if prefix == "HHRU":
        return f"Job vacancy posted on hh.ru{dated}", None
    if prefix == "CERT" and "dealer" in name:
        return f"Official dealer certificate issued by the manufacturer{dated}", None
    if prefix == "EGRUL" or name.startswith("ul-") or typ == "egrul":
        m = re.match(r"EGRUL_(\d{10})_", name) or re.match(r"ul-(\d{13})-", name)
        ident = (f" for ИНН {m.group(1)}" if len(m.group(1)) == 10 else f" for ОГРН {m.group(1)}") if m else ""
        return f"Company register extract (ЕГРЮЛ, Federal Tax Service){ident}{dated}", None
    if prefix in ("BFO", "РЕСУРС") or typ == "bfo":
        m = re.search(r"_(\d{10})_(\d{4})", name)
        fy = s.get("fiscal_year") or (m.group(2) if m else (s.get("as_of") or "")[:4])
        return f"Annual accounts filed with the Federal Tax Service{', ИНН ' + m.group(1) if m else ''}, FY {fy}", None
    if typ == "minjust":
        return f"Activity report of the non-profit to the Ministry of Justice, for {(s.get('as_of') or '')[:4]}", None
    if prefix == "TRADEMARK":
        m = re.search(r"TRADEMARK_(?:RU)?(\d+)", name)
        if m:
            return (f"Trademark registration no. {m.group(1)}, Rospatent (FIPS)",
                    f"https://new.fips.ru/registers-doc-view/fips_servlet?DB=RUTM&DocNumber={m.group(1)}")
        return "Trademark record, Rospatent (FIPS)", None
    if prefix == "OCR":
        m = re.match(r"OCR_(\d{10,12})_(\d{4})_\d{8}_.*?(bfo-notes|audit-report)", name)
        if m:
            kind = "notes to the annual accounts" if m.group(3) == "bfo-notes" else "auditor's report on the annual accounts"
            return f"Text recognised (OCR) from the scanned {kind}, ИНН {m.group(1)}, FY {m.group(2)}", None
        return f"Text recognised (OCR) from a scanned document{dated}", None
    if prefix == "PATENT":
        m = re.match(r"PATENT_(RU\w+?)_", name)
        return f"Patent record{' ' + m.group(1) if m else ''}, Rospatent{dated}", None
    if prefix == "ROSPATENT":
        return f"Rospatent register search{dated}", None
    if prefix == "GUR":
        return f"Ukraine's defence intelligence (ГУР) War & Sanctions portal{dated}", url
    if prefix == "EU" and "-fsf-" in name:
        return f"EU consolidated financial sanctions list, entry{dated}", None
    if prefix == "EU":
        m = re.search(r"(implementing-regulation|council-decision|regulation|decision)-(\d{4})-(\d+)", name)
        kind = {"implementing-regulation": "Council Implementing Regulation (EU)", "council-decision": "Council Decision (CFSP)",
                "regulation": "Council Regulation (EU)", "decision": "Council Decision"}.get(m.group(1)) if m else None
        return (f"{kind} {m.group(2)}/{m.group(3)}, Official Journal of the EU" if kind else f"EU sanctions act{dated}"), url
    if prefix == "PP719":
        m = re.search(r"zaklyuchenie-([\d-]+)", name)
        return (f"Ministry of Industry and Trade conclusion under Government Resolution 719"
                f"{', no. ' + m.group(1) if m else ''}{dated}"), None
    m = re.match(r"(А|A)(\d+)-(\d+)-(\d{4})_(\d{8})_(.+)\.\w+$", name)
    if m:
        kind = next((v for k, v in COURT_DOC.items() if m.group(6).startswith(k)), "court document")
        return (f"Arbitration court {kind}, case А{m.group(2)}-{m.group(3)}/{m.group(4)}, "
                f"{_ru(f'{m.group(5)[:4]}-{m.group(5)[4:6]}-{m.group(5)[6:]}')}"), None
    if prefix == "WAYBACK":
        title = f"«{f['page_title']}», " if f.get("page_title") else ""
        if f.get("orig_url"):
            ts = f["wayback_ts"]
            return (f"{title}web page archived by the Internet Archive, {_ru(f'{ts[:4]}-{ts[4:6]}-{ts[6:8]}')}",
                    f"https://web.archive.org/web/{ts}/{f['orig_url']}")
        return f"{title}web page archived by the Internet Archive{dated}", None
    if prefix == "PRESS" or typ == "press":
        site = _site(url)
        title = f"«{f['page_title']}», " if f.get("page_title") else ""
        return f"{title}{site or 'press article'}{dated}", url
    if prefix in ("WEBCAPTURE", "SITE", "WEB"):
        site = _site(url)
        title = f"«{f['page_title']}», " if f.get("page_title") else ""
        return f"{title}web page{' on ' + site if site else ''}, archived {date}".rstrip(", "), url
    if prefix in SIMPLE:
        stem = SIMPLE[prefix]
        return f"{stem}{(' ' if stem.endswith(('archived', 'checked')) else ', ') + date if date else ''}", url
    if typ == "ustav":
        return f"Founding charter (устав){dated}", None
    return f"Archived document{dated}", url


def _site(url):
    if not url:
        return ""
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    try:
        return host.encode("ascii").decode("idna") if "xn--" in host else host
    except UnicodeError:
        return host
