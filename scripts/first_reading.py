#!/usr/bin/env python3
"""First reading of newly pulled registry documents (ЕГРЮЛ/ЕГРИП extracts,
БФО annual accounts): what each one says that differs from the registry.

Pulls run on the user's Mac (the cloud cannot reach egrul.nalog.ru or
bo.nalog.gov.ru) and land in the gitignored data/sources/. Two halves:

  export  (Mac, after the day's pull queue)
      Turns each new pull into `pdftotext -layout` text plus a manifest
      (file name, sha256, size, ИНН, kind) and, with --push, commits them to
      the side branch `pull-inbox` under inbox/<YYYY-MM-DD>/ and pushes it.
      The commit is built with git plumbing on a private index, so the Mac
      checkout's branch, index and working tree are not touched. The PDFs
      themselves stay in data/sources/; the sha256 ties each text to its
      archived original. `pull-inbox` is never merged into main.

  read    (cloud, daily)
      For each exported document: the registry's current values next to
      what the document states (director, founders and shares, charter
      capital, name, address, main ОКВЭД, status or liquidation; revenue,
      profit, non-profit funds, headcount), with the document's own lines
      quoted in Russian. Writes a Markdown worksheet.

The worksheet is a proposal for a human to read. Nothing here writes to
data/registry/: a change enters the registry only through
corrections_*.json after someone has read the document (CLAUDE.md hard rule).

Usage:
    python3 scripts/first_reading.py export --push               # today's new pulls
    python3 scripts/first_reading.py export --since 2026-10-01 --dry-run
    python3 scripts/first_reading.py read --inbox inbox/2026-10-03 --out reading.md

Local file processing plus one `git push` of text to this repo; no registry
site is contacted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO / "data" / "sources"
ENTITIES = REPO / "data" / "registry" / "entities.json"
STATE = SOURCES_DIR / ".first_reading_exported.json"  # gitignored with data/sources/
BRANCH = "pull-inbox"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_egrul_vypiska as egrul  # noqa: E402
import parse_bfo_financials as bfo  # noqa: E402

KIND_RE = re.compile(r"^(EGRULAPI|EGRUL|EGRIP|BFO)_(\d{10,12})_(\d{4,8})_")


def classify(name: str) -> tuple[str, str, str] | None:
    """(kind, inn, date-or-year segment) from the archiving convention, else None."""
    m = KIND_RE.match(name)
    return (m.group(1), m.group(2), m.group(3)) if m else None


# ---------------------------------------------------------------- export

def to_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, timeout=120)
        return out.stdout.decode("utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        return path.read_text(encoding="utf-8")
    return ""


def pull_date(path: Path, seg: str) -> date:
    """EGRUL/EGRIP/EGRULAPI names carry the pull date; БФО names carry the
    fiscal year, so their pull date is the file's modification time."""
    if len(seg) == 8:
        try:
            return datetime.strptime(seg, "%Y%m%d").date()
        except ValueError:
            pass
    return date.fromtimestamp(path.stat().st_mtime)


def git(*args, env=None, inp=None) -> str:
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, env=env, input=inp)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def push_inbox(day: str, files: dict[str, str]) -> str:
    """Commit {path-in-branch: text} onto origin/pull-inbox without touching the checkout."""
    exists = subprocess.run(["git", "fetch", "-q", "origin", BRANCH], cwd=REPO, capture_output=True).returncode == 0
    parent = git("rev-parse", "FETCH_HEAD") if exists else None
    man_path = f"inbox/{day}/manifest.json"
    if parent and man_path in files:
        prev = subprocess.run(["git", "show", f"{parent}:{man_path}"], cwd=REPO, capture_output=True, text=True)
        if prev.returncode == 0:  # a second export the same day adds to that day's manifest
            cur = json.loads(files[man_path])
            seen = {d["sha256"] for d in cur["documents"]}
            cur["documents"] = [d for d in json.loads(prev.stdout)["documents"] if d["sha256"] not in seen] + cur["documents"]
            files[man_path] = json.dumps(cur, ensure_ascii=False, indent=2) + "\n"
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(td) / "index")}
        if parent:
            git("read-tree", parent, env=env)
        for rel, text in files.items():
            blob = git("hash-object", "-w", "--stdin", inp=text)
            git("update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}", env=env)
        tree = git("write-tree", env=env)
    msg = f"Pull inbox {day}: {sum(1 for p in files if p.endswith('.txt'))} document(s) for first reading"
    commit = git("commit-tree", tree, *(["-p", parent] if parent else []), "-m", msg)
    git("push", "-q", "origin", f"{commit}:refs/heads/{BRANCH}")
    return commit


