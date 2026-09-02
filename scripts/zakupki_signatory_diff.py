#!/usr/bin/env python3
"""Diff docx_signatories/docx_emails_found (already mined by mine_zakupki.py
into _zakupki_mined.json, from fetch-documents' signed contract/amendment
text) against the registry — same "is this already documented?" pattern
mine_leads.py uses for Telegram-mined entity names, applied to the stakeholder
names/emails this project's own zakupki tooling already extracts but has no
automatic path into people.json.

Without this, a signatory only surfaces if someone manually greps
_zakupki_mined.json after a fetch-documents pull (as happened once, by hand,
2026-08-29) — this makes that check a rerunnable one-liner instead.

Local file processing only — no network calls — safe to run directly and
repeatedly. Run after any fetch-documents pull + mine_zakupki.py re-mine.

Usage:
    python3 scripts/zakupki_signatory_diff.py                # report to stdout
    python3 scripts/zakupki_signatory_diff.py --out report.md
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from id_patterns import norm, load_known_text  # noqa: E402


RE_TABLE_INN = re.compile(r'\bИНН[:\s]*([0-9]{10}|[0-9]{12})\b')

# Russian legal boilerplate ("действующего на основании доверенности, выданной
# ФИО") states the signatory's full name in genitive case, and the source
# text's own token order varies by customer template — some write
# Surname-First-Patronymic (all genitive), others First-Patronymic-Surname.
# Without normalizing this, "Иванова Михаила Алексеевича" and a hypothetical
# later "Иванов Михаил Алексеевич" (nominative, from some other document)
# would never dedup or match against people.json's nominative fio_ru values.

# Common irregular genitive->nominative first names (fleeting vowels, stem
# changes, soft-sign endings the general suffix rules below can't derive).
_IRREGULAR_GIVEN = {
    "петра": "пётр", "павла": "павел", "льва": "лев", "марка": "марк",
    "игоря": "игорь",
}

_PATRONYMIC_RE = re.compile(r'^(.+)(ови|еви)ча$', re.IGNORECASE)
# Adjectival-surname genitive (Иванова/Максимова/Нефедов-style) — checked
# BEFORE the generic given-name rules below, since "Иванова"/"Максимова"
# would otherwise also match _GIVEN_HARD_RE (both end in consonant+"а") and
# get misclassified as a first name, corrupting the surname/given reorder.
_SURNAME_ADJ_RE = re.compile(r'^(.+?)(ов|ев|ин|ын)а$', re.IGNORECASE)
_GIVEN_SOFT_RE = re.compile(r'^(.+)я$')  # Дмитрия->Дмитрий, Юрия->Юрий, Николая->Николай
_GIVEN_HARD_RE = re.compile(r'^(.+[^аеёиоуыэюя])а$')  # Антона->Антон, Дениса->Денис

# A consonant-ending surname (Квак, Бауэр, ...) declines identically to a
# consonant-ending first name (Денис, Антон, ...) — "Квака"/"Бауэра" and
# "Дениса"/"Антона" are the same suffix shape, so suffix rules alone can't
# tell them apart. Only demote a _GIVEN_HARD_RE match to 'given' if the
# reconstructed nominative is a real, common Russian first name; otherwise
# treat it as a surname (the safer default — there are far more possible
# surnames than first names, so an unrecognized consonant-ending name is
# much more likely to be one).
_COMMON_GIVEN_NAMES = {
    "александр", "алексей", "андрей", "антон", "аркадий", "артём", "артем",
    "артур", "афанасий", "богдан", "борис", "вадим", "валентин", "валерий",
    "василий", "вениамин", "виктор", "виталий", "владимир", "владислав",
    "владлен", "всеволод", "вячеслав", "гавриил", "геннадий", "георгий",
    "герман", "григорий", "давид", "даниил", "денис", "дмитрий", "евгений",
    "егор", "ефим", "захар", "иван", "игнат", "игорь", "иннокентий",
    "ипполит", "кирилл", "константин", "кузьма", "лев", "леонид", "макар",
    "максим", "марк", "матвей", "мирон", "михаил", "назар", "наум",
    "никита", "николай", "олег", "осип", "павел", "пётр", "петр", "прохор",
    "родион", "роман", "ростислав", "рустам", "савва", "семён", "семен",
    "сергей", "спартак", "станислав", "степан", "тарас", "тимофей",
    "тимур", "фёдор", "федор", "феликс", "филипп", "эдуард", "эрик",
    "юрий", "яков", "ярослав",
}


def _degenitive_token(tok: str) -> tuple[str, str]:
    """Returns (nominative_guess, kind) where kind in {'patronymic',
    'given', 'surname', 'unknown'}. Best-effort — a triage tool, not a
    morphological analyzer; unrecognized shapes pass through unchanged."""
    low = tok.lower()
    if low in _IRREGULAR_GIVEN:
        nom = _IRREGULAR_GIVEN[low]
        return (nom[0].upper() + nom[1:], "given")
    m = _PATRONYMIC_RE.match(tok)
    if m:
        return (tok[:-1], "patronymic")  # drop trailing "а"
    m = _SURNAME_ADJ_RE.match(tok)
    if m:
        return (tok[:-1], "surname")  # Иванова->Иванов, Нефедова->Нефедов
    m = _GIVEN_SOFT_RE.match(tok)
    if m:
        return (tok[:-1] + "й", "given")  # Дмитрия->Дмитрий, Юрия->Юрий
    m = _GIVEN_HARD_RE.match(tok)
    if m:
        nom = tok[:-1]
        if nom.lower() in _COMMON_GIVEN_NAMES:
            return (nom, "given")  # Антона->Антон, Дениса->Денис
        return (nom, "surname")  # Квака->Квак, Бауэра->Бауэр (not a known given name)
    return (tok, "unknown")


def normalize_fio_genitive(raw: str) -> str:
    """Best-effort genitive->nominative + reorder to canonical "Surname
    Given Patronymic" (matching this registry's fio_ru convention). Falls
    back to the original string (whitespace-cleaned) if fewer than 2 of the
    3 tokens are confidently classified, rather than guessing at reorder."""
    tokens = raw.replace("\xa0", " ").split()
    if len(tokens) != 3:
        return " ".join(tokens)
    parsed = [(_degenitive_token(t)) for t in tokens]
    kinds = [k for _, k in parsed]
    if kinds.count("patronymic") != 1:
        return " ".join(tokens)  # can't reliably identify structure
    pat_idx = kinds.index("patronymic")
    remaining = [i for i in range(3) if i != pat_idx]
    given_idx = next((i for i in remaining if kinds[i] == "given"), None)
    if given_idx is None:
        return " ".join(t for t, _ in parsed)  # normalized but not reordered
    surname_idx = next(i for i in remaining if i != given_idx)
    surname, given, patronymic = parsed[surname_idx][0], parsed[given_idx][0], parsed[pat_idx][0]
    return f"{surname} {given} {patronymic}"


def resolve_supplier_inn(c: dict) -> str | None:
    """supplier_inn is often None (only set when derived from an ATTACH
    filename) even though the contract card's own supplier table states it
    plainly — read that instead of trusting the pre-computed field, which
    caused every such contract to match the first entity/person with a null
    ИНН (a `None == None` false match) rather than being reported unresolved."""
    if c.get("supplier_inn"):
        return c["supplier_inn"]
    for row in c.get("card_suppliers_table", []) or []:
        text = row.get("Организация", "")
        m = RE_TABLE_INN.search(text)
        if m:
            return m.group(1)
    return None


def entity_context(supplier_inn: str | None, entities: list, people: list) -> str:
    if not supplier_inn:
        return "unresolved (no ИНН found in card)"
    for e in entities:
        if e.get("inn") == supplier_inn:
            return f"entity:{e.get('slug')}"
    for p in people:
        if p.get("inn_personal") == supplier_inn:
            return f"person:{p.get('slug')}"
    return f"unresolved ИНН {supplier_inn}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()

    mined_path = REPO / "data" / "registry" / "_zakupki_mined.json"
    if not mined_path.exists():
        print("no _zakupki_mined.json — run mine_zakupki.py first", file=sys.stderr)
        return 1
    mined = json.loads(mined_path.read_text(encoding="utf-8"))["contracts"]

    entities = json.loads((REPO / "data" / "registry" / "entities.json").read_text(encoding="utf-8"))
    people = json.loads((REPO / "data" / "registry" / "people.json").read_text(encoding="utf-8"))
    known = load_known_text()

    lines = ["# zakupki signatory/email diff — new names not yet in the registry",
             "",
             "Triage list, not a source — every name here still needs the same",
             "primary-source verification (who are they, what's their actual role)",
             "before it goes into people.json. A name/context match here means",
             "\"appears as a signatory on an archived contract\", not \"confirmed as",
             "a network principal\" — most доверенность-holders are mid-level reps,",
             "not officers, per the PII policy's not-a-principal carve-out.",
             ""]

    new_names = []
    new_emails = []
    seen_names = set()
    seen_emails = set()

    for reg, c in sorted(mined.items()):
        ctx = entity_context(resolve_supplier_inn(c), entities, people)
        for sig in c.get("docx_signatories", []) or []:
            raw_name = (sig.get("name") or "").replace("\xa0", " ").strip()
            if not raw_name:
                continue
            name = normalize_fio_genitive(raw_name)
            if norm(name) in seen_names:
                continue
            seen_names.add(norm(name))
            if norm(name) not in known:
                shown = name if name == raw_name else f"{name} (raw: {raw_name})"
                # party is "customer"/"supplier"/"unknown" (missing on any
                # docx_signatories entry mined before the 2026-08-31 fix —
                # treated the same as "unknown", not re-mined implicitly).
                new_names.append((reg, ctx, shown, sig.get("authority_basis"), sig.get("party", "unknown")))

        for email in c.get("docx_emails_found", []) or []:
            if email in seen_emails:
                continue
            seen_emails.add(email)
            if email.lower() not in known:
                new_emails.append((reg, ctx, email))

    supplier_names = [n for n in new_names if n[4] == "supplier"]
    other_names = [n for n in new_names if n[4] != "supplier"]

    lines.append(f"## New signatory names — supplier side ({len(supplier_names)})")
    lines.append("")
    lines.append("These sign for the ИНН's own entity/person — the only rows here that")
    lines.append("are candidate director_history/officer evidence.")
    lines.append("")
    for reg, ctx, name, basis, _party in supplier_names:
        lines.append(f"- **{name}** — [{reg}] ({ctx}) — authority: {basis or '?'}")
    if not supplier_names:
        lines.append("(none)")

    lines.append("")
    lines.append(f"## New signatory names — customer side or unresolved ({len(other_names)})")
    lines.append("")
    lines.append("These sign for the CONTRACT'S CUSTOMER (a ministry, institute, municipal")
    lines.append("body, ...), or the side could not be determined — do NOT read either as")
    lines.append("an officer of the ИНН's own entity/person. Confirmed 2026-08-31: an")
    lines.append("earlier undifferentiated version of this report listed a customer-side")
    lines.append("\"руководитель Учреждения\" (Войсковая часть 35533) as if he were a")
    lines.append("candidate director of the supplier entity.")
    lines.append("")
    for reg, ctx, name, basis, party in other_names:
        lines.append(f"- **{name}** — [{reg}] ({ctx}, party={party}) — authority: {basis or '?'}")
    if not other_names:
        lines.append("(none)")

    lines.append("")
    lines.append(f"## New emails ({len(new_emails)})")
    lines.append("")
    for reg, ctx, email in new_emails:
        lines.append(f"- **{email}** — [{reg}] ({ctx})")
    if not new_emails:
        lines.append("(none — every email found is already in the registry)")

    report = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out} ({len(new_names)} new names, {len(new_emails)} new emails)")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
