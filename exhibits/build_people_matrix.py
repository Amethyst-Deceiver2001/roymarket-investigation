#!/usr/bin/env python3
"""People who run or own several companies on file: one row per person, one chip per company.

    python3 exhibits/build_people_matrix.py      # -> exhibits/people_matrix.html

Replaces scripts/build_affiliation_matrix.py (15.09.2026) on the reader design system: names Latin first with the
Russian under RU, every tie graded and footnoted in plain words, sanctions shown only where a list names the
regime, counts computed here. A tie is a director, founder or ownership role (graph edges directs/founded/owns, and
role edges whose label says so); co-inventors and chat participants are not counted. Local file processing only.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "exhibits"))
sys.path.insert(0, str(REPO / "scripts"))
from build_chain_view import CBST, describe_source, esc, load  # noqa: E402
from display_helpers import (NAME_JS, design_head, display_name, latin_text, name_html, person_names, sanction_regimes,  # noqa: E402
                             popup_originals, reader_grade, ru_date)

DIRECTOR = re.compile(r"директор|director|ceo|руковод|head|председат|chair|президент|president", re.I)
FOUNDER = re.compile(r"учредит|founder|owner|владел|участник|\d+(?:[.,]\d+)?\s*%|share|доля", re.I)
GRADE_RANK = {"doc": 0, "rep": 1, "open": 2}


def regimes(sanctions):
    """Official regimes named by a record's sanctions[] entries (display_helpers.sanction_regimes: an aggregator
    match or an unproven identity is not a listing)."""
    return [lab for lab, _ in sanction_regimes(sanctions)]


def thumb(path: Path, px: int = 160) -> str:
    """A small JPEG data URI of a portrait, so the page carries its pictures with it."""
    import base64
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, h)   # square crop from the top third, where a portrait's face usually is
    top = max(0, min(h - side, int((h - side) * 0.25)))
    im = im.crop(((w - side) // 2, top, (w - side) // 2 + side, top + side))
    im.thumbnail((px, px))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


class Matrix:
    def __init__(self):
        self.ents = {e["slug"]: e for e in load("entities.json")}
        self.people = {p["slug"]: p for p in load("people.json")}
        self.src = {s["id"]: s for s in load("sources.json")}
        self.graph = json.loads((REPO / "data" / "registry" / "relationship_graph.json").read_text())
        self.notes = []
        self.pops = 0
        self.candidates = {}   # preview only: slug -> {file, page_url, note}; never read from the registry
        self.linked = {e["source"] if e["target"].endswith(CBST) or e["target"] == CBST else e["target"]
                       for e in self.graph["edges"] if e["type"] == "cbst_tie"}

    def ref(self, *sids):
        nums = []
        for s in sids:
            if not s or s not in self.src:
                continue
            s = self.src[s].get("duplicate_of") or s
            d = describe_source(self.src[s])
            if d not in self.notes:
                self.notes.append(d)
            nums.append(self.notes.index(d) + 1)
        return ("<sup class=\"rm-ref\">" + ",".join(f'<a href="#n{n}">{n}</a>' for n in sorted(set(nums))) + "</sup>") if nums else ""

    def pop(self, visible, ru, what="Original name of"):
        self.pops += 1
        return name_html(visible, ru, key=f"pm-{self.pops}", what=what)

    def ent_name(self, e):
        n = display_name(e)
        legal = n["legal"] or n["head"]
        vis = latin_text(n["head"]) if n["legal"] else n["latin"]
        return self.pop(vis, legal)

    def ties(self):
        """{person: {entity: [edges]}} for director / founder / owner roles."""
        out = {}
        for e in self.graph["edges"]:
            t = e.get("type")
            if t not in ("directs", "founded", "owns", "role"):
                continue
            p, x = e.get("source"), e.get("target")
            if p not in self.people or x not in self.ents:
                continue
            if t == "role" and not (DIRECTOR.search(e.get("label") or "") or FOUNDER.search(e.get("label") or "")):
                continue
            out.setdefault(p, {}).setdefault(x, []).append(e)
        return out

    def role(self, edges):
        labels = " ".join(e.get("label") or "" for e in edges)
        d = any(e["type"] == "directs" for e in edges) or bool(DIRECTOR.search(labels))
        f = any(e["type"] in ("founded", "owns") for e in edges) or bool(FOUNDER.search(labels))
        share = re.search(r"(\d+(?:[.,]\d+)?)\s*%", labels)
        text = ("director and founder" if d and f else "director" if d else "founder or owner")
        if share and f:
            text += f", {share.group(1).replace(',', '.')}%"
        former = all(e.get("temporal_status") == "former" for e in edges)
        grade = min((e.get("grade") or "open" for e in edges), key=lambda g: GRADE_RANK.get(g, 2))
        return text + (" (former)" if former else ""), grade, sorted({e["source_id"] for e in edges if e.get("source_id")})

    def chip(self, slug, edges):
        e = self.ents[slug]
        text, grade, sids = self.role(edges)
        core = e.get("tier") == "cbst-core" or slug == CBST
        mark = ('<span class="mk core">TsBST core</span>' if core else
                '<span class="mk tie">linked to TsBST</span>' if slug in self.linked else "")
        regs = regimes(e.get("sanctions"))
        sanc = f'<span class="rm-sanction">Sanctioned <b>{esc(", ".join(regs))}</b></span>' if regs else ""
        return (f'<li class="chip g-{grade}{" core" if core else ""}"><span class="nm">{self.ent_name(e)}</span>'
                f'<span class="rl">{esc(text)}{self.ref(*sids[:2])}</span>{mark}{sanc}</li>')

    def rows(self):
        ties = self.ties()
        multi = {p: es for p, es in ties.items() if len(es) >= 2}
        order = sorted(multi, key=lambda p: (-len(multi[p]), -sum(1 for x in multi[p] if x in self.linked or
                                                                    self.ents[x].get("tier") == "cbst-core"),
                                             person_names(self.people[p]["fio_ru"])["surname"]))
        out = []
        for i, p in enumerate(order, 1):
            pr = self.people[p]
            pn = person_names(pr["fio_ru"], pr.get("name_latin"))
            regs = regimes(pr.get("sanctions"))
            n_tie = sum(1 for x in multi[p] if x in self.linked or self.ents[x].get("tier") == "cbst-core")
            chips = "".join(self.chip(x, es) for x, es in sorted(
                multi[p].items(), key=lambda kv: (0 if kv[0] in self.linked or self.ents[kv[0]].get("tier") == "cbst-core" else 1,
                                                  GRADE_RANK.get(self.role(kv[1])[1], 2))))
            out.append(f'<li class="pr" data-tie="{1 if n_tie else 0}"><div class="who">{self.face(pr, pn)}<span class="rk">{i:02d}</span>'
                       f'<h3 class="rm-name">{self.pop(pn["first"], pn["fio"])}</h3>'
                       + (f'<span class="rm-sanction">Sanctioned <b>{esc(", ".join(regs))}</b></span>' if regs else "")
                       + f'<p class="cnt"><b>{len(multi[p])}</b> companies'
                       + (f' · <b>{n_tie}</b> linked to TsBST' if n_tie else "") + '</p></div>'
                       f'<ul class="chips">{chips}</ul></li>')
        n_ties = sum(len(es) for es in multi.values())
        n_ent = len({x for es in multi.values() for x in es})
        n_tied_people = sum(1 for p in multi if any(x in self.linked or self.ents[x].get("tier") == "cbst-core" for x in multi[p]))
        return out, len(multi), n_ties, n_ent, n_tied_people

    def face(self, pr, pn):
        """The person's portrait: the registry's own photo; on a preview build, a candidate found by search, marked
        as an unverified match with its source page; otherwise initials."""
        # A photo path is repo-relative (exhibits/images/profiles/, moved off the public docs/ on 24.10.2026) or, in
        # older records, relative to docs/.
        photo = pr.get("photo") and (REPO / pr["photo"] if pr["photo"].startswith("exhibits/") else REPO / "docs" / pr["photo"])
        if photo and photo.exists():
            return f'<img class="face" src="{thumb(photo)}" alt="Portrait of {esc(pn["first"])}">'
        c = self.candidates.get(pr["slug"])
        if c and Path(c["file"]).exists():
            return (f'<figure class="face cand"><img src="{thumb(Path(c["file"]))}" alt="Possible portrait of {esc(pn["first"])}">'
                    f'<figcaption>Unverified match · <a href="{esc(c["page_url"])}" target="_blank" rel="noopener">source</a>'
                    f'</figcaption></figure>')
        ini = "".join(w[0] for w in pn["first"].split()[:2])
        return f'<span class="face none" aria-hidden="true">{esc(ini)}</span>'

    def notes_list(self):
        out = []
        for n, (text, url) in enumerate(self.notes, 1):
            short = re.sub(r"^https?://(www\.)?", "", url or "").rstrip("/")
            short = short if len(short) <= 40 else short.split("/")[0]
            link = f' <a href="{esc(url)}" target="_blank" rel="noopener">{esc(short)} ↗</a>' if url else ""
            out.append(f'<li id="n{n}">{esc(text)}.{link}</li>')
        return "".join(out)


CSS = """
/* People matrix: one row per person, the companies as chips. Layout only; tokens come from design/roymarket.css. */
.top { padding-top: 36px; }
main.rm-page { padding-bottom: 64px; }
.figs { display: flex; flex-wrap: wrap; gap: 10px 36px; margin: 0 0 var(--space-4); }
.fig { display: flex; flex-direction: column; gap: 2px; max-width: 220px; }
.fig .n { font: 500 30px/1.1 var(--font-serif); font-variant-numeric: tabular-nums; color: var(--ink); }
.fig .w { font-size: var(--t-note); color: var(--ink-2); }
.tools { display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; margin: 0 0 var(--space-4); font-size: var(--t-note); color: var(--ink-2); }
.tools label { display: inline-flex; gap: 6px; align-items: center; cursor: pointer; }
.people { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.pr { display: grid; grid-template-columns: minmax(200px, 17rem) minmax(0, 1fr); gap: 8px 24px; padding: 14px 0;
  border-top: 1px solid var(--rule-soft); }
.pr[hidden] { display: none; }
.who { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.who .rk { font: 500 12px/1 var(--font-mono); color: var(--ink-3); }
.face { width: 72px; height: 72px; border-radius: 50%; object-fit: cover; display: block; background: var(--panel-2);
  border: 1px solid var(--rule); margin: 0 0 4px; }
figure.face { border: 0; background: none; width: auto; height: auto; border-radius: 0; display: flex; flex-direction: column; gap: 3px; }
figure.face img { width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 1px dashed var(--ink-3); }
figure.face figcaption { font: 400 10.5px/1.2 var(--font-mono); color: var(--ink-3); }
.face.none { display: flex; align-items: center; justify-content: center; font: 500 20px/1 var(--font-serif); color: var(--ink-3); }
.who .rm-name { font-size: 17px; }
.who .cnt { margin: 0; font-size: var(--t-note); color: var(--ink-2); }
.who .rm-sanction { align-self: flex-start; }
.chips { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 8px; }
.chip { display: flex; flex-direction: column; gap: 3px; padding: 8px 10px; background: var(--panel); border-radius: var(--radius);
  border: 1px solid var(--rule); border-left-width: 3px; min-width: 0; font-size: var(--t-note); }
.chip.g-doc { border-left-color: var(--g-doc); }
.chip.g-rep { border-left-color: var(--g-rep); border-left-style: dashed; }
.chip.g-open { border-left-color: var(--g-open); border-left-style: dotted; }
.chip.core { border-color: var(--hub-edge); border-left-width: 3px; }
.chip .nm { font: 500 14px/1.3 var(--font-serif); color: var(--ink); overflow-wrap: anywhere; }
.chip .rl { color: var(--ink-2); }
.chip .mk { font: 600 9.5px/1.3 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-3); }
.chip .mk.core { color: var(--ink); }
.chip .rm-sanction { align-self: flex-start; font-size: 9px; }
.key { display: flex; flex-wrap: wrap; gap: 6px 18px; list-style: none; padding: 0; margin: 0 0 var(--space-4); font-size: var(--t-note); color: var(--ink-2); }
.key .sw { display: inline-block; width: 18px; height: 12px; border: 1px solid var(--rule); border-left-width: 3px; vertical-align: -1px; margin-right: 6px; background: var(--panel); }
.key .sw.g-doc { border-left-color: var(--g-doc); }
.key .sw.g-rep { border-left-color: var(--g-rep); border-left-style: dashed; }
.key .sw.core { border-color: var(--hub-edge); }
.prose { margin-top: var(--space-6); }
@media (max-width: 760px) { .pr { grid-template-columns: minmax(0, 1fr); } }
"""


def render(out: Path):
    M = Matrix()
    today = dt.date.today().isoformat()
    if "--candidates" in sys.argv:   # preview only, never the public build
        M.candidates = json.loads(Path(sys.argv[sys.argv.index("--candidates") + 1]).read_text(encoding="utf-8"))
    rows, n_people, n_ties, n_ent, n_tied = M.rows()
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_people_matrix.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>One Person, Many Companies</title>
{design_head(CSS)}</head>
<body>
<header class="rm-page top">
  <p class="rm-eyebrow">Draft · {ru_date(today)}</p>
  <h1 class="rm-h1">One person, many companies <span class="rm-muted">the people who direct or own two or more of the companies on file</span></h1>
  <p class="rm-dek">The same few people sit behind many of the companies around TsBST. Each row is one person; each chip
  is a company where the record shows them as director, founder or owner, drawn in the style of its evidence.</p>
  <div class="figs">
    <div class="fig"><span class="n">{n_people}</span><span class="w">people hold such a role at two or more companies</span></div>
    <div class="fig"><span class="n">{n_ties}</span><span class="w">roles between them</span></div>
    <div class="fig"><span class="n">{n_ent}</span><span class="w">companies involved</span></div>
    <div class="fig"><span class="n">{n_tied}</span><span class="w">of the people hold a role at a company linked to TsBST</span></div>
  </div>
  <ul class="key" aria-label="How to read the chips">
    <li><span class="sw g-doc"></span>A register entry or filing shows the role</li>
    <li><span class="sw g-rep"></span>Reported: the party's own word or the press</li>
    <li><span class="sw core"></span>TsBST itself or its core</li>
    <li>Numbers refer to the sources at the end. Counted from the registry on {ru_date(today)}.</li>
  </ul>
  <div class="tools"><label for="only-tie"><input type="checkbox" id="only-tie"> Only people with a role at a company linked to TsBST</label></div>
</header>
<main class="rm-page">
  <ol class="people">{"".join(rows)}</ol>
  <section class="prose rm-prose"><h2 class="rm-h2">What this does not show</h2><ul>
    <li>This is a floor. Only roles already sourced in the investigation's registry are counted; a person may hold more.</li>
    <li>Holding roles at several companies is common and is not in itself wrongdoing. The page shows who connects the companies, not why.</li>
    <li>"Linked to TsBST" means the record holds a graded tie to TsBST for that company. The tie's evidence is on that company's own record.</li>
    <li>A sanctions flag appears only where an official list names the person or company. Aggregator matches and matches whose identity is not confirmed are left out.</li>
    <li>Co-inventors on patents and members of training chats are not counted as roles.</li>
  </ul></section>
  <section class="prose rm-prose rm-sources"><h2 class="rm-h2">Sources</h2><ol>{M.notes_list()}</ol></section>
</main>
<script>{NAME_JS}
(() => {{
  const box = document.getElementById('only-tie');
  box.addEventListener('change', () => document.querySelectorAll('.pr').forEach(r => {{ r.hidden = box.checked && r.dataset.tie !== '1'; }}));
}})();
</script>
</body></html>
"""
    out.write_text(popup_originals(doc))
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {n_people} people, {n_ties} roles, {n_ent} companies, {len(M.notes)} sources")


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    render(Path(out).resolve() if out else REPO / "exhibits" / "people_matrix.html")
