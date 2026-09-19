#!/usr/bin/env python3
"""Extract YouTube/VK/Rutube/Дзен/OK links from archived text-like files in data/sources/.

Local only. Writes data/registry/_source_video_links.json {filename: [urls]}; promo_video_sources.py
reads it to add off-Telegram channels for entities whose own site was captured (SITE_<ИНН>_..., WEBCAPTURE_<ИНН>_...).
"""
import json, os, re, sys, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAT = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/(?:@|channel/|c/|user/|watch\?v=|embed/)[^\s"\'<>)]+|youtu\.be/[^\s"\'<>)]+'
    r'|vk\.(?:com|ru)/(?:video|club|public|[A-Za-z0-9_.]+)[^\s"\'<>)]*|vkvideo\.ru/[^\s"\'<>)]+'
    r'|rutube\.ru/(?:channel|video|u)/[^\s"\'<>)]+|dzen\.ru/[^\s"\'<>)]+|ok\.ru/[^\s"\'<>)]+)', re.I)
SKIP = re.compile(r"(share|sharer|intent|login|away\.php|widget|api\.|/dev|css|\.js|\.png|\.svg)", re.I)


def main() -> int:
    hits: dict[str, set] = {}
    n = 0
    for f in glob.glob(str(ROOT / "data/sources/*")):
        if not re.search(r"\.(html?|txt|md|json)$", f, re.I) or os.path.getsize(f) > 8_000_000:
            continue
        n += 1
        text = open(f, errors="ignore").read()
        for m in PAT.findall(text):
            u = m.rstrip(".,;\\")
            if not SKIP.search(u):
                hits.setdefault(os.path.basename(f), set()).add(u)
    out = ROOT / "data/registry/_source_video_links.json"
    out.write_text(json.dumps({k: sorted(v) for k, v in hits.items()}, ensure_ascii=False, indent=1))
    print(f"{n} files scanned, {len(hits)} with links -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
