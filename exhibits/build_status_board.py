#!/usr/bin/env python3
"""Build the internal status board page from scripts/status_board.py's output.

Internal working page, not a reader page: it shows slugs and field names on
purpose, and is published only as a private Artifact (never into docs/).

  python3 exhibits/build_status_board.py --out exhibits/status_board.html
  python3 exhibits/build_status_board.py --board board.json --out ...

Without --board it runs the board itself (same defaults as status_board.py,
including the shared weekly-scan files when /mnt/project-files/watch exists).
Local file processing only.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from display_helpers import design_head  # noqa: E402
import status_board as sb  # noqa: E402

PAGE_CSS = r"""
/* Layout: one working column; summary strip, then developments, then the filterable record list. */
.sb { padding-block: var(--space-6); display: grid; gap: var(--space-6); max-width: 1180px; }
.sb section { display: grid; gap: var(--space-3); min-width: 0; }
.sb-meta { font: 400 var(--t-note)/1.5 var(--font-mono); color: var(--ink-3); margin: 0; }
.sb-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: var(--space-2); }
.sb-tile { display: grid; gap: 4px; text-align: left; background: var(--panel); border: 1px solid var(--rule);
  border-radius: var(--radius); padding: 10px 12px; cursor: pointer; color: var(--ink); font: inherit; }
.sb-tile:hover { border-color: var(--ink-3); }
.sb-tile[aria-pressed="true"] { border-color: var(--ink); box-shadow: inset 0 0 0 1px var(--ink); }
.sb-tile .n { font: 500 28px/1 var(--font-serif); font-variant-numeric: tabular-nums; }
.sb-tile .l { font-size: var(--t-note); color: var(--ink-2); }
.sb-tile .m { font: 400 11px/1.3 var(--font-mono); color: var(--ink-3); }

.mk { display: inline-block; width: 1.1em; text-align: center; font-family: var(--font-mono); }
.chip { display: inline-flex; gap: 6px; align-items: baseline; font: 400 12.5px/1.35 var(--font-sans);
  border: 1px solid var(--rule); border-radius: 3px; padding: 3px 7px; background: var(--panel); color: var(--ink); }
.chip .k { font: 600 10px/1 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-3); white-space: nowrap; }
.chip.behind { border-color: var(--ink); }
.chip.gap { border-style: dashed; color: var(--ink-2); }
.chip a { white-space: nowrap; }

.dev { display: grid; gap: 6px; padding: 12px 14px; background: var(--panel); border: 1px solid var(--rule);
  border-left: 3px solid var(--ink); border-radius: var(--radius); }
.dev p { margin: 0; max-width: var(--measure); }
.dev .meta { display: flex; flex-wrap: wrap; gap: 6px 14px; font: 400 12px/1.4 var(--font-mono); color: var(--ink-3); }
.dev.lead { border-left-style: dashed; }
.devs { display: grid; gap: var(--space-2); }

.controls { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-4); align-items: center; }
.controls input[type=search], .controls select { font: inherit; font-size: var(--t-note); padding: 6px 8px;
  border: 1px solid var(--rule); border-radius: 3px; background: var(--panel); color: var(--ink); }
.controls input[type=search] { min-width: 0; flex: 1 1 220px; }
.seg { display: inline-flex; border: 1px solid var(--rule); border-radius: 3px; overflow: hidden; flex-wrap: wrap; }
.seg button { font: 600 11px/1 var(--font-mono); letter-spacing: .05em; text-transform: uppercase; padding: 8px 10px;
  border: 0; background: var(--panel); color: var(--ink-2); cursor: pointer; }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }
.controls label { font-size: var(--t-note); color: var(--ink-2); display: inline-flex; gap: 6px; align-items: center; }

.rows { display: grid; border-top: 1px solid var(--rule); }
.row { display: grid; grid-template-columns: minmax(0, 2.2fr) minmax(0, 1fr) minmax(0, 3.4fr); gap: 6px 18px;
  padding: 10px 0; border-bottom: 1px solid var(--rule-soft); align-items: start; }
