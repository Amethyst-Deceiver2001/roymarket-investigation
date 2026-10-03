#!/usr/bin/env python3
"""Full-roster trademark search over searchplatform.rospatent.gov.ru's real
search API -- reverse-engineered 2026-08-24 from a user-supplied HAR capture
that (unlike prior attempts) actually recorded a live search. The API runs
over Socket.IO/WebSocket, not plain HTTP -- see the rospatent_searchplatform_api
memory for why two earlier sessions of endpoint-guessing on /search, /search/tm,
/search/integral never found it.

Protocol (Engine.IO v4 / Socket.IO v4, "/search" namespace):
  1. Open  wss://searchplatform.rospatent.gov.ru/socket.io/?EIO=4&transport=websocket
  2. Server sends Engine.IO OPEN packet: 0{"sid":...}
  3. Client sends Socket.IO CONNECT to the /search namespace: 40/search,
  4. Server confirms: 40/search,{"sid":"..."}
  5. Client sends a Socket.IO EVENT: 42/search,["send_task",{...}]
  6. Server replies (may take 1-3s): 42/search,["send_results",{...}]
  7. Engine.IO PING ("2") arrives periodically; reply PONG ("3") to stay alive.

Query payload (the part that matters):
  {"method":"POST","service_name":"esi-search","service_path":"/api/v1/search",
   "params":{"page":1,"size":10},
   "data":{"query":{"data":{"data_sources":["trademarks","known_trademarks",
   "international_trademarks"],"search_kind_id":"template",
   "search_query":[{"key":"owners.name","value":"<substring>"}]},
   "type":"search_attribute"},"filter":{},"info":"<base64 client fingerprint,
   harmless placeholder ok>","oisType":"trademarks"}}

No auth/cookie required (confirmed -- a fresh anonymous connection works).
Response `data[]` entries carry: appl_number, appl_date, reg_number, reg_date,
expiry_date, corr_address, holders, goods (full text), tmk_kind, trademarkKind
-- richer than both the bulk CSV dump (s0433/s0945, bibliographic only, no
goods text) and one-at-a-time FIPS DB=RUTM/RUTMAP pulls (fips_trademark_enrich.py),
and it is genuinely searchable by owner-name substring instead of requiring an
already-known reg_number.

This script implements a minimal RFC6455 WebSocket client with the standard
library only (no `websockets`/`websocket-client` install -- this machine's
Python is externally-managed and installing into it wasn't worth the risk for
a single script). One persistent connection is reused across all queries.

Searches EVERY entity in the registry by up to two strings: the cleaned legal
name (legal-form prefix stripped) and the brand name where it differs
(brand_ru / brand_latin, when set and distinct from name_ru) -- a name-only
search misses brand-marketed products filed under a different applicant
string, same lesson as the reseller-mediated WB-overlap finding.

Writes raw results (no promotion) to
  data/sources/ROSPATENT_WS_TM_<YYYYMMDD>_<slug>.json
one file per entity with any hits, `{"slug", "queries": [...], "hits": [...]}`.
Does NOT touch corrections.json -- promotion (verify holder identity, check
for false positives like the two already caught this session) is a separate,
human-reviewed step, same two-stage pattern as the patent/trademark work so far.

**Live network job against a third-party site, ~180-200 queries (93
manufacturer-tier entities x up to 2 queries each) over one persistent
connection -- per CLAUDE.md's crawling-jobs policy, tested inline on a
handful first, but the full run should be executed by you, not run in the
background.**

After running this:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    (then hand the resulting *.json files back for review/promotion --
    verify every holder against the query entity before trusting a hit,
    per the two false positives already caught this session)

Usage:
    python3 scripts/rospatent_tm_ws_search.py                 # full manufacturer-tier roster
    python3 scripts/rospatent_tm_ws_search.py --limit 5        # first 5 entities only
    python3 scripts/rospatent_tm_ws_search.py --slug ooo-trimiks  # one entity
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import socket
import ssl
import struct
import time
from pathlib import Path
from source_files import write_new  # never overwrite a catalogued source

REPO = Path(__file__).resolve().parent.parent
HOST = "searchplatform.rospatent.gov.ru"
PORT = 443
WS_PATH = "/socket.io/?EIO=4&transport=websocket"
DELAY_SECONDS = 1.5
RESPONSE_TIMEOUT = 15.0

LEGAL_FORM_RE = re.compile(
    r'^(?:АО|ОАО|ЗАО|ПАО|ООО|АНО|НПО|НПЦ|НПП|ФГУП|ГУП|КБ)\s+'
    r'(?:«([^»]+)»|"([^"]+)")',
    re.IGNORECASE,
)


def strip_legal_form(name: str) -> str:
    """'ООО «Тримикс»' -> 'Тримикс'; falls back to the input unchanged."""
    m = LEGAL_FORM_RE.match(name.strip())
    if m:
        return (m.group(1) or m.group(2)).strip()
    # fallback: strip a bare quoted segment anywhere in the string
    m2 = re.search(r'«([^»]+)»|"([^"]+)"', name)
    if m2:
        return (m2.group(1) or m2.group(2)).strip()
    return name.strip()


# ---------------------------------------------------------------------------
# minimal RFC6455 WebSocket client (stdlib only)
# ---------------------------------------------------------------------------

class WSClient:
    def __init__(self, host: str, port: int, path: str):
        self.host = host
        ctx = ssl.create_default_context()
        raw = socket.create_connection((host, port), timeout=30)
        self.sock = ctx.wrap_socket(raw, server_hostname=host)
        self._buf = b""
        self._handshake(path)

    def _handshake(self, path: str) -> None:
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36\r\n"
            f"Origin: https://{self.host}\r\n"
            "\r\n"
        ).encode()
        self.sock.sendall(req)
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("socket closed during handshake")
            resp += chunk
        header, _, rest = resp.partition(b"\r\n\r\n")
        if b"101" not in header.split(b"\r\n", 1)[0]:
            raise ConnectionError(f"handshake failed: {header[:200]!r}")
        expected = base64.b64encode(
            hashlib.sha1(key.encode() + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest()
        ).decode()
        if expected.encode() not in header:
            raise ConnectionError("Sec-WebSocket-Accept mismatch")
        self._buf = rest

    def _recv_some(self) -> bytes:
        chunk = self.sock.recv(65536)
        if not chunk:
            raise ConnectionError("socket closed")
        return chunk

    def send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        length = len(payload)
        header = bytearray([0x81])  # FIN + text frame
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", length)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", length)
        self.sock.sendall(bytes(header) + mask + masked)

    def _read_frame(self) -> tuple[int, bytes] | None:
        # returns (opcode, payload) for one frame, reading from self._buf/socket
        while len(self._buf) < 2:
            self._buf += self._recv_some()
        b0, b1 = self._buf[0], self._buf[1]
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        length = b1 & 0x7F
        pos = 2
        if length == 126:
            while len(self._buf) < pos + 2:
                self._buf += self._recv_some()
            length = struct.unpack(">H", self._buf[pos:pos + 2])[0]
            pos += 2
        elif length == 127:
            while len(self._buf) < pos + 8:
                self._buf += self._recv_some()
            length = struct.unpack(">Q", self._buf[pos:pos + 8])[0]
            pos += 8
        mask_key = b""
        if masked:
            while len(self._buf) < pos + 4:
                self._buf += self._recv_some()
            mask_key = self._buf[pos:pos + 4]
            pos += 4
        while len(self._buf) < pos + length:
            self._buf += self._recv_some()
        payload = self._buf[pos:pos + length]
        if masked:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        self._buf = self._buf[pos + length:]
        return opcode, payload

    def recv_text(self, timeout: float) -> str | None:
        self.sock.settimeout(timeout)
        try:
            opcode, payload = self._read_frame()
        except socket.timeout:
            return None
        if opcode == 0x8:  # close
            raise ConnectionError("server closed connection")
        if opcode == 0x9:  # ping
            self._send_pong(payload)
            return self.recv_text(timeout)
        if opcode == 0xA:  # pong
            return self.recv_text(timeout)
        return payload.decode("utf-8", errors="replace")

    def _send_pong(self, payload: bytes) -> None:
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        header = bytearray([0x8A, 0x80 | len(payload)])
        self.sock.sendall(bytes(header) + mask + masked)

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class TrademarkSearchSession:
    def __init__(self):
        self.ws = WSClient(HOST, PORT, WS_PATH)
        self._eio_handshake()
        self._sio_connect_namespace()

    def _eio_handshake(self) -> None:
        msg = self._wait_for_prefix("0", timeout=15)
        if msg is None:
            raise ConnectionError("no Engine.IO OPEN packet received")

    def _sio_connect_namespace(self) -> None:
        self.ws.send_text("40/search,")
        msg = self._wait_for_prefix("40/search,", timeout=15)
        if msg is None:
            raise ConnectionError("no Socket.IO CONNECT ack for /search namespace")

    def _wait_for_prefix(self, prefix: str, timeout: float) -> str | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.5, deadline - time.time())
            msg = self.ws.recv_text(remaining)
            if msg is None:
                continue
            if msg == "2":  # engine.io ping at the packet-string level (rare)
                self.ws.send_text("3")
                continue
            if msg.startswith(prefix):
                return msg
        return None

    def search_trademarks(self, owner_substring: str, page: int = 1, size: int = 20) -> dict:
        task = {
            "method": "POST",
            "service_name": "esi-search",
            "service_path": "/api/v1/search",
            "params": {"page": page, "size": size},
            "data": {
                "query": {
                    "data": {
                        "data_sources": ["trademarks", "known_trademarks", "international_trademarks"],
                        "search_kind_id": "template",
                        "search_query": [{"key": "owners.name", "value": owner_substring}],
                    },
                    "type": "search_attribute",
                },
                "filter": {},
                "info": "",
                "oisType": "trademarks",
            },
        }
        payload = json.dumps(["send_task", task], ensure_ascii=False)
        self.ws.send_text(f"42/search,{payload}")

        deadline = time.time() + RESPONSE_TIMEOUT
        while time.time() < deadline:
            remaining = max(0.5, deadline - time.time())
            msg = self.ws.recv_text(remaining)
            if msg is None:
                continue
            if msg == "2":
                self.ws.send_text("3")
                continue
            if msg.startswith("42/search,"):
                body = msg[len("42/search,"):]
                try:
                    arr = json.loads(body)
                except json.JSONDecodeError:
                    continue
                if isinstance(arr, list) and len(arr) == 2 and arr[0] == "send_results":
                    return arr[1]
                # ignore send_task echoes and other event types, keep waiting
                continue
        raise TimeoutError(f"no send_results within {RESPONSE_TIMEOUT}s for query {owner_substring!r}")

    def close(self) -> None:
        self.ws.close()


def collect_targets() -> list[dict]:
    entities = json.loads((REPO / "data" / "registry" / "entities.json").read_text(encoding="utf-8"))
    targets = []
    for rec in entities:
        if rec.get("tier") != "manufacturer":
            continue
        name_ru = rec.get("name_ru") or ""
        queries = []
        cleaned = strip_legal_form(name_ru)
        if cleaned:
            queries.append(cleaned)
        for key in ("brand_ru", "brand_latin"):
            brand = rec.get(key)
            if brand and brand.strip() and brand.strip().lower() not in (q.lower() for q in queries):
                queries.append(brand.strip())
        if queries:
            targets.append({"slug": rec["slug"], "queries": queries})
    return targets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--slug", default=None, help="run for a single entity slug only")
    args = ap.parse_args()

    targets = collect_targets()
    if args.slug:
        targets = [t for t in targets if t["slug"] == args.slug]
        if not targets:
            print(f"no manufacturer-tier entity with slug {args.slug!r}")
            return
    if args.limit is not None:
        targets = targets[: args.limit]

    date_slug = time.strftime("%Y%m%d")
    print(f"processing {len(targets)} entit{'y' if len(targets) == 1 else 'ies'} "
          f"({sum(len(t['queries']) for t in targets)} total queries) ...")

    session = TrademarkSearchSession()
    hits_total, entities_with_hits, failed = 0, 0, []
    try:
        for i, t in enumerate(targets, 1):
            slug = t["slug"]
            out_path = REPO / "data" / "sources" / f"ROSPATENT_WS_TM_{date_slug}_{slug}.json"
            if out_path.exists():
                print(f"  [{i}/{len(targets)}] {slug}: already have output, skipping")
                continue

            record = {"slug": slug, "queries": [], "hits": []}
            seen_appl_numbers = set()
            for q in t["queries"]:
                try:
                    result = session.search_trademarks(q)
                except (TimeoutError, ConnectionError) as ex:
                    print(f"  [{i}/{len(targets)}] {slug}: query {q!r} FAILED ({ex}); reconnecting")
                    failed.append((slug, q, str(ex)))
                    try:
                        session.close()
                    except Exception:
                        pass
                    session = TrademarkSearchSession()
                    time.sleep(DELAY_SECONDS)
                    continue
                if "totalResult" not in result:
                    msg = result.get("message", str(result))
                    if "запросов в сутки" in msg or "превысили" in msg:
                        print(f"\nDAILY QUOTA EXCEEDED: {msg}")
                        print(f"Stopping after {i - 1} entit{'y' if i - 1 == 1 else 'ies'} "
                              f"({entities_with_hits} with hits so far). Re-run tomorrow to continue "
                              f"(already-written *.json files are skipped automatically).")
                        return
                    print(f"  [{i}/{len(targets)}] {slug}: query {q!r} returned no totalResult "
                          f"(unexpected response: {msg!r}), skipping this query")
                    continue
                total = result.get("totalResult", 0)
                record["queries"].append({"value": q, "totalResult": total})
                for hit in result.get("data") or []:
                    key = hit.get("appl_number") or hit.get("object_uid")
                    if key in seen_appl_numbers:
                        continue
                    seen_appl_numbers.add(key)
                    record["hits"].append(hit)
                time.sleep(DELAY_SECONDS)

            if record["hits"]:
                out_path = write_new(out_path, json.dumps(record, ensure_ascii=False, indent=2))
                entities_with_hits += 1
                hits_total += len(record["hits"])
                print(f"  [{i}/{len(targets)}] {slug}: {len(record['hits'])} hit(s) across "
                      f"{len(t['queries'])} quer{'y' if len(t['queries']) == 1 else 'ies'}")
            else:
                print(f"  [{i}/{len(targets)}] {slug}: no hits")
    finally:
        session.close()

    print(f"\nDone. {entities_with_hits} entit{'y' if entities_with_hits == 1 else 'ies'} with hits, "
          f"{hits_total} total hit(s), {len(failed)} query failure(s).")
    if failed:
        print("Failed queries (site may have rate-limited or dropped the connection):")
        for slug, q, err in failed:
            print(f"  {slug} / {q!r}: {err}")
    print("\nNext: python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("      python3 scripts/inventory_sources.py")
    print("      (then hand the resulting ROSPATENT_WS_TM_*.json files back for review/promotion --")
    print("       verify every holder against the query entity, false positives are real -- see this session's")
    print("       738742/\"Skipy\" and 925634 rejections)")


if __name__ == "__main__":
    main()
