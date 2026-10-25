"""eu_cellar.py: the entry cut and the name fold (no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import eu_cellar as ec  # noqa: E402

T = ("... Active spokesperson. 29.4.2014 13. Denys PUSHYLIN Born in Makiivka One of the leaders. 29.4.2014 "
     "14. Tsyplakov Sergey GENNADEVICH One of the leaders of the militia. 29.4.2014 15. Igor STRELKOV Staff of the GRU. 29.4.2014")
got = ec.entries(T, ["Pushylin"])
assert len(got) == 1 and got[0].startswith("13. Denys PUSHYLIN") and got[0].endswith("29.4.2014"), got
assert "Tsyplakov" not in got[0]

# a name spelled with ё or in capitals is found; two spellings of one entry give one cut
T2 = "x 1.1.2020 5. Пётр ПЕТРОВ born. 1.1.2021"
assert len(ec.entries(T2, ["петров", "ПЕТРОВ"])) == 1
assert len(ec.entries(T2, ["Петр Петров"])) == 1   # ё is folded to е on both sides
assert len(ec.entries(T2, ["Петров Пётр"])) == 0   # word order is not folded; the caller lists spellings
assert ec.fold("Пётр") == "петр"
assert ec.title_of("L_2014126EN COUNCIL IMPLEMENTING REGULATION (EU) No 433/2014 of 28 April 2014 implementing").endswith("28 April 2014")
print("test_eu_cellar: ok")
