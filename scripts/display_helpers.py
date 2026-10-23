"""Small display helpers shared by the page builders.

Moved out of build_company_profile.py on 2026-10-02 when the old case and profile
generators were archived (scripts/archive/); the chain view and any new builder import
them from here.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_contract import CONFIDENCE_GRADE  # noqa: E402

TYPE_LABELS = {
    "EGRUL": "EGRUL extract",
    "EGRULAPI": "EGRUL open-API record",
    "EGRIP": "EGRIP (sole-proprietor registry) record",
    "РЕСУРС": "БФО annual-accounts filing",
    "UD": "Founding-Устав bundle",
    "TGMEDIA": "Telegram media",
    "CATALOG": "product catalog",
    "WEBCAPTURE": "site capture",
    "SITE": "site capture",
    "TRANSCRIPT": "transcript",
    "ATR": "АТР federal-grant registry PDF",
    "AERONEXT": "АЭРОНЕКСТ member record",
    "DOSSIER": "third-party OSINT dossier",
    "TRADEMARK": "Rospatent trademark record",
    "PATENT": "Rospatent patent record",
    "ROSPATENT": "Rospatent record",
    "ALEPH": "OCCRP Aleph screening record",
    "OPENSANCTIONS": "OpenSanctions screening record",
    "GUR": "GUR war-sanctions record",
    "COURT": "court filing",
    "PRESS": "press coverage",
    "CERT": "certificate/licence record",
    "DATASET": "bulk open-data extract",
    "ROM": "securing-measures registry record",
    "RMSP": "SME-registry record",
    "OZON": "Ozon marketplace capture",
    "HAR": "browser HAR capture",
}


def ru_date(iso_date):
    """YYYY-MM-DD -> DD.MM.YYYY (Russian convention), per STYLE_GUIDE.md §2.4.
    Passes through unchanged if it doesn't match the expected ISO shape."""
    if not iso_date:
        return iso_date
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso_date)
    if not m:
        return iso_date
    year, month, day = m.groups()
    return f"{day}.{month}.{year}"


REPO = Path(__file__).resolve().parent.parent
DESIGN_CSS = REPO / "design" / "roymarket.css"
FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600'
             '&family=IBM+Plex+Sans:wght@400;600&family=Spectral:wght@400;500&subset=cyrillic&display=swap">')


def design_head(page_css: str = "", fonts_href: str | None = None) -> str:
    """Font link plus the design system CSS and a page's own CSS, inlined in that order.
    fonts_href: a self-hosted fonts.css (public pages, from design/fetch_fonts.py) in place of Google Fonts."""
    link = f'<link rel="stylesheet" href="{fonts_href}">' if fonts_href else FONT_LINK
    return f"{link}\n<style>{DESIGN_CSS.read_text()}\n{page_css}</style>"


# Reader grades (design/README.md). Every registry confidence vocabulary maps here, in one table,
# so a page never decides a grade on its own. Values do not collide across vocabularies.
READER_GRADE_LABELS = {"doc": "Documented", "rep": "Reported", "open": "Not documented"}
READER_GRADE = CONFIDENCE_GRADE   # one table, in graph_contract.py (B1)


def reader_grade(value) -> str:
    """Registry confidence value -> 'doc' | 'rep' | 'open'. Unknown or missing is 'open'."""
    return READER_GRADE.get(value, "open")


# Kind marks: 24x24 line icons, drawn in currentColor by .rm-kind svg. Military units use the
# APP-6 frame (unit_mark) instead.
KIND_ICONS = {
    "company": '<path d="M4 21V8l6-3v16M10 21V3l10 4v14M3 21h18M13 9h4M13 13h4M13 17h4"/>',
    "person": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1-4 4-6 7-6s6 2 7 6"/>',
    "product": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
    "storefront": '<path d="M4 9l1.5-5h13L20 9M4 9c0 1.7 1.3 3 3 3s2.7-1.3 2.7-3c0 1.7 1.3 3 2.3 3s2.3-1.3 2.3-3c0 1.7 1.3 3 3 3s2.7-1.3 2.7-3M5 12v8h14v-8M10 20v-5h4v5"/>',
    "buyer": '<path d="M3 9l9-5 9 5M5 9v9M9.5 9v9M14.5 9v9M19 9v9M3 20h18"/>',
    "program": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
    "event": '<rect x="4" y="5" width="16" height="15" rx="1"/><path d="M4 10h16M8 3v4M16 3v4"/>',
    "group": '<rect x="3" y="7" width="11" height="11" rx="1"/><rect x="10" y="4" width="11" height="11" rx="1"/>',
    "unit": '<path d="M12 3l9 9-9 9-9-9z"/>',   # the APP-6 hostile frame, as a label-sized mark
}


