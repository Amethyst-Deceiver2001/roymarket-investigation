#!/usr/bin/env python3
"""
Assigns each entities.json products[] entry one of the 17 Product Icon Set
categories (see the "Product Icon Set" artifact, fa4295ea-cef5-4fa0-ab0b-
27cd92407a93), plus an explicit 18th "unclassified" fallback.

Categories `electronics_compute` and `nav_gnss` (added 2026-09-14, same
session as the mount-type/unclassified pass) exist because a real slice of
this registry isn't complete-UAV manufacturers at all but B2B component
suppliers feeding OTHER manufacturers' airframes -- npts-elvis's ~30
chips/SoCs/processor modules and ooo-4gnss/ooo-orient-sistems's ~15 GNSS
receiver boards were previously indistinguishable from "unclassified"
alongside genuinely unrelated-industry noise (ao-pk-azimut's ATC/biometric
gear). `motor_propeller_part` was broadened to explicitly cover rotor
blades and starter-generators rather than spin up a 19th icon for a term
(лопасть/blade) with zero literal hits in the corpus as of this writing --
see the classifier's own patterns list, not a hardcoded guess.

This is presentation-layer classification only -- same discipline as the
Hub Icon Schema's offensive/defensive/dual read: not a new sourced
registry field, just a deterministic, checked-in, reviewable rule set so
category assignment doesn't have to be silently re-derived by hand each
time (see the icon set's own footnote on why 15 categories, not fewer/more).

Two-tier rule, in priority order:

1. STRUCTURED FIRST: if a product entry carries a `type_bvs` field (wired
   2026-09-14 from rk.2035.university's product-model sub-catalog, s1169
   -- see corrections_entities.json's why[] on the 6 entities that have
   it), map it directly. Only 4 distinct type_bvs values exist across the
   274-model source corpus, all airframe types -- this covers exactly the
   4 airframe categories (FPV/kamikaze strike is NOT one of them; strike
   intent isn't a rk.2035.university field, so a multirotor/fixed-wing
   airframe with type_bvs still needs the keyword pass below to tell a
   kamikaze quad from a cargo quad).
2. KEYWORD FALLBACK: free-text match against `name_ru` + `description`
   for every product without a usable type_bvs (the large majority --
   only 6 entities have it as of this writing). This is where the EW
   jammer sub-type ambiguity documented 2026-09-14 lived: the icon set's
   "27 hits (all jammer types)" line admitted three jammer icons existed
   with no stated way to split them. Fixed here with an explicit
   mount-type sub-rule and an explicit, stated default (never a silent
   fallthrough).

Run `python3 scripts/classify_product_icon.py` for a full-corpus report,
or `--slug <entity-slug>` to see one entity's products only. Local text
processing over already-registered data, no network calls -- safe to run
directly/repeatedly like scan_sources.py.
"""
import argparse
import json
import re
from collections import Counter

ENTITIES_PATH = "data/registry/entities.json"

# --- Tier 1: structured type_bvs -> category -----------------------------
TYPE_BVS_MAP = {
    "БВС мультироторного типа": "multirotor_cargo_utility",
    "БВС самолетного типа": "fixed_wing_vtol",
    "БВС вертолетного типа": "helicopter_uas",
    "БВС вертикального взлета и посадки": "fixed_wing_vtol",
}

