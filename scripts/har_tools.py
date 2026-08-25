"""Load a HAR (HTTP Archive) capture, salvaging mid-write-truncated exports.

Browser devtools "Save all as HAR" occasionally writes a corrupted/truncated
file (observed with Chrome on large capture sessions). load_har() tries a
plain json.loads() first; on failure it finds every entry-start offset,
brace-matches (string-escape aware) to find the last fully-written entry,
truncates there, and reconstructs valid closing brackets.

Usage: python3 scripts/har_tools.py <path-to.har>   -- prints entry count
       from scripts.har_tools import load_har        -- for scripted use
"""
import json, re, sys

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

if __name__ == '__main__':
    path = sys.argv[1]
    d = load_har(path)
    entries = d['log']['entries']
    print(len(entries), 'entries loaded from', path)
    for p in d['log'].get('pages', []):
        print(' page:', p.get('title'))
