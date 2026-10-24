#!/usr/bin/env python3
"""Self-host the reader fonts for the public site: docs/fonts/*.woff2 and docs/fonts/fonts.css.

    python3 design/fetch_fonts.py

One request for Google's CSS, then one per face file (20 files: IBM Plex Sans 400-600, IBM Plex Mono
400/600, Spectral 400/500; Latin and Cyrillic subsets). Google serves IBM Plex Sans as a variable font
(wght 100-700), the same file for every weight, so weights that share a file are written as one face with
a weight range (`font-weight: 400 600`) rather than two copies of the same bytes. All three families are under the SIL Open Font
License 1.1. Re-run only when the weights in display_helpers.FONT_LINK change.
"""
import datetime as dt
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "fonts"
URL = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600"
       "&family=Spectral:wght@400;500&display=swap")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SUBSETS = ("latin", "latin-ext", "cyrillic", "cyrillic-ext")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src = subprocess.run(["curl", "-s", "-A", UA, URL], check=True, capture_output=True, text=True).stdout
    out = [f"/* IBM Plex Sans, IBM Plex Mono, Spectral (SIL Open Font License 1.1), self-hosted; fetched "
           f"{dt.date.today().strftime('%d.%m.%Y')} by design/fetch_fonts.py. Latin and Cyrillic subsets. */"]
    faces = {}  # (subset, family, url) -> [weights, block]: one file per url
    for sub, block in re.findall(r"/\* ([a-z-]+) \*/\s*(@font-face \{.*?\})", src, re.S):
        if sub not in SUBSETS:
            continue
        fam = re.search(r"font-family: '([^']+)'", block).group(1)
        w = re.search(r"font-weight: (\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        faces.setdefault((sub, fam, url), [[], block])[0].append(w)
    for (sub, fam, url), (weights, block) in faces.items():
        w = weights[0] if len(weights) == 1 else f"{min(weights, key=int)}-{max(weights, key=int)}"
        name = f"{fam.lower().replace(' ', '-')}-{w}-{sub}.woff2"
        subprocess.run(["curl", "-s", url, "-o", str(OUT / name)], check=True)
        block = re.sub(r"font-weight: \d+", "font-weight: " + w.replace("-", " "), block.replace(url, name))
        out.append(f"/* {sub} */\n" + block)
    (OUT / "fonts.css").write_text("\n".join(out) + "\n")
    print(f"{len(out) - 1} faces in {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
