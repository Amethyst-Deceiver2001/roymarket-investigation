#!/usr/bin/env python3
"""Build the on-demand relationship-graph neighbourhood explorer.

    python3 exhibits/build_neighbourhood.py

The reader page uses only display labels, identifiers, evidence grades and
source descriptions from the generated schema-v12 graph. Registry slugs and
source ids are kept out of the page payload.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
OUT = REPO / "exhibits" / "neighbourhood.html"

EDGE_LABELS = {
    "owns": "owns",
    "related": "related to",
    "founded": "founded",
    "directs": "directs",
    "role": "has a documented role in",
    "produces": "produces",
    "procures": "purchased by",
    "confirmed_field_use": "documented field use",
    "cbst_tie": "has a documented relationship with ЦБСТ",
    "family_tie": "family relationship",
    "sells_for": "sells for",
    "operates": "operates",
    "organises": "organises",
    "resident_of": "resident of",
    "participated_in": "participated in",
    "part_of": "part of",
    "member_of": "member of",
    "banks_with": "banks with",
    "acquiring_via": "uses for acquiring",
    "ships_via": "ships via",
    "lists": "lists",
    "operated_by": "operated by",
}
GRADE_LABELS = {
    "doc": "Documented",
    "rep": "Reported",
    "open": "Not documented",
}
KIND_LABELS = {
    "entity": "Organisation",
    "person": "Person",
    "product": "Product",
    "unresolved": "Unresolved name",
    "government_customer": "Government customer",
    "military_unit": "Military unit",
    "program": "Programme",
    "event": "Event",
    "group": "Group",
    "storefront": "Storefront",
}


def fold(value: str) -> str:
    return " ".join((value or "").casefold().replace("ё", "е").split())


def source_index(sources: list[dict]) -> dict[str, dict]:
    return {source["id"]: source for source in sources if source.get("id")}


def build_payload(graph: dict, sources: list[dict]) -> dict:
    """Create the reader-safe numeric-index payload; omit registry/source ids."""
    nodes = graph.get("nodes", [])
    indexes = {node["id"]: i for i, node in enumerate(nodes)}
    by_source = source_index(sources)
    payload_nodes = []
    for node in nodes:
        item = {
            "label": node.get("label") or "Unresolved name",
            "kind": KIND_LABELS.get(node.get("kind"), "Other"),
            "search": [node.get("label") or "", node.get("name_latin") or "", node.get("inn") or ""],
            "sanctioned": bool(node.get("sanctioned")),
        }
        if node.get("inn"):
            item["inn"] = node["inn"]
        payload_nodes.append(item)

    payload_edges = []
    for edge in graph.get("edges", []):
        if edge.get("source") not in indexes or edge.get("target") not in indexes:
            continue
        grade = edge.get("grade") if edge.get("grade") in GRADE_LABELS else "open"
        source = by_source.get(edge.get("source_id"), {})
        citation = None
        if source.get("title"):
            url = source.get("public_url")
            if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                url = None
            citation = {"title": source["title"], "url": url}
        payload_edges.append({
            "from": indexes[edge["source"]],
            "to": indexes[edge["target"]],
            "relation": EDGE_LABELS.get(edge.get("type"), "related to"),
            "detail": edge.get("label") or "",
            "grade": grade,
            "as_of": edge.get("as_of"),
            "temporal": edge.get("temporal_status") or "unknown",
            "citation": citation,
        })
    return {"schema": graph.get("schema_version"), "nodes": payload_nodes, "edges": payload_edges}


def search(payload: dict, query: str, limit: int = 20) -> list[int]:
    """Return matching internal node indexes; search folds case and ё."""
    q = fold(query)
    if len(q) < 2:
        return []
    matches = []
    for i, node in enumerate(payload.get("nodes", [])):
        if any(q in fold(field) for field in node.get("search", [])):
            matches.append(i)
            if len(matches) == limit:
                break
    return matches


def neighbourhood(payload: dict, start: int, depth: int) -> tuple[dict[int, int], list[dict]]:
    """Return shortest undirected distances and edges induced by the neighbourhood."""
    if not 0 <= start < len(payload.get("nodes", [])):
        return {}, []
    depth = max(1, min(int(depth), 2))
    adjacency: dict[int, set[int]] = defaultdict(set)
    for edge in payload.get("edges", []):
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if distances[node] >= depth:
            continue
        for neighbor in adjacency[node]:
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    edges = [
        edge for edge in payload.get("edges", [])
        if edge["from"] in distances and edge["to"] in distances
    ]
    return distances, edges


PAGE_CSS = """
.rm-page{max-width:1180px;margin:auto;padding:28px 24px 64px}
.rm-tools{display:grid;grid-template-columns:minmax(220px,1fr) auto auto;gap:12px;align-items:end;margin:24px 0 12px}
.rm-field label{display:block;margin-bottom:5px;font:11px var(--font-mono);color:var(--ink-2)}
.rm-field input,.rm-field select{width:100%;min-height:42px;padding:8px 10px;border:1px solid var(--rule);border-radius:var(--radius);background:var(--panel);color:var(--ink);font:inherit}
.rm-search{position:relative}
.rm-results{position:absolute;z-index:4;left:0;right:0;top:100%;max-height:320px;overflow:auto;background:var(--panel);border:1px solid var(--rule);border-radius:var(--radius);box-shadow:var(--shadow)}
.rm-results[hidden]{display:none}
.rm-results button,.rm-node-button{font:inherit;color:inherit;background:none;border:0;text-align:left;cursor:pointer}
.rm-results button{display:flex;width:100%;justify-content:space-between;gap:12px;padding:10px;border-bottom:1px solid var(--rule)}
.rm-results button:hover,.rm-node-button:hover{color:var(--accent)}
.rm-kind-tag,.rm-hop{font:10px var(--font-mono);color:var(--ink-2)}
.rm-search-count{padding:8px 10px;color:var(--ink-2);font-size:11px;border-top:1px solid var(--rule)}
.rm-explainer{color:var(--ink-2);font-size:13px;max-width:76ch}
.rm-legend{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0;padding:12px;border-block:1px solid var(--rule);font-size:12px}
.rm-legend li{display:flex;align-items:center;gap:7px}
.rm-neighbour{margin-top:20px;padding:18px;border:1px solid var(--rule);border-radius:var(--radius);background:var(--panel)}
.rm-root{border:2px solid var(--ink);max-width:680px;margin:0 auto 20px}
.rm-root h2{font:500 23px var(--font-serif);margin:5px 0}
.rm-root .rm-kind{font:10px var(--font-mono);color:var(--ink-2);text-transform:uppercase}
.rm-id{font:11px var(--font-mono);color:var(--ink-2)}
.rm-edges{width:100%;border-collapse:collapse;font-size:13px}
.rm-edges th{text-align:left;font:10px var(--font-mono);text-transform:uppercase;color:var(--ink-2);padding:8px;border-bottom:1px solid var(--rule)}
.rm-edges td{padding:9px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
.rm-node-button{padding:0;font-weight:600}
.rm-relation{color:var(--ink-2);min-width:150px}
.rm-grade{white-space:nowrap;font:10px var(--font-mono)}
.rm-grade.doc{color:var(--g-doc)}.rm-grade.rep{color:var(--g-rep-ink)}.rm-grade.open{color:var(--ink-2)}
.rm-temporal,.rm-citation{display:block;margin-top:3px;color:var(--ink-2);font-size:11px}
.rm-citation a{color:inherit}
.rm-pagination{display:flex;align-items:center;justify-content:center;gap:14px;padding-top:16px}
.rm-pagination button,.rm-reset{border:1px solid var(--rule);border-radius:var(--radius);background:var(--panel);color:var(--ink);padding:7px 11px;cursor:pointer}
.rm-pagination button:disabled{opacity:.45;cursor:default}
.rm-sanction{display:inline-block;margin-left:6px}
.rm-empty{padding:24px;border:1px dashed var(--rule);color:var(--ink-2);text-align:center}
@media(max-width:720px){.rm-page{padding:20px 14px 48px}.rm-tools{grid-template-columns:1fr 1fr}.rm-search{grid-column:1/-1}.rm-neighbour{padding:10px}.rm-edges th:nth-child(3),.rm-edges td:nth-child(3){display:none}.rm-relation{min-width:0}}
"""


PAGE_JS = r"""
(() => {
  const data = JSON.parse(document.getElementById("graph-data").textContent);
  const input = document.getElementById("query");
  const results = document.getElementById("results");
  const depth = document.getElementById("depth");
  const status = document.getElementById("status");
  const output = document.getElementById("neighbourhood");
  const pageSize = 50;
  let selected = null, page = 0;
  const fold = s => (s || "").toLocaleLowerCase().replaceAll("ё", "е").trim().replace(/\s+/g, " ");
  const searchFields = data.nodes.map(n => n.search.map(fold));
  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const choose = i => {
    selected = i; page = 0; input.value = data.nodes[i].label;
    results.hidden = true; results.replaceChildren(); render();
  };
  const renderResults = () => {
    const q = fold(input.value);
    results.replaceChildren();
    if (q.length < 2) { results.hidden = true; return; }
    const matches = [];
    data.nodes.forEach((node, i) => {
      if (searchFields[i].some(field => field.includes(q))) matches.push(i);
    });
    matches.slice(0, 20).forEach(i => {
      const node = data.nodes[i];
      const button = el("button");
      button.type = "button";
      button.append(el("span", "", node.label), el("span", "rm-kind-tag", node.kind));
      button.addEventListener("click", () => choose(i));
      results.append(button);
    });
    if (!matches.length) results.append(el("div", "rm-empty", "No matching record."));
    else if (matches.length > 20) results.append(el("div", "rm-search-count", `Showing 20 of ${matches.length} matches; refine the search to narrow it.`));
    results.hidden = false;
  };
  const neighbours = (root, hops) => {
    const adj = data.nodes.map(() => []);
    data.edges.forEach(e => { adj[e.from].push(e.to); adj[e.to].push(e.from); });
    const distance = new Map([[root, 0]]), queue = [root];
    for (let at = 0; at < queue.length; at++) {
      const n = queue[at], d = distance.get(n);
      if (d >= hops) continue;
      adj[n].forEach(next => {
        if (!distance.has(next)) { distance.set(next, d + 1); queue.push(next); }
      });
    }
    const edges = data.edges.filter(e => distance.has(e.from) && distance.has(e.to));
    return { distance, edges };
  };
  const nodeButton = i => {
    const n = data.nodes[i], b = el("button", "rm-node-button", n.label);
    b.type = "button"; b.title = `Explore ${n.label}`;
    b.addEventListener("click", () => choose(i));
    if (n.sanctioned) b.append(el("span", "rm-sanction", "Sanctioned"));
    return b;
  };
  const render = () => {
    output.replaceChildren();
    if (selected === null) {
      status.textContent = "Search for an organisation, person, product, unit or identifier to begin.";
      output.append(el("div", "rm-empty", "Choose a search result to inspect its connected records."));
      return;
    }
    const {distance, edges} = neighbours(selected, Number(depth.value));
    const root = data.nodes[selected];
    status.textContent = `${distance.size - 1} connected record${distance.size === 2 ? "" : "s"} within ${depth.value} step${depth.value === "1" ? "" : "s"}; ${edges.length} relationship${edges.length === 1 ? "" : "s"}.`;
    const card = el("section", "rm-card rm-root");
    card.append(el("div", "rm-kind", root.kind));
    card.append(el("h2", "", root.label));
    if (root.inn) card.append(el("div", "rm-id", `ИНН ${root.inn}`));
    if (root.sanctioned) card.append(el("span", "rm-sanction", "Sanctioned"));
    output.append(card);
    if (!edges.length) {
      output.append(el("div", "rm-empty", "No relationships are recorded for this record."));
      return;
    }
    const start = page * pageSize, shown = edges.slice(start, start + pageSize);
    const table = el("table", "rm-edges"), thead = document.createElement("thead"), head = document.createElement("tr");
    ["Record", "Relationship", "Record", "Evidence"].forEach(t => head.append(el("th", "", t)));
    thead.append(head); table.append(thead);
    const body = document.createElement("tbody");
    shown.forEach(edge => {
      const row = document.createElement("tr");
      const a = document.createElement("td"), rel = el("td", "rm-relation"), b = document.createElement("td"), evidence = document.createElement("td");
      a.append(nodeButton(edge.from));
      rel.append(el("span", "rm-hop", `Step ${Math.max(distance.get(edge.from), distance.get(edge.to))}`));
      rel.append(el("div", "", edge.relation));
      if (edge.detail) rel.append(el("small", "rm-temporal", edge.detail));
      b.append(nodeButton(edge.to));
      const grade = el("span", `rm-grade ${edge.grade}`, {"doc":"Documented","rep":"Reported","open":"Not documented"}[edge.grade]);
      evidence.append(grade);
      const temporal = {"current":"Current","historical":"Historical","unknown":"Timing unknown"}[edge.temporal] || "Timing unknown";
      evidence.append(el("span", "rm-temporal", edge.as_of ? `${temporal} · ${edge.as_of}` : temporal));
      if (edge.citation) {
        const cite = el("span", "rm-citation");
        if (edge.citation.url) {
          const link = el("a", "", edge.citation.title);
          link.href = edge.citation.url; link.target = "_blank"; link.rel = "noopener noreferrer";
          cite.append(link);
        } else cite.textContent = edge.citation.title;
        evidence.append(cite);
      } else evidence.append(el("span", "rm-citation", "No source is attached to this relationship."));
      row.append(a, rel, b, evidence); body.append(row);
    });
    table.append(body); output.append(table);
    const pages = Math.ceil(edges.length / pageSize), pager = el("div", "rm-pagination");
    const prev = el("button", "", "Previous"); prev.type = "button"; prev.disabled = page === 0;
    prev.addEventListener("click", () => { page--; render(); });
    const next = el("button", "", "Next"); next.type = "button"; next.disabled = page >= pages - 1;
    next.addEventListener("click", () => { page++; render(); });
    pager.append(prev, el("span", "", `Showing ${start + 1}–${Math.min(start + pageSize, edges.length)} of ${edges.length}`), next);
    output.append(pager);
  };
  input.addEventListener("input", renderResults);
  input.addEventListener("keydown", ev => {
    if (ev.key === "Escape") { results.hidden = true; }
    if (ev.key === "Enter" && !results.hidden) results.querySelector("button")?.click();
  });
  document.addEventListener("click", ev => {
    if (!ev.target.closest(".rm-search")) results.hidden = true;
  });
  depth.addEventListener("change", () => { page = 0; render(); });
  document.getElementById("reset").addEventListener("click", () => {
    selected = null; input.value = ""; results.hidden = true; page = 0; render();
  });
  render();
})();
"""


def page(payload: dict) -> str:
    # Imported lazily so this builder can also be tested as a standalone module.
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    from display_helpers import design_head

    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    encoded = encoded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relationship neighbourhood explorer</title>
{design_head(PAGE_CSS)}
</head><body><main class="rm-page">
<header class="rm-masthead"><p class="rm-eyebrow">РОЙ.МАРКЕТ · RELATIONSHIP RECORDS</p>
<h1 class="rm-h1">Explore a neighbourhood</h1>
<p class="rm-dek rm-explainer">Search the relationship registry, then inspect one or two steps from a selected record. Each line retains its direction and evidence grade. A connection is not a finding by itself; read the cited source.</p></header>
<section class="rm-tools" aria-label="Search and neighbourhood controls">
  <div class="rm-field rm-search"><label for="query">Find a record by name or identifier</label><input id="query" type="search" autocomplete="off" aria-controls="results" placeholder="Organisation, person, product, ИНН…"><div id="results" class="rm-results" role="listbox" hidden></div></div>
  <div class="rm-field"><label for="depth">Steps from selected record</label><select id="depth"><option value="1">One step</option><option value="2">Two steps</option></select></div>
  <button class="rm-reset" id="reset" type="button">Clear</button>
</section>
<ul class="rm-legend" aria-label="Evidence grades">
  <li><span class="rm-grade doc">Documented</span> — a document shows it</li>
  <li><span class="rm-grade rep">Reported</span> — a party's own word or press</li>
  <li><span class="rm-grade open">Not documented</span> — the relationship is unresolved</li>
</ul>
<p id="status" role="status" aria-live="polite"></p>
<section id="neighbourhood" class="rm-neighbour" aria-label="Selected record neighbourhood"></section>
</main>
<script id="graph-data" type="application/json">{encoded}</script>
<script>{PAGE_JS}</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT, help=f"output HTML (default: {OUT.relative_to(REPO)})")
    args = ap.parse_args()
    graph = json.loads((REG / "relationship_graph.json").read_text(encoding="utf-8"))
    sources = json.loads((REG / "sources.json").read_text(encoding="utf-8"))
    if graph.get("schema_version") != 12:
        raise SystemExit(f"expected relationship graph schema 12, got {graph.get('schema_version')!r}")
    payload = build_payload(graph, sources)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page(payload), encoding="utf-8")
    print(f"wrote {args.out} ({len(payload['nodes'])} records, {len(payload['edges'])} relationships)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
