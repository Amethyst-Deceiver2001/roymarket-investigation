# Relationship graph quality baseline

This report is deterministic local aggregation over `data/registry/`; it does not assert facts or fill missing citations.

- Graph schema: `2`
- Canonical graph SHA-256: `d6956792c28755111f6c31c8f6ee2850a77b84fd7a79f79862516c249e632da5`
- Live-registry parity: 204/204 entities; 422/422 people
- Cited edges: 1122/1637
- Directly uncited relation edges (evidence gaps): 515/1637
- Explicit unresolved stubs: 208

## Nodes

| Kind | Count |
|---|---:|
| entity | 204 |
| person | 422 |
| product | 474 |
| unresolved | 208 |

## Edges

| Type | Total | Cited | Uncited |
|---|---:|---:|---:|
| directs | 287 | 260 | 27 |
| founded | 264 | 64 | 200 |
| owns | 15 | 15 | 0 |
| produces | 474 | 326 | 148 |
| related | 19 | 14 | 5 |
| role | 578 | 443 | 135 |

## Temporal semantics

| State | Count |
|---|---:|
| current | 193 |
| historical | 116 |
| unknown | 1328 |

Only directly cited, dated director/history facts can be labelled `current` or `historical`; all other relationship timing remains `unknown`.

## Derived views

| View | Nodes | Edges | Meaning |
|---|---:|---:|---|
| cited_only | 963 | 1122 | Edges with an originating source_id only |
| current_only | 251 | 193 | Explicitly cited and dated current historical-field edges only |
| core_network | 35 | 48 | One-hop edges incident to a cbst-core entity |
| evidence_gaps | 555 | 515 | Edges lacking an originating source_id; not evidence of absence |
