#!/usr/bin/env python3
"""Regression fixtures for scripts/mine_zakupki.py's parse_contract_card_html.

No pytest dependency — plain assertions, run directly:
    python3 tests/test_zakupki_parser.py

Exists because the 2026-08-29 price-parsing bug (older zakupki.gov.ru contract
cards put "Цена контракта" in a <div class="price"> block with
cardMainInfo__title/content spans, a different DOM shape from the
section__title/section__info blocks the parser otherwise reads) went
undetected through 32 contracts (₽1.72bn) across two full corpus mines before
being noticed. A full re-mine of ~1289 archived files is the only thing that
would have caught it before, and that takes minutes — this fixture catches it
in under a second and should be run after any change to parse_contract_card_html.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from mine_zakupki import (  # noqa: E402
    parse_contract_card_html, parse_pretenziya, parse_contract_subject,
    extract_contract_fields, extract_payment_fields, parse_neustoika,
    find_signatories,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)

# Old template (pre-~2015 contract cards): price lives in div.price's own
# title/content spans, never in a section__title/section__info block.
OLD_LAYOUT = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство промышленности и торговли Российской Федерации</span>
</section>
<div class="price">
  <span class="cardMainInfo__title">Цена контракта</span>
  <span class="cardMainInfo__content cost">45 500 000,00 &#8381;</span>
</div>
</body></html>
"""

# Current template: price also lives in a cardMainInfo__title/content pair,
# alongside (not instead of) the section__title/section__info blocks.
NEW_LAYOUT = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство промышленности и торговли Российской Федерации</span>
</section>
<div class="price">
  <span class="cardMainInfo__title">Цена контракта</span>
  <span class="cardMainInfo__content cost">5 592 211 234,00</span>
</div>
</body></html>
"""

# No price section at all (e.g. a cancelled/unpriced contract) — must not crash,
# must not fabricate a value.
NO_PRICE = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство обороны Российской Федерации</span>
</section>
</body></html>
"""

# "Объекты закупки" (contract subject/предмет) title element is a <div>,
# not a <span> like every other cardMainInfo__title field -- found
# 2026-09-15 chasing 53 empty items/subject_ru gaps on npp-radar-mms/
# ao-tsentr-telko. The old span-only selector silently skipped this field
# on every one of the 1498 archived contract cards. Long subjects are
# truncated with "..." in the visible span but carry the full text in the
# content div's own data-tooltip attribute.
OBJECT_LONG_WITH_TOOLTIP = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство обороны Российской Федерации</span>
</section>
<div class="cardMainInfo__section">
  <div class="cardMainInfo__title">Объекты закупки</div>
  <div class="cardMainInfo__content"
       data-tooltip='<div class="custom-tooltiptext text-break">Разработка технологии и конструкции ряда датчиков микроперемещений и температуры с идентификацией на поверхностных акустических волнах для применения в дистанционных автоматизированных системах контроля и мониторинга</div>'>
    <span class="text-break d-block">
      Разработка технологии и конструкции ряда датчиков микроперемещений и температуры с идентификацией на поверхностных акуст... &nbsp;
    </span>
  </div>
</div>
</body></html>
"""

# Short subject, no truncation -> no data-tooltip attribute at all; the
# visible span text is already the full value.
OBJECT_SHORT_NO_TOOLTIP = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство обороны Российской Федерации</span>
</section>
<div class="cardMainInfo__section">
  <div class="cardMainInfo__title">Объекты закупки</div>
  <div class="cardMainInfo__content">
    <span class="text-break d-block">
      Мобильная радиостанция Motorola DM4400 136-174 МГц 0-25 Вт 99 кан. &nbsp;
    </span>
  </div>
</div>
</body></html>
"""

# Multi-item "Объекты закупки" -- the card only ever shows the first item
# ("Этап 1") plus a "Посмотреть все (N)" link to a page this scrape never
# fetched. Must NOT glue the link text onto the value, and must NOT return
# the single-item fragment as if it were the whole (N-item) subject --
# real find, reg 0173100004513001187 (5 objects, card lists only 1).
OBJECT_MULTI_ITEM = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство обороны Российской Федерации</span>
</section>
<div class="cardMainInfo__section">
  <div class="cardMainInfo__title">Объекты закупки</div>
  <div class="cardMainInfo__content">
    <span class="text-break d-block">
      Этап 1 &nbsp;
      <a target="_blank" rel="noopener" href="/epz/contract/contractCard/payment-info-and-target-of-order.html?reestrNumber=0173100004513001187#contractSubjects">
        Посмотреть все&nbsp;(5)
      </a>
    </span>
  </div>
