"""Write a file into data/sources/ without ever changing one already there.

A source file is catalogued with its SHA-256 (sources.json) and fixed by the
timestamped manifest (timestamp_sources.py). Overwriting it in place breaks both:
the registry would cite bytes that no longer exist. The timestamp run of
03.10.2026 found 121 files rewritten that way (same-day re-runs, re-parses).

write_new() writes `path` if it is free; if a file is already there with the same
bytes it does nothing; if the bytes differ it writes `<stem>-r2<suffix>`,
`-r3`, ... and returns that path. Callers use the returned path.
"""
from __future__ import annotations

from pathlib import Path


def write_new(path: Path, data: bytes | str, encoding: str = "utf-8") -> Path:
    raw = data.encode(encoding) if isinstance(data, str) else data
    cand, n = path, 1
    while cand.exists():
        if cand.read_bytes() == raw:
            return cand
        n += 1
        cand = path.with_name(f"{path.stem}-r{n}{path.suffix}")
    cand.parent.mkdir(parents=True, exist_ok=True)
    cand.write_bytes(raw)
    return cand
