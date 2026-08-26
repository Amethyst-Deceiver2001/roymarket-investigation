#!/usr/bin/env python3
"""Deep structured mining over data/sources/ZAKUPKI_* — everything
`scripts/zakupki_batch_pull.py` has already downloaded (contract cards,
electronic-contract XML, payment-order XML, signed docx, delivery zips).

`scan_sources.py`'s generic ИНН/entity/ОГРН grep already runs over these
files, but it treats them as flat text and — worse — silently skips .docx
entirely (not in its extract_text() suffix list), which means every signed
contract's actual prose (technical specs, signatories, alternate contacts)
was never mined. This script is purpose-built for the zakupki document
*shapes* instead, studied directly (2026-08-26) rather than assumed:

  - `*_elektronnyy-kon-*.xml` / `*_kontrakt-s-uchet-*.xml` — root tag
    `cpElectronicContract` (schema xmlns http://zakupki.gov.ru/oos/CPtypes/1).
    The single richest source: customer AND supplier full legal/bank/contact
    detail (INCLUDING the supplier's director — name+personal ИНН+title,
    under participantInfo/legalEntityRFInfo/informationPersonsInfo — a field
    scan_sources.py's plain-text grep would only catch if a role title and
    name happened to sit within RE_ROLE_NAME's window), line-item product/
    service detail (OKPD2/KTRU codes, quantity, price, VAT), execution
    terms, delivery place, guarantee amounts, and the payment schedule.
  - `*_platezhnoe-poruch-*.xml` — root tag `FAM_PaymOrderCr` (Roskazna
    treasury schema). Payer and recipient bank details (INN/KPP/name/BIK/
    correspondent account/settlement account), the exact amount transferred,
    and — in `DepInfo_PayPurpose` — free text that routinely names the
    product/system being paid for and the invoice it corresponds to.
  - Contract-card HTML (`ZAKUPKI_contract_*.html`, or the descriptively-named
    `ZAKUPKI_<inn>_<date>_contract-*.html` pulled by hand) — a clean,
    generic `<section class="blockInfo__section section"><span
    class="section__title">KEY</span><span class="section__info">VALUE</span>
    </section>` key/value structure plus a distinct supplier table
    (org/country/address/postal/phone-email) — scraped generically (every
    key the page shows, not a hand-picked subset) so a future card layout
    addition is captured without a code change.
  - `.docx` contract/amendment/report text (a zip; `word/document.xml`'s
    `<w:t>` runs concatenated — no python-docx dependency needed) — the
    actual signed prose: signatory name+title+authority basis ("действующего
    на основании доверенности/устава"), item technical-spec paragraphs
    (verbatim marketing/capability claims — see
    roymarket_capture_self_incriminating_marketing_copy in memory), and
    sometimes a different email/phone than the card or contract XML carries
    (found live: kontrakt-ep-3 for Цыганов's ИП lists sales@pokrovsystem.ru,
    nowhere else in that contract's other documents).
  - `.pdf`/`.zip` attachments (обоснование justifications, акты, УПД,
    delivery-confirmation bundles) — reuses scan_sources.py's own
    pdf_text()/zip_text() (OCR fallback included) rather than reimplementing
    it, then runs the same id_patterns regex pass scan_sources.py uses,
    PLUS (added after studying more of the corpus, 2026-08-26) two more
    passes over every text-bearing kind, not just docx:
      - `scan_text_for_flags()` — the technical-spec/marketing-claim line
        scan originally lived only inside mine_docx(); a real hit (an OCR'd
        акт stating "работы не выполнялись" for a whole reporting period)
        never got a chance to fire because the check wasn't run on PDFs at
        all. Generalized into one shared helper, now applied to every kind
        (docx/pdf/zip/txt/xml-other), and split into two categories:
        `technical_spec_candidates` (unchanged) and the new
        `performance_flags` — an explicit admission of non-performance,
        which is a distinct evidentiary signal from a `penalties` entry
        (a customer's formal accusation) or a `payments` entry (money that
        did move) and worth its own report section.
      - `parse_neustoika()` — a `требование-об-у-*.zip`/`уточненное-треб-
        *.zip` attachment (a formal неустойка/penalty demand) sometimes
        contains a PIK (Госзакупки personal-cabinet)-generated PDF with a
        clean, machine-readable "Требование об уплате неустойки №X от Y"
        header and Label-then-Value fields (pdftotext -layout keeps them
        recoverable despite the column-wrapped layout) — doc number/date,
        the violated obligation, and (critically) a bare 19-digit regNumber
        embedded in the "Номер контракта" line that links the demand back
        to its contract without needing a filename clue. Confirmed against
        a real ₽5,000 fine for late stage-2 delivery on a Гаскар
        Технологии contract. The OTHER file this same zip-attachment
        family sometimes holds — a freeform scanned/letterhead "уточненная
        претензия" letter, not machine-generated — doesn't match this
        header shape and correctly falls back to plain id_scan.
  - `.rar` (Приказы, ФАС notices) — not parsed (no bundled unrar dependency);
    logged as present, not silently dropped.
  - "Печатная форма" HTML print-forms are a rendered duplicate of the sibling
    contract XML — not structurally parsed, just regex-scanned as a fallback
    like any other text, since the XML sibling already has the same data
    cleanly.

Every field a document exposes is kept, not just a curated subset: XML is
flattened generically (elem_to_obj — strips namespaces, converts to nested
dict/list, so an unanticipated schema field still comes through) into
`_zakupki_mined.json`, and known high-value paths (customer, supplier incl.
director, items, price, bank details, dates, legal basis) are additionally
pulled out for the human-facing report and for the new-entity/new-person
cross-check against the registry — same triage-not-source discipline as
mine_leads.py/scan_sources.py: a hit here is a lead, not a citable fact,
until hand-verified against the primary document and wired into
government_contracts[]/bank details via corrections.json.

Local file processing only — no network calls — safe to run directly and
repeatedly, same category as scan_sources.py/mine_leads.py.

Usage:
    python3 scripts/mine_zakupki.py                          # report to stdout
    python3 scripts/mine_zakupki.py --out report.md
    python3 scripts/mine_zakupki.py --json data/registry/_zakupki_mined.json
    python3 scripts/mine_zakupki.py --inn 504405055721       # one supplier only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zakupki_batch_pull as zk  # SCAN_LOG path only — see reg_numbers_for_inn()
from extract_ids import scan as _raw_id_scan
from id_patterns import load_known_text, norm, uav_score
from scan_sources import pdf_text, zip_text  # reuse the OCR/nested-zip work, don't reimplement it

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "data" / "sources"
DEFAULT_JSON_OUT = REPO / "data" / "registry" / "_zakupki_mined.json"
MINE_CACHE_PATH = REPO / "data" / "registry" / "_zakupki_mine_cache.json"

def id_scan(text: str) -> dict:
    """Wraps extract_ids.scan() with a whitespace collapse first — a raw
    docx/OCR/printform text extraction routinely has newlines embedded
    mid-name (a wrapped table cell, an OCR line break inside a guillemet-
    quoted company name) and RE_ENTITY_QUOTED/RE_QUOTED_NAME both span
    newlines by default, so an unnormalized call turns "«Гаскар ИКТ»" split
    across a line wrap into the garbled two-line match "«Гаскар\\nИКТ»" —
    found live in this corpus's own triage report. Collapsing whitespace
    runs (not just newlines, since OCR/docx also leave multi-space gaps)
    before scanning fixes it at the one choke point instead of patching
    every call site separately."""
    return _raw_id_scan(re.sub(r"\s+", " ", text))


# Self-incriminating / capability language worth flagging verbatim out of
# docx prose — same spirit as UAV_TERMS in id_patterns.py but tuned to the
# kind of spec-sheet phrasing a Спецификация/Приложение clause actually
# uses (dальность/частот/мощност/etc alongside a number+unit).
SPEC_MARKER_RE = re.compile(
    r'(дальност|частотн|мощност|подавлен|глушен|поражен|перехват|антидрон|'
    r'противодействия?\s+БПЛА|беспилотн)', re.IGNORECASE,
)
NUMBER_UNIT_RE = re.compile(r'\d+[.,]?\d*\s*(?:м|км|мгц|ггц|вт|кг|мин|час)', re.IGNORECASE)

# Explicit admissions of non-performance — found live in an OCR'd акт
# ("работы не выполнялись" for a whole reporting period) and matching the
# genre of the earlier-found «Требование об уплате неустойки» penalty
# notices. Originally only checked inside docx text; a real positive hit
# on this corpus's PDFs (акты, экспертиза results) never got a chance to
# fire because the flag check lived only in mine_docx — generalized into
# a shared helper so every document kind (pdf/zip/docx/txt) gets it.
NON_PERFORMANCE_RE = re.compile(
    r'(работы не выполнялись|услуги не оказывались|не были? выполнен\w*|'
    r'обязательств\w+ не исполнен\w*|ненадлежащ\w+ исполнен\w*|'
    r'нарушени\w+ услови\w+ (?:ГК|контракта|Контракта))', re.IGNORECASE,
)

# Every 44-ФЗ contract carries a standard "за неисполнение или ненадлежащее
# исполнение обязательств взимается неустойка" liability clause, laid out as
# a numbered sub-clause list (typically under section 7 or 9 — "7.1", "9.3.2",
# "2.5.4" ...). Those numbered clause headers matched NON_PERFORMANCE_RE at
# a high rate (e.g. 31 hits on one routine IT-services contract, 9 on
# another) despite being boilerplate that defines the penalty mechanism, not
# a factual report that non-performance actually happened — confirmed by
# hand-reading several (ЦБС Tula/Гаскар/Центр-Телко contracts, 2026-08-26).
# A real admission (see 2770135608620000033's "работы не выполнялись и не
# подлежат оплате") is a plain declarative sentence, never a numbered clause
# line — so a line starting with clause numbering is filtered out here
# rather than trying to make the phrase regex itself more specific.
CLAUSE_NUMBERING_RE = re.compile(r'^\d+(\.\d+){0,3}\.?\s')


def scan_text_for_flags(text: str) -> dict:
    """Line-level scan shared by every text-bearing document kind (pdf/zip/
    docx/txt/xml-other) for two categories worth surfacing verbatim: a
    technical/marketing capability claim (SPEC_MARKER_RE + a number+unit,
    same test mine_docx already used) and an explicit non-performance
    admission (NON_PERFORMANCE_RE). Kept as one shared function instead of
    duplicating the line-scan loop at each of the 6+ call sites."""
    specs, flags = [], []
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 15 or len(line) > 500:
            continue
        if SPEC_MARKER_RE.search(line) and NUMBER_UNIT_RE.search(line):
            specs.append(line)
        if NON_PERFORMANCE_RE.search(line) and not CLAUSE_NUMBERING_RE.match(line):
            flags.append(line)
    return {"technical_spec_candidates": sorted(set(specs)),
            "performance_flags": sorted(set(flags))}


FILENAME_REG_RE = re.compile(r'ZAKUPKI_(?:ATTACH_\d+|contract)_(\d{10,25})_')
FILENAME_REG_RE2 = re.compile(r'contract-(\d{10,25})-')
FILENAME_INN_RE = re.compile(r'ZAKUPKI_ATTACH_(\d{10,12})_')


def strip_ns(tag: str) -> str:
    return tag.split('}', 1)[-1] if '}' in tag else tag


def elem_to_obj(elem: ET.Element):
    """Generic namespace-stripping XML->dict/list flattener. Every field the
    document has survives, including ones this script doesn't specifically
    look for — the point of "every possible bit of data", not just the
    fields anticipated while studying the two sample schemas."""
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        return text if text else None
    result: dict = {}
    for child in children:
        tag = strip_ns(child.tag)
        value = elem_to_obj(child)
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result


def parse_xml_generic(path: Path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return None, f"[xml parse failed: {e}]"
    return {strip_ns(root.tag): elem_to_obj(root)}, strip_ns(root.tag)


def g(d, *path, default=None):
    """Chained .get() over a possibly-missing nested dict path."""
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def extract_contract_fields(data: dict) -> dict:
    """Pull the known high-value fields out of a flattened cpElectronicContract."""
    root = data.get("cpElectronicContract", {})
    cust = g(root, "customerInfo", default={}) or {}
    # Supplier is either a legal entity (legalEntityRFInfo, with its own
    # director under informationPersonsInfo) or an individual entrepreneur
    # (individualPersonRFInfo — no separate director, the ИП *is* the
    # signatory) — the two are structurally different subtrees, not just a
    # naming variant, so both need reading or every ИП supplier's own name/
    # address/contact silently comes back empty (found live: Цыганов Вадим
    # Борисович's own contract XML uses individualPersonRFInfo throughout).
    part = g(root, "participantInfo", "legalEntityRFInfo", default=None)
    ip = g(root, "participantInfo", "individualPersonRFInfo", default=None)
    is_ip = ip is not None
    if part is None:
        part = ip or {}
    director = g(part, "informationPersonsInfo", "informationPersonInfo", default={}) or {}
    if isinstance(director, list):
        director = director[0] if director else {}
    # lastName-first, matching the surname-first convention used everywhere
    # else in this registry (people.json, reports) — the schema itself
    # orders firstName/middleName/lastName, and building the display string
    # in that order produced "ИГОРЬ КОНСТАНТИНОВИЧ АФАНАСЬЕВ" for an already-
    # documented director, which a plain substring check against known_text
    # (word-order sensitive) then reported as a brand-new person 3 times
    # over in the triage report — a real false-positive source, not a
    # cosmetic one.
    director_name = " ".join(
        x for x in (g(director, "nameInfo", "lastName"), g(director, "nameInfo", "firstName"),
                    g(director, "nameInfo", "middleName")) if x
    ) or None
    if is_ip:
        ip_name = " ".join(x for x in (g(part, "nameInfo", "lastName"), g(part, "nameInfo", "firstName"),
                                        g(part, "nameInfo", "middleName")) if x) or None
    else:
        ip_name = None

    cust_acct = g(cust, "customerAccountsDetailsInfo", "customerAccountDetailsInfo", default={}) or {}
    if isinstance(cust_acct, list):
        cust_acct = cust_acct[0] if cust_acct else {}
    part_acct = g(root, "participantInfo", "participantAccountsDetailsInfo",
                  "electronicContractAccountsDetailsInfo", "electronicContractAccountDetailsInfo", default={}) or {}
    if isinstance(part_acct, list):
        part_acct = part_acct[0] if part_acct else {}

    items = g(root, "contractSubjectInfo", "productsInfo", "productsInfoElectronicContract",
              "productInfo", default=[])
    if isinstance(items, dict):
        items = [items]
    parsed_items = []
    for it in (items or []):
        parsed_items.append({
            "name": g(it, "name"),
            "okpd2_code": g(it, "OKPD2Info", "OKPDCode"),
            "okpd2_name": g(it, "OKPD2Info", "OKPDName"),
            "ktru_code": g(it, "KTRUInfo", "code"),
            "ktru_name": g(it, "KTRUInfo", "name"),
            "quantity": g(it, "quantity"),
            "unit": g(it, "OKEIInfo", "name"),
            "price": g(it, "price"),
            "sum": g(it, "sum"),
            "vat": g(it, "VATRateInfo", "VATName"),
        })

    return {
        "purchase_number": g(root, "foundationInfo", "purchaseNumber"),
        "placing_way": g(root, "foundationInfo", "placingWay", "name"),
        "subject": g(root, "contractSubjectInfo", "contractSubject"),
        "customer": {
            "full_name": g(cust, "fullName"), "short_name": g(cust, "shortName"),
            "inn": g(cust, "INN"), "kpp": g(cust, "KPP"),
            "post_address": g(cust, "postAddress"), "fact_address": g(cust, "factAddress"),
            "email": g(cust, "email"), "phone": g(cust, "contactPhone"),
            "contact_person": " ".join(x for x in (
                g(cust, "contactPersonInfo", "firstName"), g(cust, "contactPersonInfo", "middleName"),
                g(cust, "contactPersonInfo", "lastName")) if x) or None,
            "bank_account": g(cust_acct, "bankAccountNumber"), "bik": g(cust_acct, "bik"),
            "corr_account": g(cust_acct, "corrAccountNumber"), "bank_name": g(cust_acct, "creditOrgName"),
        },
        "supplier": {
            "is_individual_entrepreneur": is_ip,
            "full_name": ip_name or g(part, "fullName"), "short_name": g(part, "shortName"),
            "inn": g(part, "INN"), "kpp": g(part, "KPP"),
            "post_address": g(part, "postAddress"), "fact_address": g(part, "factAddress"),
            "email": g(part, "email"), "phone": g(part, "contactPhone"),
            "director_name": director_name, "director_inn": g(director, "INN"),
            "director_position": g(director, "position"),
            "bank_account": g(part_acct, "bankAccountNumber"), "bik": g(part_acct, "bik"),
            "corr_account": g(part_acct, "corrAccountNumber"), "bank_name": g(part_acct, "creditOrgName"),
        },
        "items": parsed_items,
        "price_total": g(root, "contractFinancingInfo", "contractPriceInfo", "price"),
        "guarantee_part_pct": g(root, "contractConditionsInfo", "contractGuaranteeInfo", "part"),
        "guarantee_amount": g(root, "contractConditionsInfo", "contractGuaranteeInfo", "amount"),
        "delivery_place": g(root, "contractConditionsInfo", "deliveryPlaceInfo", "byGARInfo", "GARInfo", "GARAddress"),
        "execution_end_date": g(root, "contractConditionsInfo", "contractExecutionTermsInfo",
                                 "notRelativeTermsInfo", "endDate"),
        # A contract amended via доп.соглашение republishes as a NEW
        # kontrakt-s-uchet-* XML (same regNumber, same schema) carrying this
        # extra block — the authoritative amendment timeline (ordinal +
        # sign date), no need to diff snapshot text by hand. Only present
        # on an amended snapshot; a first-version elektronnyy-kon has none.
        "amendments": [
            {"ordinal": g(a, "ordinalNumberAdd"), "sign_date": g(a, "signDate")}
            for a in (lambda v: v if isinstance(v, list) else ([v] if v else []))(
                g(root, "printFormFieldsInfo", "additionalAgreementsInfo", "additionalAgreementInfo"))
        ],
    }


def extract_payment_fields(data: dict) -> dict:
    root = data.get("FAM_PaymOrderCr", {})
    return {
        "doc_date": g(root, "AccDoc_DocDate"),
        "sum": g(root, "BasicRequisites_PaySum"),
        "payer_inn": g(root, "Payer_INN"), "payer_name": g(root, "Payer_Name"),
        "payer_bik": g(root, "Payer_BIK"), "payer_bank": g(root, "Payer_BankName"),
        "payer_account": g(root, "Payer_CheckAcc"), "payer_corr_account": g(root, "Payer_CorrAcc"),
        "recipient_inn": g(root, "Recip_INN"), "recipient_name": g(root, "Recip_Name"),
        "recipient_bik": g(root, "Recip_BIK"), "recipient_bank": g(root, "Recip_BankName"),
        "recipient_account": g(root, "Recip_CheckAcc"), "recipient_corr_account": g(root, "Recip_CorrAcc"),
        "purpose": g(root, "DepInfo_PayPurpose"),
        "linked_reg_number": g(root, "StmInfrmtn_ReestrNumGK"),
    }


PAYORDER_INN_RE = re.compile(r'ИНН\s*\n?\s*(\d{10,12})')
PAYORDER_KPP_RE = re.compile(r'КПП\s*\n?\s*(\d{9})')
PAYORDER_BIK_RE = re.compile(r'БИК\s*\n?\s*(\d{9})')
PAYORDER_ACCT_RE = re.compile(r'Сч\.\s*№\s*\n?\s*(\d{15,25})')
PAYORDER_SUM_RE = re.compile(r'Сумма\s*[\r\n\s]*(\d[\d\s]*-\d{2})')
PAYORDER_NUM_RE = re.compile(r'ПЛАТЕЖНОЕ ПОРУЧЕНИЕ №\s*\n?\s*(\d+)')
PAYORDER_LABEL_CELL_RE = re.compile(r'^(ИНН|КПП|БИК|Сч\.|Плательщик|Получатель|Сумма прописью|Вид|Наз\.|Очер\.|Код|Рез\.)')


NEUSTOIKA_TITLE_RE = re.compile(r'Требование об уплате неустойки №(\S+) от (\d{2}\.\d{2}\.\d{4})')
NEUSTOIKA_SUM_RE = re.compile(r'Фиксированная сумма, руб\.:\s*([\d\s.,]+)')
NEUSTOIKA_CONTRACT_DATE_RE = re.compile(r'Дата заключения:\s*(\d{2}\.\d{2}\.\d{4})')
# zakupki regNumbers in this corpus are consistently 19 digits (10-digit
# customer ИНН/regNum prefix + a longer suffix) — a bare 19-digit run inside
# the "Номер контракта (ЕАСУЗ/ЕИС/Внутренний)" line is reliably the
# regNumber, letting a penalty notice buried inside a zip attachment link
# back to the right contract record without needing its own filename clue.
NEUSTOIKA_REGNUM_RE = re.compile(r'\b(\d{19})\b')


def parse_neustoika(text: str):
    """PIK-generated (Госзакупки personal-cabinet) `Требование об уплате
    неустойки` penalty-demand document — found live inside a `требование-
    об-у-*.zip`/`уточненное-треб-*.zip` attachment, a genuinely new
    negative-performance signal distinct from the payment/contract data:
    a fixed fine amount tied to a specific violated obligation, machine-
    generated with clean Label:\\nValue fields (pdftotext -layout keeps
    them recoverable despite the column-wrapped layout). Returns None for
    the OTHER kind of file this same zip-attachment family sometimes holds
    — a freeform scanned/letterhead "уточненная претензия" letter with no
    fixed-field structure — which falls back to plain id_scan same as
    before; not every file matching the filename pattern matches this
    specific machine-generated form."""
    title = NEUSTOIKA_TITLE_RE.search(text)
    if not title:
        return None
    amt = NEUSTOIKA_SUM_RE.search(text)
    reg = NEUSTOIKA_REGNUM_RE.search(text)
    contract_date = NEUSTOIKA_CONTRACT_DATE_RE.search(text)
    return {
        "doc_number": title.group(1),
        "doc_date": title.group(2),
        "linked_reg_number": reg.group(1) if reg else None,
        "contract_date": contract_date.group(1) if contract_date else None,
        "fine_amount": re.sub(r"\s+", "", amt.group(1)) if amt else None,
    }


def parse_payment_order_html(path: Path):
    """Some `платежное поручение` attachments render as a full ОКУД 0401060
    bank-form page (bootstrap HTML) rather than the FAM_PaymOrderCr XML
    schema extract_payment_fields() reads — found live studying
    ZAKUPKI_ATTACH_7733894200_2502412952426000007_platezhnoe-poruch-...html,
    which carries the exact same category of data (payer/recipient bank
    detail, amount, purpose text with contract/invoice/item-stage
    description) but in a completely different DOM shape scan_sources.py's
    plain id_scan pass would never turn into structured fields. Layout is
    fixed by the OKUD template: Плательщик / Банк плательщика / Банк
    получателя / Получатель blocks always appear in that order, so the
    first ИНН/КПП/Сч.№/name found belongs to the payer side and the second
    to the recipient side, and the middle two Сч.№ values are the payer's
    and recipient's *bank* correspondent accounts respectively — confirmed
    against this sample, where positional order exactly matches the visible
    form layout."""
    raw = path.read_bytes().decode("utf-8", errors="ignore")
    if "ПЛАТЕЖНОЕ ПОРУЧЕНИЕ" not in raw.upper():
        return None
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw, "html.parser")
    text = soup.get_text("\n")

    inns = PAYORDER_INN_RE.findall(text)
    kpps = PAYORDER_KPP_RE.findall(text)
    biks = PAYORDER_BIK_RE.findall(text)
    accts = PAYORDER_ACCT_RE.findall(text)
    sum_m = PAYORDER_SUM_RE.search(text)
    amount = None
    if sum_m:
        parts = sum_m.group(1).replace(" ", "").split("-")
        if len(parts) == 2:
            amount = f"{parts[0]}.{parts[1]}"
    order_num_m = PAYORDER_NUM_RE.search(text)
    headers = dict((label.strip(), val.strip()) for val, label in re.findall(
        r'<forsubscr[^>]*>([^<]*)</forsubscr>\s*<br>\s*<small>([^<]*)</small>', raw))
    names = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in soup.select("td.border-start-0")]
    names = [n for n in names if n and not PAYORDER_LABEL_CELL_RE.match(n)]
    purpose = None
    purpose_m = re.search(r'</table>\s*(.*?)<br><br><br>', raw, re.S)
    if purpose_m:
        purpose = re.sub(r"\s+", " ", BeautifulSoup(purpose_m.group(1), "html.parser").get_text(" ", strip=True))

    def take(lst, i):
        return lst[i] if len(lst) > i else None

    return {
        "order_number": order_num_m.group(1) if order_num_m else None,
        "doc_date": headers.get("Дата"),
        "sum": amount,
        "payer_inn": take(inns, 0), "payer_kpp": take(kpps, 0),
        "payer_name": take(names, 0), "payer_account": take(accts, 0),
        "payer_bik": take(biks, 0), "payer_bank": take(names, 1),
        "payer_corr_account": take(accts, 1),
        "recipient_inn": take(inns, 1), "recipient_kpp": take(kpps, 1),
        "recipient_name": take(names, 3), "recipient_account": take(accts, 3),
        "recipient_bik": take(biks, 1), "recipient_bank": take(names, 2),
        "recipient_corr_account": take(accts, 2),
        "purpose": purpose,
    }


def parse_contract_card_html(path: Path):
    """Generic key/value scrape of the zakupki contract-card page — every
    section__title/section__info pair the page has, not a hand-picked list,
    plus the supplier table (a separate DOM shape from the key/value blocks)."""
    from bs4 import BeautifulSoup
    html = path.read_bytes().decode("utf-8", errors="ignore")
    if "section__title" not in html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for section in soup.select("section.blockInfo__section, section.section"):
        title_el = section.find("span", class_="section__title")
        info_el = section.find("span", class_="section__info")
        if not title_el or not info_el:
            continue
        key = title_el.get_text(" ", strip=True)
        val = info_el.get_text(" ", strip=True)
        if key and val:
            fields[key] = val

    suppliers = []
    table = soup.select_one("div.participantsInnerHtml table")
    if table:
        headers = [th.get_text(" ", strip=True) for th in table.select("thead th")]
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            rec = {}
            for i, cell in enumerate(cells):
                key = headers[i] if i < len(headers) and headers[i] else f"col{i}"
                text = cell.get_text(" ", strip=True)
                inn_span = cell.find("span", string=re.compile("ИНН"))
                if inn_span:
                    inn_val = cell.find_all("span")
                    text = " ".join(s.get_text(" ", strip=True) for s in inn_val)
                if text:
                    rec[key or f"col{i}"] = text
            if rec:
                suppliers.append(rec)

    return {"fields": fields, "suppliers_table": suppliers}


def docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[docx read failed: {e}]"
    # <w:t> runs are split across formatting boundaries; a paragraph break
    # (</w:p>) becomes a newline so downstream regexes don't glue unrelated
    # clauses together.
    xml = xml.replace("</w:p>", "\n")
    return "".join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml))


def rar_text(path: Path) -> str:
    """RAR attachments (Приказы orders bundles, Уведомление ФАС antitrust
    notices) were logged as `rar-unparsed` and skipped entirely — no
    rarfile/unrar/7z binary in this environment. But macOS's bundled
    `bsdtar` (libarchive) DOES read this corpus's RARs (confirmed live on
    both a "Приказы" and a "Уведомление ФАС" attachment, store/non-solid
    RAR as zakupki produces) — no new dependency needed, just the right
    tool. Extracts to a temp dir and runs the same per-kind text extraction
    every other path uses (pdf_text with its OCR fallback for the PDFs
    these bundles actually contain), not a bespoke reimplementation.
    A production RAR bsdtar genuinely can't read (RAR5 solid/encrypted)
    fails silently to empty text rather than raising — same "degrade, don't
    crash the batch" contract as everything else in this script."""
    import subprocess
    import tempfile
    chunks = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(["bsdtar", "-xf", str(path), "-C", tmp],
                                capture_output=True, timeout=120)
            if r.returncode != 0:
                return f"[rar extract failed: {r.stderr.decode('utf-8', errors='ignore')[:200]}]"
            for member in sorted(Path(tmp).rglob("*")):
                if not member.is_file():
                    continue
                chunks.append(f"--- {member.relative_to(tmp)} ---")
                if member.suffix.lower() == ".pdf":
                    chunks.append(pdf_text(member))
                elif member.suffix.lower() in (".txt", ".xml"):
                    chunks.append(member.read_text(encoding="utf-8", errors="ignore"))
                # .sig/.sign attachment-integrity signatures alongside the
                # real document — not text, intentionally not read.
    except Exception as e:
        return f"[rar read failed: {e}]"
    return "\n".join(chunks)