</div>
</body></html>
"""

# Multi-item, but the first item's text is a real descriptive sentence (not
# a bare "Этап N" placeholder) -- kept, unlike OBJECT_MULTI_ITEM above.
# Real find, reg 1770425226117000798 (5 objects under one described supply
# contract).
OBJECT_MULTI_ITEM_SUBSTANTIVE = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство обороны Российской Федерации</span>
</section>
<div class="cardMainInfo__section">
  <div class="cardMainInfo__title">Объекты закупки</div>
  <div class="cardMainInfo__content">
    <span class="text-break d-block">
      поставка гидрометеостанций корабельных «Характер-К» с монтажными и пусконаладочными работами для нужд Минобороны России &nbsp;
      <a target="_blank" rel="noopener" href="/epz/contract/contractCard/payment-info-and-target-of-order.html?reestrNumber=1770425226117000798#contractSubjects">
        Посмотреть все&nbsp;(5)
      </a>
    </span>
  </div>
</div>
</body></html>
"""

# No "Объекты закупки" section at all on the card -- must not crash, must
# not fabricate a value (real-absence case, distinct from a parser miss).
OBJECT_ABSENT = """
<html><body>
<section class="blockInfo__section">
  <span class="section__title">Полное наименование заказчика</span>
  <span class="section__info">Министерство обороны Российской Федерации</span>
</section>
</body></html>
"""


def write_fixture(name: str, html: str) -> Path:
    path = FIXTURES_DIR / name
    path.write_text(html, encoding="utf-8")
    return path


# Freeform "ПРЕТЕНЗИЯ о взыскании пени" letterhead penalty demand — the
# document parse_neustoika's own docstring flags as falling back to plain
# id_scan (no PIK-generated fixed-field structure). Real text (whitespace
# preserved as pdftotext -layout produces it, including the mid-sentence
# newline that broke the first regex draft) from the npts-elvis
# «Процессор-ИМА-БК» ₽49.1m late-delivery penalty letter found 2026-08-29.
PRETENZIYA_TEXT = """ПРЕТЕНЗИЯ
                                 о взыскании пени

     В     соответствии      с      условиями        государственного     контракта
от 03.12.2024 № 2427020100952000000020323/24208.4420029.11.044 срок сдачи
1 этапа ОКР «Процессор-ИМА-БК» предусмотрен 02.06.2025.
     Согласно акту сдачи-приемки 1 этапа ОКР «Процессор-ИМА-БК» от
11.09.2025 фактическая дата выполнения работ – 19.08.2025.
     На   основании     пункта   10.3   указанного     государственного   контракта
с АО НПЦ «Элвис» подлежит взысканию неустойка в размере 49 127 400 (Сорок
девять миллионов сто двадцать семь тысяч четыреста) рублей 04 копейки согласно
прилагаемому расчету.

Цена 1 этапа государственного контракта – 1 145 160 840,00 рублей;
Стоимость фактически исполненных обязательств – 0,00 рублей;
Количество дней просрочки с 02.06.2025 по 19.08.2025 – 78 дней;
"""


