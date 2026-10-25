"""sanctions_entities_check.py: distinctive-word matching (no lists loaded)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sanctions_entities_check as se  # noqa: E402

assert se.words('Общество с ограниченной ответственностью "Тримикс"') == se.words("Limited Liability Company Trimix")
assert se.words("Limited Liability Company Unmanned Systems") == set()      # nothing distinctive: never a candidate
org = {"inn": "7802942873", "ogrn": "1", "name_ru": "ООО «Тримикс»"}
hit = {"list": "JP", "id": "x", "names": ["Limited Liability Company Trimix"], "text": "", "info": ""}
other = {"list": "JP", "id": "y", "names": ["Limited Liability Company Trimex Holdings"], "text": "", "info": ""}
byid = {"list": "CSL", "id": "z", "names": ["Unrelated"], "text": "INN 7802942873", "info": ""}
assert [h[0] for h in se.candidates(org, [hit, other, byid])] == ["name", "id"]
print("test_sanctions_entities_check: ok")
