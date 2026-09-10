# Relationship graph quality baseline

This report is deterministic local aggregation over `data/registry/`; it does not assert facts or fill missing citations.

- Graph schema: `2`
- Canonical graph SHA-256: `1c336c4c11c8acd3f800510174aa3b50ddc9085e887c7544c14f411a61f5fee9`
- Live-registry parity: 204/204 entities; 422/422 people
- Cited edges: 1058/1571
- Directly uncited relation edges (evidence gaps): 513/1571
- Explicit unresolved stubs: 157

## Nodes

| Kind | Count |
|---|---:|
| entity | 204 |
| person | 422 |
| product | 474 |
| unresolved | 157 |

## Edges

| Type | Total | Cited | Uncited |
|---|---:|---:|---:|
| directs | 287 | 260 | 27 |
| founded | 198 | 0 | 198 |
| owns | 15 | 15 | 0 |
| produces | 474 | 326 | 148 |
| related | 19 | 14 | 5 |
| role | 578 | 443 | 135 |

## Temporal semantics

| State | Count |
|---|---:|
| current | 193 |
| historical | 57 |
| unknown | 1321 |

Only directly cited, dated director/history facts can be labelled `current` or `historical`; all other relationship timing remains `unknown`.

## Derived views

| View | Nodes | Edges | Meaning |
|---|---:|---:|---|
| cited_only | 911 | 1058 | Edges with an originating source_id only |
| current_only | 251 | 193 | Explicitly cited and dated current historical-field edges only |
| core_network | 31 | 42 | One-hop edges incident to a cbst-core entity |
| evidence_gaps | 553 | 513 | Edges lacking an originating source_id; not evidence of absence |