# --- Tier 2: keyword fallback ---------------------------------------------
# Order matters: first matching category wins. Each entry is
# (category_id, [regex patterns tried against name_ru + description]).
# Patterns are deliberately narrow Russian domain terms, not single
# letters, to avoid the over-eager collapse that bit the rk.2035.university
# name-matching pass earlier this session.
KEYWORD_RULES = [
    ("fpv_kamikaze_strike", [
        r"\bfpv\b", r"\bфпв\b", r"камикадзе", r"\bkamikaze\b",
        r"ударн\w* дрон", r"ударн\w* fpv",
        r"боеприпас", r"боевая нагрузка", r"поражени\w* цел",
    ]),
    ("munition_warhead", [
        r"боевая часть", r"взрывател", r"кумулятивн", r"осколочн",
    ]),
    ("ew_jammer_vehicle", []),   # resolved by _classify_jammer_mount()
    ("ew_jammer_stationary", []),
    ("ew_jammer_portable", []),
    ("detector_counter_uas", [
        r"детектор", r"пеленгатор", r"обнаружени\w* (?:бпла|дрон)",
        r"противодрон\w* ружь", r"антидрон\w* ружь",
        r"\bdetector\b", r"counter-uas", r"counter-drone", r"counter-uav",
        r"перехватчик", r"\binterceptor\b", r"поражени\w* (?:бпла|дрон)",
    ]),
    ("_detector_false_positive_guard", [
        # "детектор"/"пеленгатор"/"detector" alone also matches landmine/
        # walkthrough metal detectors (ooo-opkb-eksplomet's АЛЬФАМАРИН/ARENA
        # security-screening line) and manned-aviation radio direction
        # finders (ao-pk-azimut's DF 2000) -- neither is UAV-related. This
        # pseudo-category is never assigned; classify() checks it first and
        # skips the real detector_counter_uas match when it fires.
        r"миноискател", r"металлодетектор", r"mine detector",
        r"радиопеленгатор", r"арочн\w* детектор",
    ]),
    ("antenna_mast", [
        r"\bантенн", r"мачт[ауы]?\b", r"\bantenna\b", r"\bmast\b",
    ]),
    ("battery_power", [
        r"аккумулятор", r"\bбатаре", r"\bbms\b", r"систем\w* питани",
        r"электроснабжени", r"энергоснабжени",
        r"\bbattery\b", r"power supply",
    ]),
    ("motor_propeller_part", [
        # negative lookbehind on bare motor/propeller excludes "4-motor UAS"/
        # "N-propeller" engine-count phrasing that describes a WHOLE airframe,
        # not the part itself (found misrouting «Пиранья-13», a complete
        # quadcopter, here via its own "4-motor UAS" spec line)
        r"\bдвигател", r"пропеллер", r"\bвинт[аоы]?\b(?!.*вертолет)",
        r"лопаст", r"(?<!-)\bblade\b", r"стартер.генератор",
        r"(?<!-)\bmotor\b", r"(?<!-)\bpropeller\b",
    ]),
    ("electronics_compute", [
        r"микросхем", r"\bsoc\b", r"процессорн\w* модул", r"отладочн\w* модул",
        r"препроцессор", r"интегральн\w* схем", r"\bchip\b",
    ]),
    ("nav_gnss", [
        r"гнсс", r"\bgnss\b",
    ]),
    ("video_control_link", [
        r"видео.?приемник", r"видео.?передатчик", r"канал управлени",
        r"видеосвяз", r"систем\w* связи", r"video receiver", r"video link",
        r"control link", r"communication system",
    ]),
    ("ground_control_station", [
        r"\bнсу\b", r"наземн\w* станци\w* управлени", r"\bgcs\b",
        r"ground control station", r"дронопорт", r"док-станци", r"dock station",
    ]),
    ("repeater_relay", [
        r"ретранслятор", r"репитер", r"\brepeater\b", r"\brelay\b",
    ]),
    ("multirotor_cargo_utility", [
        r"мультиротор", r"квадрокоптер", r"грузов\w* дрон", r"доставк\w* груз",
        r"multi-?rotor", r"cargo (?:uav|drone|uas)",
    ]),
    ("fixed_wing_vtol", [
        r"самолетн\w* тип", r"самол[её]тн\w*\b", r"\bсамол[её]т\b",
        r"fixed.?wing", r"\bvtol\b", r"aircraft.?type",
    ]),
    ("helicopter_uas", [
        r"вертолетн\w* тип", r"несущ\w* винт", r"\bвертол[её]т\b",
        r"\bhelicopter\b", r"single-rotor",
    ]),
]

# Generic БПЛА/БВС mention with no more specific airframe/role signal --
# stated explicit default, same discipline as _classify_jammer_mount(): a
# bare "unmanned aircraft" descriptor with nothing else to go on defaults to
# multirotor_cargo_utility, the modal airframe type across this corpus's
# structured type_bvs data (see TYPE_BVS_MAP) -- never a silent fallthrough
# to "unclassified" for a product a source has explicitly called a drone.
GENERIC_UAV_TERM = re.compile(
    r"\bбпла\b|\bбвс\b|\bбас\b|\bдрон\b|\bunmanned\b|\bdrone\b", re.IGNORECASE
)

JAMMER_TRIGGER = re.compile(
    r"\bрэб\b|радиоэлектронн\w* борьб|подавлени\w* (?:сигнал|навигац)"
    r"|подавит\w* (?:бпла|дрон|радиоканал)|станци\w* подавлени\w* (?:бпла|дрон)"
    r"|обнаружител\w*.подавител\w*|глушител|джаммер"
    r"|\bew\b|jammer\b|jamming\b|signal generator|neutraliz\w* (?:uav|drone)",
    re.IGNORECASE,
)
# The product ITSELF is a jammer, vs. merely resistant to being jammed by
# someone else's EW -- "EW-resistant... maintain link when jammed" (real
# text on «Пиранья-10», a strike drone, not an EW system) matched the old
# bare "jamm" substring and misclassified a whole airframe as its own
# countermeasure. Checked before JAMMER_TRIGGER fires.
JAMMER_RESISTANCE_PHRASING = re.compile(
    r"resist\w*\W{0,20}jam|jam\w*\W{0,20}resist|anti-jam|jam-resistant"
    r"|помехоустойчив|устойчив\w* к (?:рэб|подавлени|глушени)"
    r"|maintain\w* link when jammed",
    re.IGNORECASE,
)
JAMMER_MOUNT_PORTABLE = re.compile(
    r"переносн|ранцев|портатив|носим\w*|\bportable\b|man-pack|handheld",
    re.IGNORECASE,
)
JAMMER_MOUNT_STATIONARY = re.compile(
    r"стационарн|купол\w*|фиксирован\w* установк|\bstationary\b|\bfixed\b(?! wing)|\bdome\b",
    re.IGNORECASE,
)
JAMMER_MOUNT_VEHICLE = re.compile(
    r"автомобил|транспортн\w* средств|бортов\w*|\bкунг\b|vehicle.?mounted|\bomnidirectional\b",
    re.IGNORECASE,
)

