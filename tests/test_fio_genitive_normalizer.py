#!/usr/bin/env python3
"""Regression fixtures for scripts/zakupki_signatory_diff.py's
normalize_fio_genitive — Russian legal boilerplate ("доверенности, выданной
ФИО") states signatory names in genitive case, and the token order varies by
customer template (Surname-Given-Patronymic vs Given-Patronymic-Surname).

No pytest dependency — plain assertions, run directly:
    python3 tests/test_fio_genitive_normalizer.py

All 27 cases here are real names pulled from actual zakupki_signatory_diff.py
output on 2026-08-29 — not synthetic examples — after the user flagged that
raw genitive names needed normalizing before being useful for dedup/matching
against people.json's nominative fio_ru values.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from zakupki_signatory_diff import normalize_fio_genitive  # noqa: E402

CASES = [
    ("Иванова Михаила Алексеевича", "Иванов Михаил Алексеевич"),
    ("Нефедова Сергея Михайловича", "Нефедов Сергей Михайлович"),
    ("Кудякова Алексея Николаевича", "Кудяков Алексей Николаевич"),
    ("Гапонова Александра Алексеевича", "Гапонов Александр Алексеевич"),
    ("Семилетова Антона Дмитриевича", "Семилетов Антон Дмитриевич"),
    ("Игоря Вячеславовича Бибичева", "Бибичев Игорь Вячеславович"),
    ("Юрия Алексеевича Максимова", "Максимов Юрий Алексеевич"),
    ("Петра Владимировича Гонтара", "Гонтар Пётр Владимирович"),
    ("Квака Дениса Сунчеровича", "Квак Денис Сунчерович"),
    ("Фадеева Игоря Анатольевича", "Фадеев Игорь Анатольевич"),
    ("Будаева Георгия Артуровича", "Будаев Георгий Артурович"),
    ("Мясникова Игоря Геннадьевича", "Мясников Игорь Геннадьевич"),
    ("Афанасьева Игоря Константиновича", "Афанасьев Игорь Константинович"),
    ("Бауера Петра Роландовича", "Бауер Пётр Роландович"),
    ("Крылова Сергея Викторовича", "Крылов Сергей Викторович"),
    ("Красильникова Павла Владимировича", "Красильников Павел Владимирович"),
    ("Чадаева Алексея Викторовича", "Чадаев Алексей Викторович"),
    ("Киселева Дмитрия Витальевича", "Киселев Дмитрий Витальевич"),
    ("Борисова Александра Сергеевича", "Борисов Александр Сергеевич"),
    ("Шаркова Евгения Александровича", "Шарков Евгений Александрович"),
    ("Саитова Рената Фаритовича", "Саитов Ренат Фаритович"),
    ("Горбатько Александра Владимировича", "Горбатько Александр Владимирович"),
    ("Мишакова Михаила Васильевича", "Мишаков Михаил Васильевич"),
    ("Анисимова Алексея Михайловича", "Анисимов Алексей Михайлович"),
    ("Абрамченкова Николая Григорьевича", "Абрамченков Николай Григорьевич"),
    ("Синельщикова Андрея Валентиновича", "Синельщиков Андрей Валентинович"),
]


def run() -> int:
    failures = []
    for raw, expected in CASES:
        got = normalize_fio_genitive(raw)
        if got != expected:
            failures.append(f"{raw!r}: expected {expected!r}, got {got!r}")
    if failures:
        print(f"FAILED ({len(failures)}/{len(CASES)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"OK: {len(CASES)}/{len(CASES)} FIO genitive-normalization fixtures passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