def kind_icon(kind: str) -> str:
    body = KIND_ICONS.get(kind)
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{body}</svg>' if body else ""


# APP-6 echelon marks drawn above the frame. Only from the unit record's own echelon field.
_ECHELON = {"battalion": 2, "regiment": 3, "brigade": "x1", "division": "x2", "army": "x4"}


def unit_mark(echelon: str | None = None) -> str:
    """Monochrome APP-6 hostile (diamond) land-unit frame with an optional echelon mark.
    No branch glyph is drawn until the unit record carries a sourced branch."""
    e = _ECHELON.get(echelon or "")
    marks = ""
    if isinstance(e, int):
        xs = [17 + (i - (e - 1) / 2) * 5 for i in range(e)]
        marks = "".join(f'<path class="ech" d="M{x} 3v5"/>' for x in xs)
    elif isinstance(e, str):
        n = int(e[1:])
        xs = [17 + (i - (n - 1) / 2) * 6 for i in range(n)]
        marks = "".join(f'<path class="ech" d="M{x-2} 3l4 5M{x+2} 3l-4 5"/>' for x in xs)
    return (f'<svg class="rm-unit" viewBox="0 0 34 40" aria-hidden="true">{marks}'
            '<path class="frame" d="M17 10l14 14-14 14L3 24z"/></svg>')


# Media (track V). Provenance is said in words, from asserted_by; never shown by colour.
PROVENANCE = {"self": "Published by {who}", "third_party": "Posted by a third party", "platform": "From a marketplace listing",
              "press": "From press coverage", "counterparty": "From the counterparty", "regulator": "From a regulator",
              "investigator": "Our capture"}


def load_media() -> list[dict]:
    p = REPO / "data" / "registry" / "media.json"
    import json
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def media_about(media: list[dict], refs: set[tuple[str, str]], publishable=True) -> list[dict]:
    """Media whose about[] names any (type, id) in refs. Publishable only: publish ok/excerpt and no face pending."""
    out = []
    for m in media:
        if not any((a.get("type"), a.get("id")) in refs for a in m.get("about") or []):
            continue
        if publishable and (m.get("publish") == "internal" or m.get("redact") == "blur_pending"):
            continue
        out.append(m)
    return out


def publish_copy(m: dict, dest_dir: Path, max_px: int = 1200) -> str | None:
    """Copy a media file into dest_dir as <id>.<ext>, downscaled to max_px; returns the file name."""
    src = REPO / (m.get("file") or "")
    if not m.get("file") or not src.exists():
        # a clone without data/sources/ keeps the committed copy rather than dropping the picture
        made = sorted(dest_dir.glob(f"{m['id']}.*")) if m.get("id") else []
        return made[0].name if made else None
    dest_dir.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".svg":
        out = dest_dir / f"{m['id']}.svg"
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            out.write_bytes(src.read_bytes())
        return out.name
    ext = src.suffix.lower() if src.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"
    out = dest_dir / f"{m['id']}{ext}"
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        from PIL import Image
        im = Image.open(src)
        if m.get("genre") == "logo":   # trim the empty margin so the mark fills its slot
            from PIL import ImageChops
            rgb = im.convert("RGB")
            bg = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
            box = ImageChops.difference(rgb, bg).convert("L").point(lambda v: 255 if v > 24 else 0).getbbox()
            if box:
                pad = 6
                im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad)))
        im.thumbnail((max_px, max_px))
        im.save(out)
    return out.name


