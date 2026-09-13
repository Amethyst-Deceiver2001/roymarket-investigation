# Hub Insignia — design notes

Started as a standalone mockup:
https://claude.ai/code/artifact/8bed5183-6ced-4df0-8c2d-8a4352ceaacd

**Update 2026-09-08 (v3): wired into the live Network Graph.** No longer
mockup-only — see the "v3 — wired into the live graph" entry in the
revision log below.
https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2

Working notes on the design decisions made across this thread, plus
supporting research into visual semiotics, kept here so the reasoning
survives past chat scrollback. See `spicy-beaming-kite.md` (plan mode
output) for the original scope; this file is the running rationale log
the plan doesn't capture.

## Revision log

**v1 — dark CRT terminal skin.** First pass adopted
`github.com/loryanstrant/ha-weylandyutani`'s literal palette (near-black
ground, neon terminal green, scanline overlay, glow/text-shadow) plus
Ron Cobb's Nostromo winged-sun-disk motif for the wordmark. Three-glyph
offensive/defensive/dual-use system, shape-coded per the dataviz skill's
CVD-safety rule (never hue-alone). Tested against 5 real registry
entities with live-fetched logos and bilingual naming.

**v2 — pivot to light/utilitarian.** User correction: the dark villain-
lair skin is the wrong read of Weyland-Yutani. The actual W-Y identity
(and Cobb's actual Nostromo signage) is *utilitarian first, aesthetic
second* — flat industrial signage, not mood lighting. Sharper point
underneath it: the real subjects of this investigation (state arms
producers, small grassroots drone shops) present themselves in
techno-optimist, venture-deck registers — clean, confident, "innovation"
language — despite manufacturing strike drones. A menacing dark skin
undersells that irony; a clean one lets the actual subject matter do the
unsettling work on its own. Rebuilt on paper-white ground, cobalt accent,
IBM Plex Sans/Mono, all glow/scanline/CRT-tint effects removed. Kept the
shape-coding grammar — that was never the problem.

**v2.1 — extended kit.** Added three more glyph layers using the same
modular parts (bar/ring/chevron/dot), grounded in real data rather than
invented cases: hub-site type (technopark/consortium vs. Soviet-legacy
institute/factory), hardware component tags (RF/EW, optical, fiber-optic
guidance, warhead), and drone platform type — critically, distinguishing
a purpose-built FPV kamikaze from a consumer quad + aftermarket
*система сброса* release rig, pulled from `wb_watch`'s own
`data/wb_watch.db` (`category='drone_drop_system'`, 219 real Wildberives
listings, e.g. "Система сброса груза для DJI MAVIC 3 Classic").

**v2.2 — badge contrast bug.** User flagged icons "nearly invisible
against background." Root cause: the offensive/defensive/dual glyph
badge sat on a *translucent* dark scrim over the card photo — fine
against a dark photo, but the dual-use glyph is drawn in `var(--ink)`
(near-black), so on a bright photo (ГОУДРОН's white showroom) the badge
read as an empty dark square. Separately flagged: the offensive/
defensive shapes themselves (an abstract filled chevron vs. an open
ring-with-arcs) were too visually similar to read at a glance. Fixed
both at once — opaque solid-white badges (contrast now independent of
whatever photo sits behind them), and swapped the abstract Cobb-derived
shapes for literal pictograms: a dagger (offensive), a shield
(defensive), a shield-with-dagger-inside (dual). This trades strict
grammar-purity (recombine only from a fixed abstract part-kit) for
outright recognizability — a deliberate call, logged in-page as a
"second revision" note, on the reasoning that legibility beats grammar
fidelity when the whole point of the mark is instant recognition.

**v2.3 — slug in the badge.** The top-corner id badge showed the repo's
own internal slug (`ooo-npts-basirtk`) — meaningless outside this
project's own file-naming convention. First fix (ИНН number) was itself
wrong for the same underlying reason the user then named directly: that
corner is signage real estate, not a data field — printing a raw literal
identifier there (whether an internal slug or an external database key)
occupies prime design space with the wrong *kind* of content. Landed on
an abstract classification code instead — `RM/DU-01`, `RM/OFF-01`,
`RM/DEF-01` — styled like a placard/stencil stamp (category + sequence),
the register a Nostromo bulkhead code or a shipping-container mark
actually works in. The ИНН didn't disappear; it moved to the card body
(`Full legal name (RU) ... — ИНН <n>`), where literal data belongs.

**v2.4 — company vs. product ambiguity.** User: not immediately obvious
which text is the company and which is the product line — the entity
name (H3) and the product chips at the bottom carried the same visual
register with no explicit label distinguishing them. Added two small
mono eyebrow labels: "Manufacturer / operator" above the entity name,
"Product / service lines" above the chip row.

**v2.5 — caption-panel contrast regression.** Adding the v2.4 field-label
line increased the caption block's content height, pushing text above
where the photo's darkening gradient (`.frame::after`, dark only in the
bottom 45%) actually took effect — against a light-toned photo (БАСИРТК's
grey facility facade) the label and tier line read as pale text on pale
stone, nearly unreadable. Root cause was compounded by a second, older
bug: the "dual-use" tier text was still colored `var(--ink)` (the body
near-black), which is unreadable on *any* dark scrim regardless of
gradient coverage — it was only ever surviving on darker photos by
accident. Fixed by giving the caption block its own solid opaque backdrop
(independent of the photo's tone, same fix pattern as v2.2's badges) and
brightening all three on-photo tier colors so none of them collapse
toward black or otherwise low-contrast hues.

**Pattern across v2.2 / v2.5**: every legibility bug so far has been the
same root mistake — styling an overlay element's contrast *relative to
the photo underneath it* instead of giving it a guaranteed-opaque surface
of its own. Worth checking any new overlay element against this before
it ships, not after a screenshot catches it.

**v3 — wired into the live Network Graph (2026-09-08).** The mockup was
explicitly scoped as a proposal to review before touching the live graph
(see the plan's "explicitly out of scope for this pass" section) — this
closes that loop, at user direction ("apply design notes to graph").
Three things carried over, one new problem solved along the way:

- **The dagger/shield/shield+dagger glyphs**, ported path-for-path from
  the mockup's finalized v2.2 SVGs into the graph's D3 render loop —
  same shapes, same "shape+color both load-bearing" rule, so the two
  artifacts read as one visual system rather than two unrelated ones.
- **Classification at graph scale, not just 5 hand-picked entities.**
  The mockup's offensive/defensive read was manual, entity-by-entity —
  fine for 5 cards, not for 118+ manufacturer nodes. Added
  `classify_variant()` to `build_relationship_graph.py`: a keyword
  heuristic over each entity's `products[]` text (same class of approach
  as `id_patterns.py`'s `UAV_TERMS` scoring elsewhere in this project),
  landing 24 of 207 entities with a classification (14 defensive, 7
  offensive, 3 dual). Explicitly logged in the script's own comment as a
  **presentation read, not a sourced registry claim** — same caveat the
  mockup carried by hand, now automated. Spot-checked against the
  mockup's own 5 manual calls: Овод → offensive and Тримикс/ГОУДРОН →
  defensive matched exactly; БАСИРТК didn't get picked up by the
  heuristic at all (its registry `products[]` text doesn't happen to
  contain the matched keywords) — a known, acceptable gap for a keyword
  pass, not silently pretended away.
- **Badges only render on hub-labeled nodes** (the same highest-degree-
  per-component set that already gets a persistent text label), not
  every classified entity — keeps the canvas from turning into a wall of
  icons on a 931-node graph. A sidebar legend explains the three marks
  and repeats the "presentation aid, not sourced" caveat where a viewer
  will actually see it, not just in a code comment.
- **New problem this pass, not present in the card-based mockup**: the
  mockup never had to solve "badge in a force-directed layout, node
  position changes every tick." Solved by binding the badge `<g>` to the
  same `hubLabelNodes` array the text label already uses and repositioning
  both inside the existing `ticked()` callback — an offset placement
  (upper-right of the node) rather than the label's straight-up
  placement, so the two don't collide.

Also carried the headshot work into the same graph, unrelated to the
glyph system but from the same "apply this session's work to the graph"
instruction: person nodes now carry a `photo` field, and the 23 (of 24)
locally-stored portraits in the registry render in the detail panel when
you click a person node — the 24th (`pinimasov-aleksandr`) is stored as
an external URL rather than a local `docs/images/` file and was skipped
rather than fetched live for this pass.

## Visual semiotics — research notes

Pulled in because the project has now made three real design calls that
are actually semiotic classification questions in disguise, and it's
worth grounding the vocabulary rather than reinventing it ad hoc.

**Peirce's icon / index / symbol** (foundational semiotic taxonomy).
An *icon* signifies by resemblance (a drawing of a printer for "print").
An *index* signifies by an existential/causal link (smoke → fire,
a footprint → the person). A *symbol* signifies by pure arbitrary
convention (a national flag, a legal-form abbreviation like ООО). The
v2.2 pivot from abstract shapes (chevron/ring — closer to symbols,
requiring the legend to be learned) to a dagger/shield (icons — read
by resemblance, no legend needed) is exactly a move down Peirce's
hierarchy from symbol toward icon, and that's *why* it fixed the
legibility complaint: icons don't require the viewer to have already
seen the key. [Icon, Index, and Symbol — Three Categories of Signs](https://vanseodesign.com/web-design/icon-index-symbol/),
[Charles Peirce - Icon, Index, Symbol](https://media-studies.com/peirce-sign-categories/)

**Otto Neurath's Isotype** (1920s–30s "wordless global language" for
statistical/social data, executed by Gerd Arntz — 4,000+ pictograms cut
in linocut). Two rules worth stealing directly for any future revision
of this schema: (1) a *greater quantity is never a bigger icon* — it's
more icons repeated at a fixed size, because size variation defeats
accurate comparison; relevant if this schema ever needs to encode
something like contract volume or headcount rather than category.
(2) Pictograms are drawn flat, never in perspective, specifically to
preserve legibility at a glance — the same instinct behind rejecting the
photo-realistic/gradient-heavy v1 glyphs in favor of flat silhouettes.
[Isotype (picture language) — Wikipedia](https://en.wikipedia.org/wiki/Isotype_(picture_language)),
[The Original Manifesto for Information Visualization — Maria Popova](https://www.themarginalian.org/2018/12/10/exact-thinking-in-demented-times-otto-neurath-isotype/)

**ISO 7001** (public information symbols — airports, transit,
wayfinding). Governed by a *design-and-test* standard (ISO 22727), not
just a symbol library — candidate pictograms are tested for comprehension
across countries/cultures before being registered. The discipline worth
borrowing isn't the symbol set itself (irrelevant domain) but the
methodology: a pictogram earns its place by testing legibility against
real viewers, not by looking right to its own designer. This project's
"take a screenshot, catch what's actually illegible" loop this session
is an ad hoc version of exactly that discipline, just with one viewer
instead of a cross-cultural test panel. [ISO 7001 — Wikipedia](https://en.wikipedia.org/wiki/ISO_7001),
[ISO 7001:2023 — ISO](https://www.iso.org/standard/77442.html)

**ANSI Z535 / GHS hazard pictograms** (industrial safety signage —
the direct lineage Cobb's Nostromo stencils were themselves referencing).
Splits pictograms into three functional classes — hazard alerts,
mandatory actions, prohibitions — each with its own reserved color
register, so category is never inferred from the pictogram shape alone
in isolation; shape and color-class are both load-bearing and both
standardized. Directly analogous to this project's own
offensive/defensive/dual split needing *both* a distinct shape (dagger/
shield/shield+dagger) and a distinct accent color per category, not
either alone — which is also exactly the dataviz skill's standing rule
(shape carries identity so it survives grayscale; color reinforces it
but is never load-bearing on its own). [ANSI Z535.1-2022 — ANSI Blog](https://blog.ansi.org/ansi/ansi-z535-1-2022-safety-colors-standard/),
[ANSI Z535 — Wikipedia](https://en.wikipedia.org/wiki/ANSI_Z535)

## Working principles distilled so far

1. **Icons over symbols where legibility is the goal.** A viewer
   shouldn't need the legend to guess right — favor resemblance-based
   marks (Peirce's icon) over abstract, arbitrarily-assigned ones
   (Peirce's symbol) unless the abstract system is genuinely more
   precise for a technical audience that already knows the key.
2. **Shape and color are both load-bearing, never either alone**
   (ANSI Z535 / dataviz skill). Test every glyph in grayscale.
3. **Never trust an overlay's contrast to the content behind it.**
   Give any text/icon sitting on a photo a guaranteed-opaque backdrop
   of its own — every contrast bug this session traced back to skipping
   this.
4. **Signage real estate carries classification marks, not raw data
   fields.** Prime visual real estate (card corners, badges) is for
   abstract, systematic, at-a-glance marks; literal identifiers (ИНН,
   full legal name, source citations) belong in the body text where
   they're read, not glanced at.
5. **Flat over dimensional, repetition over scaling** (Isotype). If this
   schema ever needs to encode magnitude, use repeated fixed-size marks,
   not a resized icon.

## v4 (2026-09-08, same day) — node/edge semiotic system, applied to the live graph

Follow-on to v3's hub badges: the user asked to keep researching visual
semiotics and apply new principles to *all* node types (companies,
products, etc.) and the *relationships* between them, not just hub
classification. Two more sources grounded this pass:

**Jacques Bertin's seven visual variables** (*Sémiologie Graphique*,
1967/1983) — position, size, shape/form, orientation, color/hue,
texture, value. The graph already used size (degree → radius) and
color (tier hue) correctly; **shape/form was unused as a categorical
channel** — every node kind (entity/person/unresolved) rendered as a
plain circle, distinguished only by fill color. That's a real gap by
Bertin's own rule: a *categorical* variable (node kind) should map to
a *categorical* visual variable (shape), not be folded into the same
channel (hue) already carrying a different categorical variable (tier).
[Visual Variables — ResearchGate](https://www.researchgate.net/publication/317266613_Visual_Variables),
[Jacques Bertin — Wikipedia](https://en.wikipedia.org/wiki/Jacques_Bertin)

**POLE methodology / i2 Analyst's Notebook link-analysis conventions**
(People, Objects, Locations, Events as distinct entity classes in
investigative link charts) — the genre this graph actually belongs to,
more directly than general dataviz. Two things taken directly: (1)
**"Objects" is its own first-class node class**, not a property folded
into an organization's record — this justified promoting `products[]`
from an entity's field into its own graph node kind rather than leaving
products invisible on canvas. (2) **"A link is drawn as a line, and
becomes an arrow if the relationship is directed"** — ownership,
founding, directorship, and production are all inherently directional
facts (X owns Y, not the reverse), and the graph was drawing them as
plain undirected lines. [What is link analysis? — i2 Group](https://i2group.com/articles/what-is-link-analysis-and-link-visualization)

**What changed, concretely:**

- **Shape now encodes node kind**, ported into the live graph via
  `d3.symbol()`: circle = organization/entity, diamond = person, square
  = product. (The sidebar legend's `.swatch.person` CSS had *already*
  promised a diamond for person nodes since an earlier revision — the
  canvas just never honored it. This pass closes that gap rather than
  inventing a new one.) Color continues to carry tier (entities) or a
  dedicated neutral token (`--product-fill`, a muted khaki/bronze,
  chosen to sit outside every existing tier hue so it doesn't collide
  with the tier channel's meaning). Symbol sizes are area-matched
  (`Math.PI * r²` fed to every shape's `.size()`) so apparent size stays
  consistent across shapes at a given degree, per how d3's symbol types
  are calibrated.
- **Product nodes**, new: `build_relationship_graph.py` now emits one
  node per `entities.json` `products[]` entry (dict or bare-string form)
  plus a `produces` edge from the parent entity — 477 product nodes,
  477 new edges, across 72 entities. Off by default (a `showProduct`
  toggle, same pattern as the existing person/stub toggles) since
  477 extra nodes would otherwise clutter every view — same instinct as
  the tier/degree filters already in place. `parent_entity`/`source_id`
  carried onto the node so the detail panel can cite where a product
  claim comes from.
  **This is a presentation promotion of already-registry data, not a
  new fact** — no `entities.json` schema change, no new correction
  needed. `variant` (offensive/defensive) classification was *not*
  pushed down to individual products this pass, even though it would be
  more precise there than at the hub/entity level — logged as a
  follow-on idea, not built, to keep this pass scoped.
- **Directed edges get arrowheads**: `owns`, `founded`, `directs`, and
  the new `produces` type now render with an SVG marker arrow pointing
  source → target, with the line trimmed back from the target node's
  radius so the tip clears the node instead of hiding under it.
  `role`/`related` stay undirected — deliberately, since those ties are
  genuinely ambiguous in direction, not just unencoded. Historical ties
  skip the arrow too (they already read as faded/uncertain via the
  existing dotted-and-dimmed treatment; adding an arrow on top would
  fight that signal rather than reinforce it).
- **Legend updated to explain both**: a one-line note under "Node kind"
  ("Shape marks kind... colour marks tier") and one under "Edge type"
  ("Arrowheads on owns/founded/directs/produces point source → target
  ... role/related stay undirected") — Bertin's own point that a visual
  system only works if the reader is told which channel means what.

Verified inline via a headless-Chrome render of the working file before
publish (per the artifact-design skill's "write, look once" discipline):
product toggle produces the expected khaki squares fanned off their
parent entities, a product node's detail panel correctly resolves back
to its parent via the new `produces` edge, arrowheads render visibly at
the ЦБСТ/Стратим/etc. hub clusters, and no new console errors appeared.
Republished to the same live graph URL,
https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2.

New working principles from this pass (continuing the numbered list
above):

6. **A categorical fact needs its own visual channel — don't stack two
   categorical variables onto one hue.** Node kind and entity tier are
   both categorical; they now live on shape and color respectively
   instead of competing for color alone.
7. **A relationship's directionality is itself a fact worth drawing.**
   If X owns/founded/directs/produces Y is asymmetric in the data, an
   undirected line is quietly discarding information the reader has no
   way to recover. Only add the arrow where the direction is genuinely
   known — don't force it onto ties (role/related) whose directionality
   is actually ambiguous.
8. **A field buried in a parent record is invisible to a link-chart
   reader.** Promoting `products[]` to real nodes (POLE's "Objects")
   made 477 already-sourced facts visible on the canvas for the first
   time, at zero new-sourcing cost — the data already existed and was
   already cited, it just weren't drawable.

## v4.1 (2026-09-08, later same day) — grouping made explicit, not implied

User feedback on the v4 screenshot: with the full 1408-node graph on
screen, the labeled hub clusters read fine individually, but everything
in between collapsed into what the user called "a sparse cluster of
loosely if at all connected galaxies of dots and diamonds grouped by an
uncertain principle." Diagnosis: `clusterCenters()` gave every connected
component of size ≥3 its own dedicated grid cell (that part worked —
visible in the screenshot as the well-spaced, labeled clusters), but
every component of size 1–2 — the overwhelming majority of the graph,
since a huge share of entities have exactly one director or founder and
nothing else — fell back to one shared anchor point at canvas center
with only weak (0.10-strength) pull toward it. Physically, that's ~150+
*unrelated* pairs all fighting for the same spot, spreading out via
collision force into what looks like one big diffuse cloud. There is no
actual false pattern there — every dot's position really is just
noise relative to its neighbors — but the *reader* has no way to tell
that from a real, weakly-drawn cluster, so it reads as "uncertain
grouping" even though the underlying data has a perfectly certain
grouping (each pair belongs to exactly one component). The bug was that
the layout wasn't telling the reader what it already knew.

Two changes, both aimed at removing that inference burden rather than
adding decoration:

1. **Every component gets its own anchor cell, sized to its own
   footprint.** Replaced the uniform grid (`clusterCenters()`, one cell
   size for every component regardless of member count) with a
   size-aware shelf pack (`packComponents()`): cell size scales with
   `sqrt(component size)`, clamped to [64px, 460px] for components of 2+
   members (a fixed small 40px cell for the residual true singletons —
   nodes whose only edge landed outside the current filtered view).
   A 100-node hub cluster now gets proportionally more canvas than a
   lone founder pair, instead of both being squeezed into the same cell
   size — the failure mode that made big clusters look cramped *and*
   pairs look like unstructured noise at the same time.
2. **Grouping is now drawn explicitly, not left to inferred proximity.**
   Every component of 3+ nodes gets a soft convex-hull halo
   (`d3.polygonHull`, padded 16px outward from centroid) behind it; every
   exactly-2-node pair gets a translucent rounded capsule between its two
   points (a 2-point hull is degenerate, so pairs get a simpler stand-in
   shape). Both recompute every simulation tick, same pattern as the
   existing hub-badge position updates. Styled as a single flat, very
   low-opacity neutral wash (`--hull-fill`/`--hull-stroke`, ~3.5–5%
   opacity) — deliberately *not* tier-colored, so it doesn't compete with
   the tier-color channel or read as a fourth categorical variable; its
   only job is "these belong to one component," nothing else. This is
   the standard graph-drawing technique for making cluster membership
   unambiguous (sometimes called set/bubble-set visualization) rather
   than relying on force-layout proximity alone to imply it — proximity
   is a *weak* signal once a canvas gets dense; an explicit boundary
   isn't.

Secondary legibility pass in the same edit: edge opacity floors raised
(role 0.35→0.42, related 0.30→0.36, everything else 0.65→0.78) since the
new halos gave edges more contrast to compete against; `clusterX`/
`clusterY` force strength raised 0.10→0.16 so components pull together
more decisively instead of drifting loosely inside their own cell. The
sidebar hint text and the reset-view / initial-load behavior were
updated to match (`fitToCurrentNodes()` now runs on load and on
"Reset filters & view", since the shelf-packed layout is routinely
taller than one screen — no longer safe to assume an identity zoom
transform shows the whole graph).

Verified via the same headless-Chrome-before-publish loop: reloaded,
checked console for new errors (none), screenshotted the settled
layout. The result: every visible clump on the canvas now has a drawn
boundary and a proportional size, and the residual true singletons
settle into one neat row at the bottom instead of a central blob —
"uncertain grouping" is no longer a description anyone would reach for.
Republished to the same live URL,
https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2.

New working principle:

9. **A real pattern the reader can't perceive is functionally the same
   as no pattern.** If a grouping is a known, certain fact in the data
   (component membership, in this case), don't make the reader infer it
   from weakly-drawn positional proximity — draw the boundary. Reserve
   inferred/implied relationships for cases where the ambiguity itself
   is the honest signal (this graph already does that correctly for
   `role`/`related` edges, which stay deliberately undirected because
   their directionality really is unclear).

## v5 (2026-09-09) — hub badge glyph replaced with hex/pattern family

Standalone "Hub Icon Schema" mockup artifact
(https://claude.ai/code/artifact/8bed5183-6ced-4df0-8c2d-8a4352ceaacd) was
built first per the plan approved this session, tested against real
imagery for three hub entities already carrying the richest `images[]`
coverage — «Овод» (offensive), ГОУДРОН (defensive, via its «Набат» drone
detector), and НПЦ БАСИРТК (dual — both «Ковровец» FPV and «Ступор»
counter-drone hardware). The mockup replaced the v3 dagger/shield glyph
pair with one fixed hex glyph whose *fill pattern*, not a second shape or
hue, carries the offensive/defensive/dual distinction: solid hex =
offensive, hollow hex with a center radar-return ring = defensive, hex
outline with a solid left half = dual. Rationale unchanged from v3's own
badge work — tier already owns the color channel, so a second categorical
fact needs a channel of its own (pattern), not a second hue stacked on the
same one; a grayscale strip on the mockup confirmed the three variants
stay distinguishable with color removed entirely.

User approved the mockup and asked to wire it into the live graph. This
did **not** require touching `build_relationship_graph.py`'s
`classify_variant()` — that keyword-heuristic products[]-read logic
(already run at full graph scale, not just the 5 hand-picked mockup
entities) is unchanged; only the glyph rendering changed. Replaced
`hubGlyphInner()` (three inline `<polygon>`/`<circle>` shapes drawn in a
local -9..9 coordinate space, backed by a `--panel`-colored circle for
contrast against whatever's underneath) and the corresponding
`.hub-badge` CSS rules (`.hex-backing`/`.hex-solid`/`.hex-outline`/
`.hex-ring`/`.hex-half`), reusing the existing `--variant-offensive`/
`--variant-defensive` theme tokens rather than introducing new ones. The
badge legend in the sidebar re-derives from the same `hubGlyphInner()`
call, so it updated automatically with no separate edit.

One process note worth keeping: mid-verification, a chrome-devtools
`evaluate_script` call meant to zoom in on a canvas badge for a screenshot
used `document.querySelector('svg')` and `svg.querySelector('g')` as a
fallback selector — the file has four `<svg>` elements (three small
sidebar legend swatches before the main 1100×680 canvas one), so the
"first g in first svg" fallback landed on the sidebar badge-legend's own
`<g>` and left a stray `transform="translate(555,0) scale(1)"` attribute
on it, live in the browser tab only. Caught by re-reading the legend's
outerHTML before publish, not by eyeballing a screenshot — the attribute
pushed the glyph outside the tiny 18×18 legend swatch's viewBox, so it
would have rendered blank. Removed before the page was reloaded fresh
from the saved file and re-verified; the published file was never at
risk since the mutation only ever touched a running page instance, not
the file on disk — but worth remembering for next time: when a page has
multiple `<svg>`s, always scope a debug selector to the specific one
being inspected (e.g. by size or by walking from a known node), never a
bare `document.querySelector('svg')`.

Verified via the same headless-reload-then-screenshot loop as v4/v4.1,
this time reloading straight from the saved file after the DOM mutation
was undone, confirming zero new console errors and all three glyph
variants rendering correctly at high zoom (solid/hollow-ring/split-fill
all legible). Republished to the same live URL,
https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2.

## v6 (2026-09-09) — product subtype icons, from a second standalone mockup

User asked for "more varied and intuitive icons for quadcopters vs FPV,
parts, various EW setups (antenna, dome, other types)" plus more
researched categories — extending the shape/pattern grammar established
by the hub badge (v3/v5) down to `products[]` nodes, which had rendered
as one undifferentiated square since v4 promoted them to graph nodes at
all. Surveyed the registry's 477 product entries by keyword before
designing anything (same discipline as classify_variant()'s own basis):
counted real hits for FPV/kamikaze (44), EW jammers (27), detectors (19),
batteries (17), antennas (12), multirotors (9), fixed-wing (8), and eight
smaller categories down to 1-2 hits each, which don't get their own
glyph — folded into a neighbor instead, per the same "why not more"
principle v5 already used for the hub badge.

Grounded the icon *design* in two further precedents beyond v4's
Bertin/POLE research: **MIL-STD-2525/APP-6** military symbology (a
symbol's frame — affiliation — and its interior icon — unit type — are
orthogonal; an operator learns the icon vocabulary once and reuses it
regardless of frame) justifies the icon sitting *inside* the existing
square-shape frame rather than replacing it — node `kind` still owns the
shape channel, tier still owns color, the icon is a fourth independent
channel same as the hub badge's fill-pattern. **ISO 7000** (equipment
graphical symbols) supplied the consistency discipline — one stroke
weight, one coordinate grid, held constant across all 15 icons so the set
reads as one vocabulary, not 15 unrelated drawings.

Standalone mockup built and approved first, same process as the hub
badge: https://claude.ai/code/artifact/fa4295ea-cef5-4fa0-ab0b-27cd92407a93.
First-pass icons for fixed-wing, helicopter, EW-portable, motor/
propeller, video-link, and repeater/relay read poorly at small size (the
fixed-wing glyph read as a plus-sign/medical-cross; the motor glyph as an
unrecognizable comma) — caught by reviewing the rendered mockup once,
per the "write, look once" discipline, and redrawn before publishing:
fixed-wing became a proper swept-wing silhouette, the motor a clean
two-blade X-prop, video-link the standard WiFi arcs-over-a-dot glyph
(abandoning a custom diagonal-arc attempt that rendered as a stray
letter shape), repeater/relay a truss-tower silhouette with
symmetric side arcs instead of a shape that read as a quote-mark next
to a letter A.

Wiring into the live graph, at user direction ("now apply to graph
artifact"):
- `scripts/build_relationship_graph.py` gained `classify_product()` — 15
  ordered keyword patterns (specific EW-subtype patterns checked before
  the generic jammer catch-all, generic UAV/multirotor checked last as
  the true fallback) plus a `fiber_optic` boolean modifier, run over each
  product's own name+description text, same presentation-layer-read
  discipline and same non-registry-field status as `classify_variant()`.
  Regenerated `relationship_graph.json`: of 477 product nodes, 153 (32%)
  matched a category, 4 tagged fiber-optic-guided; the other 324 are
  genuine misses — GISP-catalogue IT/office hardware (servers,
  motherboards, biometric kiosks) an АО «ПК «Азимут»-style entity lists
  alongside its actual UAV products, correctly outside the UAV/EW
  vocabulary this set was scoped to, not a classifier bug.
- `network_graph.html`: product nodes got a size floor
  (`effectiveRadius()`, min 7px — a raw degree-1 product node's natural
  radius is often the domain floor of 4px, too small to draw a legible
  icon in) threaded through symbol sizing, collision radius, and directed-
  edge arrow trim so the enlarged square agrees with the physics and the
  arrowheads. `productIconMarkup(category)` ports the 15 mockup icons
  into a local -12..12 coordinate space, rendered as a `<g class=
  "product-icon">` scaled to each node's own radius (`scale(effectiveRadius
  (d)/12)`) and drawn straight onto the square's own fill (no separate
  backing circle, unlike the hub badge — the square IS the icon's
  background here) via a new `--product-icon-ink` token, picked
  per-theme for contrast against `--product-fill` rather than reusing an
  existing token, since the two fills sit on top of each other. Fiber-
  optic gets a small dashed-ring corner tag, same "modifier not its own
  category" treatment the mockup used. An uncategorized product still
  renders as the plain square exactly as before this revision.

Verified the same way as every prior revision: `node --check` on the
extracted script, then headless reload with the product toggle switched
on, confirming the console stayed clean and multiple categories (antenna,
EW-vehicle, EW-stationary, multirotor, repeater) render legibly at zoom
around a real cluster (ГК «Логос», ООО «СКБ Пиранья»). Republished to the
same live graph URL, https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2.

New working principle:

10. **A frame/icon system generalizes past its first use case.** The
    same three-part contract that made the hub badge work — node kind
    keeps the shape channel, tier keeps color, the new fact gets its own
    independent channel (fill-pattern for the hub, an interior icon for
    the product) — applied a second time with no redesign of the
    existing channels, because MIL-STD-2525's frame/icon orthogonality
    was the right model from the start, not just a convenient one for
    the hub badge specifically.

## v7 (2026-09-13) — merged a parallel hardening pass; product icons cut to 2

A separate working copy of this repo (same machine, confirmed by the user)
had, in parallel, rebuilt `build_relationship_graph.py` around a stricter
contract (`graph_contract.py`, schema_version 2, exact-equality validation
wired into `check_registry.py`), fixed a real founder-share-parsing bug,
excluded `_merged_into` tombstones from the graph, and — the one point of
actual disagreement — replaced `classify_product()`'s 15-category keyword
heuristic (v6, above) with a deliberately conservative 2-signal version:
only explicit "multirotor/quadcopter" or "vehicle-mounted" wording gets
classified; every other product (462 of 474, post-merge) now reads
`unclassified` rather than inferring a subtype from generic UAV/jammer
language. Reasoning given: generic wording doesn't actually support a
specific-subtype inference, and this project's own standard is to survive
a hostile lawyer, not to look complete.

User's call after reviewing both: adopt the conservative classifier
everywhere (recommended by both the handoff's own reasoning and this
project's "no guessing, no placeholders"/"never present inference as
fact" standing rules), but keep `classify_variant()` (the offensive/
defensive/dual hub badge from v3/v5) — a separate, already-approved,
entity-level read of the same `products[]` text, not something the
product-classifier decision was about. Re-added `classify_variant()` to
the merged `build_relationship_graph.py`, wired `variant=classify_variant
(entity)` back into the entity node emission, and extended
`graph_contract.py`'s entity `NODE_FIELDS` to allow it — `check_registry
.py --quiet` and `graph_contract.validate_graph()` both pass clean with
this addition, confirming it doesn't fight the new contract.

On the live graph: `productIconMarkup()` cut from 15 cases down to 2
(multirotor, vehicle-mounted EW), reading the new `classification: {status,
uav_platform, ew_installation}` node shape instead of the old flat
`category`/`fiber_optic` fields; the fiber-optic corner-tag modifier was
retired entirely (the merged classifier doesn't track it). Sidebar copy
rewritten to say plainly that only explicit wording earns an icon. Hub
badges needed no changes — same `variant` field, same rendering — since
that classifier round-trips through the merge unchanged.

Merge mechanics, for the record: committed this session's own uncommitted
work as a checkpoint first (`d9d48a5`), then `git merge` the recovered
branch, resolving the one real code conflict (`build_relationship_graph
.py`) by taking the incoming rewrite wholesale and re-adding
`classify_variant()` on top, rather than hand-splicing two divergent
files. `relationship_graph.json`/`_views.json` regenerated from the
merged code rather than merged as data (1308 nodes, 1637 edges, 208
unresolved — matches the incoming branch's own reported figures exactly).
Restored `tests/fixtures/bfo_*.xlsx` after running `test_bfo_parser.py`
per the incoming branch's own documented note that its `build()` step
regenerates those tracked fixtures as an unrelated side effect.

Verified: `python3 tests/test_relationship_graph.py` (8 passed),
`test_graph_explorer.py` (4 passed), full existing `test_*.py` suite,
`graph_contract.validate_graph()` (0 errors), `check_registry.py --quiet`
(0 errors, pre-existing warnings only), `check_tag_balance.py` on both
`docs/index.html` and the new `docs/relationship-graph.html`, `node
--check` on the extracted script, and a headless reload of the live
graph confirming node/edge counts match and the 12 now-classified
products (10 multirotor, 2 vehicle-mounted) render their icons correctly
with no new console errors. Republished to the same live URL,
https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2.

New working principle:

11. **A more conservative classifier is a legitimate design decision, not
    just a smaller one.** Cutting 13 of 15 icon categories reads like a
    regression by icon count alone, but the actual trade is precision for
    recall in a document meant to survive adversarial scrutiny — the
    right call depends on what the visual is *for*, which is a judgment
    only the project owner can make, not something to resolve by
    defaulting to whichever version already shipped.