CATEGORY_LABELS = {
    "fpv_kamikaze_strike": "FPV / kamikaze strike",
    "multirotor_cargo_utility": "Multirotor / cargo utility",
    "fixed_wing_vtol": "Fixed-wing / VTOL",
    "helicopter_uas": "Helicopter-type UAS",
    "ew_jammer_vehicle": "EW jammer, vehicle-mounted",
    "ew_jammer_stationary": "EW jammer, stationary/dome",
    "ew_jammer_portable": "EW jammer, portable",
    "detector_counter_uas": "Detector / counter-UAS",
    "antenna_mast": "Antenna / mast",
    "battery_power": "Battery / power",
    "motor_propeller_part": "Motor / propeller / rotor blade",
    "electronics_compute": "Electronics / compute module",
    "nav_gnss": "Navigation / GNSS module",
    "video_control_link": "Video / control link",
    "ground_control_station": "Ground control station",
    "munition_warhead": "Munition / warhead attachment",
    "repeater_relay": "Repeater / relay",
    "unclassified": "Unclassified (no rule matched)",
}


def _classify_jammer_mount(text: str) -> str:
    """Explicit, stated default: vehicle-mounted is the modal case in the
    source corpus (27 of 27 jammer hits in the original icon-set read were
    undifferentiated and counted under vehicle-mounted) -- so an ambiguous
    jammer falls there, not to whichever icon happens to be checked first.
    """
    if JAMMER_MOUNT_PORTABLE.search(text):
        return "ew_jammer_portable"
    if JAMMER_MOUNT_STATIONARY.search(text):
        return "ew_jammer_stationary"
    if JAMMER_MOUNT_VEHICLE.search(text):
        return "ew_jammer_vehicle"
    return "ew_jammer_vehicle"  # explicit stated default, not a silent fallthrough


def classify(product: dict) -> tuple[str, str]:
    """Returns (category_id, tier) where tier is 'structured', 'keyword',
    or 'unclassified'."""
    type_bvs = product.get("type_bvs")
    if type_bvs and type_bvs in TYPE_BVS_MAP:
        base = TYPE_BVS_MAP[type_bvs]
        # a structured airframe type still can't distinguish strike intent;
        # only override to strike if the text itself says so
        text = f"{product.get('name_ru','')} {product.get('description','')}"
        if re.search(r"\bfpv\b|камикадзе|ударн\w* дрон", text, re.IGNORECASE):
            return "fpv_kamikaze_strike", "structured+keyword"
        return base, "structured"

    text = f"{product.get('name_ru','')} {product.get('description','')}"

    if JAMMER_TRIGGER.search(text) and not JAMMER_RESISTANCE_PHRASING.search(text):
        return _classify_jammer_mount(text), "keyword"

    detector_false_positive = any(
        re.search(pat, text, re.IGNORECASE)
        for _, pats in KEYWORD_RULES if _ == "_detector_false_positive_guard"
        for pat in pats
    )

    for cat_id, patterns in KEYWORD_RULES:
        if cat_id.startswith("ew_jammer") or cat_id == "_detector_false_positive_guard":
            continue
        if cat_id == "detector_counter_uas" and detector_false_positive:
            continue
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return cat_id, "keyword"

    if GENERIC_UAV_TERM.search(text):
        return "multirotor_cargo_utility", "keyword-generic-default"

    return "unclassified", "unclassified"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="only classify one entity's products")
    args = ap.parse_args()

    entities = json.load(open(ENTITIES_PATH, encoding="utf-8"))
    counter = Counter()
    tier_counter = Counter()
    unclassified_examples = []

    for e in entities:
        if not isinstance(e, dict):
            continue
        if args.slug and e.get("slug") != args.slug:
            continue
        for p in e.get("products") or []:
            if not isinstance(p, dict):
                continue
            cat, tier = classify(p)
            counter[cat] += 1
            tier_counter[tier] += 1
            if args.slug:
                print(f"  {p.get('name_ru','?'):35s} -> {CATEGORY_LABELS[cat]:35s} [{tier}]")
            elif cat == "unclassified" and len(unclassified_examples) < 15:
                unclassified_examples.append(f"{e.get('slug')}: {p.get('name_ru','?')}")

    if not args.slug:
        print("Category distribution across all products[]:\n")
        for cat_id, n in counter.most_common():
            print(f"  {n:4d}  {CATEGORY_LABELS[cat_id]}")
        print("\nBy classification tier:")
        for tier, n in tier_counter.most_common():
            print(f"  {n:4d}  {tier}")
        if unclassified_examples:
            print("\nSample unclassified entries (first 15):")
            for ex in unclassified_examples:
                print(f"  - {ex}")


if __name__ == "__main__":
    main()
