#!/usr/bin/env python3
"""Fixtures for scripts/first_reading.py's read half: a synthetic ЕГРЮЛ extract
and БФО page laid out like `pdftotext -layout` output, checked against
ООО «МПТМ»'s registry record. Run: python3 tests/test_first_reading.py"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
out = subprocess.run([sys.executable, str(REPO / "scripts/first_reading.py"), "read",
                      "--inbox", str(REPO / "tests/fixtures/first_reading")],
                     capture_output=True, text=True, check=True).stdout
expect = [
    "Director: extract names Иванов Пётр Сергеевич",       # changed director, ё kept
    "Charter capital: extract 250,000 ₽",                   # changed capital
    "2025 revenue: filing 1,500,000 ₽, registry 1,002,000 ₽",  # тыс. руб. scaled
    "Nothing here is in the registry",
]
absent = ["Main ОКВЭД", "Founders: the extract now withholds"]  # unchanged: no false alarm
bad = [s for s in expect if s not in out] + [s for s in absent if s in out]
if bad:
    print("FAIL:", bad); print(out); sys.exit(1)
print("first_reading fixtures pass")
