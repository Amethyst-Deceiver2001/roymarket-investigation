#!/usr/bin/env python3
"""Generate the Design System artifact's tokens.json and bundle.css from design/roymarket.css.

    python3 design/build_ds_artifact.py

roymarket.css stays the single source: its bare :root block gives the light values, the
[data-theme="dark"] block the dark ones, and everything after the token blocks is the
component stylesheet. Writes design/artifact/project/{tokens.json,components/bundle.css};
the README, previews and index in that folder are hand-written. Local, no network.
"""
import datetime as dt
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS = (HERE / "roymarket.css").read_text()
OUT = HERE / "artifact" / "project"

USAGE = {
    "paper": "Page ground. Chrome, carries no finding.",
    "panel": "Card and callout surface, one step off the paper.",
    "panel-2": "Quote blocks and recessed surfaces.",
    "ink": "Body and heading text; the hub's 2px border.",
    "ink-2": "Secondary text: dek, card rows, glosses.",
    "ink-3": "Labels, kind tags, metadata. Use at 11px+ in mono caps only.",
    "rule": "Card borders and column rules.",
    "rule-soft": "Faint dividers.",
    "accent": "Links, focus rings, footnote numbers. Structure only, never a finding.",
    "accent-soft": "Highlight behind a targeted footnote.",
    "g-doc": "Documented grade: solid line, chip text. A primary document shows the link.",
    "g-doc-bg": "Ground of the Documented chip.",
    "g-rep": "Reported grade: dashed line, chip text. One party's own word or the press.",
    "g-rep-bg": "Ground of the Reported chip.",
    "g-rep-ink": "Reported chip text. The line amber is under 4.5:1 as small text; darkening the line instead would merge it with sanction red for deuteranopes.",
    "g-open": "Not documented grade: dotted line, chip text. A gap, not an alarm.",
    "g-open-bg": "Ground of the Not documented chip.",
    "sanction": "The Sanctioned flag only. The only red on a page; the flag always names the regimes.",
    "sanction-bg": "Ground of the Sanctioned flag.",
    "hub-edge": "ЦБСТ hub card border: marked by weight, not hue.",
}


def block(css, selector_re):
    m = re.search(selector_re + r"\s*\{(.*?)\n\}", css, re.S | re.M)
    return dict(re.findall(r"--([\w-]+):\s*([^;]+);", m.group(1))) if m else {}


def main():
    light = block(CSS, r"^:root")
    dark = block(CSS, r':root\[data-theme="dark"\]')
    colors, other = [], {}
    for name, val in light.items():
        val = val.strip()
        if val.startswith("#") or val.startswith("var(--"):
            v = "{" + val[6:-1] + "}" if val.startswith("var(") else val
            d = dark.get(name, "").strip()
            entry = {"name": name, "value": {"light": v, "dark": d} if d.startswith("#") else v,
                     "usage": USAGE.get(name, "")}
            colors.append(entry)
        else:
            other[name] = val
    tokens = {
        "name": "РОЙ.МАРКЕТ Reader System", "version": 2,
        "meta": {"source": "local codebase", "paths": {"tokens": ["design/roymarket.css"], "docs": ["design/README.md", "STYLE_GUIDE.md"]},
                 "synced": dt.date.today().isoformat()},
        "color": {"themes": [{"id": "light", "name": "Light"}, {"id": "dark", "name": "Dark"}], "tokens": colors},
        "type": {
            "fonts": [],
            "families": {"serif": '"Spectral", Georgia, "Times New Roman", serif',
                         "sans": '"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                         "mono": '"IBM Plex Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace'},
            "groups": [
                {"name": "Findings", "family": "serif", "styles": [
                    {"name": "h1", "fontSize": "34px", "lineHeight": 1.12, "fontWeight": 500, "sample": "«Булат» from ЦБСТ to the front line", "usage": "The page's finding, stated flat."},
                    {"name": "h2", "fontSize": "22px", "lineHeight": 1.2, "fontWeight": 500, "sample": "What this does not show", "usage": "Section heads."},
                    {"name": "card-name", "fontSize": "16px", "lineHeight": 1.25, "fontWeight": 500, "sample": "ООО «Тримикс»", "usage": "A name on a chain card; the Cyrillic legal name as registered."},
                    {"name": "quote", "fontSize": "15px", "lineHeight": 1.55, "fontWeight": 400, "sample": "«Всю нашу продукцию можно приобрести только у нас на сайте 3mx.ru»", "usage": "Verbatim Russian quotes."}]},
                {"name": "Text", "family": "sans", "styles": [
                    {"name": "lead", "fontSize": "17px", "lineHeight": 1.5, "fontWeight": 400, "sample": "Portable UAV detector made by ООО «Тримикс», a company under sanctions.", "usage": "The dek under a headline."},
                    {"name": "body", "fontSize": "15px", "lineHeight": 1.5, "fontWeight": 400, "sample": "Bought by state agencies under 3 contracts.", "usage": "Running text."},
                    {"name": "note", "fontSize": "13px", "lineHeight": 1.45, "fontWeight": 400, "sample": "As reported by the donor on its own Telegram channel.", "usage": "Card rows, legends, source notes."}]},
                {"name": "Evidence", "family": "mono", "styles": [
                    {"name": "label", "fontSize": "11px", "lineHeight": 1, "fontWeight": 600, "letterSpacing": "0.08em", "sample": "SOLD OR GIVEN BY", "usage": "Eyebrows, column heads, kind tags; uppercase."},
                    {"name": "identifier", "fontSize": "12.5px", "lineHeight": 1.3, "fontWeight": 400, "sample": "ИНН 7802942873", "usage": "ИНН, ОГРН, в/ч numbers: bare digits, tabular."}]}]},
        "spacing": {"tokens": [{"name": k, "value": other[k], "usage": u} for k, u in
                               (("space-1", "Hairline gaps inside chips."), ("space-2", "Icon to label; legend item gap."),
                                ("space-3", "Below eyebrows and headlines."), ("space-4", "Phone gutter; card stack gap."),
                                ("space-5", "Desktop gutter; legend to chain."), ("space-6", "Between page sections."))]},
        "radius": {"tokens": [{"name": "radius", "value": other["radius"], "usage": "Cards, quotes, callouts. Chips use 3px. Square-ish on purpose: these are documents."}]},
        "size": {"tokens": [{"name": k, "value": other[k], "usage": u} for k, u in
                            (("t-label", "Mono labels."), ("t-note", "Notes and card rows."), ("t-body", "Body."),
                             ("t-lead", "Dek."), ("t-h2", "Section heads."), ("t-h1", "Headline; 26px under 700px wide."),
                             ("measure", "Running-text width."))]},
        "shadow": {"tokens": [{"name": "shadow", "value": {"light": light["shadow"].strip(), "dark": dark["shadow"].strip()},
                               "usage": "Cards only. Callouts, quotes and absent cards carry none."}]},
    }
    (OUT / "components").mkdir(parents=True, exist_ok=True)
    (OUT / "tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=1) + "\n")
    comp = CSS[CSS.index("/* Base */"):]
    (OUT / "components" / "bundle.css").write_text("/* Generated from design/roymarket.css by design/build_ds_artifact.py. */\n" + comp)
    print(f"tokens.json: {len(colors)} colours; bundle.css: {len(comp)} bytes")


if __name__ == "__main__":
    main()
