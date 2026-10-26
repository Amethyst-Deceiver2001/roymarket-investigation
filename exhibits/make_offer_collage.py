"""Two captures of the ROY.MARKET supplier offer side by side, differences highlighted.

Left: Internet Archive capture of 22.08.2026 (full text). Right: our capture of 25.10.2026 (login wall).
Quoted lines are copied from the saved captures; run, then screenshot offer_collage.html with Firefox headless.

    ~/.venvs/roymarket311/bin/python exhibits/make_offer_collage.py
"""
import html
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "sources"
A = (SRC / "WAYBACK_20260822_roimarket-supplier-offer-decoded.html")
B = (SRC / "WEBCAPTURE_20261025_roimarket-ru-supplier-offer.html")
from bs4 import BeautifulSoup


def lines(p):
    s = BeautifulSoup(p.read_text(errors="ignore"), "html.parser")
    for t in s(["script", "style"]):
        t.decompose()
    return [" ".join(l.split()) for l in s.get_text("\n").split("\n") if l.strip()]


la, lb = lines(A), lines(B)
need_a = ["ООО «МПТМ» · ИНН 9714068459", "Скачать DOCX", "Полный агентский договор: подключение, карточки товаров, заказы, расчёты, отчётность, возвраты, ответственность и приложения.",
          "17. РЕКВИЗИТЫ АГЕНТА", "Общество с ограниченной ответственностью «МПТМ»", "ОГРН 1257700021468, ИНН 9714068459, КПП 771401001"]
need_b = ["Защищённый документ для Поставщиков", "Наименование Агента: ООО «****»", "ИНН: **********", "ОГРН: *************",
          "Юридический адрес и банковские реквизиты: скрыты до входа", "Войти и открыть полную редакцию",
          "Публично доступно только обезличенное описание. Полная редакция договора и реквизиты сторон открываются уполномоченному представителю Поставщика после входа, до подтверждения условий."]
for n in need_a:
    assert any(n in l for l in la), n
for n in need_b:
    assert any(n in l for l in lb), n
addr = next(l for l in la if l.startswith("Юридический и почтовый адрес"))
addr2 = la[la.index(addr) + 1]
e = html.escape


def mk(cls, label, ru):
    return f'<div class="row {cls}"><div class="lb">{e(label)}</div><div class="ru">{ru}</div></div>'


left = [
    mk("same", "Revision, date, status", "Редакция 3.0 · 01 августа 2026 года · Вступает в силу 01.08.2026"),
    mk("gone", "Page header: the operator named", '<mark>ООО «МПТМ» · ИНН 9714068459</mark>'),
    mk("gone", "What the page says it is", f'<mark>{e(need_a[2])}</mark>'),
    mk("gone", "Full text and downloads", "<mark>Скачать DOCX</mark> · <mark>Печать / PDF</mark> · Оглавление · 22 раздела"),
    mk("gone", "Section 17, the operator's details", f'{e(need_a[3])}<br><mark>{e(need_a[4])}</mark><br><mark>{e(addr)} {e(addr2)}</mark><br><mark>{e(need_a[5])}</mark>'),
]
right = [
    mk("same", "Revision, date, status", "Редакция 3.0 · 01 августа 2026 года · Вступает в силу 01.08.2026"),
    mk("new", "Page header: the operator named", "<em>no line</em>"),
    mk("new", "What the page says it is", f'<mark>{e(need_b[0])}</mark><br>{e(need_b[6])}'),
    mk("new", "Full text and downloads", "<mark>Войти и открыть полную редакцию</mark> · Оглавление · 3 раздела"),
    mk("new", "Section 17 becomes «Реквизиты в публичной версии»", '<mark>Наименование Агента: ООО «****»</mark><br><mark>ИНН: **********</mark><br><mark>КПП: *********</mark><br><mark>ОГРН: *************</mark><br><mark>Юридический адрес и банковские реквизиты: скрыты до входа</mark>'),
]
page = f"""<!doctype html><meta charset="utf-8"><title>Supplier offer, two captures</title>
<style>
body{{font:15px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;padding:28px 32px;background:#f6f4ef;color:#1d1d1b;width:1436px}}
h1{{font-size:24px;margin:0 0 4px}}p.sub{{margin:0 0 18px;color:#555;max-width:1100px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.col{{background:#fff;border:1px solid #cfcabd;border-radius:6px;padding:14px 16px}}
.col h2{{font-size:16px;margin:0 0 2px}}.col .d{{color:#666;font-size:13px;margin-bottom:12px}}
.row{{padding:9px 10px;margin-bottom:8px;border-radius:4px;border-left:4px solid #ccc;background:#faf9f6}}
.row.gone{{border-left-color:#b45309}}.row.new{{border-left-color:#1d4ed8}}
.lb{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#6b6b66;margin-bottom:3px}}
.ru{{font-size:14px}}mark{{background:#ffe08a;padding:0 2px}}.new mark{{background:#bcd4ff}}em{{color:#888}}
.foot{{margin-top:14px;font-size:12.5px;color:#555;max-width:1250px}}
.key span{{display:inline-block;padding:1px 8px;margin-right:8px;border-radius:3px;font-size:12px}}
</style>
<h1>The supplier offer, 22 August against 25 October 2026</h1>
<p class="sub">Same document, same revision 3.0 dated 1 August 2026. On 22 August the whole text was public and named the operator. By 25 October the page is a login wall and the operator's details are starred out.</p>
<p class="key"><span style="background:#ffe08a">on 22.08, gone by 25.10</span><span style="background:#bcd4ff">on 25.10, new</span></p>
<div class="grid">
<div class="col"><h2>22.08.2026</h2><div class="d">roimarket.ru/legal/supplier-offer, Internet Archive capture of 22.08.2026 09:13</div>{''.join(left)}</div>
<div class="col"><h2>25.10.2026</h2><div class="d">roimarket.ru/legal/supplier-offer, our own capture of 25.10.2026</div>{''.join(right)}</div>
</div>
<p class="foot">Quoted from the two saved page captures. «Защищённый документ для Поставщиков» is the page's own label; the starred fields are as printed.</p>"""
out = REPO / "exhibits" / "offer_collage.html"
out.write_text(page)
print(out)