SIGNATORY_RE = re.compile(
    r'([А-ЯЁ][а-яёА-Я]+(?:\s+[А-ЯЁ][а-яёА-Я]+){1,2})[,\s]+'
    # A bare "\.[^.]*" stops at a date's decimal point ("...от 09.06.2025 №
    # 110" gets truncated to "...от 09") — a real clause boundary is a
    # period followed by whitespace+capital, a newline, or (the reliable one
    # for these dual-party government contracts, which run the whole
    # preamble as one comma-separated sentence: "...действующего на
    # основании доверенности..., с одной стороны, и [Поставщик]...") the
    # standard "с одной/другой стороны" hand-off phrase. Without that
    # alternative the lookahead never finds a match within the 150-char cap
    # on this preamble shape and the whole signatory silently drops instead
    # of just truncating.
    r'действующ\w*\s+на\s+основании\s+(.{3,150}?)'
    r'(?=,\s*с\s+(?:одной|другой)\s+сторон|\.\s+[А-ЯЁ]|\n|$)', re.UNICODE,
)


def mine_docx(path: Path) -> dict:
    text = docx_text(path)
    signatories = [{"name": m.group(1).strip(), "authority_basis": m.group(2).strip()}
                   for m in SIGNATORY_RE.finditer(text)]
    flags = scan_text_for_flags(text)
    # docx runs are concatenated with no inter-clause whitespace (see
    # docx_text's newline-only-at-</w:p> handling), so a Cyrillic word
    # routinely glues onto either end of an email — a trailing one onto the
    # TLD ("sales@pokrovsystem.ru" + "р/счет..." -> "...ruр") and, just as
    # often, a LEADING one onto the local part, e.g. a signatory's
    # patronymic gluing onto the next clause's address ("Владимировна" +
    # "tischenkomv@it.mos.ru" -> "Владимировнаtischenkomv@it.mos.ru").
    # Python's \w matches Cyrillic under the default Unicode flag, so a
    # `[\w.+-]+` local-part class happily swallows that glued prefix too —
    # real email local parts are ASCII, so restricting to that excludes it
    # on both ends without needing to guess where the real boundary is.
    # Domain/TLD labels restricted to lowercase-only: real corporate email
    # domains are conventionally written lowercase in contract prose, and a
    # trailing glued Latin-alphabet surname is capitalized ("...gaskar.group"
    # + "Maklyusova" -> stops before the capital M). Doesn't catch a glued
    # lowercase abbreviation with no case boundary (e.g. "...groupitc") —
    # accepted as a rare residual case, not worth a domain allowlist for.
    emails = sorted(set(re.findall(r'[A-Za-z0-9._+-]+@[a-z0-9-]+\.[a-z]{2,}(?:\.[a-z]{2,})?', text)))
    return {
        "text_len": len(text),
        "signatories": signatories,
        "technical_spec_candidates": flags["technical_spec_candidates"],
        "performance_flags": flags["performance_flags"],
        "emails_found": emails,
        "id_scan": id_scan(text),
    }


