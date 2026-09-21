"""Generates docs/profiles/index.html -- a browsable list of every generated
company, person and product profile page, so the landing page has one place
to link to. Local file processing only; titles are read off the pages that
already exist, tiers off entities.json, so it can never list a dead link.
"""
import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROFILES = REPO / "docs" / "profiles"
TIER_ORDER = [("cbst-core", "ЦБСТ core"), ("manufacturer", "Manufacturers"), ("money-layer", "Money layer"),
              ("plumbing", "Plumbing"), ("network", "Network"), ("unverified", "Unverified"),
              ("adjacent", "Adjacent (no confirmed ЦБСТ tie)")]


def title_of(path):
    m = re.search(r"<title>(.*?)</title>", path.read_text(encoding="utf-8"), re.S)
    t = html.unescape(m.group(1)) if m else path.stem
    return re.sub(r"\s+[—-]\s+РОЙ\.МАРКЕТ investigation$", "", t).strip()


def li(rel, path):
    return f'<li><a href="{rel}">{html.escape(title_of(path))}</a></li>'


def main():
    raw = json.load(open(REPO / "data/registry/entities.json", encoding="utf-8"))
    ents = raw if isinstance(raw, list) else raw["entities"]
    tier = {e["slug"]: (e.get("tier") or "unverified") for e in ents}
    groups = {k: [] for k, _ in TIER_ORDER}
    for f in sorted(PROFILES.glob("*.html")):
        if f.name == "index.html":
            continue
        t = tier.get(f.stem, "unverified")
        groups.setdefault(t if t in groups else "unverified", []).append(li(f.name, f))
    people = [li(f"persons/{f.name}", f) for f in sorted((PROFILES / "persons").glob("*.html"))]
    products = [li(f"products/{f.name}", f) for f in sorted((PROFILES / "products").glob("*.html"))]

    def section(label, items):
        cols = "column-count:2;column-gap:2rem;" if len(items) > 12 else ""
        return f'<section><p class="eyebrow">{html.escape(label)} · {len(items)}</p><ul class="plain" style="{cols}">{"".join(items)}</ul></section>'

    body = "".join(section(lbl, groups[k]) for k, lbl in TIER_ORDER if groups.get(k))
    body += section("Products", products) + section("People", people)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profile index — РОЙ.МАРКЕТ investigation</title>
<link rel="stylesheet" href="../assets/profile.css">
</head>
<body>
<div class="wrap">
  <div class="mast">
    <p class="kicker">РОЙ.МАРКЕТ investigation</p>
    <h1>Profile index</h1>
    <p><a href="../index.html">Home</a> · <a href="../cases/index.html">Cases</a> · <a href="../story.html">Guided read</a> · <a href="../relationship-graph.html">Relationship graph</a></p>
  </div>
{body}
</div>
</body>
</html>
"""
    (PROFILES / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote docs/profiles/index.html — {sum(len(v) for v in groups.values())} companies, {len(products)} products, {len(people)} people")


if __name__ == "__main__":
    main()