.row .nm { font: 500 16px/1.3 var(--font-serif); overflow-wrap: anywhere; }
.row .sub { font: 400 11.5px/1.4 var(--font-mono); color: var(--ink-3); overflow-wrap: anywhere; }
.row .sub.why { color: var(--ink-2); }
.row .facts { font: 400 12px/1.5 var(--font-mono); color: var(--ink-2); font-variant-numeric: tabular-nums; }
.row .fl { display: flex; flex-wrap: wrap; gap: 5px; min-width: 0; }
.row .ok { font-size: var(--t-note); color: var(--ink-3); }
.hdr { font: 600 var(--t-label)/1 var(--font-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); padding-block: 8px; }
.more { justify-self: start; font: 600 11px/1 var(--font-mono); letter-spacing: .05em; text-transform: uppercase;
  padding: 9px 12px; border: 1px solid var(--ink); background: var(--panel); color: var(--ink); border-radius: 3px; cursor: pointer; }
.count { font-size: var(--t-note); color: var(--ink-3); margin: 0; }
.cp { font: 600 10px/1 var(--font-mono); letter-spacing: .05em; text-transform: uppercase; padding: 4px 6px; margin-left: 4px;
  border: 1px solid var(--ink-3); background: var(--panel); color: var(--ink); border-radius: 3px; cursor: pointer; white-space: nowrap; }
.cp:hover { border-color: var(--ink); }
.cp[data-done] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.queue { display: grid; gap: var(--space-2); }
.qi { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 12px; align-items: start; padding: 10px 12px;
  background: var(--panel); border: 1px solid var(--rule); border-radius: var(--radius); }