# Legal-entity contract-xml fixture (cpElectronicContract, already flattened
# to a plain dict — extract_contract_fields operates on the parsed dict, not
# raw XML, so no ET construction needed). Exercises: 2 items, amendments as
# a LIST (>=2 доп.соглашения), legalEntityRFInfo + its own director.
CONTRACT_XML_LEGAL = {
    "cpElectronicContract": {
        "foundationInfo": {
            "purchaseNumber": "0173100004514000947",
            "placingWay": {"name": "Электронный аукцион"},
        },
        "contractSubjectInfo": {
            "contractSubject": "Поставка корабельной гидрометеорологической станции «Характер-К»",
            "productsInfo": {"productsInfoElectronicContract": {"productInfo": [
                {"name": "Станция гидрометеорологическая",
                 "OKPD2Info": {"OKPDCode": "26.51.66.190", "OKPDName": "Приборы гидрометеорологические"},
                 "KTRUInfo": {"code": "26.51.66.190-00000001", "name": "Станция"},
                 "quantity": "1", "OKEIInfo": {"name": "штука"},
                 "price": "96393305.55", "sum": "96393305.55", "VATRateInfo": {"VATName": "НДС 20%"}},
                {"name": "Комплект ЗИП",
                 "OKPD2Info": {"OKPDCode": "26.51.66.190", "OKPDName": "Приборы гидрометеорологические"},
                 "quantity": "1", "OKEIInfo": {"name": "комплект"},
                 "price": "0", "sum": "0", "VATRateInfo": {"VATName": "НДС 20%"}},
            ]}},
        },
        "customerInfo": {
            "fullName": "Министерство обороны Российской Федерации", "shortName": "Минобороны России",
            "INN": "7704252261", "KPP": "770401001",
            "postAddress": "119160, г. Москва, ул. Знаменка, д. 19",
            "factAddress": "119160, г. Москва, ул. Знаменка, д. 19",
            "email": "mail@mil.ru", "contactPhone": "+74956881500",
            "contactPersonInfo": {"firstName": "Иван", "middleName": "Иванович", "lastName": "Иванов"},
            "customerAccountsDetailsInfo": {"customerAccountDetailsInfo": {
                "bankAccountNumber": "40105810700000010079", "bik": "044501002",
                "corrAccountNumber": "", "creditOrgName": "Отделение 1 Москва",
            }},
        },
        "participantInfo": {
            "legalEntityRFInfo": {
                "fullName": "Акционерное общество «Научно-производственное предприятие «Радар ммс»»",
                "shortName": "АО «НПП «Радар ммс»»", "INN": "7814027653", "KPP": "783450001",
                "postAddress": "197375, г. Санкт-Петербург, Приморский пр-т, д. 63",
                "factAddress": "197375, г. Санкт-Петербург, Приморский пр-т, д. 63",
                "email": "info@radar-mms.ru", "contactPhone": "+78124304040",
                "informationPersonsInfo": {"informationPersonInfo": {
                    "nameInfo": {"firstName": "Сергей", "middleName": "Михайлович", "lastName": "Нефедов"},
                    "INN": "781000000000", "position": "Заместитель генерального директора по экономике и финансам",
                }},
            },
        },
        "contractFinancingInfo": {"contractPriceInfo": {"price": "96393305.55"}},
        "contractConditionsInfo": {
            "contractGuaranteeInfo": {"part": "10", "amount": "9639330.56"},
            "deliveryPlaceInfo": {"byGARInfo": {"GARInfo": {"GARAddress": "г. Москва"}}},
            "contractExecutionTermsInfo": {"notRelativeTermsInfo": {"endDate": "2015-12-31"}},
        },
        "printFormFieldsInfo": {"additionalAgreementsInfo": {"additionalAgreementInfo": [
            {"ordinalNumberAdd": "1", "signDate": "2015-03-01"},
            {"ordinalNumberAdd": "2", "signDate": "2015-09-01"},
        ]}},
    }
}

EXPECTED_CONTRACT_LEGAL = {
    "purchase_number": "0173100004514000947",
    "placing_way": "Электронный аукцион",
    "subject": "Поставка корабельной гидрометеорологической станции «Характер-К»",
    "customer": {
        "full_name": "Министерство обороны Российской Федерации", "short_name": "Минобороны России",
        "inn": "7704252261", "kpp": "770401001",
        "post_address": "119160, г. Москва, ул. Знаменка, д. 19",
        "fact_address": "119160, г. Москва, ул. Знаменка, д. 19",
        "email": "mail@mil.ru", "phone": "+74956881500",
        "contact_person": "Иван Иванович Иванов",
        "bank_account": "40105810700000010079", "bik": "044501002",
        "corr_account": "", "bank_name": "Отделение 1 Москва",
    },
    "supplier": {
        "is_individual_entrepreneur": False,
        "full_name": "Акционерное общество «Научно-производственное предприятие «Радар ммс»»",
        "short_name": "АО «НПП «Радар ммс»»", "inn": "7814027653", "kpp": "783450001",
        "post_address": "197375, г. Санкт-Петербург, Приморский пр-т, д. 63",
        "fact_address": "197375, г. Санкт-Петербург, Приморский пр-т, д. 63",
        "email": "info@radar-mms.ru", "phone": "+78124304040",
        "director_name": "Нефедов Сергей Михайлович", "director_inn": "781000000000",
        "director_position": "Заместитель генерального директора по экономике и финансам",
        "bank_account": None, "bik": None, "corr_account": None, "bank_name": None,
    },
    "items": [
        {"name": "Станция гидрометеорологическая", "okpd2_code": "26.51.66.190",
         "okpd2_name": "Приборы гидрометеорологические", "ktru_code": "26.51.66.190-00000001",
         "ktru_name": "Станция", "quantity": "1", "unit": "штука",
         "price": "96393305.55", "sum": "96393305.55", "vat": "НДС 20%"},
        {"name": "Комплект ЗИП", "okpd2_code": "26.51.66.190",
         "okpd2_name": "Приборы гидрометеорологические", "ktru_code": None, "ktru_name": None,
         "quantity": "1", "unit": "комплект", "price": "0", "sum": "0", "vat": "НДС 20%"},
    ],
    "price_total": "96393305.55",
    "guarantee_part_pct": "10", "guarantee_amount": "9639330.56",
    "delivery_place": "г. Москва",
    "execution_end_date": "2015-12-31",
    "amendments": [
        {"ordinal": "1", "sign_date": "2015-03-01"},
        {"ordinal": "2", "sign_date": "2015-09-01"},
    ],
}

