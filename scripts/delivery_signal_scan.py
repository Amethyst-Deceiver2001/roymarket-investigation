#!/usr/bin/env python3
"""Find posts that report a handover of equipment to fighters or a unit: «передали бойцам 155-й бригады дроны «Овод»».

A delivery signal is a delivery verb (передали, привезли, вручили, доставили, отправили на фронт...) within a window of
a recipient (бойцам, парням, батальон, бригада, группировка «Центр»...) in one post. The post is then classed:
  A  it also names a registry product (products[].name_ru, «guillemet» form, or a distinctive bare word) or a maker brand
  B  it names only a product category (дрон, детектор, РЭБ, антенна, FPV...)
Class A is where a delivery event for products.json can come from; class B is the long tail to read.

Local text processing over data/roymarket.db, no network. A signal is a lead to read, never a fact: the donor, carrier,
recipient and product are only recorded after the post (and its links) is read in full, and several channels repeating
one text are one event, so hits are grouped by normalised text.

    python3 scripts/delivery_signal_scan.py --out /path/scan.jsonl          # every group, full text
    python3 scripts/delivery_signal_scan.py --channel ANO_CBST --class A
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "roymarket.db"
REG = ROOT / "data" / "registry"

WINDOW = 220  # characters between the verb and the recipient

VERB = re.compile(
    r"переда(?:ли|л|ем|ется|н[оаы]?|нных)\b|передач[аиу]\b|вручил[иа]?\b|вручен[оаы]?\b|"
    r"достав(?:или|ил|ляем|лен[оаы]?)\b|привез(?:ли|ла|ен[оаы]?)?\b|привоз(?:им|ят)\b|"
    r"отправил[иа]?\b|отправлен[оаы]?\b|направил[иа]?\b|направлен[оаы]?\b|"
    r"поставил[иа]\b|поставлен[оаы]?\b|поставк[аиу]\b|доставк[аиу]\b|выдал[иа]?\b|"
    r"получил[иа]\b|получен[оаы]?\b|вручаем\b|отгрузил[иа]?\b")

RECIPIENT = re.compile(
    r"бойц\w*|ребят\w*|парн\w*|военнослужащ\w*|подразделен\w*|отряд\w*|батальон\w*|полк[аеуомов]*\b|бригад\w*|"
    r"дивизи\w*|\bрот[аеуыой]\b|взвод\w*|группировк\w*|корпус\w*|\bармии\b|\bвдв\b|спецназ\w*|\bспн\b|"
    r"\b\d{1,3}-?(?:й|я|е|го|му|м)\s+(?:отдельн\w+\s+)?(?:бригад|полк|дивизи|батальон|рот|корпус)\w*|"
    r"добровольч\w*|штурмов\w*|расчет\w*|экипаж\w*|на\s+фронт\w*|на\s+передов\w*|в\s+зон\w*\s+сво|\bсво\b|"
    r"\bомсбр\b|\bомбр\b|\bмсп\b|\bмсд\b|\bтсд\b")

CATEGORY = re.compile(
    r"дрон\w*|беспилотн\w*|квадрокоптер\w*|\bбпла\b|\bбпл\b|\bfpv\b|мавик\w*|мультикоптер\w*|детектор\w*|"
    r"\bрэб\b|\bрэр\b|антенн\w*|тепловизор\w*|ретранслятор\w*|рации?\b|радиостанц\w*|станци\w+\s+связи|"
    r"тактическ\w+\s+(?:наушник|очк|связ)\w*|оптоволокон\w*|перехватчик\w*|подавител\w*|купол\w*")

NOISE = re.compile(r"привет\w*|поздравлен\w*|соболезнован\w*|гуманитарн\w+\s+помощь\s+(?:детям|школ)")

GENERIC_PRODUCT_WORDS = {"система", "комплекс", "модуль", "антенна", "дрон", "детектор", "станция", "изделие",
                         # ordinary nouns that are also registry product names: a match proves nothing
                         "ретранслятор", "передатчик", "приемник", "приёмник", "сигнал", "зонт", "тень", "огонек", "огонёк"}
# actors that are brands in the registry but donate or carry rather than make: reported as donors, not products
DONOR_BRANDS = {"архангел", "архангел спецназа", "архангел легион", "цбст", "наша правда", "народный фронт"}


def fold(s: str) -> str:
    return (s or "").lower().replace("ё", "е")


def product_matchers():
    """(display name, compiled regex over ORIGINAL text) for every registry product and maker brand."""
    raw = json.loads((REG / "entities.json").read_text(encoding="utf-8"))
    ents = raw if isinstance(raw, list) else raw.get("entities", raw)
    names = {}
    for e in ents:
        for p in e.get("products") or []:
            n = (p.get("name_ru") or "").strip() if isinstance(p, dict) else ""
            names.setdefault(re.sub(r"[«»\"]", "", n).strip(), e["slug"])
        for b in (e.get("brand_ru"),):
            if b:
                names.setdefault(re.sub(r"[«»\"]", "", b).strip(), e["slug"])
    # products.json records carry the bare product name («Булат»), where entity products[] hold versions
    prod_path = REG / "products.json"
    if prod_path.exists():
        for pr in json.loads(prod_path.read_text(encoding="utf-8")):
            names.setdefault(re.sub(r"[«»\"]", "", pr["name_ru"]).strip(), pr["maker"])
            for acc in pr.get("accessories") or []:
                names.setdefault(re.sub(r"[«»\"]", "", acc["name_ru"]).strip(), pr["maker"])
    out = []
    for n, slug in names.items():
        if len(n) < 3 or n.lower() in GENERIC_PRODUCT_WORDS or len(n) > 60:
            continue
        if n.lower() in DONOR_BRANDS:
            continue
        quoted = r"«\s*" + re.escape(n) + r"\s*»"
        # a bare (unquoted) word counts only when it is distinctive: 7+ letters, no spaces
        bare = r"|\b" + re.escape(n) + r"\w{0,3}\b" if len(n) >= 7 and " " not in n and n.isalpha() else ""
        out.append((n, slug, re.compile(quoted + bare, re.I)))
    return out


def classify(text: str, matchers=None):
    """Return None, or {'class','verbs','recipients','products','categories','window'} for one post's text."""
    f = fold(text)
    if not f:
        return None
    best = None
    for m in VERB.finditer(f):
        lo, hi = max(0, m.start() - WINDOW), min(len(f), m.end() + WINDOW)
        near = f[lo:hi]
        if NOISE.search(near):  # a greeting or condolence around the verb is not a handover
            continue
        rec = [r.group(0) for r in RECIPIENT.finditer(near)]
        if rec:
            best = (m, lo, hi, rec)
            break
    if not best:
        return None
    m, lo, hi, rec = best
    cats = sorted({c.group(0) for c in CATEGORY.finditer(f)})
    prods = []
    for name, slug, rx in matchers or []:
        if rx.search(text):
            prods.append({"name": name, "entity": slug})
    if not prods and not cats:
        return None
    donors = sorted({d for d in ("Архангел", "ЦБСТ", "Наша Правда", "Народный фронт", "Единая Россия", "Единой России")
                     if d.lower() in text.lower()})
    return {"donors": donors, "class": "A" if prods else "B", "verbs": sorted({v.group(0) for v in VERB.finditer(f[lo:hi])}),
            "recipients": sorted(set(rec))[:8], "products": prods[:8], "categories": cats[:6],
            "window": text[lo:hi]}