def cmd_export(a) -> int:
    since = date.fromisoformat(a.since) if a.since else date.today()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    picked = []
    for p in sorted(SOURCES_DIR.iterdir()):
        c = classify(p.name)
        if not c or not p.is_file() or p.suffix.lower() not in (".pdf", ".json"):
            continue
        if pull_date(p, c[2]) < since:
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha in state and not a.force:
            continue
        picked.append((p, c, sha))
    day = date.today().isoformat()
    print(f"{len(picked)} new document(s) pulled since {since}")
    files, manifest = {}, []
    for p, (kind, inn, seg), sha in picked:
        text = to_text(p)
        note = None if text.strip() else "no text layer (scanned PDF?): read the PDF on the Mac"
        rel = f"inbox/{day}/{p.stem}.txt"
        files[rel] = text
        manifest.append({"file": p.name, "text": Path(rel).name, "kind": kind, "inn": inn,
                         "segment": seg, "sha256": sha, "bytes": p.stat().st_size,
                         "text_chars": len(text), "note": note})
        print(f"  {kind:8} {inn}  {p.name}  ({len(text):,} chars){'  ' + note if note else ''}")
    if not picked:
        return 0
    files[f"inbox/{day}/manifest.json"] = json.dumps(
        {"exported": datetime.now().isoformat(timespec="seconds"), "since": since.isoformat(),
         "documents": manifest}, ensure_ascii=False, indent=2) + "\n"
    if a.local_dir and not a.dry_run:  # Mac: read the same day without the branch round-trip
        for rel, text in files.items():
            out = Path(a.local_dir) / Path(rel).relative_to("inbox")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
        print(f"wrote {len(files)} file(s) under {Path(a.local_dir) / day}")
    if a.dry_run or not a.push:
        print("dry run: nothing committed" if a.dry_run else "not pushed (add --push)")
        return 0
    commit = push_inbox(day, files)
    for _, _, sha in picked:
        state[sha] = day
    STATE.write_text(json.dumps(state, indent=1))
    print(f"pushed {commit[:10]} to {BRANCH} (inbox/{day}/)")
    return 0


# ---------------------------------------------------------------- read

def fold(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).replace("ё", "е").replace("Ё", "Е").strip().casefold()


def lines_with(text: str, *needles: str, width: int = 3) -> list[str]:
    """The document's own lines around each needle, verbatim (for quoting)."""
    ls = text.splitlines()
    out = []
    for i, l in enumerate(ls):
        if any(n in l for n in needles):
            chunk = [x.rstrip() for x in ls[i:i + width] if x.strip()]
            out.append(" / ".join(re.sub(r"\s{2,}", "  ", x.strip()) for x in chunk))
    return out


SECTIONS = {  # label -> (start marker, end markers): quoted verbatim for the reader
    "Наименование": ("Наименование", ["Место нахождения", "Адрес юридического лица", "Сведения о регистрации"]),
    "Адрес": ("Адрес юридического лица", ["Сведения о регистрации", "Сведения о регистрирующем", "Сведения о состоянии"]),
    "Состояние / прекращение": ("Сведения о состоянии", ["Сведения о регистрирующем", "Сведения о лице", "Сведения о прекращении"]),
    "Прекращение": ("Сведения о прекращении", ["Сведения о регистрирующем", "Сведения о лице"]),
    "Основной вид деятельности": ("Сведения об основном виде деятельности", ["Сведения о дополнительных", "Сведения о лицензиях", "Сведения о записях"]),
}


def section_text(text: str, start: str, ends: list[str], cap: int = 900) -> str | None:
    sec = egrul.section(text, start, ends)
    if not sec:
        return None
    sec = "\n".join(re.sub(r"\s{2,}", "  ", l.strip()) for l in sec.splitlines() if l.strip())
    return sec[:cap] + (" …" if len(sec) > cap else "")