def classify_and_mine(path: Path) -> dict:
    suf = path.suffix.lower()
    name = path.name

    if suf == ".xml":
        data, root_tag = parse_xml_generic(path)
        if data is None:
            return {"kind": "xml-error", "detail": root_tag}
        if root_tag == "cpElectronicContract":
            return {"kind": "contract-xml", "fields": extract_contract_fields(data), "raw": data}
        if root_tag == "FAM_PaymOrderCr":
            return {"kind": "payment-xml", "fields": extract_payment_fields(data), "raw": data}
        # Any other XML schema (control99Notice, etc.) — kept generically,
        # still text-scanned for entity/ИНН mentions.
        flat_text = json.dumps(data, ensure_ascii=False)
        return {"kind": f"xml-other:{root_tag}", "raw": data, "id_scan": id_scan(flat_text),
                **scan_text_for_flags(flat_text)}

    if suf == ".html":
        card = parse_contract_card_html(path)
        if card is not None:
            return {"kind": "contract-card-html", **card}
        payorder = parse_payment_order_html(path)
        if payorder is not None:
            return {"kind": "payment-order-html", "fields": payorder}
        from scan_sources import html_text
        text = html_text(path)
        return {"kind": "printform-html", "id_scan": id_scan(text)}

    if suf == ".docx":
        return {"kind": "docx", **mine_docx(path)}

    if suf == ".pdf":
        text = pdf_text(path)
        neustoika = parse_neustoika(text)
        if neustoika is not None:
            return {"kind": "neustoika", "fields": neustoika, "id_scan": id_scan(text)}
        return {"kind": "pdf", "text_len": len(text), "id_scan": id_scan(text),
                "uav_score": uav_score(text), **scan_text_for_flags(text)}

    if suf == ".zip":
        text = zip_text(path)
        # The неустойка penalty-demand PDF this whole zip-attachment family
        # sometimes carries (see parse_neustoika's docstring) — checked here
        # too since most of these attachments arrive zipped, not bare.
        neustoika = parse_neustoika(text)
        if neustoika is not None:
            return {"kind": "neustoika", "fields": neustoika, "id_scan": id_scan(text)}
        return {"kind": "zip", "text_len": len(text), "id_scan": id_scan(text), **scan_text_for_flags(text)}

    if suf == ".txt":
        # Some EDI attachments (счет-фактура detail, "ON_DIT1084NSCHF...")
        # are actually well-formed XML saved with a .txt extension (BOM +
        # <?xml ...?> header) — route those through the same generic
        # flattener as real .xml files instead of losing their structure to
        # a flat id_scan pass; anything else here really is plain text.
        raw = path.read_bytes().decode("utf-8-sig", errors="ignore").lstrip()
        if raw.startswith("<?xml"):
            try:
                root = ET.fromstring(raw)
            except ET.ParseError as e:
                return {"kind": "txt-xml-error", "detail": str(e)}
            tag = strip_ns(root.tag)
            data = {tag: elem_to_obj(root)}
            return {"kind": f"txt-xml:{tag}", "raw": data,
                    "id_scan": id_scan(json.dumps(data, ensure_ascii=False))}
        return {"kind": "txt", "id_scan": id_scan(raw), **scan_text_for_flags(raw)}

    if suf == ".xlsx":
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True)
            rows = []
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    rows.append(" ".join(str(c) for c in row if c is not None))
            text = "\n".join(rows)
        except Exception as e:
            return {"kind": "xlsx-error", "detail": str(e)}
        return {"kind": "xlsx", "text_len": len(text), "id_scan": id_scan(text)}

    if suf == ".rar":
        text = rar_text(path)
        if not text.strip():
            return {"kind": "rar-unparsed", "size": path.stat().st_size}
        neustoika = parse_neustoika(text)
        if neustoika is not None:
            return {"kind": "neustoika", "fields": neustoika, "id_scan": id_scan(text)}
        return {"kind": "rar", "text_len": len(text), "id_scan": id_scan(text), **scan_text_for_flags(text)}

    if suf == ".doc":
        # Legacy binary Word format — no antiword/catdoc/libreoffice in this
        # environment, and not worth adding a system dependency for the 2
        # files (out of 454) that turned up in this format. Logged as its
        # own kind rather than falling through to a silent "skipped", so a
        # future run with the right tool installed is easy to find and wire
        # up, and the report/JSON output makes the gap visible instead of
        # implying full coverage.
        return {"kind": "doc-unparsed", "size": path.stat().st_size}

    return {"kind": "skipped"}


