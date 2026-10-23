#!/usr/bin/env python3
"""Build every reader page from the committed registry and run scripts/check_reader_page.py over it.

This is the build CI could not do before: the story builder needed the Mac's Telegram database. It now runs with
--fixture (tests/fixtures/story_sources.json, written on the Mac by `build_story.py --export-fixture`); without that
file it still builds and checks the page, and says how many quotation checks it skipped. Pages go to exhibits/_check/
(gitignored) and the folder is removed afterwards. Pictures absent from this clone are left out, as on any clone
without data/sources/.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "exhibits" / "_check"
sys.path.insert(0, str(ROOT / "scripts"))
from check_reader_page import Registry, check  # noqa: E402

# (output file, builder and arguments): every reader page that goes out as a preview
PAGES = [
    ("chain_bulat.html", ["build_chain_view.py", "bulat"]),
    ("chain_kapyushon.html", ["build_chain_view.py", "kapyushon"]),
    ("company_ooo-trimiks.html", ["build_company_page.py", "ooo-trimiks"]),
    ("landing_preview.html", ["build_landing.py", "--preview"]),
    ("landing.html", ["build_landing.py"]),
    ("people_matrix.html", ["build_people_matrix.py"]),
    ("arkhangel.html", ["build_arkhangel_page.py"]),
    ("story_01.html", ["build_story.py", "--fixture"]),
]


def build_all() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    built = {}
    for name, (script, *args) in PAGES:
        out = OUT / name
        r = subprocess.run([sys.executable, str(ROOT / "exhibits" / script), *args, "--out", str(out)],
                           cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, f"{script} {' '.join(args)} failed:\n{r.stderr[-2000:]}"
        assert out.exists(), f"{script} wrote no {name}"
        built[name] = r.stdout
    return built


def test_every_reader_page_builds_and_passes_the_page_check():
    try:
        built = build_all()
        reg, failures = Registry(), []
        for name in built:
            errors, _ = check(OUT / name, reg)
            failures += [f"{name}: {e}" for e in errors]
        assert not failures, "page check failed:\n  " + "\n  ".join(failures)
        print("  " + built["story_01.html"].strip().splitlines()[-1])
    finally:
        shutil.rmtree(OUT, ignore_errors=True)


def test_checker_catches_what_it_is_for():
    """Fixtures for scripts/check_reader_page.py: each defect is caught, each allowed form passes."""
    OUT.mkdir(parents=True, exist_ok=True)
    reg = Registry()
    cases = {
        "cyrillic": ('<p>Фонд «Наша Правда»</p>', "english-first"),
        "alt": ('<img alt="Логотип" src="x.png">', "english-first"),
        "notation": ('<p>see s0389 and ooo-trimiks</p>', "notation"),
        "msg": ('<p>post (msg 10619, 04.08.2026)</p>', "notation"),
        "anchor": ('<p><a href="#n9">9</a></p>', "references"),
        "popover": ('<button popovertarget="nm-x">RU</button>', "references"),
        "dup": ('<span id="a"></span><span id="a"></span>', "references"),
        "sanction": ('<article><h3>X<small class="cyr" lang="ru">ООО «Тримикс»</small></h3>'
                     '<p><span class="rm-sanction">Sanctioned <b>UK</b></span></p></article>', "sanctions"),
        "tags": ('<div><p>x</p>', "tags"),
    }
    ok = ('<p>Nasha Pravda<button popovertarget="nm-np">RU</button></p><span popover id="nm-np">Фонд «Наша Правда»</span>'
          '<h3>3mx<small class="cyr" lang="ru">ООО «Тримикс»</small></h3>'
          '<section class="rm-sources"><ol><li id="n1">Сведения из ЕГРЮЛ</li></ol></section><p><a href="#n1">1</a></p>')
    try:
        for label, (body, kind) in cases.items():
            f = OUT / f"{label}.html"
            f.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")
            errors, _ = check(f, reg)
            assert any(e.startswith(kind) for e in errors), f"{label}: expected a {kind} error, got {errors}"
        f = OUT / "ok.html"
        f.write_text(f"<html><body>{ok}</body></html>", encoding="utf-8")
        errors, _ = check(f, reg)
        assert not errors, errors
    finally:
        shutil.rmtree(OUT, ignore_errors=True)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
