#!/usr/bin/env python3
"""Tamper-evident record of every source file: a fingerprint list, timestamped.

`sources.json` gives each file in `data/sources/` a SHA-256. That proves nothing
about *when* we held the file: we could have changed both the file and the hash
later. This script writes the list of fingerprints as a plain `shasum` file and
has it timestamped by independent RFC 3161 timestamping authorities. The signed
token proves the list, and so every file named in it, existed by that time and
has not changed since. One request covers every source, so there is no rate
limit to work around.

It does not prove a Telegram post or web page was served as we saved it (Telegram
does not sign posts): a third-party capture (`archive_sources.py`) does that.

Layout, one folder per run, committed:
    data/registry/timestamps/<YYYYMMDD>/manifest.sha256   `shasum -a 256 -c` format, repo-relative paths
    data/registry/timestamps/<YYYYMMDD>/manifest.tsq      the request (hash of the manifest)
    data/registry/timestamps/<YYYYMMDD>/<tsa>.tsr         each authority's signed reply

Anyone with the files can check it with standard tools, from the repo root:
    shasum -a 256 -c data/registry/timestamps/<day>/manifest.sha256
    openssl ts -reply -in data/registry/timestamps/<day>/freetsa.tsr -text
    openssl ts -verify -data data/registry/timestamps/<day>/manifest.sha256 \
        -in data/registry/timestamps/<day>/freetsa.tsr -CAfile <freetsa cacert.pem> -untrusted <freetsa tsa.crt>

Subcommands:
    build    Hash every source file and write the manifest (local, no network).
             The manifest holds the bytes as they are now. A file whose hash
             differs from the one sources.json catalogued is listed beside it in
             `changed_since_catalogued.tsv` (both hashes, file date): that is a
             work item to explain, and the stamp fixes the current bytes from here on.
    stamp    Send the manifest's hash to each authority and save the replies
             (one small request each; the file itself never leaves the machine).
    verify   Re-hash the files and check each reply against the manifest (local
             apart from fetching an authority's public certificates).

Usage (on the Mac, where data/sources/ exists):
    python3 scripts/timestamp_sources.py build && python3 scripts/timestamp_sources.py stamp
    python3 scripts/timestamp_sources.py verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES_JSON = REPO / "data" / "registry" / "sources.json"
OUT = REPO / "data" / "registry" / "timestamps"

# Two unrelated authorities, so the record does not rest on one company.
# `certs` are what `verify` needs besides the system trust store.
TSAS = {
    "freetsa": {"url": "https://freetsa.org/tsr",
                "certs": {"ca": "https://freetsa.org/files/cacert.pem",
                          "tsa": "https://freetsa.org/files/tsa.crt"}},
    "digicert": {"url": "http://timestamp.digicert.com", "certs": {}},
}
SYSTEM_CA = "/opt/homebrew/etc/openssl@3/cert.pem"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_lines(sources: list[dict]) -> tuple[list[str], list[str], list[str]]:
    """(lines, missing, differs). Lines are `<sha256>  <path>`, sorted by path."""
    lines, missing, differs = [], [], []
    for r in sorted(sources, key=lambda r: r["path"]):
        p = REPO / r["path"]
        if not p.is_file():
            missing.append(r["path"])
            continue
        h = sha256_file(p)
        if r.get("sha256") and h != r["sha256"]:
            differs.append(None)
        lines.append(f"{h}  {r['path']}")
        if r.get("sha256") and h != r["sha256"]:
            differs[-1] = (r["id"], r["path"], r["sha256"], h,
                           date.fromtimestamp(p.stat().st_mtime).isoformat())
    return lines, missing, differs


def latest_dir() -> Path:
    runs = sorted(d for d in OUT.iterdir() if d.is_dir()) if OUT.exists() else []
    if not runs:
        sys.exit("no timestamp run yet: run `build` first")
    return runs[-1]


def cmd_build(args) -> int:
    sources = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    lines, missing, differs = manifest_lines(sources)
    print(f"build: {len(lines)} files hashed, {len(missing)} missing, {len(differs)} differ from sources.json")
    for m in missing[:20]:
        print(f"  missing: {m}")
    day = OUT / date.today().strftime("%Y%m%d")
    day.mkdir(parents=True, exist_ok=True)
    (day / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if differs:
        rows = ["source_id\tpath\tsha256_catalogued\tsha256_now\tfile_modified"]
        rows += ["\t".join(d) for d in sorted(differs)]
        (day / "changed_since_catalogued.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"  {len(differs)} listed in {(day / 'changed_since_catalogued.tsv').relative_to(REPO)}")
    print(f"wrote {(day / 'manifest.sha256').relative_to(REPO)}")
    return 0


def openssl(*a: str, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["openssl", *a], input=data, capture_output=True)


def cmd_stamp(args) -> int:
    day = latest_dir()
    man, tsq = day / "manifest.sha256", day / "manifest.tsq"
    r = openssl("ts", "-query", "-data", str(man), "-sha256", "-cert", "-out", str(tsq))
    if r.returncode:
        sys.exit(r.stderr.decode())
    failed = 0
    for name, t in TSAS.items():
        req = urllib.request.Request(t["url"], data=tsq.read_bytes(),
                                     headers={"Content-Type": "application/timestamp-query"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
        except Exception as err:
            print(f"  {name}: {err}")
            failed += 1
            continue
        (day / f"{name}.tsr").write_bytes(body)
        txt = openssl("ts", "-reply", "-in", str(day / f"{name}.tsr"), "-text").stdout.decode()
        when = next((l.split(":", 1)[1].strip() for l in txt.splitlines() if l.startswith("Time stamp:")), "?")
        print(f"  {name}: stamped {when}")
    return 1 if failed == len(TSAS) else 0


def fetch(url: str, dest: Path) -> Path:
    with urllib.request.urlopen(url, timeout=60) as resp:
        dest.write_bytes(resp.read())
    return dest


def cmd_verify(args) -> int:
    day = Path(args.dir) if args.dir else latest_dir()
    man = day / "manifest.sha256"
    bad = 0
    lines = man.read_text(encoding="utf-8").splitlines()
    missing = changed = 0
    for l in lines:
        h, p = l.split("  ", 1)
        f = REPO / p
        if not f.is_file():
            missing += 1
        elif sha256_file(f) != h:
            changed += 1
            print(f"  changed since stamped: {p}")
    print(f"files: {len(lines) - missing - changed} unchanged, {changed} changed, {missing} not on this machine")
    bad += changed
    with tempfile.TemporaryDirectory() as tmp:
        for name, t in TSAS.items():
            tsr = day / f"{name}.tsr"
            if not tsr.exists():
                print(f"  {name}: no reply on file")
                continue
            extra = []
            if t["certs"]:
                extra = ["-CAfile", str(fetch(t["certs"]["ca"], Path(tmp) / f"{name}_ca.pem")),
                         "-untrusted", str(fetch(t["certs"]["tsa"], Path(tmp) / f"{name}_tsa.crt"))]
            else:
                extra = ["-CAfile", SYSTEM_CA]
            r = openssl("ts", "-verify", "-data", str(man), "-in", str(tsr), *extra)
            ok = r.returncode == 0
            bad += not ok
            print(f"  {name}: {'verified' if ok else 'FAILED ' + (r.stdout + r.stderr).decode().strip()[-200:]}")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("stamp")
    v = sub.add_parser("verify")
    v.add_argument("--dir", help="a run folder (default: the latest)")
    args = ap.parse_args(argv)
    return {"build": cmd_build, "stamp": cmd_stamp, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