def read_egrul(text: str, e: dict | None) -> tuple[list[str], list[str]]:
    """(differences, verbatim sections)."""
    diffs = []
    reg = e or {}
    d = egrul.parse_director(text)
    if d and d.get("restricted"):
        if not str(reg.get("director") or "").startswith("—"):
            diffs.append(f"Director: the extract withholds it («Доступ к сведениям ограничен»); registry has {reg.get('director')!r}")
    elif d:
        if fold(d["name"]) != fold(reg.get("director")):
            diffs.append(f"Director: extract names {d['name']} ({d.get('position') or 'должность не прочитана'}, "
                         f"record dated {d.get('as_of') or '?'}); registry has {reg.get('director')!r}")
    else:
        diffs.append("Director: the parser found no director section; read it in the text")
    cap = egrul.parse_capital(text)
    if cap and reg.get("charter_capital") not in (None, "") and float(cap["value"]) != float(reg["charter_capital"] or 0):
        diffs.append(f"Charter capital: extract {cap['value']:,} ₽ (record dated {cap.get('as_of')}); registry {reg.get('charter_capital')}")
    elif cap and reg.get("charter_capital") in (None, ""):
        diffs.append(f"Charter capital: extract {cap['value']:,} ₽ (record dated {cap.get('as_of')}); registry has none")
    fr = egrul.parse_founders(text)
    reg_f = {fold(f.get("name")): f for f in (reg.get("founders") or []) if isinstance(f, dict)}
    if fr["restricted"]:
        if reg_f:
            diffs.append("Founders: the extract now withholds them («Доступ к сведениям ограничен»); registry lists "
                         + "; ".join(f.get("name", "?") for f in reg_f.values()))
    else:
        doc_f = {fold(f["name"]): f for f in fr["founders"]}
        for k, f in doc_f.items():
            share = f.get("share_percent")
            if k not in reg_f:
                diffs.append(f"Founder not in registry: {f['name']}"
                             f"{' ИНН ' + (f.get('inn') or f.get('inn_personal')) if f.get('inn') or f.get('inn_personal') else ''}"
                             f", share {share if share is not None else '?'}% (dated {f.get('as_of') or '?'})")
            elif share is not None and reg_f[k].get("share_percent") not in (None, share):
                diffs.append(f"Founder share changed: {f['name']} {reg_f[k].get('share_percent')}% → {share}%")
        for k, f in reg_f.items():
            if k not in doc_f and fr["founders"]:
                diffs.append(f"Founder in registry but not in the extract: {f.get('name')}")
    m = re.search(r"Сведения об основном виде деятельности[\s\S]{0,300}?Код и наименование вида деятельности\s+(\d{2}(?:\.\d{1,2}){0,2})\s", text)
    reg_ok = str(reg.get("okved_code") or reg.get("okved_main") or "").split()[0:1]
    if m and reg_ok and m.group(1) != reg_ok[0]:
        diffs.append(f"Main ОКВЭД: extract {m.group(1)}; registry {reg_ok[0]}")
    elif m and not reg_ok:
        diffs.append(f"Main ОКВЭД: extract {m.group(1)}; registry has none")
    secs = []
    for label, (start, ends) in SECTIONS.items():
        s = section_text(text, start, ends)
        if s:
            secs.append(f"**{label}** (verbatim):\n```\n{s}\n```")
    if "Сведения о прекращении" in text or re.search(r"ликвидац|исключени|недействующ", text, re.I):
        hits = lines_with(text, "ликвидац", "исключени", "недействующ", "прекращ")[:6]
        diffs.append("Status: the extract mentions liquidation, exclusion or termination: " + " | ".join(hits))
    return diffs, secs