def reg_number_for(path: Path) -> str | None:
    m = FILENAME_REG_RE.match(path.name) or FILENAME_REG_RE2.search(path.name)
    return m.group(1) if m else None


def inn_for(path: Path) -> str | None:
    m = FILENAME_INN_RE.match(path.name)
    return m.group(1) if m else None


def merge_contract_record(rec: dict, mined: dict, fname: str) -> None:
    rec.setdefault("files", []).append(fname)
    kind = mined["kind"]
    if kind == "contract-xml":
        # A contract with N доп.соглашения has N+1 contract-schema XML files
        # for the same regNumber (1 original + N amended kontrakt-s-uchet
        # snapshots) — filename sort order happening to match chronological
        # order is a coincidence of this corpus's numeric suffixes, not a
        # guarantee (uid-derived or hash-derived suffixes elsewhere would
        # break it silently). The snapshot with the most `amendments`
        # entries is unambiguously the most current one regardless of
        # processing order, so prefer that instead of blind last-write-wins.
        new_fields = mined["fields"]
        prev_fields = rec.get("contract_fields")
        if prev_fields is None or len(new_fields.get("amendments", [])) >= len(prev_fields.get("amendments", [])):
            rec["contract_fields"] = new_fields
    elif kind in ("payment-xml", "payment-order-html"):
        # The same платежное поручение frequently exists twice in the
        # attachment set: once as the FAM_PaymOrderCr XML, once as the
        # rendered ОКУД-0401060 HTML — same transaction, different date
        # format ("2025-12-22" vs "22.12.2025") and no shared filename to
        # key on. Comparing (sum, payer_inn, recipient_inn) — which does
        # match across both renderings — instead of the raw date/file
        # avoids double-counting one payment as two.
        fields = mined["fields"]
        dup_key = (fields.get("sum"), fields.get("payer_inn"), fields.get("recipient_inn"))
        existing = rec.setdefault("payments", [])
        if not any((p.get("sum"), p.get("payer_inn"), p.get("recipient_inn")) == dup_key
                   for p in existing):
            existing.append({"file": fname, **fields})
    elif kind == "contract-card-html":
        rec.setdefault("card_fields", {}).update(mined.get("fields", {}))
        if mined.get("suppliers_table"):
            rec["card_suppliers_table"] = mined["suppliers_table"]
    elif kind == "docx":
        rec.setdefault("docx_signatories", []).extend(mined.get("signatories", []))
        rec.setdefault("docx_emails_found", []).extend(mined.get("emails_found", []))
    elif kind == "neustoika":
        # A PIK penalty-demand PDF (see parse_neustoika) — dedup on
        # (doc_number, doc_date) since the зип attachment set frequently
        # holds 2 copies of the same neустойка letter (a plain and a
        # signature-stamped "(МСК)" rendering, same doc number/date).
        fields = mined["fields"]
        dup_key = (fields.get("doc_number"), fields.get("doc_date"))
        existing = rec.setdefault("penalties", [])
        if not any((p.get("doc_number"), p.get("doc_date")) == dup_key for p in existing):
            existing.append({"file": fname, **fields})

    # Technical-spec and non-performance line flags apply to every text-
    # bearing kind (docx/pdf/zip/txt/xml-other), not just docx — a
    # Спецификация table or a "работы не выполнялись" admission can equally
    # turn up in a scanned акт PDF or an EDI zip bundle.
    for flag_key in ("technical_spec_candidates", "performance_flags"):
        if flag_key in mined:
            rec.setdefault(flag_key, []).extend(mined[flag_key])

    for key in ("id_scan",):
        if key in mined:
            rec.setdefault("aggregate_id_scan", {})
            for section, items in mined[key].items():
                rec["aggregate_id_scan"].setdefault(section, set()).update(items)


