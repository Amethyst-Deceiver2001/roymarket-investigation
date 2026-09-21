#!/usr/bin/env python3
"""Multi-hop, source-cited neighborhood query over data/registry/relationship_graph.json.

Why this exists: answering "how is X connected to Y" or "what's around X" by eyeballing
relationship_graph.json or grepping entities.json misses real multi-hop paths -- see the
[[roymarket_multihop_reachability_check]] lesson (a real 3-hop Цыганов -> ПОКРОВ -> Тримикс
-> ЦБСТ path was missed by a 1-hop check). This script does a real BFS, treating every edge
type as undirected for reachability, and prints every edge it touches as a
(source) --[type: label]--> (target) [sNNNN] triple -- so every claim in the printed
neighborhood traces to a real registry edge and its source_id, the same discipline
CLAUDE.md requires everywhere else. It does NOT call any LLM and does NOT answer a question
on its own -- it prints grounded context; a human (or Claude, reading the output in-session)
answers from the printed edges and can then go read each cited source before using the
answer anywhere. This deliberately stops short of the cookbook's "ask Claude to answer,
citing edges" step: that step is just reading this output, not a new capability, and adding
an actual API call would mean a second untracked path into project conclusions.

Local, no network -- reads only data/registry/relationship_graph.json. Safe to run
directly/repeatedly, same as registry_lookup.py.

Usage:
    python3 scripts/graph_query.py "Цыганов В.Б."                  # 2-hop neighborhood
    python3 scripts/graph_query.py "Цыганов В.Б." --hops 3
    python3 scripts/graph_query.py --between "Цыганов В.Б." "ЦБСТ"  # shortest path(s) only
    python3 scripts/graph_query.py --slug ip-tsyganov-v-b            # skip name resolution
"""
import argparse
import json
import os
import sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from registry_lookup import Registry  # noqa: E402


def load_graph():
    return json.load(open(os.path.join(ROOT, "data/registry/relationship_graph.json"), encoding="utf-8"))


def build_adjacency(graph):
    """slug -> list of (neighbor_slug, edge_dict). Undirected: every edge is added both ways,
    matching the multi-hop reachability discipline (an edge's direction is a data field on
    the edge itself, still visible in the printed triple; it is not a barrier to traversal)."""
    adj = {}
    for e in graph["edges"]:
        adj.setdefault(e["source"], []).append((e["target"], e))
        adj.setdefault(e["target"], []).append((e["source"], e))
    return adj


def resolve(query, graph, registry):
    """Return a single node id for `query`, or exit with the ambiguous/no-match candidates."""
    node_ids = {n["id"] for n in graph["nodes"]}
    if query in node_ids:
        return query
    hits = registry.find(query)
    hits = [h for h in hits if h[2] in node_ids]  # only hits that are actually on the graph
    if not hits:
        print(f"No graph node matches {query!r}. Try registry_lookup.py to see why "
              f"(unresolved stub, off-graph tier like graph_tier=reference, or genuinely absent).",
              file=sys.stderr)
        sys.exit(1)
    top_tier = hits[0][0]
    top = [h for h in hits if h[0] == top_tier]
    if len(top) > 1:
        print(f"Ambiguous match for {query!r} at tier {top_tier!r} -- pass --slug explicitly:",
              file=sys.stderr)
        for tier, score, slug, kind, label, field in top:
            print(f"  {slug}  ({kind}, matched {field}: {label})", file=sys.stderr)
        sys.exit(1)
    tier, score, slug, kind, label, field = top[0]
    print(f"# resolved {query!r} -> {slug} ({kind}, {label}) via {tier} match on {field}", file=sys.stderr)
    return slug


def neighborhood(center, adj, hops):
    """BFS outward `hops` steps. Returns (nodes_visited, edges_touched) -- edges_touched is a
    list of (dist_of_shallower_endpoint, edge_dict), deduped by (source, target, type, source_id)."""
    visited = {center: 0}
    frontier = [center]
    edges = []
    seen_edges = set()
    for dist in range(hops):
        nxt = []
        for n in frontier:
            for neighbor, e in adj.get(n, []):
                key = (e["source"], e["target"], e["type"], e.get("source_id"))
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append((dist, e))
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    nxt.append(neighbor)
        frontier = nxt
        if not frontier:
            break
    return visited, edges


