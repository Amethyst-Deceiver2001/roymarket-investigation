#!/usr/bin/env python3
"""Shared schema contract for generated relationship-graph artifacts.

The graph is a derived view of the registry.  Its edges may be intentionally
uncited when the source registry field is an unresolved legacy assertion; the
contract preserves that distinction rather than inventing a source reference.
"""
from __future__ import annotations

import re
from collections import Counter

GRAPH_SCHEMA_VERSION = 13
NODE_KINDS = {"entity", "person", "product", "unresolved",
              "government_customer", "military_unit", "program", "event", "group", "storefront"}
EDGE_TYPES = {"owns", "related", "founded", "directs", "role", "produces",
              "procures", "confirmed_field_use", "cbst_tie", "family_tie",
              "sells_for", "operates", "organises", "resident_of",
              "participated_in", "part_of", "member_of",
              "banks_with", "acquiring_via", "ships_via", "lists", "operated_by"}
TEMPORAL_STATUSES = {"current", "historical", "unknown"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UNIT_TYPES = {"army", "division", "brigade", "regiment", "battalion", "detachment",
              "volunteer_detachment", "unit_designator", "grouping",
              "unspecified_role"}
UNIT_DESIGNATION_CONFIDENCE = {"named", "descriptive", "grouping"}

NODE_FIELDS = {
    "entity": {"id", "kind", "label", "name_latin", "inn", "tier",
               "sanctioned", "legal_form", "degree", "product_count"},
    "person": {"id", "kind", "label", "name_latin", "sanctioned", "degree"},
    "product": {"id", "kind", "label", "owner_slug", "source_id",
                "classification", "degree"},
    "unresolved": {"id", "kind", "label", "degree"},
    "government_customer": {"id", "kind", "label", "degree"},
    "military_unit": {"id", "kind", "label", "unit_type", "parent_grouping",
                       "designation_confidence", "degree"},
    "program": {"id", "kind", "label", "subtype", "degree"},
    "event": {"id", "kind", "label", "subtype", "degree"},
    "group": {"id", "kind", "label", "subtype", "degree"},
    "storefront": {"id", "kind", "label", "platform", "degree"},
}
EDGE_FIELDS = {
    "source", "target", "type", "label", "source_id", "as_of", "weight",
    "temporal_status", "confidence", "detail", "grade",
}
# B1 (schema v12): every edge carries a reader grade, doc / rep / open, the same three a page shows.
# An edge with its own confidence is graded from it (display_helpers.READER_GRADE). Every other edge
# is graded from the kind of document its source_id points at, through this one table; an edge with
# no source is "open". The filename prefix decides first, because a content-guessed source type can be
# wrong (Telegram posts typed "court"); the type is the fallback. Nobody grades an edge by hand.
EDGE_GRADES = {"doc", "rep", "open"}
# Every registry confidence value -> reader grade, in one table (display_helpers.READER_GRADE reads it).
def has_designation(record: dict) -> bool:
    """True when a record's sanctions[] names at least one regime.

    An entry with regime null is an aggregator match (OpenSanctions topics such as
    sanction.linked) with no official listing read; it is a lead, not a designation,
    so it must not draw the Sanctioned mark.
    """
    for s in record.get("sanctions") or []:
        if isinstance(s, dict) and s.get("regime"):
            return True
    return False


CONFIDENCE_GRADE = {
    "doc": "doc", "press": "rep", "inferred": "open",          # basis (sells_for, memberships, partners)
    "t-doc": "doc", "t-open": "rep",                            # cbst_tie
    "corroborated": "rep", "single": "rep",                     # relation-envelope and delivery credibility
    "confirmed": "doc", "probable": "rep", "unconfirmed": "open",   # family_of
}
SOURCE_PREFIX_GRADE = {
    # registers, filings, official records: a document shows it
    "EGRUL": "doc", "EGRULAPI": "doc", "EGRIP": "doc", "UD": "doc", "BFO": "doc", "РЕСУРС": "doc",
    "ZAKUPKI": "doc", "PATENT": "doc", "TRADEMARK": "doc", "ROSPATENT": "doc", "GISP": "doc", "FNS": "doc",
    "PBNALOG": "doc", "FEDRESURS": "doc", "COURT": "doc", "NSPD": "doc", "RKN": "doc", "MCHS": "doc",
    "FSA": "doc", "PP719": "doc", "CERT": "doc", "PROVERKI": "doc", "ROM": "doc", "DATASET": "doc",
    "AERONEXT": "doc", "OCR": "doc", "EU": "doc", "OFAC": "doc", "UKAZ": "doc", "SECO": "doc", "UKSL": "doc", "NSDC": "doc", "DRS": "doc", "GUR": "doc", "FUNDNTI": "doc", "MINPROMTORG": "doc",
    # the press, aggregators and third-party compilations: reported
    "PRESS": "rep", "TRANSCRIPT": "rep", "DOSSIER": "rep", "RUSPROFILE": "rep", "CHECKO": "rep",
    "ALEPH": "rep", "OPENSANCTIONS": "rep", "RUPEP": "rep", "PEP": "rep",
    # a party's own posts, pages and listings: its own word, reported
    "TGPOST": "rep", "TGWEB": "rep", "TG": "rep", "TGMEDIA": "rep", "TGFILE": "rep", "TGUSERS": "rep",
    "WEB": "rep", "SITE": "rep", "WEBCAPTURE": "rep", "WAYBACK": "rep", "CATALOG": "rep", "OZON": "rep",
    "WILDBERRIES": "rep", "NALETAY": "rep", "YOUTUBE": "rep", "IMG": "rep",
}
SOURCE_TYPE_GRADE = {"egrul": "doc", "egrul_api": "doc", "bfo": "doc", "ustav": "doc", "minjust": "doc",
                     "court": "doc", "government_contract": "doc", "press": "rep", "transcript": "rep"}


def source_grade(src: dict | None) -> str:
    """doc / rep / open for one sources.json record (None: no source -> open)."""
    if not src:
        return "open"
    if src.get("type") == "sanctions_list":
        return "doc"                      # an official list or notice saved as a web capture (US Federal Register, Japan MOF)
    name = (src.get("path") or "").rsplit("/", 1)[-1]
    if name.startswith("ul-") or name.startswith("ip-"):
        return "doc"
    if name[:1] in "AА" and name[1:2].isdigit():
        return "doc"                      # arbitration court filings, A40-…
    g = SOURCE_PREFIX_GRADE.get(name.split("_", 1)[0])
    if g:
        return g
    g = SOURCE_TYPE_GRADE.get(src.get("type") or "")
    # A source whose prefix and type both miss the table above is one this
    # table has no documented grade for -- defaulting that to "rep" would
    # silently overstate it as a party's own word/the press, one of only
    # three grades a reader sees. "open" is the honest default: cited but
    # ungraded, not "we checked and it's reported." (Found 05.10.2026 by an
    # adversarial code review; 86 of 9064 sources.json records hit this path
    # at the time, mostly internal ARTIFACT_ captures and a few odd-named
    # pulls with no recognized prefix/type.)
    return g or "open"
# Confidence vocabulary carried over verbatim from entities.json's own
# cbst_tie.confidence field (t-doc/t-open/press are positive-tie values;
# "none"/"not_established" mean no tie and are never emitted as edges).
CBST_TIE_CONFIDENCE = {"t-doc", "t-open", "press"}
# family_tie.confidence: mirrors the source dossier's own hedging language
# ("мать X" stated plainly vs "вероятно дядя"/"предположительно отец" vs an
# explicit "установить кто" unresolved flag) rather than inventing a new
# vocabulary -- see people.json's family_of.confidence.
FAMILY_TIE_CONFIDENCE = {"confirmed", "probable", "unconfirmed"}

# sells_for (added 2026-10-01, schema v7): seller -> manufacturer or brand whose goods it sells, from the
# seller's own entity record (`sells_for[]`). It exists because a manufacturer's product reaches buyers
# through legal entities that are not the manufacturer: the Ozon sole traders selling КБ «СПЕКТР»
# propellers, the named dealers of «3mx». An edge says "this seller of record sells that maker's goods";
# it never says the maker authorised it unless the basis does. The edge label is the sales channel.
#   doc      a primary document (marketplace seller panel, dealer certificate, the maker's own dealer
#            page, the seller's own site) states that this seller sells that maker's goods
#   press    a press or third-party report says so
#   inferred the investigator's reading, not stated by any document (recorded so it is visible and gradable)
SELLS_FOR_BASIS = {"doc", "press", "inferred"}

# Relation envelope (added 2026-10-02, schema v9; piloted on sells_for). Every field is optional and
# rides in the edge's `detail` object (null when the record carries none). `basis`/`confidence` stays the
# coarse grade the graph draws; the envelope adds who said it and how sure we are, kept apart
# (Admiralty principle: source and information are graded separately).
#   products       what moves on this edge (strings, as the document names them)
#   status         latest of the record's dated status_history[] (announced -> onboarding -> listed ->
#                  shipping -> delisted); every history entry needs a date and a source
#   asserted_by    who makes the claim: self (the seller or maker), counterparty (the other party, e.g. a
#                  maker naming its dealer), platform (a marketplace panel), regulator, press, investigator
#   credibility    doc (a primary document states it), corroborated (two or more independent sources),
#                  single (one non-document source), inferred (the investigator's reading)
#   authorised     did the maker authorise the sale: yes / no / unknown / n/a (the seller is the maker)
#   role           what the seller is on THIS edge (manufacturer, seller_of_record, licensed_dealer, distributor):
#                  one company can be maker of one product and dealer of another, so the role belongs to the
#                  relation; the entity's `ecosystem_roles` is only a summary and must cover every role used
#   open           what the edge does not prove (free text)
SALE_STATUSES = ("announced", "onboarding", "listed", "shipping", "delisted")
ASSERTED_BY = {"self", "counterparty", "platform", "regulator", "press", "investigator"}
CREDIBILITY = {"doc", "corroborated", "single", "inferred"}
AUTHORISED = {"yes", "no", "unknown", "n/a"}
RELATION_ROLES = {"manufacturer", "seller_of_record", "licensed_dealer", "distributor"}

# Media records (data/registry/media.json, track V, 2026-10-02). Not drawn on the graph; validated by
# check_registry.py. A picture is evidence only for what `shows` says someone saw in it.
MEDIA_KINDS = {"photo", "video", "still", "satellite", "street-level", "screenshot", "scan", "graphic"}
MEDIA_GENRES = {"marketing", "field_test", "combat", "facility", "production", "training", "recruitment",
                "event", "handover", "interview", "portrait", "logo", "document",
                "user_photo"}   # user_photo: a buyer's or user's own picture of a product
MEDIA_ASSERTED_BY = ASSERTED_BY | {"third_party"}   # third_party: e.g. a customer's upload on a map service
MEDIA_PUBLISH = {"ok", "excerpt", "internal"}        # excerpt: a maker's marketing, used in part for reporting
MEDIA_ABOUT_TYPES = {"entity", "person", "product", "version", "delivery", "listing", "unit", "program"}
MEDIA_GEO_PRECISION = {"exact", "building", "street", "town"}
MEDIA_GEO_METHOD = {"register_address", "source_stated", "geolocated"}   # register_address: ЕГРЮЛ/ЕГРИП, geocoded
MEDIA_REDACT = {"none_needed", "blur_pending", "blurred"}   # blur only clearly uninvolved bystanders; the involved are shown
MEDIA_REDACT_GENRES = {"handover", "training", "recruitment", "production", "event", "combat", "portrait"}
DETAIL_KEYS = {"products", "status", "asserted_by", "credibility", "authorised", "open", "role"}
# the coarse basis must not contradict the finer credibility
BASIS_CREDIBILITY = {"doc": {"doc", "corroborated", "single"}, "press": {"corroborated", "single"},
                     "inferred": {"inferred"}}


def sale_detail(sale: dict):
    """The edge `detail` object for one sells_for[] record, or None when it carries no envelope field."""
    d = {}
    if sale.get("products"):
        d["products"] = list(sale["products"])
    hist = [h for h in sale.get("status_history") or [] if isinstance(h, dict) and h.get("status")]
    if hist:
        d["status"] = sorted(hist, key=lambda h: h.get("as_of") or "")[-1]["status"]
    for k in ("role", "asserted_by", "credibility", "authorised", "open"):
        if sale.get(k):
            d[k] = sale[k]
    return d or None

# Programs, events and groups (added 2026-10-01, schema v8), kept in data/registry/programs.json.
#   program  a body of support or membership with many members and attributes of its own: a residency
#            (НПЦ «Ушкуйник»), an accelerator, a centre network, the national project «БАС»
#   event    a recurring series or one edition of a gathering (Дронница, ПМЭФ)
#   group    a cluster of separate legal entities that share a brand or a founder network; it has no
#            legal identity and never replaces its members
# Edges: operates / organises (entity -> program / event), resident_of (entity -> program),
# participated_in (entity -> event), part_of (program -> program, event -> event), member_of
# (entity -> group). `confidence` carries the same basis grade as sells_for; part_of is structural
# and carries none. Counts such as "30+ residents" stay claims on the record, never edges.
PROGRAM_KINDS = {"program", "event", "group"}
PROGRAM_SUBTYPES = {
    "program": {"national_project", "federal_project", "centre_network", "residency", "accelerator",
                "grant_scheme", "legal_regime"},
    "event": {"event_series", "event_edition"},
    "group": {"brand_cluster", "founder_network"},
}
MEMBERSHIP_ROLES = {"resident", "accelerator_participant", "graduate", "applicant",
                    "exhibitor", "speaker", "organiser", "co-organiser", "signatory", "participant",
                    "sponsor", "attendee"}
STRUCTURAL_NO_BASIS = {"part_of"}
BASIS_EDGE_TYPES = {"sells_for", "operates", "organises", "resident_of", "participated_in", "member_of",
                    "banks_with", "acquiring_via", "ships_via", "lists", "operated_by"}
# Product records and storefronts (added 2026-10-02, schema v11), from data/registry/products.json. A product record
# is ONE product node however many dealers sell it; the per-version leaves of the maker's products[] that the record
# covers are not drawn separately. A storefront node is a store account on a platform or a seller's own site, with
# no legal identity of its own: `lists` (storefront -> product, label = channel) says it offers the product, and
# `operated_by` (storefront -> entity) is drawn only when the listing names a registry entity as the seller. A dealer
# with no registry entity stays a storefront. Both are graded like sells_for. Entity nodes carry `product_count`
# (the products drawn for them) so a viewer can show a count badge and expand on demand instead of a leaf cloud.
# Platform partners (added 2026-10-02, schema v10): an entity's `platform_partners[]` (usually the platform operator)
# names the bank, the card acquirer and the logistics partner it works through, each as an edge to that partner's
# entity: kind bank -> banks_with, acquirer -> acquiring_via, logistics -> ships_via. Graded like sells_for. A
# partner is recorded only from a document that names it; a role named only generically («платёжные системы и
# эквайеры», «логистические партнёры») is not a partner.
PARTNER_KIND_EDGE = {"bank": "banks_with", "acquirer": "acquiring_via", "logistics": "ships_via"}

# entities[].ecosystem_roles (added 2026-10-01): what an entity does in the product chain, orthogonal to
# `tier` (tier measures closeness to ЦБСТ). Absent means "not yet classified", NOT "manufacturer".
ECOSYSTEM_ROLES = {
    "manufacturer",       # makes the product
    "brand",              # a product brand whose legal entity is not established (use legal_entity_status)
    "seller_of_record",   # the legal entity that appears as seller on a marketplace or invoice
    "licensed_dealer",    # named or certified by the manufacturer as an official dealer/supplier
    "distributor",        # wholesale or regional distribution
    "platform_operator",  # operates the marketplace/agent contract through which sellers sell (ООО «МПТМ», РОЙ.МАРКЕТ)
}
# Brands (B5, 2026-10-02): the names readers meet on boxes, marketplaces and channels. A card leads with a
# documented primary brand and shows the legal name directly beneath it. A product name is never a company brand.
BRAND_KINDS = {"trade_name", "trademark"}   # trademark: a registration in the entity's own trademarks[]
LEGAL_ENTITY_STATUS = {"established", "unresolved"}

# related_entities[].relationship_type (added 2026-09-15, schema v5) — a
# controlled vocabulary replacing the previous hardcoded "related
# (ambiguous)" edge label with the real category each of the registry's 42
# related_entities[] ties actually falls into, derived from reading all 42
# entries rather than invented ahead of the data. `competitor` is defined
# here for future use even though no entity currently carries it — no
# confirmed product-competitor claim exists in the registry as of this
# writing; adding the category doesn't mean populating it without evidence.
RELATED_ENTITY_RELATIONSHIP_TYPES = {
    "dealer",                        # authorized reseller of another entity's product
    "co-exhibited",                  # separate exhibitors at the same event/forum
    "co-speaker",                    # named speakers/co-appearances at the same conference or press piece
    "sister-entity",                 # confirmed common director/founder/ownership, same corporate family
    "group-structure",               # nonprofit R&D arm + commercial arm, or -СП joint-venture vehicle, within one group
    "managed-by",                    # ЕГРЮЛ-listed управляющая организация relationship
    "external-registry-cross-listed",# a third-party registry (GUR/OpenSanctions) lists them as related; mechanism not independently confirmed
    "same-name-different-entity",    # shares a brand/name; CONFIRMED to be a distinct legal entity, not the same one
    "training-partnership",          # co-runs a training/operational program, not a corporate tie
    "competitor",                    # rival products/entities in the same market segment (unpopulated as of schema v5 -- no sourced claim exists yet)
    "shared-address",                # registered at the identical street address per EGRUL, with NO confirmed director/founder overlap -- a co-location signal only, distinct from sister-entity (which requires a confirmed common principal)
    "counterparty",                  # buyer/seller or lender/borrower tie established by a litigation record (arbitration court filing) -- an ordinary commercial transaction confirmed by a court's own findings of fact, not a marketing claim or a corporate-family assertion
    "operated-brand",                # a sole trader or company that traded under the other record's brand during the dated period, per a document; says nothing about who runs the brand now
    "component-supplier",            # one entity publicly names another's product as a component of its own product, and/or the other publicly names it as a customer (BOM line, own-channel statement) -- a self-reported supply tie, not a contract or corporate link
}
PRODUCT_CLASSIFICATION_FIELDS = {
    "status", "uav_platform", "ew_installation",
}

# event_type (added 2026-09-15) -- a controlled vocabulary for re-typing a
# battlefield_evidence[]/government_contracts[]/marketing_claims[] entry as a
# dated transaction between two named parties, instead of a bare prose
# paragraph on one entity's own record. Derived from a validated design
# prototype (a 9-row hand-built timeline over the Кузнечик/Булат flagship
# chains -- see notes/rebuild_plan.md's 2026-09-15 evidence-ledger entry)
# before being applied to real registry data, same "prototype the visual
# before committing to a schema change" discipline as every other exhibit
# this project has shipped.
#
# Each typed entry also carries an `actor_to` object naming the second
# party: {"kind": one of ACTOR_KINDS, "id": a resolvable slug/node id or
# null, "label": a human-readable name -- filled always, since `id` is
# frequently not yet resolvable to an existing catalogued node (see the
# multi-role-individuals/military-unit lesson below)}.
#
# Deliberately NOT wired into build_relationship_graph.py yet, and NOT
# validated by validate_graph() above: doing so would require resolving
# every actor_to.label to a real graph node, and this project already hit
# the failure mode that guards against -- a peer audit (2026-09-15) found
# `confirmed_field_use` sitting at a single edge was CORRECT, not a gap,
# because military_units.json is deliberately scoped to one specific source
# network (a delivery-tracking channel) and must not be widened with units
# named only in unrelated drone-manufacturer battlefield posts, even though
# those posts are perfectly good evidence in their own right. event_type
# lets that evidence exist as a structured, dated, typed record -- and
# drive a browsable evidence-ledger exhibit -- without forcing a premature
# or catalog-polluting graph edge. Wire actor_to.id -> a real node (and add
# graph validation) only once a specific event_type's target is something
# this project has already decided belongs in the graph (e.g. a
# `government_customer` contract award, which the graph already resolves
# via `procures` edges independent of this field).
EVENT_TYPES = {
    "press_self_report",       # on-record interview/press statement by the entity itself
    "field_confirmation",      # independent (non-marketing) third-party republication of field use
    "thank_you_letter",        # «благодарственное письмо» genre -- see CLAUDE.md's documented pattern
    "commendation",            # «почетная грамота» genre, same family as thank_you_letter
    "delivery_confirmation",   # a УПД/Акт or equivalent closing a contract_award
    "contract_award",          # a government_contracts[] entry, sole-supplier or tendered
    "handover_ceremony",       # a staged/photographed handover event
    "battlefield_sighting",    # combat-footage/downed-unit sighting, independent of self-reporting
    "marketing_claim",         # self-incriminating self-promotion, not independently corroborated
}
ACTOR_KINDS = {"entity", "person", "military_unit", "government_customer"}


def _error(errors: list[str], message: str) -> None:
    errors.append(f"graph: {message}")


def _is_date(value) -> bool:
    return isinstance(value, str) and bool(DATE_RE.fullmatch(value))


def validate_graph(
    graph: dict,
    entities: list[dict],
    people: list[dict],
    sources: list[dict],
) -> list[str]:
    """Return graph-contract failures without printing or mutating inputs."""
    errors: list[str] = []
    if not isinstance(graph, dict):
        return ["graph: top-level value must be an object"]
    if graph.get("schema_version") != GRAPH_SCHEMA_VERSION:
        _error(errors, f"schema_version must be {GRAPH_SCHEMA_VERSION}")

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    unresolved = graph.get("unresolved")
    if not isinstance(nodes, list):
        _error(errors, "nodes must be a list")
        nodes = []
    if not isinstance(edges, list):
        _error(errors, "edges must be a list")
        edges = []
    if not isinstance(unresolved, list):
        _error(errors, "unresolved must be a list")
        unresolved = []

    for count_key, values in (("node_count", nodes), ("edge_count", edges),
                              ("unresolved_count", unresolved)):
        if graph.get(count_key) != len(values):
            _error(errors, f"{count_key} does not equal its array length")

    live_entities = {
        e["slug"] for e in entities
        if isinstance(e, dict) and e.get("slug") and not e.get("_merged_into")
    }
    live_people = {
        p["slug"] for p in people
        if isinstance(p, dict) and p.get("slug") and not p.get("_merged_into")
    }
    # graph_tier == "reference" people (relatives, staff, signatories) are kept on
    # file but may be absent from the graph, so a missing node is not an error.
    reference_people = {
        p["slug"] for p in people
        if isinstance(p, dict) and p.get("slug") and p.get("graph_tier") == "reference"
    }
    # Nodes with no path to the ЦБСТ hub are deliberately left off the graph and
    # listed in detached_ids; a missing node is only an error if it is not listed.
    detached = set(graph.get("detached_ids") or [])
    tombstone_entities = {
        e["slug"] for e in entities
        if isinstance(e, dict) and e.get("slug") and e.get("_merged_into")
    }
    tombstone_people = {
        p["slug"] for p in people
        if isinstance(p, dict) and p.get("slug") and p.get("_merged_into")
    }
    source_ids = {s.get("id") for s in sources if isinstance(s, dict) and s.get("id")}

    node_by_id: dict[str, dict] = {}
    for i, node in enumerate(nodes):
        where = f"nodes[{i}]"
        if not isinstance(node, dict):
            _error(errors, f"{where} must be an object")
            continue
        kind = node.get("kind")
        node_id = node.get("id")
        if kind not in NODE_KINDS:
            _error(errors, f"{where}.kind has invalid value {kind!r}")
            continue
        if set(node) - NODE_FIELDS[kind]:
            _error(errors, f"{where} has unsupported field(s) {sorted(set(node) - NODE_FIELDS[kind])}")
        if not isinstance(node_id, str) or not node_id:
            _error(errors, f"{where}.id must be a non-empty string")
            continue
        if node_id in node_by_id:
            _error(errors, f"duplicate node id {node_id!r}")
            continue
        node_by_id[node_id] = node
        if not isinstance(node.get("label"), str) or not node["label"]:
            _error(errors, f"{where}.label must be a non-empty string")
        if not isinstance(node.get("degree"), int) or node["degree"] < 0:
            _error(errors, f"{where}.degree must be a non-negative integer")
        if kind == "entity":
            if node_id not in live_entities:
                _error(errors, f"{where} entity id {node_id!r} is not a live entity")
            if not isinstance(node.get("sanctioned"), bool):
                _error(errors, f"{where}.sanctioned must be bool")
        elif kind == "person":
            if node_id not in live_people:
                _error(errors, f"{where} person id {node_id!r} is not a live person")
            if not isinstance(node.get("sanctioned"), bool):
                _error(errors, f"{where}.sanctioned must be bool")
        elif kind == "product":
            owner = node.get("owner_slug")
            if not node_id.startswith(f"product::{owner}::"):
                _error(errors, f"{where}.id must be namespaced to owner_slug")
            if owner not in live_entities:
                _error(errors, f"{where}.owner_slug {owner!r} is not a live entity")
            sid = node.get("source_id")
            if sid is not None and sid not in source_ids:
                _error(errors, f"{where}.source_id references unknown source {sid!r}")
            classification = node.get("classification")
            if not isinstance(classification, dict):
                _error(errors, f"{where}.classification must be an object")
            else:
                if set(classification) != PRODUCT_CLASSIFICATION_FIELDS:
                    _error(errors, f"{where}.classification has invalid field set")
                if classification.get("status") not in {"classified", "unclassified"}:
                    _error(errors, f"{where}.classification.status is invalid")
                if classification.get("uav_platform") not in {"multirotor", "unknown"}:
                    _error(errors, f"{where}.classification.uav_platform is invalid")
                if classification.get("ew_installation") not in {"vehicle-mounted", "unknown"}:
                    _error(errors, f"{where}.classification.ew_installation is invalid")
        elif kind == "government_customer":
            if not node_id.startswith("customer::"):
                _error(errors, f"{where} government_customer node id must start with 'customer::'")
        elif kind in PROGRAM_KINDS:
            if not node_id.startswith(f"{kind}::"):
                _error(errors, f"{where} {kind} node id must start with '{kind}::'")
            if node.get("subtype") not in PROGRAM_SUBTYPES[kind]:
                _error(errors, f"{where}.subtype {node.get('subtype')!r} is not valid for kind {kind}")
        elif kind == "storefront":
            if not node_id.startswith("storefront::"):
                _error(errors, f"{where} storefront node id must start with 'storefront::'")
            if not node.get("platform"):
                _error(errors, f"{where}.platform is required on a storefront")
        elif kind == "military_unit":
            if not node_id.startswith("unit::"):
                _error(errors, f"{where} military_unit node id must start with 'unit::'")
            if node.get("unit_type") not in UNIT_TYPES:
                _error(errors, f"{where}.unit_type has invalid value {node.get('unit_type')!r}")
            if node.get("designation_confidence") not in UNIT_DESIGNATION_CONFIDENCE:
                _error(errors, f"{where}.designation_confidence has invalid value "
                               f"{node.get('designation_confidence')!r}")
            pg = node.get("parent_grouping")
            if pg is not None and not isinstance(pg, str):
                _error(errors, f"{where}.parent_grouping must be a string or null")
        else:
            if not node_id.startswith("stub::"):
                _error(errors, f"{where} unresolved node id must start with 'stub::'")

    for tombstone in sorted(tombstone_entities | tombstone_people):
        if tombstone in node_by_id:
            _error(errors, f"tombstoned registry node {tombstone!r} is included")
    for missing in sorted((live_entities | (live_people - reference_people)) - set(node_by_id) - detached):
        _error(errors, f"live registry node {missing!r} is missing")

    observed_degree = Counter()
    for i, edge in enumerate(edges):
        where = f"edges[{i}]"
        if not isinstance(edge, dict):
            _error(errors, f"{where} must be an object")
            continue
        if set(edge) != EDGE_FIELDS:
            _error(errors, f"{where} has invalid field set")
        if edge.get("grade") not in EDGE_GRADES:
            _error(errors, f"{where}.grade must be one of {sorted(EDGE_GRADES)}, got {edge.get('grade')!r}")
        src, dst = edge.get("source"), edge.get("target")
        if src not in node_by_id or dst not in node_by_id:
            _error(errors, f"{where} endpoint must reference a graph node")
            continue
        observed_degree[src] += 1
        observed_degree[dst] += 1
        etype = edge.get("type")
        if etype not in EDGE_TYPES:
            _error(errors, f"{where}.type has invalid value {etype!r}")
        else:
            src_kind = node_by_id[src]["kind"]
            dst_kind = node_by_id[dst]["kind"]
            permitted = {
                "owns": ({"entity"}, {"entity"}),
                "related": ({"entity"}, {"entity"}),
                "founded": ({"entity", "person", "unresolved"}, {"entity"}),
                "directs": ({"entity", "person", "unresolved"}, {"entity"}),
                # government_customer added 2026-09-16: a person's role can
                # be a contract-signatory position at a government customer
                # body (acceptance-committee member, financially-responsible
                # officer, agency head) rather than a corporate role at a
                # registry entity -- these were previously unresolvable
                # (role.entity_slug has no equivalent field for a customer
                # id) and fell through as false degree-0 stub-free gaps.
                "role": ({"person"}, {"entity", "government_customer"}),
                "produces": ({"entity"}, {"product"}),
                "procures": ({"government_customer"}, {"entity"}),
                "confirmed_field_use": ({"entity", "product"}, {"military_unit"}),
                "cbst_tie": ({"entity"}, {"entity"}),
                # family_tie added 2026-09-16: a relative of a network
                # principal, sourced from a leaked dossier's own family-tree
                # notes rather than a corporate role -- the "maybe bucket:
                # relatives" case from the degree-0 audit. person->person
                # only; direction is relative -> principal.
                "family_tie": ({"person"}, {"person"}),
                "sells_for": ({"entity"}, {"entity"}),
                "operates": ({"entity"}, {"program"}),
                "organises": ({"entity"}, {"event"}),
                "resident_of": ({"entity"}, {"program"}),
                "participated_in": ({"entity"}, {"event"}),
                "part_of": ({"program", "event"}, {"program", "event"}),
                "member_of": ({"entity"}, {"group"}),
                "banks_with": ({"entity"}, {"entity"}),
                "acquiring_via": ({"entity"}, {"entity"}),
                "ships_via": ({"entity"}, {"entity"}),
                "lists": ({"storefront"}, {"product"}),
                "operated_by": ({"storefront"}, {"entity"}),
            }[etype]
            if src_kind not in permitted[0] or dst_kind not in permitted[1]:
                _error(errors, f"{where} has invalid {src_kind}->{dst_kind} endpoints for {etype}")
        sid = edge.get("source_id")
        if sid is not None and sid not in source_ids:
            _error(errors, f"{where}.source_id references unknown source {sid!r}")
        if edge.get("as_of") is not None and not _is_date(edge["as_of"]):
            _error(errors, f"{where}.as_of must be YYYY-MM-DD or null")
        if not isinstance(edge.get("weight"), (int, float)) or isinstance(edge.get("weight"), bool):
            _error(errors, f"{where}.weight must be numeric")
        confidence = edge.get("confidence")
        if etype == "cbst_tie":
            if confidence not in CBST_TIE_CONFIDENCE:
                _error(errors, f"{where}.confidence has invalid value {confidence!r} for cbst_tie")
        elif etype == "family_tie":
            if confidence not in FAMILY_TIE_CONFIDENCE:
                _error(errors, f"{where}.confidence has invalid value {confidence!r} for family_tie")
        elif etype in BASIS_EDGE_TYPES:
            if confidence not in SELLS_FOR_BASIS:
                _error(errors, f"{where}.confidence has invalid value {confidence!r} for {etype}")
        elif confidence is not None:
            _error(errors, f"{where}.confidence must be null for edge type {etype!r}")
        detail = edge.get("detail")
        if detail is not None:
            if etype != "sells_for" or not isinstance(detail, dict) or not detail or set(detail) - DETAIL_KEYS:
                _error(errors, f"{where}.detail must be null, or a non-empty object of {sorted(DETAIL_KEYS)} on a sells_for edge")
            else:
                if "products" in detail and not (isinstance(detail["products"], list) and all(isinstance(x, str) for x in detail["products"])):
                    _error(errors, f"{where}.detail.products must be a list of strings")
                for key, vocab in (("status", set(SALE_STATUSES)), ("role", RELATION_ROLES), ("asserted_by", ASSERTED_BY),
                                   ("credibility", CREDIBILITY), ("authorised", AUTHORISED)):
                    if key in detail and detail[key] not in vocab:
                        _error(errors, f"{where}.detail.{key} has invalid value {detail[key]!r}")
                if detail.get("credibility") and confidence in BASIS_CREDIBILITY \
                        and detail["credibility"] not in BASIS_CREDIBILITY[confidence]:
                    _error(errors, f"{where}.detail.credibility {detail['credibility']!r} contradicts basis {confidence!r}")
        status = edge.get("temporal_status")
        if status not in TEMPORAL_STATUSES:
            _error(errors, f"{where}.temporal_status has invalid value {status!r}")
        elif status in {"current", "historical"}:
            if sid is None or not _is_date(edge.get("as_of")):
                _error(errors, f"{where} {status} status requires a cited YYYY-MM-DD as_of")

    produced = Counter(e.get("source") for e in edges if isinstance(e, dict) and e.get("type") == "produces")
    for node_id, node in node_by_id.items():
        if node.get("kind") == "entity" and node.get("product_count") != produced.get(node_id, 0):
            _error(errors, f"node {node_id!r} product_count does not match its produces edges")
        if node.get("degree") != observed_degree[node_id]:
            _error(errors, f"node {node_id!r} degree does not match its incident edges")

    unresolved_by_id: dict[str, dict] = {}
    for i, item in enumerate(unresolved):
        where = f"unresolved[{i}]"
        if not isinstance(item, dict) or set(item) != {"id", "raw_name", "contexts"}:
            _error(errors, f"{where} must contain exactly id, raw_name, contexts")
            continue
        node_id = item.get("id")
        if node_id in unresolved_by_id:
            _error(errors, f"duplicate unresolved stub {node_id!r}")
            continue
        unresolved_by_id[node_id] = item
        node = node_by_id.get(node_id)
        if not node or node.get("kind") != "unresolved":
            _error(errors, f"{where}.id does not identify an unresolved node")
            continue
        if item.get("raw_name") != node.get("label"):
            _error(errors, f"{where}.raw_name must match its node label")
        if not isinstance(item.get("contexts"), list) or not all(isinstance(x, str) for x in item["contexts"]):
            _error(errors, f"{where}.contexts must be a list of strings")
        if observed_degree[node_id] == 0:
            _error(errors, f"{where}.id has no incident edge")
    stub_ids = {node_id for node_id, node in node_by_id.items() if node.get("kind") == "unresolved"}
    if stub_ids != set(unresolved_by_id):
        _error(errors, "unresolved[] does not have one entry for every unresolved node")

    return errors


VIEW_NAMES = ("cited_only", "current_only", "core_network", "evidence_gaps")


def _projection_ready(graph: dict) -> bool:
    """Return whether projection code can safely read required graph members."""
    if not isinstance(graph, dict):
        return False
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return False
    return (
        all(isinstance(node, dict) and isinstance(node.get("id"), str)
            and isinstance(node.get("kind"), str) for node in nodes)
        and all(isinstance(edge, dict) and isinstance(edge.get("source"), str)
                and isinstance(edge.get("target"), str)
                and "source_id" in edge and "temporal_status" in edge
                for edge in edges)
    )


def build_view_projections(graph: dict) -> dict[str, dict]:
    """Derive every view directly from the canonical graph, deterministically."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = graph["edges"]

    def subgraph(selected: list[dict]) -> dict:
        ids = {edge["source"] for edge in selected} | {edge["target"] for edge in selected}
        return {
            "nodes": [nodes[node_id] for node_id in sorted(ids)],
            "edges": selected,
        }

    core_ids = {
        node["id"] for node in graph["nodes"]
        if node["kind"] == "entity" and node.get("tier") == "cbst-core"
    }
    return {
        "cited_only": subgraph([edge for edge in edges if edge["source_id"] is not None]),
        "current_only": subgraph([edge for edge in edges if edge["temporal_status"] == "current"]),
        "core_network": subgraph([
            edge for edge in edges
            if edge["source"] in core_ids or edge["target"] in core_ids
        ]),
        "evidence_gaps": subgraph([edge for edge in edges if edge["source_id"] is None]),
    }


def validate_views(graph: dict, views: dict) -> list[str]:
    """Require serialized views to exactly equal their canonical projections."""
    errors: list[str] = []
    if not isinstance(views, dict) or views.get("schema_version") != GRAPH_SCHEMA_VERSION:
        return ["graph views: schema_version must match the graph schema"]
    if set(views) != {"schema_version", "generated_from", "views"}:
        return ["graph views: top-level fields must be schema_version, generated_from, views"]
    if views.get("generated_from") != "relationship_graph.json":
        return ["graph views: generated_from must be relationship_graph.json"]
    if not _projection_ready(graph):
        return ["graph views: cannot derive expected projections because the "
                "canonical graph has malformed node or edge members"]
    view_map = views.get("views")
    if not isinstance(view_map, dict) or set(view_map) != set(VIEW_NAMES):
        return ["graph views: expected cited_only, current_only, core_network, evidence_gaps"]
    expected_views = build_view_projections(graph)

    for name in VIEW_NAMES:
        view = view_map[name]
        if not isinstance(view, dict) or not isinstance(view.get("nodes"), list) or not isinstance(view.get("edges"), list):
            errors.append(f"graph views: {name} must contain nodes and edges lists")
            continue
        expected = expected_views[name]
        if view["edges"] != expected["edges"]:
            actual_keys = Counter(json_key(edge) for edge in view["edges"] if isinstance(edge, dict))
            expected_keys = Counter(json_key(edge) for edge in expected["edges"])
            missing = sum((expected_keys - actual_keys).values())
            extra = sum((actual_keys - expected_keys).values())
            errors.append(
                f"graph views: {name} edge projection differs from its canonical "
                f"predicate ({missing} missing, {extra} extra or substituted; "
                "run scripts/build_relationship_graph.py)")
        if view["nodes"] != expected["nodes"]:
            actual_ids = Counter(
                node.get("id") for node in view["nodes"]
                if isinstance(node, dict) and node.get("id")
            )
            expected_ids = Counter(node["id"] for node in expected["nodes"])
            missing = sum((expected_ids - actual_ids).values())
            extra = sum((actual_ids - expected_ids).values())
            errors.append(
                f"graph views: {name} node projection differs from endpoints of "
                f"its canonical edges ({missing} missing, {extra} extra, or "
                "non-canonical node content/order; run scripts/build_relationship_graph.py)")
    return errors


def json_key(value: dict) -> str:
    """Canonical comparison key without importing a second graph dependency."""
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