# ИП (individual-entrepreneur) supplier fixture — a structurally different
# subtree (individualPersonRFInfo, no separate director; the ИП *is* the
# signatory) that silently broke once already (see extract_contract_fields's
# own docstring comment on Цыганов Вадим Борисович). Also exercises
# additionalAgreementInfo as a bare DICT (single доп.соглашение), not a list —
# the other branch of that same isinstance coercion.
CONTRACT_XML_IP = {
    "cpElectronicContract": {
        "foundationInfo": {"purchaseNumber": "1463204748024000101"},
        "contractSubjectInfo": {
            "contractSubject": "Поставка детекторов беспилотных летательных аппаратов",
            "productsInfo": {"productsInfoElectronicContract": {"productInfo": {
                "name": "Детектор БПЛА «Булат» v.4",
                "OKPD2Info": {"OKPDCode": "26.30.50.000", "OKPDName": "Аппаратура радиолокационная"},
                "quantity": "184", "OKEIInfo": {"name": "штука"},
                "price": "88000.00", "sum": "16192000.00", "VATRateInfo": {"VATName": "Без НДС"},
            }}},
        },
        "participantInfo": {
            "individualPersonRFInfo": {
                "nameInfo": {"firstName": "Вадим", "middleName": "Борисович", "lastName": "Цыганов"},
                "INN": "504405055721",
                "postAddress": "г. Москва", "factAddress": "г. Москва",
                "email": "vipochka@bk.ru", "contactPhone": "+79262153015",
            },
        },
        "contractFinancingInfo": {"contractPriceInfo": {"price": "16192000.00"}},
        "printFormFieldsInfo": {"additionalAgreementsInfo": {
            "additionalAgreementInfo": {"ordinalNumberAdd": "1", "signDate": "2024-11-01"}
        }},
    }
}

EXPECTED_CONTRACT_IP = {
    "purchase_number": "1463204748024000101",
    "placing_way": None,
    "subject": "Поставка детекторов беспилотных летательных аппаратов",
    "customer": {
        "full_name": None, "short_name": None, "inn": None, "kpp": None,
        "post_address": None, "fact_address": None, "email": None, "phone": None,
        "contact_person": None,
        "bank_account": None, "bik": None, "corr_account": None, "bank_name": None,
    },
    "supplier": {
        "is_individual_entrepreneur": True,
        "full_name": "Цыганов Вадим Борисович", "short_name": None,
        "inn": "504405055721", "kpp": None,
        "post_address": "г. Москва", "fact_address": "г. Москва",
        "email": "vipochka@bk.ru", "phone": "+79262153015",
        "director_name": None, "director_inn": None, "director_position": None,
        "bank_account": None, "bik": None, "corr_account": None, "bank_name": None,
    },
    "items": [
        {"name": "Детектор БПЛА «Булат» v.4", "okpd2_code": "26.30.50.000",
         "okpd2_name": "Аппаратура радиолокационная", "ktru_code": None, "ktru_name": None,
         "quantity": "184", "unit": "штука", "price": "88000.00", "sum": "16192000.00", "vat": "Без НДС"},
    ],
    "price_total": "16192000.00",
    "guarantee_part_pct": None, "guarantee_amount": None,
    "delivery_place": None,
    "execution_end_date": None,
    "amendments": [{"ordinal": "1", "sign_date": "2024-11-01"}],
}