_CYR = r"[А-Яа-яЁё][А-Яа-яЁё0-9\-]*"
_KNOWN_EN = [("«Единая Россия»", "United Russia"), ("Единая Россия", "United Russia"), ("Единой России", "United Russia"),
             ("ЦБСТ", "TsBST"), ("ПСБ", "PSB"), ("МПТМ", "MPTM"), ("«Наша Правда»", "Nasha Pravda"), ("«Наша правда»", "Nasha Pravda"),
             ("РОЙ.МАРКЕТ", "ROY.MARKET"), ("«Роймаркет»", "Roymarket"), ("Роймаркет", "Roymarket"),
             # Ukrainian places in their Ukrainian-based English spelling (STYLE_GUIDE §2.2), also in stored English
             ("Zaporozhye", "Zaporizhzhia"), ("Zaporozhie", "Zaporizhzhia"), ("Lugansk", "Luhansk"), ("Gorlovka", "Horlivka"),
             ("Nikolaev", "Mykolaiv"), ("Kharkov", "Kharkiv")]


def latinize_gloss(t: str) -> str:
    """English prose that still carries Cyrillic names (a stored gloss written before the Latin-first rule): known names
    first, then letter-by-letter transliteration. A Russian slang phrase quoted and glossed ("тупо одноразовые" /
    effectively disposable) keeps only the gloss. Quoted originals belong under RU, never here."""
    t = re.sub(r'"[^"]*[А-Яа-яЁё][^"]*"\s*/\s*', "", t or "")
    for a, b in _KNOWN_EN:
        t = t.replace(a, b)
    return re.sub(_CYR, lambda m: latin_text(m.group(0)).upper() if m.group(0).isupper() and len(m.group(0)) > 1 and not any(c.isdigit() for c in m.group(0)) else latin_text(m.group(0)), t)


def orig_line(ru: str, key: str, en: str | None = None, what: str = "Russian original of") -> str:
    """A Russian line quoted from a document, English first: our translation (or a transliteration) in quotation marks,
    the original under RU."""
    tr = translation(ru)
    shown = en or (tr["en"] if tr else latinize_gloss(ru))
    shown = latinize_gloss(shown)
    return name_html("\u201c" + shown.strip().strip("\u201c\u201d") + "\u201d", ru, key=key, what=what)


def caption_html(text: str, key: str = "cap", en: str | None = None) -> str:
    """Render a picture caption in English, with its original wording under RU when it contains Cyrillic."""
    import html as _h
    text = text or ""
    en = (en or "").strip()
    if en and re.search(r"[А-Яа-яЁё]", en):
        raise ValueError(f"{key}: English media caption must not contain Cyrillic")
    if re.search(r"[А-Яа-яЁё]", text):
        if en:
            return name_html(en.strip(), text, key=key, what="Original caption for")
        # no supplied translation (descriptions that are not media records): translate each printed «…» passage,
        # transliterate the rest; check_registry.py demands shows_en for publishable media captions
        out, pos, n = [], 0, 0
        for m in re.finditer(r"«([^«»]*[А-Яа-яЁё][^«»]*)»", text):
            out.append(_h.escape(latinize_gloss(text[pos:m.start()])))
            n += 1
            tr = translation(m.group(1))
            shown = tr["en"] if tr else latinize_gloss(m.group(1))
            out.append(name_html("«" + shown + "»", "«" + m.group(1) + "»", key=f"{key}-{n}", what="Printed text, original of"))
            pos = m.end()
        out.append(_h.escape(latinize_gloss(text[pos:])))
        return "".join(out)
    return _h.escape(en or text.strip())


def popup_originals(doc: str) -> str:
    """Final pass over a page: an inline Russian original beside its Latin form, `X (<span lang="ru">…</span>)` or
    `X <span class="cyr" lang="ru">…</span>`, becomes a small RU control with the original in a popover.
    Card name blocks use `<small class="cyr">` and are left as they are (the Cyrillic stays visible beside the Latin)."""
    import html as _h
    n = [0]

    def pop(m):
        n[0] += 1
        ru = _h.unescape(m.group(1))
        pid = f"nm-po-{n[0]}"
        return (f'<button type="button" class="rm-nm-k" popovertarget="{pid}" aria-label="Russian original">RU</button>'
                f'<span popover id="{pid}" class="rm-nm-pop"><span class="rm-nm-row"><span class="rm-label">Russian</span>'
                f'<span lang="ru" class="rm-nm-v">{_h.escape(ru)}</span><button type="button" class="rm-nm-copy" '
                f'data-copy="{_h.escape(ru)}">Copy</button></span></span>')
    doc = re.sub(r'\s*\(<span lang="ru">([^<]+)</span>\)', pop, doc)
    return re.sub(r'\s*<span class="cyr" lang="ru">([^<]+)</span>', pop, doc)


