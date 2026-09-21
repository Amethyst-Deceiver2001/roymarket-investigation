"""Shared post-processing for generated profile pages.

Free-text registry notes cite sources as a bare `s1234`; a published page
cites them as `[s1234]` (resolved in the page's Sources table). Applied to
rendered output, text nodes only -- never inside a tag or URL.

On HTML output, when `src_by_id` is given, each bracketed id also becomes a
native-popover button (see .cite / .cite-pop in profile.css) so a reader can
check a claim's locator/dates inline without leaving the paragraph -- still
resolved in the Sources table too, this is additive. Progressive enhancement
only: Popover is Baseline "Newly available", not "Widely available", and this
is a read-only published page (no polyfill budget to spend on it) -- where
unsupported, the button is simply inert and the bracketed id still reads
fine as plain text, same as before this existed.
"""
import html as _html
import re

_BARE = re.compile(r"(?<![\[\w/._=-])s(\d{4})(?![\]\w])")


_CELL = re.compile(r"\s*s\d{4}\s*")

# company_profile.html.jinja2 emits most citations pre-bracketed, as
# <span class="id">[sNNNN]</span> (financials, contracts, litigation,
# principals, open questions, ...) -- the bare-id pass above never sees
# these since they're already wrapped. Match that exact span so those
# citations become popovers too, not just leftover bare `sNNNN` mentions
# in free-text fields.
_SPAN_ID = re.compile(r'<span class="id">\[s(\d{4})\]</span>')


def _source_locator(s):
    return s.get("url") or (s.get("path") or "").rsplit("/", 1)[-1] or "—"


def popover_html(sid, s):
    loc = _html.escape(_source_locator(s))
    meta_bits = [s.get("type")]
    if s.get("captured_date"):
        meta_bits.append(f"captured {s['captured_date']}")
    if s.get("as_of"):
        meta_bits.append(f"as of {s['as_of']}")
    meta = _html.escape(" · ".join(b for b in meta_bits if b))
    return (
        f'<div id="cite-{sid}" popover class="cite-pop">'
        f'<p class="cite-pop-id">{sid}</p>'
        f'<p class="cite-pop-loc">{loc}</p>'
        f'<p class="cite-pop-meta">{meta}</p>'
        f'</div>'
    )


def bracket_source_ids_html(html, src_by_id=None):
    parts = re.split(r"(<[^>]*>)", html)
    cited = set()

    def repl(m):
        sid = f"s{m.group(1)}"
        if src_by_id is not None and sid in src_by_id:
            cited.add(sid)
            return f'<button type="button" class="cite" popovertarget="cite-{sid}">[{sid}]</button>'
        return f"[{sid}]"

    # a text node that is nothing but the id is the Sources-table key cell
    out = "".join(p if p.startswith("<") or _CELL.fullmatch(p) else _BARE.sub(repl, p) for p in parts)

    def span_repl(m):
        sid = f"s{m.group(1)}"
        if src_by_id is not None and sid in src_by_id:
            cited.add(sid)
            return f'<button type="button" class="cite" popovertarget="cite-{sid}">[{sid}]</button>'
        return m.group(0)

    out = _SPAN_ID.sub(span_repl, out)
    if cited:
        pops = "".join(popover_html(sid, src_by_id[sid]) for sid in sorted(cited))
        out = out.replace("</body>", pops + "</body>", 1) if "</body>" in out else out + pops
    return out


def bracket_source_ids_md(md):
    parts = re.split(r"(<[^>\s]+>|https?://\S+|`[^`]*`)", md)
    return "".join(p if i % 2 else _BARE.sub(r"[s\1]", p) for i, p in enumerate(parts))