def shortest_paths(a, b, adj):
    """All shortest undirected paths a -> b as lists of edge_dicts, BFS-based."""
    if a == b:
        return []
    parents = {a: []}  # node -> list of (prev_node, edge) achieving shortest dist
    dist = {a: 0}
    q = deque([a])
    found_dist = None
    while q:
        n = q.popleft()
        if found_dist is not None and dist[n] >= found_dist:
            continue
        for neighbor, e in adj.get(n, []):
            nd = dist[n] + 1
            if neighbor not in dist:
                dist[neighbor] = nd
                parents[neighbor] = [(n, e)]
                q.append(neighbor)
                if neighbor == b:
                    found_dist = nd
            elif dist[neighbor] == nd:
                parents.setdefault(neighbor, []).append((n, e))
    if b not in dist:
        return None  # unreachable
    # walk back from b to a, collecting every shortest path (can branch)
    paths = [[]]
    node = b
    while node != a:
        prev, e = parents[node][0]  # first parent only -- keep it simple, note if others exist
        paths[0].insert(0, e)
        node = prev
    extra = sum(len(parents[n]) - 1 for n in parents if len(parents.get(n, [])) > 1)
    return paths, extra


def node_label(graph, slug):
    for n in graph["nodes"]:
        if n["id"] == slug:
            return n
    return {"id": slug, "label": slug, "kind": "?"}


def fmt_edge(graph, dist, e):
    src = node_label(graph, e["source"])
    tgt = node_label(graph, e["target"])
    label = e.get("label") or e["type"]
    sid = e.get("source_id") or "NO-SOURCE"
    conf = f" conf={e['confidence']}" if e.get("confidence") else ""
    return (f"  [{dist}] ({src['id']} \"{src['label']}\") --[{e['type']}: {label}]--> "
            f"({tgt['id']} \"{tgt['label']}\")  [{sid}]{conf}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="name to resolve, or exact node slug")
    ap.add_argument("--slug", help="skip name resolution, use this exact graph node id")
    ap.add_argument("--hops", type=int, default=2, help="neighborhood radius (default 2)")
    ap.add_argument("--between", nargs=2, metavar=("A", "B"),
                     help="print shortest path(s) between two names/slugs instead of a neighborhood")
    args = ap.parse_args()

    graph = load_graph()
    adj = build_adjacency(graph)
    registry = Registry()

    def resolve_arg(q):
        node_ids = {n["id"] for n in graph["nodes"]}
        return q if q in node_ids else resolve(q, graph, registry)

    if args.between:
        a = resolve_arg(args.between[0])
        b = resolve_arg(args.between[1])
        result = shortest_paths(a, b, adj)
        if result is None:
            print(f"# no path found between {a} and {b} within the graph's connected structure "
                  f"(genuinely unconnected, per undirected BFS over every edge type)")
            sys.exit(0)
        paths, extra_branches = result
        print(f"# shortest path, {a} -> {b} ({len(paths[0])} hop(s)):")
        for e in paths[0]:
            print(fmt_edge(graph, "-", e))
        if extra_branches:
            print(f"# note: {extra_branches} other shortest-path branch(es) exist at equal "
                  f"length -- this prints one; re-run neighborhood mode on intermediate nodes "
                  f"to see alternates")
        return

    center = args.slug or resolve_arg(args.query)
    if not center:
        ap.error("provide a query name, --slug, or --between A B")
    visited, edges = neighborhood(center, adj, args.hops)
    center_info = node_label(graph, center)
    print(f"# {args.hops}-hop neighborhood of {center} (\"{center_info['label']}\"): "
          f"{len(visited)} nodes, {len(edges)} edges")
    print(f"# every edge below is (source) --[type: label]--> (target) [source_id], "
          f"undirected-BFS reachable -- direction is a data field on the edge, not a "
          f"traversal barrier. Read the cited source before using any edge as a finding.")
    for dist, e in sorted(edges, key=lambda x: x[0]):
        print(fmt_edge(graph, dist, e))
    no_source = [e for _, e in edges if not e.get("source_id")]
    if no_source:
        print(f"\n# WARNING: {len(no_source)} edge(s) above carry no source_id -- "
              f"placeholder, not evidence (see CLAUDE.md's dated-history rule). Do not "
              f"use these in a finding without going back to add one.")


if __name__ == "__main__":
    main()
