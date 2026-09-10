# Relationship graph quality baseline

This report is deterministic local aggregation over `data/registry/`; it does not assert facts or fill missing citations.

- Graph schema: `2`
- Canonical graph SHA-256: `84730337220c9d1e92549160331c611dafb1f5943aaf634a2108d18cf4070c17`
- Live-registry parity: 204/204 entities; 422/422 people
- Cited edges: 1213/1728
- Directly uncited relation edges (evidence gaps): 515/1728
- Explicit unresolved stubs: 297

## Nodes

| Kind | Count |
|---|---:|
| entity | 204 |
| person | 422 |
| product | 474 |
| unresolved | 297 |

## Edges

| Type | Total | Cited | Uncited |
|---|---:|---:|---:|
| directs | 287 | 260 | 27 |
| founded | 355 | 155 | 200 |
| owns | 15 | 15 | 0 |
| produces | 474 | 326 | 148 |
| related | 19 | 14 | 5 |
| role | 578 | 443 | 135 |

## Temporal semantics

| State | Count |
|---|---:|
| current | 193 |
| historical | 204 |
| unknown | 1331 |

Only directly cited, dated director/history facts can be labelled `current` or `historical`; all other relationship timing remains `unknown`.

## Derived views

| View | Nodes | Edges | Meaning |
|---|---:|---:|---|
| cited_only | 1051 | 1213 | Edges with an originating source_id only |
| current_only | 251 | 193 | Explicitly cited and dated current historical-field edges only |
| core_network | 38 | 51 | One-hop edges incident to a cbst-core entity |
| evidence_gaps | 555 | 515 | Edges lacking an originating source_id; not evidence of absence |