def is_target_file(p: Path) -> bool:
    if not p.is_file() or not p.name.startswith("ZAKUPKI_") or "supplier-search" in p.name:
        return False
    return ("_ATTACH_" in p.name or p.name.startswith("ZAKUPKI_contract_")
            or bool(re.search(r"ZAKUPKI_\d+_\d{8}_contract-", p.name)))


def reg_numbers_for_inn(inn: str) -> set[str] | None:
    """Authoritative regNumber whitelist for one supplier ИНН, from the
    zakupki_batch_pull.py scan log — used instead of filename-based ИНН
    matching alone, because contract-card HTML files (`ZAKUPKI_contract_
    <reg>_<date>.html`) carry no ИНН in their own filename. Filtering only
    by inn_for() on ATTACH files let every OTHER supplier's card-HTML
    skeleton (no items/customer/supplier — just whatever bare fields that
    file's own card has) leak into a supposedly single-ИНН run, since a
    file with no extractable ИНН was never excluded. Returns None if the
    scan log doesn't have this ИНН (caller falls back to filename-only
    filtering)."""
    if not zk.SCAN_LOG.exists():
        return None
    log = json.loads(zk.SCAN_LOG.read_text(encoding="utf-8"))
    entry = log.get(inn)
    if not entry:
        return None
    return set(entry.get("reg_numbers", []))


