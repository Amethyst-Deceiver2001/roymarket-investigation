"""Shared post-processing for generated profile pages.

Free-text registry notes cite sources as a bare `s1234`; a published page
cites them as `[s1234]` (resolved in the page's Sources table). Applied to
rendered output, text nodes only -- never inside a tag or URL.
"""
import re

_BARE = re.compile(r"(?<![\[\w/._=-])s(\d{4})(?![\]\w])")


_CELL = re.compile(r"\s*s\d{4}\s*")


def bracket_source_ids_html(html):
    parts = re.split(r"(<[^>]*>)", html)
    # a text node that is nothing but the id is the Sources-table key cell
    return "".join(p if p.startswith("<") or _CELL.fullmatch(p) else _BARE.sub(r"[s\1]", p) for p in parts)


def bracket_source_ids_md(md):
    parts = re.split(r"(<[^>\s]+>|https?://\S+|`[^`]*`)", md)
    return "".join(p if i % 2 else _BARE.sub(r"[s\1]", p) for i, p in enumerate(parts))
