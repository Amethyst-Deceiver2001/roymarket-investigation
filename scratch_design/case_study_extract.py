import json

g = json.load(open('/Users/ak/Downloads/roymarket-investigation/data/registry/relationship_graph.json'))
nodes_by_id = {n['id']: n for n in g['nodes']}
edges = g['edges']

def neighborhood(center_ids):
    """center_ids: list of node ids treated as one combined hub set."""
    node_ids = set(center_ids)
    sel_edges = []
    for e in edges:
        if e['source'] in center_ids or e['target'] in center_ids:
            sel_edges.append(e)
            node_ids.add(e['source'])
            node_ids.add(e['target'])
    sel_nodes = [nodes_by_id[i] for i in node_ids if i in nodes_by_id]
    return sel_nodes, sel_edges

cases = {
    'gagaring': ['ooo-gagaring'],
    'goudron': ['ooo-goudron'],
    'cherezov': ['ooo-vozdushnyy-traktat', 'ovod'],
    'piranya': ['ooo-skb-piranya'],
    'tsyganov': ['ip-tsyganov-vadim-borisovich'],
}

out = {}
for key, centers in cases.items():
    nodes, sel_edges = neighborhood(centers)
    out[key] = {'centers': centers, 'nodes': nodes, 'edges': sel_edges}
    print(f"=== {key} ({centers}) ===")
    print(f"  nodes: {len(nodes)}  edges: {len(sel_edges)}")
    for n in nodes:
        tag = '*CENTER*' if n['id'] in centers else ''
        print(f"    [{n['kind']:18s}] {n['id']:50s} {n.get('label','')[:40]} {tag}")
    for e in sel_edges:
        print(f"    edge: {e['source']} --{e['type']}--> {e['target']}  {e.get('label') or ''}")
    print()

json.dump(out, open('/private/tmp/claude-501/-Users-ak-Downloads-roymarket-investigation/f2a0c6cb-5635-40da-ac73-3c3d3f9f5370/scratchpad/case_study_subgraphs.json', 'w'), ensure_ascii=False, indent=2)