def figure_html(m: dict, img_src: str, who: str, ref_html: str, video_note: str = "") -> str:
    """One evidence figure. `who` names the publisher for self-published media."""
    import html as _h
    prov = PROVENANCE.get(m.get("asserted_by"), "Source").format(who=who)
    when = ru_date(m.get("published")) or ""
    cls = "rm-fig rm-video" if video_note else "rm-fig"
    caption = caption_html(m["shows"], "cap-" + str(m.get("id")), m.get("shows_en"))
    alt = m.get("shows_en") or m["shows"]
    return (f'<figure class="{cls}"><div class="frame"><img src="{_h.escape(img_src)}" alt="{_h.escape(alt)}"></div>'
            f'<figcaption><span class="rm-prov">{_h.escape(prov)}</span><span>{caption}{ref_html}</span>'
            + (f'<span class="orig">{_h.escape(video_note)}</span>' if video_note else "")
            + (f'<span class="when">{when}</span>' if when else "") + "</figcaption></figure>")


def display_name(e: dict) -> dict:
    """The names a card shows (B5). `head` is the documented primary brand when there is one, else the legal
    name; `legal` is the registered name, always shown when it differs from head; `gloss` the English line."""
    parts = (e.get("name_ru") or "").split(" | ", 1)
    legal, gloss = _strip_note(parts[0]), (parts[1] if len(parts) > 1 else "")
    brand = next((b["name"] for b in e.get("brands") or [] if b.get("primary") and b.get("name")), None)
    return {"head": brand or legal, "legal": legal if brand and brand != legal else "", "gloss": gloss,
            "latin": e.get("name_display") or latin_display(legal)}


# Latin display names (B5, STYLE_GUIDE §2.3): the legal form transliterated, never translated (OOO, AO, ANO), and
# the name in «» transliterated letter by letter, never translated. A simplified BGN/PCGN scheme without
# diacritics, matching the guide's own examples (OOO «Tekhnodron», NPTs); ё is written e, as sanctions lists do.
_LAT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s",
                 "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya"]))
# Spelled-out legal forms in a registered name -> the abbreviation they stand for, so the Latin form is the
# string a screening analyst searches (OOO, not "Obshchestvo s ogranichennoy otvetstvennostyu").
_LONG_FORMS = [
    (r"общество с ограниченной ответственностью", "ООО"), (r"публичное акционерное общество", "ПАО"),
    (r"закрытое акционерное общество", "ЗАО"), (r"акционерное общество", "АО"),
    (r"автономная некоммерческая организация", "АНО"), (r"индивидуальный предприниматель", "ИП"),
]


def _lat_word(w: str) -> str:
    # An all-caps abbreviation (no vowel) keeps one capital per Cyrillic letter (НПЦ -> NPTs, ЦБСТ -> TsBST);
    # an all-caps word is set wholly in capitals (НАУЧНО -> NAUCHNO, ДЖИ -> DZHI), as sanctions lists write it.
    if len(w) > 1 and w.isupper() and re.search(r"[АЕЁИОУЫЭЮЯ]", w):
        return "".join(_LAT.get(ch.lower(), ch) for ch in w).upper()
    caps = len(w) > 1 and w.isupper()
    out = []
    for ch in w:
        t = _LAT.get(ch.lower())
        if t is None:
            out.append(ch)
        elif ch.isupper():
            out.append(t.upper() if caps and len(t) == 1 else t[:1].upper() + t[1:])
        else:
            out.append(t)
    return "".join(out)


