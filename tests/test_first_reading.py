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

# Unit checks on the two labels a real inbox (02.10.2026) got wrong.
sys.path.insert(0, str(REPO / "scripts"))
import first_reading as fr  # noqa: E402
egrul_text = ("Сведения о лицензиях\n  деятельность по техническому обслуживанию шифровальных средств "
              "(за исключением случая, если ...)\n")
diffs, _ = fr.read_egrul(egrul_text, {})
assert not any(d.startswith("Status:") for d in diffs), diffs        # boilerplate is not a status
diffs, _ = fr.read_egrul(egrul_text + "Сведения о прекращении\n  Способ прекращения  Исключение юридического "
                         "лица из ЕГРЮЛ\n", {})
assert any(d.startswith("Status:") for d in diffs), diffs
commercial = ("Единица измерения  Тыс. руб.\nВыручка  2110  256 862  231 712\n"
              "Чистая прибыль (убыток)  2400  2 851 156  (493 725)\n"
              "Всего поступило средств  6200  500 000  -\nВсего использовано средств  6300  (-)  (-)\n")
diffs, _ = fr.read_bfo(commercial, {}, "2022")
assert any(d.startswith("Targeted funds in a commercial filing") for d in diffs), diffs
assert not any(d.startswith("Non-profit filing") for d in diffs), diffs
dashes = commercial.replace("500 000", "-")                            # an empty targeted-funds page says nothing
diffs, _ = fr.read_bfo(dashes, {}, "2022")
assert not any("funds" in d.lower() for d in diffs if not d.startswith("Accounts")), diffs
print("first_reading fixtures pass")
