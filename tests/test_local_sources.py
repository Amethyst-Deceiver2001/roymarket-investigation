"""local_sources: add is idempotent and numbers L-ids; merge rewrites quoted L-ids to the s-id of the same path,
only after the file's sha256 matches, and leaves anything not yet inventoried alone."""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import local_sources as ls  # noqa: E402


def make_repo(tmp: Path):
    tmp = tmp.resolve()   # macOS temp dirs sit behind a /var -> /private/var symlink
    (tmp / "data" / "registry").mkdir(parents=True)
    (tmp / "data" / "sources").mkdir(parents=True)
    (tmp / "notes").mkdir()
    ls.REPO, ls.REG = tmp, tmp / "data" / "registry"
    ls.SOURCES_JSON, ls.IDS_JSON = ls.REG / "sources.json", ls.REG / "_source_ids.json"
    ls.save_sources([{"id": "s0001", "path": "data/sources/old.pdf", "sha256": "0" * 64}])
    ls.IDS_JSON.write_text(json.dumps({"data/sources/old.pdf": "s0001"}))


def test_add_numbers_and_is_idempotent():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        make_repo(tmp)
        for name, body in (("a.txt", "first"), ("b.txt", "second")):
            (tmp / "data" / "sources" / name).write_text(body)
        ls.citation_for = lambda rec: ("Title " + rec["path"][-5:], None)
        ns = lambda p: SimpleNamespace(path=p, url=None, title=None, public_url=None, captured=None, inn=None)  # noqa: E731
        ls.cmd_add(ns("data/sources/a.txt"))
        ls.cmd_add(ns("data/sources/b.txt"))
        ls.cmd_add(ns("data/sources/a.txt"))   # same bytes: no new id
        rows = ls.load_sources()
        local = [r["id"] for r in rows if r.get("_local")]
        assert local == ["L0001", "L0002"], local
        assert all(r["sha256"] and r["title"] for r in rows if r.get("_local"))


def test_merge_rewrites_only_what_is_ready():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        make_repo(tmp)
        for name, body in (("a.txt", "first"), ("b.txt", "second")):
            (tmp / "data" / "sources" / name).write_text(body)
        ls.citation_for = lambda rec: ("T", None)
        ns = lambda p: SimpleNamespace(path=p, url=None, title=None, public_url=None, captured=None, inn=None)  # noqa: E731
        ls.cmd_add(ns("data/sources/a.txt"))
        ls.cmd_add(ns("data/sources/b.txt"))
        (ls.REG / "entities.json").write_text(json.dumps([{"slug": "x", "source_id": "L0001", "other": ["L0002", "s0001"]}]))
        # only a.txt has been inventoried on the "archive" machine
        ls.IDS_JSON.write_text(json.dumps({"data/sources/old.pdf": "s0001", "data/sources/a.txt": "s0777"}))
        ls.cmd_merge(SimpleNamespace(apply=False))
        assert "L0001" in (ls.REG / "entities.json").read_text(), "dry run must not write"
        ls.cmd_merge(SimpleNamespace(apply=True))
        got = json.loads((ls.REG / "entities.json").read_text())[0]
        assert got["source_id"] == "s0777" and got["other"] == ["L0002", "s0001"], got
        assert [r["id"] for r in ls.load_sources()] == ["s0001", "L0002"]
        # a changed file is refused
        ls.IDS_JSON.write_text(json.dumps({"data/sources/b.txt": "s0888"}))
        (tmp / "data" / "sources" / "b.txt").write_text("tampered")
        ls.cmd_merge(SimpleNamespace(apply=True))
        assert "L0002" in (ls.REG / "entities.json").read_text()


if __name__ == "__main__":
    test_add_numbers_and_is_idempotent()
    test_merge_rewrites_only_what_is_ready()
    print("ok: local_sources fixtures pass")