.qi .ql { font-size: var(--t-note); color: var(--ink-2); overflow-wrap: anywhere; }
.qi pre { grid-column: 1; margin: 0; font: 400 12px/1.45 var(--font-mono); white-space: pre-wrap; overflow-wrap: anywhere; color: var(--ink); }
.qi .cp { grid-column: 2; grid-row: 1 / span 2; align-self: center; padding: 8px 10px; }
.how { font-size: var(--t-note); color: var(--ink-2); max-width: var(--measure); }
.how code { font: 400 12px/1.4 var(--font-mono); background: var(--panel-2); padding: 1px 4px; border-radius: 2px; overflow-wrap: anywhere; }
.ids { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.id { font: 400 11.5px/1.2 var(--font-mono); padding: 3px 6px; border: 1px dashed var(--ink-3); background: var(--panel);
  color: var(--ink); border-radius: 3px; cursor: pointer; font-variant-numeric: tabular-nums; }
.id:hover { border-style: solid; border-color: var(--ink); }
.id[data-done] { background: var(--ink); color: var(--paper); }
.oq { flex: 1 1 100%; font-size: var(--t-note); }
.oq summary { cursor: pointer; font: 600 11px/1.4 var(--font-mono); letter-spacing: .05em; text-transform: uppercase; color: var(--ink-2); }
.oq .q { padding: 6px 0; border-top: 1px solid var(--rule-soft); }
.oq .q p { margin: 0 0 2px; max-width: var(--measure); overflow-wrap: anywhere; }
.oq .k { font: 400 11px/1.3 var(--font-mono); color: var(--ink-3); }
@media (max-width: 760px) {
  .row { grid-template-columns: minmax(0, 1fr); }
  .hdr { display: none; }
}
"""

MARK = {"behind": "●", "stale": "◐", "pull": "○", "review": "◆", "gap": "┄"}

PAGE_JS = r"""
const B = JSON.parse(document.getElementById('board').textContent);
const MARK = %MARK%;
const TIERS = ["cbst-core","money-layer","network","manufacturer","plumbing","unverified","adjacent","person","reference","product","channel"];
const KLABEL = {entity:"Company", person:"Person", product:"Product", channel:"Channel"};
const st = {q:"", kind:"all", flag:null, flaggedOnly:true, tier:"", shown:80};
try { const s = JSON.parse(localStorage.getItem('sb-state')||'{}'); Object.assign(st, s, {shown:80}); } catch(e) {}
const save = () => { try { localStorage.setItem('sb-state', JSON.stringify({kind:st.kind, flaggedOnly:st.flaggedOnly, tier:st.tier})); } catch(e) {} };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ru = d => d ? d.slice(8,10)+"."+d.slice(5,7)+"."+d.slice(0,4) : "";
const age = d => d ? Math.round((new Date(B.generated) - new Date(d))/86400000) : null;

// Copy a command to the clipboard (inside the click, so the browser allows it); select-text fallback.
async function copyText(btn, text) {
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch(e) {}
  if (!ok) {
    const ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly',''); ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.select(); try { ok = document.execCommand('copy'); } catch(e) {} ta.remove();
  }
  const was = btn.textContent; btn.textContent = ok ? "Copied" : "Copy failed"; btn.dataset.done = "";
  setTimeout(() => { btn.textContent = was; delete btn.dataset.done; }, 1600);
}
const CMDS = [];
const cpBtn = (cmd, label) => { CMDS.push(cmd); return `<button class="cp" type="button" data-c="${CMDS.length-1}" title="${esc(cmd)}">${label||"Copy cmd"}</button>`; };
function chip(f) {
  let t = esc(f.text);
  if (f.cmds) t += f.cmds.map(c => cpBtn(c.cmd, c.label)).join("");
  if (f.url) t += ` <a href="${esc(f.url)}" target="_blank" rel="noopener">post</a>`;
  if (f.code === "development" && f.archived) t += ` <span class="k">archived, not closed</span>`;
  return `<span class="chip ${f.kind}"><span class="k"><span class="mk" aria-hidden="true">${MARK[f.kind]}</span>${f.kind}</span><span>${t}</span></span>`;
}
function facts(r) {
  const out = [];
  if (r.kind === "entity") {
    out.push(r.last_register_pull ? `register ${ru(r.last_register_pull)} (${age(r.last_register_pull)}d)` : "register: none");
  }
  if (r.kind === "entity" || r.kind === "person") out.push(r.screened ? `screened ${ru(r.screened)} (${age(r.screened)}d)` : "screened: never");
  if (r.kind === "product") out.push(`${r.versions} versions · ${r.deliveries} deliveries` + (r.last_delivery ? ` · last ${ru(r.last_delivery)}` : ""));
  if (r.kind === "channel") {
    out.push(r.high_water ? "scan at post " + r.high_water : (r.in_weekly_scan ? "scan: not read" : "scan: not watched"));
    out.push(r.last_archived ? "archived to " + r.last_archived : "archived: none");
    if (r.owners.length) out.push("of " + r.owners.join(", "));
  }
  if (r.channels && r.channels.length) out.push(r.channels.map(h => "@"+h).join(" "));
  return out.join("<br>");
}
function rowHTML(r) {
  const sub = [KLABEL[r.kind], r.kind === "entity" || r.kind === "person" && r.tier === "reference" ? r.tier : null, r.slug !== r.name ? r.slug : null].filter(Boolean).join(" · ");
  const lat = r.latin && r.latin !== r.name ? `<div class="sub">${esc(r.latin)}</div>` : "";
  const role = r.role ? `<div class="sub">${esc(r.role)}</div>` : "";
  const sanc = r.sanctioned ? ` <span class="rm-sanction">Sanctioned</span>` : "";
  const fl = r.flags.length ? r.flags.map(chip).join("") : `<span class="ok">No flags</span>`;
  const idc = [["ИНН", r.inn], ["ОГРН", r.ogrn], ["ИНН физ.", r.inn_personal]].filter(x => x[1])
    .map(x => `<button class="id" type="button" data-t="${esc(x[1])}" title="Copy ${x[0]} ${esc(x[1])}">${x[0]} ${esc(x[1])}</button>`).join("");
  const oqs = (r.oq||[]).length ? `<details class="oq"><summary>Open questions (${r.oq.length})</summary>` + r.oq.map(q =>
    `<div class="q"><p>${esc(q.t)}</p>${q.s ? `<span class="k">${esc(q.s)}</span>` : ""}</div>`).join("") + `</details>` : "";
  const p = r.priority || {};
  const why = r.flags.length && (p.why || p.hops != null) ? `<div class="sub why">Priority: ${esc([p.why, p.hops != null ? `${p.hops} hop${p.hops===1?"":"s"} from ЦБСТ, ${p.degree} edges` : null].filter(Boolean).join("; "))}</div>` : "";
  return `<div class="row"><div><div class="nm">${esc(r.name || r.slug)}${sanc}</div>${lat}${role}<div class="sub">${esc(sub)}</div>${why}${idc ? `<div class="ids">${idc}</div>` : ""}</div><div class="facts">${facts(r)}</div><div class="fl">${fl}${oqs}</div></div>`;
}
function match(r) {
  if (st.kind !== "all" && r.kind !== st.kind) return false;
  if (st.tier && r.tier !== st.tier) return false;
  if (st.flag && !r.flags.some(f => f.kind === st.flag)) return false;
  if (st.flaggedOnly && !r.flags.length) return false;
  if (st.q) {
    const q = st.q.toLowerCase().replace(/ё/g,"е");
    const hay = [r.name, r.latin, r.slug, r.inn, (r.channels||[]).join(" "), r.flags.map(f=>f.text).join(" ")].join(" ").toLowerCase().replace(/ё/g,"е");
    if (!hay.includes(q)) return false;
  }
  return true;
}
// Priority order is computed by scripts/status_board.py (priority_key): sanctions relevance, hops from ЦБСТ,
// connections, then the work the flags hold.
const rank = r => (r.priority && r.priority.rank != null) ? r.priority.rank : 1e9;
function render() {
  const rows = B.rows.filter(match).sort((a,b) => rank(a)-rank(b) || String(a.name).localeCompare(String(b.name),"ru"));
  const shown = rows.slice(0, st.shown);
  CMDS.length = QN;
  document.getElementById('rows').innerHTML = `<div class="row hdr"><div>Record</div><div>Last pulls</div><div>Flags</div></div>` + shown.map(rowHTML).join("");
  document.getElementById('count').textContent = `${rows.length} record${rows.length===1?"":"s"} match` + (rows.length > shown.length ? `, showing ${shown.length}` : "");
  const m = document.getElementById('more'); m.hidden = rows.length <= shown.length;
  document.querySelectorAll('#kinds button').forEach(b => b.setAttribute('aria-pressed', b.dataset.k === st.kind));
  document.querySelectorAll('.sb-tile').forEach(b => b.setAttribute('aria-pressed', b.dataset.f === st.flag));
  document.getElementById('flagged').checked = st.flaggedOnly;
  document.getElementById('tier').value = st.tier;
}
// Today's capped queue, one copy button per command.
const q = document.getElementById('queue');
q.innerHTML = (B.queue||[]).map(it => `<div class="qi"><span class="ql">${esc(it.label)}</span><pre>${esc(it.cmd)}</pre>${cpBtn(it.cmd, "Copy")}</div>`).join("") || `<p class="count">Nothing queued today.</p>`;
const QN = CMDS.length;
document.addEventListener('click', e => {
  const i = e.target.closest('.id'); if (i) { copyText(i, i.dataset.t); return; }
  const b = e.target.closest('.cp'); if (!b) return; copyText(b, CMDS[+b.dataset.c]);
});
// Every one-record pull command on the rows currently shown, to paste to the Mac in one go.
document.getElementById('bulk').addEventListener('click', e => {
  const seen = new Set(), out = [];
  B.rows.filter(match).slice(0, st.shown).forEach(r => r.flags.forEach(f => (f.cmds||[]).forEach(c => { if (!seen.has(c.cmd)) { seen.add(c.cmd); out.push(c.cmd); } })));
  copyText(e.currentTarget, out.join("\n") || "# no pullable flags on the rows shown");
});
// Summary tiles: records carrying at least one flag of each kind.
const strip = document.getElementById('strip');
strip.innerHTML = Object.entries(B.kinds).map(([k,l]) => {
  const recs = B.rows.filter(r => r.flags.some(f => f.kind === k));
  const by = {}; recs.forEach(r => by[r.kind] = (by[r.kind]||0)+1);
  const PL = {entity:["company","companies"], person:["person","people"], product:["product","products"], channel:["channel","channels"]};
  const m = Object.entries(by).map(([kk,n]) => `${n} ${PL[kk][n===1?0:1]}`).join(" · ");
  return `<button class="sb-tile" data-f="${k}" type="button"><span class="n">${recs.length}</span><span class="l"><span class="mk" aria-hidden="true">${MARK[k]}</span> ${esc(l)}</span><span class="m">${esc(m)}</span></button>`;
}).join("");
strip.addEventListener('click', e => { const b = e.target.closest('.sb-tile'); if (!b) return; st.flag = st.flag === b.dataset.f ? null : b.dataset.f; st.shown = 80; render(); document.getElementById('records').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}); });
document.getElementById('kinds').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; st.kind = b.dataset.k; st.shown = 80; save(); render(); });
document.getElementById('q').addEventListener('input', e => { st.q = e.target.value.trim(); st.shown = 80; render(); });
document.getElementById('flagged').addEventListener('change', e => { st.flaggedOnly = e.target.checked; save(); render(); });
document.getElementById('tier').addEventListener('change', e => { st.tier = e.target.value; save(); render(); });
document.getElementById('more').addEventListener('click', () => { st.shown += 120; render(); });
const tsel = document.getElementById('tier');
TIERS.filter(t => B.rows.some(r => r.tier === t)).forEach(t => tsel.insertAdjacentHTML('beforeend', `<option value="${t}">${t}</option>`));
render();
"""


def dev_html(board):
    """Open weekly-scan developments, newest first, with the records they touch."""
    names = {r["slug"]: r.get("name") or r["slug"] for r in board["rows"]}
    seen, items = set(), []
    for r in board["rows"]:
        for f in r["flags"]:
            if f["code"] == "development" and f.get("dev_id") not in seen:
                seen.add(f.get("dev_id"))
                items.append(f)
    about = {}
    for r in board["rows"]:
        for f in r["flags"]:
            if f["code"] == "development":
                about.setdefault(f.get("dev_id"), []).append(r["slug"])
    out = []
    for f in sorted(items, key=lambda f: (f.get("found") or "", f.get("dev_id") or ""), reverse=True):
        recs = ", ".join(html.escape(names.get(s, s)) for s in about.get(f.get("dev_id"), []))
        arch = " · archived, not closed" if f.get("archived") else ""
        out.append(
            f'<article class="dev"><p>{html.escape(f["text"])}</p>'
            f'<div class="meta"><span>{html.escape(f.get("dev_kind") or "")}</span>'
            f'<span>found {html.escape(sb_ru(f.get("found")))}{arch}</span>'
            f'<a href="{html.escape(f.get("url") or "#")}" target="_blank" rel="noopener">{html.escape((f.get("url") or "").replace("https://", ""))}</a>'
            f'<span>touches: {recs}</span></div></article>')
    for it in board.get("unattached_developments", []):
        out.append(
            f'<article class="dev lead"><p>{html.escape(it.get("summary") or "")}</p>'
            f'<div class="meta"><span>{html.escape(it.get("kind") or "lead")}, no registry record</span>'
            f'<span>found {html.escape(sb_ru(it.get("found")))}</span>'
            f'<a href="{html.escape(it.get("url") or "#")}" target="_blank" rel="noopener">{html.escape((it.get("url") or "").replace("https://", ""))}</a></div></article>')
    if not out:
        msg = ("No open findings from the weekly scan." if board.get("unattached_developments") is not None
               and not any("developments.json" in n for n in board["notes"])
               else "The weekly scan's findings file was not available when this page was built.")
        out.append(f'<p class="count">{msg}</p>')
    return "\n".join(out)


FLAG_CMDS = {
    "egrul_missing": ("ЕГРЮЛ", "python3 scripts/egrul_vypiska_pull.py --inn {inn}"),
    "egrul_stale": ("ЕГРЮЛ", "python3 scripts/egrul_vypiska_pull.py --inn {inn}"),
    "bfo_missing": ("БФО", "python3 scripts/bfo_pull.py --inn {inn}"),
    "bfo_behind": ("БФО", "python3 scripts/bfo_pull.py --inn {inn}"),
}


def attach_commands(board):
    """Give each pullable flag the exact command for that one record, and the page today's capped queue.

    The page only copies these to the clipboard; nothing runs from it. The
    commands are the same ones status_board.py --pull-queue prints, for one
    record at a time (an OpenSanctions screen of one uses 1 of its monthly quota).
    """
    board = json.loads(json.dumps(board))
    for r in board["rows"]:
        for f in r["flags"]:
            cmds = []
            if f["code"] in FLAG_CMDS and r.get("inn"):
                label, cmd = FLAG_CMDS[f["code"]]
                cmds.append({"label": "Copy " + label, "cmd": cmd.format(inn=r["inn"])})
            elif f["code"] in ("screen_never", "screen_stale"):
                for key in f.get("due") or []:
                    if key in sb.SCREEN_COMMANDS:
                        cmds.append({"label": "Copy " + key,
                                     "cmd": sb.SCREEN_COMMANDS[key].format(n=1, slugs=r["slug"])})
            if cmds:
                f["cmds"] = cmds
    queue, label, chain = [], "", []
    for line in sb.pull_queue(board, used=sb.done_today(date.fromisoformat(board["generated"]))).splitlines():
        if line.startswith("#"):
            label = line.lstrip("# ")
        elif any(k in line for k in ("egrul_vypiska_pull", "bfo_pull", "screen_")):
            queue.append({"label": label, "cmd": line})
        else:
            chain.append(line)
    if queue:
        queue.append({"label": "Then index, parse and check what arrived, and send the text for first reading.",
                      "cmd": "\n".join(chain)})
        queue.append({"label": "Or run the whole round in one go (queue, pulls, ingest, export, report).",
                      "cmd": "python3 scripts/daily_mac.py"})
    board["queue"] = queue
    return board


def sb_ru(d):
    return f"{d[8:10]}.{d[5:7]}.{d[:4]}" if d and len(d) >= 10 else (d or "")


def attach_record_detail(board):
    """Add what a person at the dashboard copies or reads: ОГРН / personal ИНН and the open questions.

    Read from data/registry/ (committed, so it works in the cloud). Only open
    questions are carried; nothing here is written back.
    """
    reg = ROOT / "data" / "registry"
    def load(name):
        try:
            d = json.loads((reg / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return list(d.values()) if isinstance(d, dict) else d
    ents = {e.get("slug"): e for e in load("entities.json")}
    ppl = {p.get("slug"): p for p in load("people.json")}
    oq = {}
    for q in load("open_questions.json"):
        for key in ("entity_slug", "person_slug"):
            if q.get(key) and q.get("status", "open") == "open":
                oq.setdefault(q[key], []).append({"t": q.get("text", ""), "s": q.get("source_id")})
    board = json.loads(json.dumps(board))
    for r in board["rows"]:
        rec = ents.get(r["slug"]) if r["kind"] == "entity" else ppl.get(r["slug"]) if r["kind"] == "person" else None
        if rec:
            if r["kind"] == "entity":
                r["ogrn"] = rec.get("ogrn") or None
            else:
                r["inn_personal"] = rec.get("inn_personal") or None
        qs = [{"t": q.get("text", ""), "s": q.get("source_id")}
              for q in (rec or {}).get("open_questions") or [] if q.get("status", "open") == "open"]
        seen = {q["t"] for q in qs}
        qs += [q for q in oq.get(r["slug"], []) if q["t"] not in seen]
        if qs:
            r["oq"] = qs
    return board


STATUS_MARK = {"ok": "✓", "watch": "◐", "act": "●"}


def sys_html(board):
    rows = "".join(
        f'<tr class="{html.escape(c["status"])}"><td class="m" title="{html.escape(c["status"])}">{STATUS_MARK[c["status"]]}</td>'
        f'<th scope="row">{html.escape(c["label"])}</th><td>{html.escape(str(c["value"]))}</td>'
        f'<td class="d">{html.escape(c.get("detail") or "")}</td></tr>'
        for c in board.get("system") or [])
    if not rows:
        return ""
    return f"""<section aria-labelledby="h-sys">
  <h2 class="rm-h2" id="h-sys">System checks</h2>
  <p class="count">How current the inputs are, and checks that belong to no single record. ● act, ◐ watch, ✓ fine.</p>
  <style>.sys{{border-collapse:collapse;width:100%;font-size:14px}}.sys th,.sys td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule,#d5d9d4);vertical-align:top}}.sys th{{font-weight:500}}.sys .m{{width:1.5em}}.sys .d{{color:var(--ink-2,#555);font-size:13px}}.sys tr.act th,.sys tr.act .m{{font-weight:700}}</style>
  <table class="sys"><tbody>{rows}</tbody></table>