PAYMENT_XML = {
    "FAM_PaymOrderCr": {
        "AccDoc_DocDate": "2025-09-19",
        "BasicRequisites_PaySum": "694260-00",
        "Payer_INN": "5003008102", "Payer_Name": "УФК по г.Москве (ФГКУ ЦСООР Лидер)",
        "Payer_BIK": "004525988", "Payer_BankName": "ГУ Банка России по ЦФО",
        "Payer_CheckAcc": "03214643000000017300", "Payer_CorrAcc": "40102810545370000003",
        "Recip_INN": "5038189259", "Recip_Name": "ООО «ПОКРОВ»",
        "Recip_BIK": "044525225", "Recip_BankName": "ПАО Сбербанк",
        "Recip_CheckAcc": "40702810738150008739", "Recip_CorrAcc": "30101810400000000225",
        "DepInfo_PayPurpose": "Оплата по контракту ЕП 3-25 от 18.09.2025",
        "StmInfrmtn_ReestrNumGK": "1500300810225000152",
    }
}

EXPECTED_PAYMENT = {
    "doc_date": "2025-09-19", "sum": "694260-00",
    "payer_inn": "5003008102", "payer_name": "УФК по г.Москве (ФГКУ ЦСООР Лидер)",
    "payer_bik": "004525988", "payer_bank": "ГУ Банка России по ЦФО",
    "payer_account": "03214643000000017300", "payer_corr_account": "40102810545370000003",
    "recipient_inn": "5038189259", "recipient_name": "ООО «ПОКРОВ»",
    "recipient_bik": "044525225", "recipient_bank": "ПАО Сбербанк",
    "recipient_account": "40702810738150008739", "recipient_corr_account": "30101810400000000225",
    "purpose": "Оплата по контракту ЕП 3-25 от 18.09.2025",
    "linked_reg_number": "1500300810225000152",
}

# Synthetic (not a real document) but exact-format PIK-generated neustoika
# text — parse_pretenziya already had a real-document fixture; this sibling
# function had zero coverage despite being in the same file/era.
NEUSTOIKA_TEXT = """Требование об уплате неустойки №25-0044 от 15.03.2025

Номер контракта (ЕАСУЗ/ЕИС/Внутренний): 1770559633924000207

Дата заключения: 03.12.2024

Фиксированная сумма, руб.: 5 000,00
"""

EXPECTED_NEUSTOIKA = {
    "doc_number": "25-0044",
    "doc_date": "15.03.2025",
    "linked_reg_number": "1770559633924000207",
    "contract_date": "03.12.2024",
    "fine_amount": "5000,00",
}