def read_bfo(text: str, e: dict | None, year: str) -> tuple[list[str], list[str]]:
    reg = e or {}
    got = bfo.parse_pdf_text(text)
    units = got.get("units") or "?"
    scale = 1000 if "тыс" in units.lower() else 1
    have = {str(f.get("year")): f for f in (reg.get("financials") or [])}
    diffs = []
    fig = {k: (v * scale if isinstance(v, (int, float)) else v) for k, v in got.items()
           if k in ("revenue", "net_profit") or k.startswith("funds_")}
    shown = ", ".join(f"{k} {v:,.0f} ₽" for k, v in fig.items() if isinstance(v, (int, float)))
    if year not in have:
        diffs.append(f"Accounts for {year} are new to the registry: {shown or 'no figures parsed: read the text'} (units: {units})")
    else:
        old = have[year]
        for k, rk in (("revenue", "revenue"), ("net_profit", "profit")):
            v, r = fig.get(k), old.get(rk)
            if isinstance(v, (int, float)) and isinstance(r, (int, float)) and abs(v - r) > 1:
                diffs.append(f"{year} {rk}: filing {v:,.0f} ₽, registry {r:,.0f} ₽ (a correction filing?)")
    if got.get("funds_identity_check"):
        diffs.append("Non-profit funds identity: " + got["funds_identity_check"])
    if any(k.startswith("funds_") for k in fig):
        diffs.append("Non-profit filing: funds_* are not revenue")
    m = re.search(r"[Сс]реднесписочная численность[^\n]*?(\d[\d\s]*)\s*(?:чел|$)", text)
    if m:
        n = re.sub(r"\s", "", m.group(1))
        diffs.append(f"Headcount stated: {n} "
                     f"(registry workforce_history has {len(reg.get('workforce_history') or [])} entries)")
    quotes = lines_with(text, " 2110 ", " 2400 ", " 6200 ", " 6300 ", "Единица измерения", "численность", width=1)
    return diffs, ["**Lines read** (verbatim):\n```\n" + "\n".join(quotes[:10]) + "\n```"] if quotes else []


def cmd_read(a) -> int:
    inbox = Path(a.inbox)
    man = json.loads((inbox / "manifest.json").read_text(encoding="utf-8"))
    ents = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_inn = {e["inn"]: e for e in ents if e.get("inn") and not e.get("_merged_into")}
    out = [f"# First reading: pulls exported {man['exported']}",
           "", "Proposals for a human to check against the documents. Nothing here is in the registry.", ""]
    for d in man["documents"]:
        e = by_inn.get(d["inn"])
        head = f"## {e['name_ru'] if e else 'ИНН ' + d['inn'] + ' (no registry record)'} · {d['kind']} · {d['file']}"
        out += [head, f"sha256 `{d['sha256'][:16]}…`, {d['bytes']:,} bytes" + (f"; {d['note']}" if d.get("note") else ""), ""]
        text = (inbox / d["text"]).read_text(encoding="utf-8")
        if not text.strip():
            out += ["No text to read.", ""]
            continue
        if d["kind"] in ("EGRUL", "EGRIP"):
            diffs, secs = read_egrul(text, e)
        elif d["kind"] == "BFO":
            diffs, secs = read_bfo(text, e, d["segment"])
        else:  # EGRULAPI: the light JSON snapshot
            diffs, secs = [], [f"```\n{text[:1200]}\n```"]
        out += ["**Differences found by the parser:**"] + ([f"- {x}" for x in diffs] or ["- none"]) + [""] + secs + [""]
    Path(a.out).write_text("\n".join(out), encoding="utf-8") if a.out else print("\n".join(out))
    if a.out:
        print(f"wrote {a.out} ({len(man['documents'])} documents)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export", help="Mac: text of new pulls to the pull-inbox branch")
    ex.add_argument("--since", help="YYYY-MM-DD, pull date on or after (default: today)")
    ex.add_argument("--push", action="store_true", help="commit to origin/pull-inbox")
    ex.add_argument("--dry-run", action="store_true")
    ex.add_argument("--force", action="store_true", help="re-export documents already exported")
    ex.add_argument("--local-dir", help="also write <dir>/<date>/ locally, for `read` on the Mac")
    rd = sub.add_parser("read", help="cloud: worksheet of differences for one inbox day")
    rd.add_argument("--inbox", required=True, help="an inbox/<date> directory from the pull-inbox branch")
    rd.add_argument("--out")
    a = ap.parse_args()
    return cmd_export(a) if a.cmd == "export" else cmd_read(a)


if __name__ == "__main__":
    sys.exit(main())
