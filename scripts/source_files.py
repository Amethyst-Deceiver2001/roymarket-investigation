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

import os
import tempfile
from pathlib import Path


def write_new(path: Path, data: bytes | str, encoding: str = "utf-8") -> Path:
    raw = data.encode(encoding) if isinstance(data, str) else data
    path.parent.mkdir(parents=True, exist_ok=True)
    cand, n = path, 1
    while True:
        if cand.exists():
            if cand.read_bytes() == raw:
                return cand
            n += 1
            cand = path.with_name(f"{path.stem}-r{n}{path.suffix}")
            continue
        # Write the bytes to a private temp file in the same directory first,
        # fsync them, then claim `cand`'s name with a hard link -- os.link
        # fails with FileExistsError if anything already holds that exact
        # name, so a second writer racing us onto the same candidate (TOCTOU
        # on the `cand.exists()` check above) retries onto the next -rN
        # instead of overwriting. A crash mid-write leaves only the orphaned
        # temp file, never a half-written file under `cand`'s own name --
        # the one guarantee this whole module exists to give the RFC3161
        # timestamping chain (found missing by an adversarial code review,
        # 05.10.2026; the original version wrote straight to `cand` with a
        # plain exists() check, no atomicity).
        fd, tmp_name = tempfile.mkstemp(dir=str(cand.parent), prefix=f".{cand.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.link(tmp_name, cand)
            except FileExistsError:
                n += 1
                cand = path.with_name(f"{path.stem}-r{n}{path.suffix}")
                continue
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return cand