def _strip_note(name: str) -> str:
    """Drop our own trailing bracketed note from a registered name: "(прекратил деятельность …)", or a founder's
    surname used to tell two namesakes apart ("(Шестопалов)"). An all-caps alias like "(ФКК)" is kept. Readers tell
    namesakes apart by the ИНН on the card, never by our note."""
    return re.sub(r"\s*\((?![А-ЯЁA-Z0-9.\-]+\))[^)]*\)\s*$", "", name)


def latin_display(legal: str) -> str:
    """'ООО «Тримикс»' -> 'OOO «Trimiks»'; 'НПЦ «Ушкуйник»' -> 'NPTs «Ushkuynik»'. Latin letters pass unchanged."""
    # A trailing note in brackets is ours, not part of the registered name ("(прекратил деятельность …)",
    # a founder's surname used to tell two namesakes apart); an all-caps alias like "(ФКК)" is kept.
    s = _strip_note(legal)
    for pat, abbr in _LONG_FORMS:
        s = re.sub(pat, abbr, s, flags=re.I)
    return re.sub(r"[А-Яа-яЁё]+", lambda m: _lat_word(m.group(0)), s)


def latin_text(s: str) -> str:
    """Transliterate the Cyrillic words of any proper name (brand, product, event): «Булат» -> «Bulat»."""
    return re.sub(r"[А-Яа-яЁё]+", lambda m: _lat_word(m.group(0)), s or "")


# EN names (STYLE_GUIDE §2.2-2.3a): Latin first, Cyrillic always within reach. People are "Given Surname" on
# first mention with the full ФИО beside it, surname after; state bodies are translated, with the official name
# and its sanctions-style transliteration attached. Translations are hand-held in data/registry/name_translations.json.
_TRANSLATIONS = REPO / "data" / "registry" / "name_translations.json"


_PATRONYMIC_LAT = re.compile(r"(vich|vna|ichna|ogly|kyzy)$", re.I)
_PATRONYMIC = re.compile(r"(вич|вна|ична|инична|ьич|ич|оглы|кызы)$", re.I)
# Common Russian given names, to tell "Дмитрий Медведев" (given name first) from "Медведев Дмитрий" (register order)
_GIVEN = set("""Александр Алексей Анатолий Андрей Антон Аркадий Артём Артем Борис Вадим Валентин Валерий Василий Виктор Виталий
Владимир Владислав Вячеслав Геннадий Георгий Глеб Григорий Даниил Денис Дмитрий Евгений Егор Иван Игорь Илья Кирилл Константин
Лев Леонид Максим Марк Матвей Михаил Никита Николай Олег Павел Пётр Петр Роман Руслан Семён Семен Сергей Станислав Степан Тимур
Фёдор Федор Юрий Ярослав Айрат Вахид Анастасия Анна Валентина Валерия Вера Виктория Галина Дарья Евгения Екатерина Елена Ирина
Ксения Лариса Людмила Мария Марина Наталья Наталия Надежда Нина Ольга Полина Светлана Софья Татьяна Юлия""".split())


def person_names(fio_ru: str, name_latin: str | None = None) -> dict:
    """'Цыганов Вадим Борисович' -> {'first': 'Vadim Tsyganov', 'surname': 'Tsyganov', 'fio': the ФИО}.
    Also reads the given-name-first order some records use ('Александр Геннадьевич Сидякин', 'Дмитрий Медведев'),
    by the patronymic's position or a known given name. name_latin, when the registry holds it, is in register
    order (surname first) and wins over generation."""
    fio = re.sub(r"^ИП\s+", "", (fio_ru or "").strip())
    if name_latin and name_latin.strip():
        lat = re.sub(r"\s*\([^)]*\)", "", name_latin.strip()).split()
        if len(lat) >= 3 and _PATRONYMIC_LAT.search(lat[1]) and not _PATRONYMIC_LAT.search(lat[2]):
            return {"first": f"{lat[0]} {lat[2]}", "surname": lat[2], "fio": fio}   # Given Patronymic Surname
        if len(lat) >= 2:
            return {"first": f"{lat[1]} {lat[0]}", "surname": lat[0], "fio": fio}
        return {"first": " ".join(lat), "surname": " ".join(lat), "fio": fio}
    ru = re.sub(r"\s*\([^)]*\)", "", fio).split()   # a former surname in brackets stays on the card, not in prose
    if len(ru) >= 3 and _PATRONYMIC.search(ru[1]) and not _PATRONYMIC.search(ru[2]):
        given, surname = ru[0], ru[2]                    # Имя Отчество Фамилия
    elif len(ru) == 2 and ru[0] in _GIVEN and ru[1] not in _GIVEN:
        given, surname = ru[0], ru[1]                    # Имя Фамилия
    elif len(ru) >= 2:
        given, surname = ru[1], ru[0]                    # register order: Фамилия Имя Отчество
    else:
        return {"first": latin_text(fio), "surname": latin_text(fio), "fio": fio}
    return {"first": f"{latin_text(given)} {latin_text(surname)}", "surname": latin_text(surname), "fio": fio}


