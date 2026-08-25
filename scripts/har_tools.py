"""Load and query a HAR (HTTP Archive) capture, salvaging mid-write-truncated
exports, without dumping full response bodies into the caller's context.

Browser devtools "Save all as HAR" occasionally writes a corrupted/truncated
file (observed with Chrome on large capture sessions). load_har() tries a
plain json.loads() first; on failure it finds every entry-start offset,
brace-matches (string-escape aware) to find the last fully-written entry,
truncates there, and reconstructs valid closing brackets.

CLI subcommands (designed so big payloads land in a file, not stdout --
run these yourself for a large .har and hand Claude the resulting file
path/grep hits instead of pasting raw output):

  list <har> [--filter SUBSTR] [--type TYPE]
      Compact one-line-per-entry summary: index, method, status, size, url.
      --filter matches the url substring; --type matches the mimeType
      (e.g. 'json', 'html'). No response bodies are printed.

  extract <har> <index> [--out FILE]
      Writes ONE entry's decoded response body to FILE (default: a
      predictable path under /tmp derived from index+url). Prints only the
      file path and byte count -- read the file separately (Read tool with
      offset/limit, or grep) instead of catting it into a prompt.

  grep <har> <pattern> [--field url|body] [--type TYPE]
      Regex-searches response bodies (or urls) across all entries and
      prints only index/url/byte-offset/short-context per match -- not
      full matches or full bodies. Use `extract` on the indices that look
      relevant to pull the full body to a file.

Usage: python3 scripts/har_tools.py <path-to.har>          -- entry count only
       python3 scripts/har_tools.py list big.har --type json
       python3 scripts/har_tools.py extract big.har 42 --out /tmp/entry42.json
       python3 scripts/har_tools.py grep big.har "fetchReviews"
       from scripts.har_tools import load_har                -- for scripted use
"""
import argparse, base64, json, os, re, sys

def load_har(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        data = f.read()
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        pass
    # salvage: find entry starts, brace-match, truncate at last good one
    starts = []
    for m in re.finditer(r'\n      \{\n        "_initiator"', data):
        starts.append(m.start()+7)
    if not starts:
        for m in re.finditer(r'\n      \{\n        "startedDateTime"', data):
            starts.append(m.start()+7)
    def find_matching_brace(s, start):
        depth = 0; i = start; in_str = False; esc = False; n = len(s)
        while i < n:
            c = s[i]
            if in_str:
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == '"': in_str = False
            else:
                if c == '"': in_str = True
                elif c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0: return i
            i += 1
        return -1
    last_good_end = None
    for s in starts:
        end = find_matching_brace(data, s)
        if end == -1:
            break
        last_good_end = end
    if last_good_end is None:
        raise ValueError("no complete entries found")
    salvage = data[:last_good_end+1] + '\n    ]\n  }\n}\n'
    return json.loads(salvage)


def _entry_body_text(entry):
    content = entry.get('response', {}).get('content', {})
    text = content.get('text', '')
    if content.get('encoding') == 'base64':
        try:
            return base64.b64decode(text).decode('utf-8', errors='replace')
        except Exception:
            return ''
    return text


def cmd_list(args):
    d = load_har(args.har)
    entries = d['log']['entries']
    for i, e in enumerate(entries):
        url = e.get('request', {}).get('url', '')
        if args.filter and args.filter.lower() not in url.lower():
            continue
        mime = e.get('response', {}).get('content', {}).get('mimeType', '')
        if args.type and args.type.lower() not in mime.lower():
            continue
        method = e.get('request', {}).get('method', '?')
        status = e.get('response', {}).get('status', '?')
        size = e.get('response', {}).get('content', {}).get('size', 0)
        print(f"[{i}] {status} {method} {size:>8}B {mime:<20} {url}")


def cmd_extract(args):
    d = load_har(args.har)
    entries = d['log']['entries']
    if args.index >= len(entries):
        print(f"index {args.index} out of range (0..{len(entries)-1})", file=sys.stderr)
        sys.exit(1)
    e = entries[args.index]
    body = _entry_body_text(e)
    out = args.out
    if not out:
        url = e.get('request', {}).get('url', 'entry')
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', url)[-60:]
        out = f"/tmp/har_extract_{args.index}_{slug}.txt"
    with open(out, 'w', encoding='utf-8') as f:
        f.write(body)
    print(f"wrote {len(body)} bytes to {out}")
    print(f"url: {e.get('request', {}).get('url', '')}")


def cmd_grep(args):
    d = load_har(args.har)
    entries = d['log']['entries']
    pat = re.compile(args.pattern, re.IGNORECASE)
    hits = 0
    for i, e in enumerate(entries):
        mime = e.get('response', {}).get('content', {}).get('mimeType', '')
        if args.type and args.type.lower() not in mime.lower():
            continue
        url = e.get('request', {}).get('url', '')
        haystack = url if args.field == 'url' else _entry_body_text(e)
        m = pat.search(haystack)
        if m:
            hits += 1
            start = max(0, m.start() - 40)
            end = min(len(haystack), m.end() + 40)
            context = haystack[start:end].replace('\n', ' ')
            print(f"[{i}] {url}\n     ...{context}...")
    if not hits:
        print("no matches")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd')

    p_list = sub.add_parser('list')
    p_list.add_argument('har')
    p_list.add_argument('--filter', default=None)
    p_list.add_argument('--type', default=None)

    p_extract = sub.add_parser('extract')
    p_extract.add_argument('har')
    p_extract.add_argument('index', type=int)
    p_extract.add_argument('--out', default=None)

    p_grep = sub.add_parser('grep')
    p_grep.add_argument('har')
    p_grep.add_argument('pattern')
    p_grep.add_argument('--field', choices=['url', 'body'], default='body')
    p_grep.add_argument('--type', default=None)

    args, remainder = parser.parse_known_args()

    if args.cmd == 'list':
        cmd_list(args)
    elif args.cmd == 'extract':
        cmd_extract(args)
    elif args.cmd == 'grep':
        cmd_grep(args)
    else:
        # backward-compatible bare invocation: python3 har_tools.py <path.har>
        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit(1)
        path = sys.argv[1]
        d = load_har(path)
        entries = d['log']['entries']
        print(len(entries), 'entries loaded from', path)
        for p in d['log'].get('pages', []):
            print(' page:', p.get('title'))