</section>
"""


def build(board):
    board = attach_record_detail(attach_commands(board))
    th = board["thresholds"]
    notes = "".join(f"<br>{html.escape(n)}" for n in board["notes"])
    data = json.dumps(board, ensure_ascii=False).replace("</", "<\\/")
    js = PAGE_JS.replace("%MARK%", json.dumps(MARK, ensure_ascii=False))
    return f"""<title>Investigation Status Board</title>
<meta name="robots" content="noindex">
{design_head(PAGE_CSS)}
<main class="rm-page sb">
<header>
  <p class="rm-eyebrow">Internal · РОЙ.МАРКЕТ investigation</p>
  <h1 class="rm-h1">Status board</h1>
  <p class="rm-dek">Every company, person, product and channel on file, with what its record is missing, what is out of date, and what the network has said since the record was last touched.</p>
  <p class="sb-meta">Built {sb_ru(board['generated'])} from the registry and the weekly scan. A register extract counts as stale after {th['egrul_stale_days']} days, a ГУР or Aleph screen after {th.get('gur_stale_days', th['screen_stale_days'])} days, an OpenSanctions screen after {th.get('opensanctions_stale_days', th['screen_stale_days'])} days (its monthly quota).{notes}</p>
</header>
{sys_html(board)}<section aria-labelledby="h-sum">
  <h2 class="rm-h2" id="h-sum">Records needing work</h2>
  <div class="sb-strip" id="strip"></div>