def translation(name_ru: str) -> dict | None:
    """{'en': ..., 'kind': ...} for a state body's official name, or None when no one has translated it yet."""
    try:
        table = json.loads(_TRANSLATIONS.read_text()).get("names", {})
    except (OSError, ValueError):
        return None
    key = re.sub(r"\s+", " ", name_ru or "").strip()
    return table.get(key) or next((v for k, v in table.items() if k.casefold() == key.casefold()), None)


def name_html(visible: str, cyrillic: str, translit: str | None = None, key: str = "", what: str = "Original name of") -> str:
    """Latin or English name in running text, with a small control that opens the original: the Cyrillic form and,
    for a translated state body, its transliteration, each copyable (screeners paste these into registers)."""
    import html as _h
    pid = "nm-" + (key or re.sub(r"\W+", "-", latin_text(cyrillic)).strip("-").lower()[:40])
    rows = [("Russian", cyrillic, "ru")] + ([("Transliterated", translit, "ru-Latn")] if translit else [])
    body = "".join(f'<span class="rm-nm-row"><span class="rm-label">{lbl}</span><span lang="{lang}" class="rm-nm-v">'
                   f'{_h.escape(v)}</span><button type="button" class="rm-nm-copy" data-copy="{_h.escape(v)}">Copy</button></span>'
                   for lbl, v, lang in rows)
    return (f'<span class="rm-nm">{_h.escape(visible)}<button type="button" class="rm-nm-k" popovertarget="{pid}" '
            f'aria-label="{_h.escape(what)} {_h.escape(visible[:60])}">RU</button></span>'
            f'<span popover id="{pid}" class="rm-nm-pop">{body}</span>')


def quote_html(ru: str, en: str, cite: str = "", key: str = "") -> str:
    """A quotation, English first (STYLE_GUIDE §3.1, 23.10.2026): our translation in quotation marks, the verbatim
    Russian original under the RU control, copyable. `cite` is ready-made HTML (who, when, footnote)."""
    shown = "\u201c" + latinize_gloss(en).strip().strip("\u201c\u201d\"") + "\u201d"
    inner = name_html(shown, ru, key=key, what="Russian original of")
    tail = f"<cite>{cite}</cite>" if cite else ""
    return f'<blockquote class="rm-quote"><span class="rm-label">Translation</span><span class="q">{inner}</span>{tail}</blockquote>'


NAME_JS = """// Original-name popovers: copy the Cyrillic or transliterated form; select it where the clipboard is refused.
document.addEventListener('click', ev => {
  const b = ev.target.closest('.rm-nm-copy');
  if (!b) return;
  const done = () => { b.textContent = 'Copied'; setTimeout(() => { b.textContent = 'Copy'; }, 1500); };
  const pick = () => { const r = document.createRange(); r.selectNodeContents(b.previousElementSibling);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r); };
  try { navigator.clipboard.writeText(b.dataset.copy).then(done, pick); } catch (e) { pick(); }
});
"""


def source_type_label(path: str) -> str:
    stem = Path(path).name
    if stem.startswith("ul-") or stem.startswith("ip-"):
        return "EGRUL extract"
    if re.match(r"^A\d", stem):
        return "arbitration court filing"
    prefix = stem.split("_", 1)[0]
    if prefix in TYPE_LABELS:
        return TYPE_LABELS[prefix]
    return prefix.title() if prefix.isalpha() else "document"