def _mine_cache_key(path: Path) -> str:
    st = path.stat()
    return f"{st.st_size}:{int(st.st_mtime)}"


def load_mine_cache() -> dict:
    if not MINE_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(MINE_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_mine_cache(cache: dict) -> None:
    MINE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MINE_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def scan_all(inn_filter: str | None = None) -> dict:
    """Per-file mining (classify_and_mine) is cached to MINE_CACHE_PATH,
    keyed by filename + size + mtime — same incremental pattern
    inventory_sources.py already uses for its own content cache. Without
    this, every full-corpus run re-OCRs every scanned PDF from scratch
    (10+ seconds each), which is what made a plain rescan slow enough that
    the user had to kill and restart it. A file is only re-mined if its
    size or mtime changed since the cached entry."""
    files = sorted(p for p in SOURCES.iterdir() if is_target_file(p))
    reg_whitelist = reg_numbers_for_inn(inn_filter) if inn_filter else None
    contracts: dict[str, dict] = {}
    unlinked = []
    total = len(files)
    mine_cache = load_mine_cache()
    cache_hits = 0
    considered = 0
    for i, path in enumerate(files, 1):
        inn = inn_for(path)
        if inn_filter and inn and inn != inn_filter:
            continue
        reg = reg_number_for(path)
        if inn_filter and reg_whitelist is not None and reg is not None and reg not in reg_whitelist:
            continue
        considered += 1
        cache_key = _mine_cache_key(path)
        cached = mine_cache.get(path.name)
        if cached and cached.get("_cache_key") == cache_key:
            mined = cached["mined"]
            cache_hits += 1
        else:
            # OCR on a scanned PDF can take 10+ seconds each, and this is the
            # only visibility into a long run otherwise — the tool that
            # discovered this gap (an interactive "how many left?" with no
            # answer available) is exactly the failure mode this line fixes.
            print(f"  [{i}/{total}] {path.name}", file=sys.stderr, flush=True)
            mined = classify_and_mine(path)
            mine_cache[path.name] = {"_cache_key": cache_key, "mined": mined}
        if reg is None:
            reg = g(mined, "fields", "linked_reg_number") if mined["kind"] == "payment-xml" else None
        if reg is None:
            unlinked.append({"file": path.name, "mined": mined})
            continue
        rec = contracts.setdefault(reg, {"reg_number": reg, "supplier_inn": inn})
        if inn and not rec.get("supplier_inn"):
            rec["supplier_inn"] = inn
        merge_contract_record(rec, mined, path.name)

    # sets aren't JSON-serializable — freeze aggregate_id_scan before returning
    for rec in contracts.values():
        if "aggregate_id_scan" in rec:
            rec["aggregate_id_scan"] = {k: sorted(v) for k, v in rec["aggregate_id_scan"].items()}

    save_mine_cache(mine_cache)
    print(f"  ({cache_hits}/{considered} in-scope file(s) served from mine cache, "
          f"{considered - cache_hits} (re-)mined; {total - considered} filtered out by --inn)",
          file=sys.stderr)

    return {"contracts": contracts, "unlinked_files": unlinked}


def _contract_fingerprint(rec: dict) -> str:
    """Stable digest of a contract record's mined content, ignoring nothing
    volatile (there isn't anything — mining is deterministic over the same
    files). Used by --diff to skip printing a contract unchanged since the
    baseline snapshot, instead of re-showing the same detail every run."""
    return json.dumps(rec, ensure_ascii=False, sort_keys=True)


def build_report(result: dict, known_text: str, depth: str = "deep", baseline: dict | None = None) -> str:
    """depth='scan' (the default for a whole-corpus, no --inn run) prints
    one compact line per contract plus the full aggregate new-entity/flag
    sections — those aggregate sections are the actual triage signal and
    stay cheap to read regardless of corpus size. depth='deep' (the default
    when --inn narrows to one target) prints the full per-contract detail
    block, for the close-reading pass on a target the scan tier flagged as
    worth it.

    baseline, if given (from --diff), is a previously-saved result dict —
    contracts whose mined content is byte-identical to the baseline are
    skipped entirely (already reported last run); only new or changed
    contracts and the unlinked-files diff are shown."""
    contracts = result["contracts"]
    baseline_contracts = (baseline or {}).get("contracts", {})
    baseline_unlinked = {u["file"] for u in (baseline or {}).get("unlinked_files", [])}

    to_report = {}
    skipped_unchanged = 0
    for reg, rec in contracts.items():
        if baseline is not None and reg in baseline_contracts and \
                _contract_fingerprint(rec) == _contract_fingerprint(baseline_contracts[reg]):
            skipped_unchanged += 1
            continue
        to_report[reg] = rec

    title = f"# zakupki.gov.ru mined data — {len(contracts)} contract(s) total"
    if baseline is not None:
        title += f", {len(to_report)} new/changed since baseline ({skipped_unchanged} unchanged, not re-shown)"
    lines = [title + "\n"] + [
        "Triage list, not a source — hand-verify against the primary document",
        "before wiring anything into government_contracts[]/corrections.json.\n"]

    new_entities: dict[str, set] = {}
    new_people: dict[str, set] = {}
    new_contacts: dict[str, set] = {}
    spec_hits: list[tuple[str, str]] = []
    performance_flag_hits: list[tuple[str, str]] = []
    penalty_rows = []
    bank_rows = []

    for reg, rec in sorted(to_report.items()):
        cf = rec.get("contract_fields", {})
        cust = cf.get("customer", {})
        supp = cf.get("supplier", {})

        if depth == "scan":
            # one line: customer, value, subject/item summary, flag counts —
            # enough to decide whether this ИНН deserves a --depth deep pass.
            # Falls back to card_fields (the HTML contract-card scrape) when
            # contract_fields (parsed from a raw cpElectronicContract XML) is
            # empty — most of this corpus's contracts have no such XML file
            # attached at all (only docx/pdf/card-html), which otherwise
            # left every one of them showing "?" here.
            card = rec.get("card_fields", {})
            n_pen = len(rec.get("penalties", []))
            n_flag = len(rec.get("performance_flags", []))
            items_summary = "; ".join(it.get("name", "") for it in cf.get("items", [])[:3]) or cf.get("subject", "")
            customer_name = cust.get("full_name") or card.get("Полное наименование заказчика") \
                or card.get("Сокращенное наименование заказчика")
            price = cf.get("price_total") or card.get("Цена контракта")
            flag_note = f", {n_pen} penalt{'y' if n_pen==1 else 'ies'}" if n_pen else ""
            flag_note += f", {n_flag} non-perf flag(s)" if n_flag else ""
            lines.append(f"- [{reg}] {customer_name or '?'} — {price or '?'} RUB"
                          f" — {items_summary}{flag_note}")
            # still feed the aggregate sections below so new-entity/flag
            # triage isn't lost in scan mode — only the per-contract prose
            # narrative is skipped, not the signal that drives a deep pass
        if depth == "deep":
            if cf.get("subject"):
                lines.append(f"- Subject: {cf['subject']}")
            if cf.get("price_total"):
                lines.append(f"- Price: {cf['price_total']} RUB")
            if cf.get("placing_way"):
                lines.append(f"- Placing way: {cf['placing_way']}")
            if cf.get("amendments"):
                dates = ", ".join(f"#{a['ordinal']}" + (f" ({a['sign_date']})" if a.get("sign_date") else " (unsigned)")
                                   for a in cf["amendments"])
                lines.append(f"- Amendments ({len(cf['amendments'])}): {dates}")
            basis = rec.get("card_fields", {}).get("Основание заключения контракта с единственным поставщиком")
            if basis:
                lines.append(f"- Sole-supplier basis: {basis}")
            if cust.get("full_name"):
                lines.append(f"- Customer: {cust['full_name']} (ИНН {cust.get('inn')})")
            if supp.get("full_name"):
                lines.append(f"- Supplier: {supp['full_name']} (ИНН {supp.get('inn')})")
            if supp.get("director_name"):
                lines.append(f"  - Director: {supp['director_name']} (ИНН {supp.get('director_inn')}, {supp.get('director_position')})")
            if cf.get("items"):
                lines.append(f"- Items ({len(cf['items'])}):")
                for it in cf["items"][:10]:
                    lines.append(f"  - {it.get('name')} x{it.get('quantity')} @ {it.get('price')} = {it.get('sum')} ({it.get('okpd2_code')})")
            payments = rec.get("payments", [])
            if payments:
                lines.append(f"- Payments ({len(payments)}):")
                for pay in payments:
                    lines.append(f"  - {pay.get('doc_date')}: {pay.get('sum')} RUB, "
                                  f"{pay.get('payer_name')} (ИНН {pay.get('payer_inn')}) -> "
                                  f"{pay.get('recipient_name')} (ИНН {pay.get('recipient_inn')})"
                                  + (f" — {pay['purpose']}" if pay.get("purpose") else ""))
            penalties = rec.get("penalties", [])
            if penalties:
                lines.append(f"- Penalty demands (неустойка) ({len(penalties)}):")
                for pen in penalties:
                    lines.append(f"  - № {pen.get('doc_number')} от {pen.get('doc_date')}: "
                                  f"{pen.get('fine_amount')} RUB")

        # Aggregate triage signal collected regardless of depth — this is
        # what a scan-tier pass over the whole corpus needs to surface, even
        # though the verbose per-contract prose above is skipped for it.
        if supp.get("director_name"):
            key = norm(supp["director_name"])
            if key and key not in known_text:
                new_people.setdefault(key, set()).add(f"{supp['director_name']} — contract {reg}")
        for bank_side, label in ((cust, "customer"), (supp, "supplier")):
            if bank_side.get("bank_account"):
                bank_rows.append((reg, label, bank_side.get("full_name"), bank_side.get("inn"),
                                   bank_side.get("bank_account"), bank_side.get("bik"), bank_side.get("bank_name")))
        known_inns = {cust.get("inn"), supp.get("inn")}
        for pay in rec.get("payments", []):
            # A payer/recipient ИНН this contract's own customer/supplier
            # fields never mentioned is a real lead — found live on
            # contract 2502412952426000007, where the actual paying
            # customer (Министерство строительного комплекса Московской
            # области) only ever appears in a payment order, never in
            # the contract-card/contract-xml data for that regNumber.
            for side_inn, side_name in ((pay.get("payer_inn"), pay.get("payer_name")),
                                         (pay.get("recipient_inn"), pay.get("recipient_name"))):
                if side_inn and side_name and side_inn not in known_inns and side_name not in known_text:
                    new_entities.setdefault(norm(side_name), set()).add(
                        f"{side_name} (ИНН {side_inn}) — payment on contract {reg}")
        for sig in rec.get("docx_signatories", []):
            key = norm(sig["name"])
            if key and key not in known_text:
                new_people.setdefault(key, set()).add(f"{sig['name']} ({sig['authority_basis']}) — contract {reg}")
        for spec in rec.get("technical_spec_candidates", [])[:5]:
            spec_hits.append((reg, spec))
        for flag in rec.get("performance_flags", [])[:5]:
            performance_flag_hits.append((reg, flag))
        for pen in rec.get("penalties", []):
            penalty_rows.append((reg, pen.get("doc_number"), pen.get("doc_date"), pen.get("fine_amount")))
        for email in rec.get("docx_emails_found", []):
            new_contacts.setdefault(email, set()).add(f"contract {reg}")
        for section, items in rec.get("aggregate_id_scan", {}).items():
            if section == "Entities (АО/ООО/НПЦ/etc.)":
                for e in items:
                    k = norm(e)
                    if k and k not in known_text:
                        new_entities.setdefault(k, set()).add(f"{e} — contract {reg}")
            elif section == "Named individuals (role + name)":
                for p in items:
                    k = norm(p)
                    words = [w for w in k.split() if len(w) > 1]
                    if words and not all(w in known_text.split() for w in words):
                        new_people.setdefault(k, set()).add(f"{p} — contract {reg}")
        lines.append("")

    if new_entities:
        lines.append("## New entities (not yet in registry)\n")
        for key, refs in sorted(new_entities.items()):
            lines.append(f"- **{sorted(refs)[0].split(' — ')[0]}** — {', '.join(sorted(refs))}")
        lines.append("")
    if new_people:
        lines.append("## New named individuals (not yet in registry)\n")
        for key, refs in sorted(new_people.items()):
            lines.append(f"- {', '.join(sorted(refs))}")
        lines.append("")
    if new_contacts:
        lines.append("## New emails/contacts found in docx text\n")
        for contact, refs in sorted(new_contacts.items()):
            lines.append(f"- {contact} — {', '.join(sorted(refs))}")
        lines.append("")
    if spec_hits:
        lines.append("## Technical-spec / marketing-claim candidates (verbatim)\n")
        for reg, spec in spec_hits:
            lines.append(f"- [{reg}] {spec}")
        lines.append("")
    if performance_flag_hits:
        lines.append("## Non-performance admissions found (verbatim — акты, экспертиза, etc.)\n")
        for reg, flag in performance_flag_hits:
            lines.append(f"- [{reg}] {flag}")
        lines.append("")
    if penalty_rows:
        lines.append("## Penalty demands (неустойка) summary\n")
        lines.append("| contract | doc № | date | fine (RUB) |")
        lines.append("|---|---|---|---|")
        for reg, num, date, amt in penalty_rows:
            lines.append(f"| {reg} | {num} | {date} | {amt} |")
        lines.append("")
    if bank_rows:
        lines.append("## Bank details observed\n")
        lines.append("| contract | side | name | ИНН | account | BIK | bank |")
        lines.append("|---|---|---|---|---|---|---|")
        for reg, label, fname, inn, acct, bik, bank in bank_rows:
            lines.append(f"| {reg} | {label} | {fname} | {inn} | {acct} | {bik} | {bank} |")
        lines.append("")

    new_unlinked = [u for u in result["unlinked_files"] if u["file"] not in baseline_unlinked]
    if new_unlinked:
        lines.append(f"## {len(new_unlinked)} file(s) with no contract regNumber resolved"
                      + (f" (of {len(result['unlinked_files'])} total, rest already seen in baseline)"
                         if baseline is not None else "") + "\n")
        for u in new_unlinked[:20]:
            lines.append(f"- {u['file']} ({u['mined']['kind']})")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None, help="write markdown triage report here instead of stdout")
    ap.add_argument("--json", type=Path, default=None, nargs="?", const=DEFAULT_JSON_OUT,
                     help=f"also write the full structured dump (default {DEFAULT_JSON_OUT})")
    ap.add_argument("--inn", default=None, help="restrict to one supplier ИНН")
    ap.add_argument("--depth", choices=["scan", "deep"], default=None,
                     help="scan = one line/contract + aggregate triage sections only (cheap, for a "
                          "whole-corpus sweep); deep = full per-contract detail (for a chosen target). "
                          "Default: deep if --inn given, scan otherwise.")
    ap.add_argument("--diff", action="store_true",
                     help="load the previous run's --json snapshot (from the --json path, or the "
                          "default location if --json wasn't given) and only report contracts/files "
                          "new or changed since then; unchanged contracts are counted but not re-shown")
    args = ap.parse_args()

    if not SOURCES.exists():
        raise SystemExit(f"{SOURCES} not found")

    depth = args.depth or ("deep" if args.inn else "scan")
    json_path = args.json or DEFAULT_JSON_OUT

    baseline = None
    if args.diff and json_path.exists():
        baseline = json.loads(json_path.read_text(encoding="utf-8"))

    result = scan_all(inn_filter=args.inn)
    print(f"{len(result['contracts'])} contract(s), {len(result['unlinked_files'])} unlinked file(s)", file=sys.stderr)

    if args.json or args.diff:
        # --diff needs the snapshot written back out even if --json wasn't
        # explicitly passed, or the next --diff run would compare against a
        # stale baseline forever instead of advancing it.
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Wrote {json_path}", file=sys.stderr)

    known_text = load_known_text(REPO)
    report = build_report(result, known_text, depth=depth, baseline=baseline)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