</section>
<section aria-labelledby="h-q">
  <h2 class="rm-h2" id="h-q">Today's pull queue</h2>
  <p class="count">The capped commands <code>status_board.py --pull-queue</code> prints for today. Copy one and paste it to the Mac session; nothing runs from this page (a page cannot reach the Mac). Click an ИНН or ОГРН on any row to copy it. A pulled document is read before any fact from it enters the registry, and a screen hit is a lead to read. Pullable flags below carry their own one-record copy button.</p>
  <div class="queue" id="queue"></div>
</section>
<section aria-labelledby="h-dev">
  <h2 class="rm-h2" id="h-dev">Behind on developments</h2>
  <p class="count">Open findings from the weekly Telegram and news scan that are not yet in the record. Close one in <code>watch/developments.json</code> once its fact is wired in or dismissed.</p>
  <div class="devs">{dev_html(board)}</div>
</section>
<section aria-labelledby="h-rec" id="records">
  <h2 class="rm-h2" id="h-rec">All records</h2>
  <div class="controls">
    <input type="search" id="q" placeholder="Name, ИНН, slug, channel or flag text" aria-label="Search records">
    <div class="seg" id="kinds" role="group" aria-label="Record kind">
      <button type="button" data-k="all">All</button><button type="button" data-k="entity">Companies</button><button type="button" data-k="person">People</button><button type="button" data-k="product">Products</button><button type="button" data-k="channel">Channels</button>
    </div>
    <select id="tier" aria-label="Tier"><option value="">Any tier</option></select>
    <label><input type="checkbox" id="flagged"> Only records with flags</label>
    <button class="cp" id="bulk" type="button" title="Copy every pull command on the rows shown">Copy pull commands for rows shown</button>
  </div>
  <p class="count" id="count"></p>
  <div class="rows" id="rows"></div>
  <button class="more" id="more" type="button">Show more</button>