def run() -> int:
    failures = []

    path = write_fixture("zakupki_old_layout.html", OLD_LAYOUT)
    result = parse_contract_card_html(path)
    price = result["fields"].get("Цена контракта")
    if price != "45 500 000,00 ₽":
        failures.append(f"OLD_LAYOUT: expected '45 500 000,00 ₽', got {price!r}")

    path = write_fixture("zakupki_new_layout.html", NEW_LAYOUT)
    result = parse_contract_card_html(path)
    price = result["fields"].get("Цена контракта")
    if price != "5 592 211 234,00":
        failures.append(f"NEW_LAYOUT: expected '5 592 211 234,00', got {price!r}")
    customer = result["fields"].get("Полное наименование заказчика")
    if customer != "Министерство промышленности и торговли Российской Федерации":
        failures.append(f"NEW_LAYOUT: section__title/info block broken, got {customer!r}")

    path = write_fixture("zakupki_no_price.html", NO_PRICE)
    result = parse_contract_card_html(path)
    price = result["fields"].get("Цена контракта")
    if price is not None:
        failures.append(f"NO_PRICE: expected no price key, got {price!r}")

    pret = parse_pretenziya(PRETENZIYA_TEXT)
    expected_pret = {
        "contract_date": "03.12.2024",
        "contract_number": "2427020100952000000020323/24208.4420029.11.044",
        "due_date": "02.06.2025",
        "actual_date": "19.08.2025",
        "fine_rub": "49127400.04",
        "stage_price_rub": "1145160840.00",
        "days_late": "78",
    }
    if pret != expected_pret:
        failures.append(f"PRETENZIYA: expected {expected_pret}, got {pret}")

    # parse_contract_subject — 3 real confirmed OKR-genre phrasings (2026-08-30)
    # plus a negative case (plain prose with no OKR/supply phrase -> None).
    subj_cases = [
        (
            "MIKROS-IZ",
            "Исполнитель по заданию Заказчика обязуется выполнить опытно-конструкторскую "
            "работу «Разработка и освоение серийного производства на отечественном "
            "предприятии электронного модуля измерения на основе сорбционно-емкостного "
            "датчика влажности и температуры», шифр «Микрос-ИЗ» (далее — Работа)",
            {"contract_type": "okr",
             "subject": "Разработка и освоение серийного производства на отечественном "
                        "предприятии электронного модуля измерения на основе "
                        "сорбционно-емкостного датчика влажности и температуры",
             "cipher": "Микрос-ИЗ"},
        ),
        (
            "REBUM-M",
            "Исполнитель по заданию Заказчика обязуется выполнить опытно-конструкторскую "
            "работу «Разработка базовых ресурсосберегающих и импортозамещающих технологий "
            "получения и применения современных композиционных материалов для производства "
            "базовых несущих конструкций и функциональных элементов бортовых "
            "радиоэлектронных комплексов нового поколения», шифр «Рэбум-м» (далее — Работа)",
            {"contract_type": "okr",
             "subject": "Разработка базовых ресурсосберегающих и импортозамещающих "
                        "технологий получения и применения современных композиционных "
                        "материалов для производства базовых несущих конструкций и "
                        "функциональных элементов бортовых радиоэлектронных комплексов "
                        "нового поколения",
             "cipher": "Рэбум-м"},
        ),
        (
            "MODUL-PEREGRUZ",
            "государственному контракту на выполнение опытно-конструкторской работы "
            "«Разработка базовой технологии создания унифицированных электронных модулей "
            "обработки сигналов сенсоров веса и движения для большегрузных автомобилей», "
            "шифр «Модуль-Перегруз»",
            {"contract_type": "okr",
             "subject": "Разработка базовой технологии создания унифицированных "
                        "электронных модулей обработки сигналов сенсоров веса и движения "
                        "для большегрузных автомобилей",
             "cipher": "Модуль-Перегруз"},
        ),
    ]
    for label, text, expected in subj_cases:
        got = parse_contract_subject(text)
        if got != expected:
            failures.append(f"CONTRACT_SUBJECT {label}: expected {expected}, got {got}")

    negative = parse_contract_subject(
        "Стороны договорились расторгнуть настоящий договор по соглашению сторон "
        "с 01.01.2025 без взаимных претензий."
    )
    if negative is not None:
        failures.append(f"CONTRACT_SUBJECT negative case: expected None, got {negative}")

    got = extract_contract_fields(CONTRACT_XML_LEGAL)
    if got != EXPECTED_CONTRACT_LEGAL:
        failures.append(f"CONTRACT_XML_LEGAL: expected {EXPECTED_CONTRACT_LEGAL}, got {got}")

    got = extract_contract_fields(CONTRACT_XML_IP)
    if got != EXPECTED_CONTRACT_IP:
        failures.append(f"CONTRACT_XML_IP: expected {EXPECTED_CONTRACT_IP}, got {got}")

    got = extract_payment_fields(PAYMENT_XML)
    if got != EXPECTED_PAYMENT:
        failures.append(f"PAYMENT_XML: expected {EXPECTED_PAYMENT}, got {got}")

    got = parse_neustoika(NEUSTOIKA_TEXT)
    if got != EXPECTED_NEUSTOIKA:
        failures.append(f"NEUSTOIKA: expected {EXPECTED_NEUSTOIKA}, got {got}")

    # Customer/supplier disambiguation -- added 2026-08-31 after a "по
    # Уставу" hit that looked like a plausible new director turned out to be
    # the customer's own "руководитель Учреждения" (see the note above
    # SIGNATORY_RE in mine_zakupki.py). Text drawn from real archived
    # contract preambles: quoted role labels, unquoted role labels, and a
    # "доверенности" (not "Устава") authority basis.
    SIGNATORY_QUOTED = (
        'Федеральное государственное бюджетное учреждение «Сахалинское УГМС» '
        '(ФГБУ «Сахалинское УГМС»), именуемое в дальнейшем «Заказчик», в лице '
        'начальника Ширнина Алексея Викторовича, действующего на основании '
        'Устава, с одной стороны, и Общество с ограниченной ответственностью '
        '«Радиофид Системы» (ООО «Радиофид Системы»), именуемое в дальнейшем '
        '«Поставщик», в лице генерального директора Незнамова Александра '
        'Васильевича, действующего на основании Устава, с другой стороны.'
    )
    got = find_signatories(SIGNATORY_QUOTED)
    expected = [
        {"name": "Ширнина Алексея Викторовича", "authority_basis": "Устава", "party": "customer"},
        {"name": "Незнамова Александра Васильевича", "authority_basis": "Устава", "party": "supplier"},
    ]
    if got != expected:
        failures.append(f"SIGNATORY_QUOTED: expected {expected}, got {got}")

    SIGNATORY_UNQUOTED_POA = (
        'Федеральное государственное казенное учреждение «Войсковая часть 35533», '
        'именуемое в дальнейшем Заказчик, в лице руководителя Учреждения Аравина '
        'Владислава Викторовича, действующего на основании Устава, с одной стороны, '
        'и Закрытое акционерное общество «НИИ СТТ», именуемое в дальнейшем '
        'Поставщик, в лице генерального директора Галкина Вадима Сергеевича, '
        'действующего на основании доверенности от 12.01.2015 № 3, с другой стороны.'
    )
    got = find_signatories(SIGNATORY_UNQUOTED_POA)
    expected = [
        {"name": "Аравина Владислава Викторовича", "authority_basis": "Устава", "party": "customer"},
        {"name": "Галкина Вадима Сергеевича", "authority_basis": "доверенности от 12.01.2015 № 3",
         "party": "supplier"},
    ]
    if got != expected:
        failures.append(f"SIGNATORY_UNQUOTED_POA: expected {expected}, got {got}")

    # An individual-entrepreneur supplier has no delegated authority to cite
    # ("действующего на основании ОГРНИП <n>") -- its role label sits right
    # after that clause instead of before it, unlike every other case above.
    # Confirmed live on ИП Цыганов's own contract (reg 1500300810225000152),
    # which this text is drawn from almost verbatim; first caught this
    # resolving to "customer" (wrong -- inherited the preceding "Заказчик"
    # label) before the self-declared-label-after-clause handling was added.
    SIGNATORY_IP_SUPPLIER = (
        'Федеральное государственное казенное учреждение «Центр по проведению '
        'спасательных операций особого риска «Лидер», именуемое в дальнейшем '
        '«Заказчик», в лице заместителя начальника Центра Кудякова Алексея '
        'Николаевича, действующего на основании доверенности от 09.06.2025 '
        '№ 110, с одной стороны, и индивидуальный предприниматель Цыганов '
        'Вадим Борисович, действующего на основании ОГРНИП 318500700040208, '
        'именуемое в дальнейшем «Поставщик», с другой стороны.'
    )
    got = find_signatories(SIGNATORY_IP_SUPPLIER)
    expected = [
        {"name": "Кудякова Алексея Николаевича", "authority_basis": "доверенности от 09.06.2025 № 110",
         "party": "customer"},
        {"name": "Цыганов Вадим Борисович", "authority_basis": "ОГРНИП 318500700040208", "party": "supplier"},
    ]
    if got != expected:
        failures.append(f"SIGNATORY_IP_SUPPLIER: expected {expected}, got {got}")

    # "далее именуемое «Роль»" word order (reversed from the usual "именуемое
    # в дальнейшем «Роль»") -- found live on an АО НПЦ «ЭЛВИС» Минпромторг
    # contract, reg 1770559633924000207 -- both mean "hereinafter", but the
    # reversed order needs its own alternative in PARTY_LABEL_RE.
    SIGNATORY_DALEE_WORD_ORDER = (
        'Министерство промышленности и торговли Российской Федерации, '
        'действующее от имени Российской Федерации, далее именуемое '
        '«Заказчик», в лице заместителя директора Гапонова Александра '
        'Алексеевича, действующего на основании доверенности от 30.09.2024 '
        '№ 01012409000045005801, с одной стороны, и Акционерное общество '
        'НПЦ «ЭЛВИС», далее именуемое «Исполнитель», в лице генерального '
        'директора Семилетова Антона Дмитриевича, действующего на основании '
        'Устава, с другой стороны.'
    )
    got = find_signatories(SIGNATORY_DALEE_WORD_ORDER)
    expected = [
        {"name": "Гапонова Александра Алексеевича",
         "authority_basis": "доверенности от 30.09.2024 № 01012409000045005801", "party": "customer"},
        {"name": "Семилетова Антона Дмитриевича", "authority_basis": "Устава", "party": "supplier"},
    ]
    if got != expected:
        failures.append(f"SIGNATORY_DALEE_WORD_ORDER: expected {expected}, got {got}")

    # A parenthetical gender-ending blob glued onto "именуем\w*" before the
    # required whitespace ("именуемое(ая,ый) в дальнейшем «Заказчик»") used
    # to break the \w*-then-\s+ match entirely -- costing BOTH signatories'
    # role labels in the whole document, not just this clause. Found live on
    # ООО «Гаскар Интеграция» доп.соглашение № 3, reg 2502412952426000007.
    SIGNATORY_GENDER_PAREN = (
        'МИНИСТЕРСТВО СТРОИТЕЛЬНОГО КОМПЛЕКСА МОСКОВСКОЙ ОБЛАСТИ, '
        'именуемое(ая,ый) в дальнейшем «Заказчик», в лице Заместителя '
        'министра Крылова Сергея Викторовича, действующего на основании '
        'Доверенности от 06.05.2026 №121, с одной стороны, и Общество с '
        'ограниченной ответственностью «Гаскар Интеграция», именуемое(ая,ый) '
        'в дальнейшем «Подрядчик», в лице Генерального директора Афанасьева '
        'Игоря Константиновича, действующего на основании Устава, с другой '
        'стороны.'
    )
    got = find_signatories(SIGNATORY_GENDER_PAREN)
    expected = [
        {"name": "Крылова Сергея Викторовича", "authority_basis": "Доверенности от 06.05.2026 №121",
         "party": "customer"},
        {"name": "Афанасьева Игоря Константиновича", "authority_basis": "Устава", "party": "supplier"},
    ]
    if got != expected:
        failures.append(f"SIGNATORY_GENDER_PAREN: expected {expected}, got {got}")

    # "Объекты закупки" (contract subject) — div-titled field the old
    # span-only selector skipped entirely.
    path = write_fixture("zakupki_object_long_tooltip.html", OBJECT_LONG_WITH_TOOLTIP)
    result = parse_contract_card_html(path)
    obj = result["fields"].get("Объекты закупки")
    expected_obj = ("Разработка технологии и конструкции ряда датчиков "
                    "микроперемещений и температуры с идентификацией на "
                    "поверхностных акустических волнах для применения в "
                    "дистанционных автоматизированных системах контроля и "
                    "мониторинга")
    if obj != expected_obj:
        failures.append(f"OBJECT_LONG_WITH_TOOLTIP: expected {expected_obj!r}, got {obj!r}")

    path = write_fixture("zakupki_object_short.html", OBJECT_SHORT_NO_TOOLTIP)
    result = parse_contract_card_html(path)
    obj = result["fields"].get("Объекты закупки")
    expected_obj = "Мобильная радиостанция Motorola DM4400 136-174 МГц 0-25 Вт 99 кан."
    if obj != expected_obj:
        failures.append(f"OBJECT_SHORT_NO_TOOLTIP: expected {expected_obj!r}, got {obj!r}")

    path = write_fixture("zakupki_object_multi_item.html", OBJECT_MULTI_ITEM)
    result = parse_contract_card_html(path)
    obj = result["fields"].get("Объекты закупки")
    if obj is not None:
        failures.append(f"OBJECT_MULTI_ITEM: expected no key (partial fragment "
                         f"should not be reported as the subject), got {obj!r}")

    path = write_fixture("zakupki_object_multi_item_substantive.html", OBJECT_MULTI_ITEM_SUBSTANTIVE)
    result = parse_contract_card_html(path)
    obj = result["fields"].get("Объекты закупки")
    expected_obj = ("поставка гидрометеостанций корабельных «Характер-К» с "
                    "монтажными и пусконаладочными работами для нужд "
                    "Минобороны России")
    if obj != expected_obj:
        failures.append(f"OBJECT_MULTI_ITEM_SUBSTANTIVE: expected {expected_obj!r}, got {obj!r}")

    path = write_fixture("zakupki_object_absent.html", OBJECT_ABSENT)
    result = parse_contract_card_html(path)
    obj = result["fields"].get("Объекты закупки")
    if obj is not None:
        failures.append(f"OBJECT_ABSENT: expected no key, got {obj!r}")

    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK: 21/21 zakupki parser fixtures passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