def norm_key(text: str) -> str:
    return re.sub(r"\W+", "", fold(text))[:140]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--channel", action="append", help="username (repeatable); default all channels")
    ap.add_argument("--class", dest="cls", choices=["A", "B"], help="only this class")
    ap.add_argument("--out", help="write every group as JSON lines (full, unsliced)")
    a = ap.parse_args()
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    chans = {r[0]: (r[1] or f"id{r[0]}") for r in conn.execute("select id, username from tg_channels")}
    matchers = product_matchers()
    # positive control: the matcher must find a delivery in a known sentence before it is trusted
    ctl = classify("Передали бойцам бригады дроны «Овод».", matchers)
    if not ctl or ctl["class"] != "A":
        ctl = classify("Передали бойцам бригады дроны.", matchers)
    if not ctl:
        print("control failed: the matcher found no delivery in a known sentence", file=sys.stderr)
        return 2
    only = {c.lower() for c in a.channel or []}
    groups = defaultdict(list)
    n = 0
    q = "select channel_id, msg_id, date, text, links, is_forward from tg_posts where text is not null and length(text) > 40"
    for cid, mid, date, text, links, fwd in conn.execute(q):
        n += 1
        ch = chans.get(cid, str(cid))
        if only and ch.lower() not in only:
            continue
        r = classify(text, matchers)
        if r and (not a.cls or r["class"] == a.cls):
            groups[norm_key(text)].append((date, ch, mid, links, r))
    rows = []
    for key, items in groups.items():
        items.sort(key=lambda x: x[0] or "")
        date, ch, mid, links, r = items[0]
        rows.append({"class": r["class"], "first_date": date, "first_post": f"{ch}/{mid}", "channels": sorted({i[1] for i in items}),
                     "posts": [f"{i[1]}/{i[2]}" for i in items], "links": links, **{k: r[k] for k in ("donors", "verbs", "recipients", "products", "categories", "window")}})
    rows.sort(key=lambda x: (x["class"], x["first_date"] or ""))
    cA = sum(1 for r in rows if r["class"] == "A")
    print(f"{n} posts scanned; {sum(len(g) for g in groups.values())} posts carry a delivery signal; "
          f"{len(rows)} distinct texts (class A {cA}, class B {len(rows) - cA}); control passed.")
    if a.out:
        Path(a.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        print(f"wrote {len(rows)} rows to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