</section>
<section class="how" aria-labelledby="h-how">
  <h2 class="rm-h2" id="h-how">How this is made</h2>
  <p>Every flag is a mechanical test in <code>scripts/status_board.py</code>, run over <code>data/registry/</code>, <code>config/channels.txt</code> and the weekly scan's files. A flag is a work item, not a finding: read the record before acting on it. Run <code>python3 exhibits/serve_status_board.py</code> and reload the tab: the page is rebuilt from the registry on every load.</p>
  <p><span class="mk">●</span> behind: the network said something the record lacks, or an own channel is unread. <span class="mk">◐</span> stale: a pull or screen past its threshold. <span class="mk">○</span> pull: a register extract, accounts or screen never done. <span class="mk">◆</span> review: open questions or unreviewed screening hits. <span class="mk">┄</span> gap: a field with no identifier or no source.</p>
</section>
</main>
<script type="application/json" id="board">{data}</script>
<script>{js}</script>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board", help="board JSON from status_board.py --json")
    ap.add_argument("--out", default=str(ROOT / "exhibits" / "status_board.html"))
    ap.add_argument("--today", help="YYYY-MM-DD")
    a = ap.parse_args()
    if a.board:
        board = json.loads(Path(a.board).read_text(encoding="utf-8"))
    else:
        today = sb.parse_date(a.today) if a.today else date.today()
        ss, dv = sb.default_path("weekly_scan_state.json"), sb.default_path("developments.json")
        board = sb.Board(today,
                         json.loads(ss.read_text(encoding="utf-8")) if ss else None,
                         json.loads(dv.read_text(encoding="utf-8")) if dv else None).build()
    Path(a.out).write_text(build(board), encoding="utf-8")
    print(f"wrote {a.out} ({len(board['rows'])} records)")


if __name__ == "__main__":
    main()
