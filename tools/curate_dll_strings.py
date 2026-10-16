# -*- coding: utf-8 -*-
"""Curate hardcoded UI strings from the decompiled source — v2.

Adds: any string used as a Find()/Load() argument ANYWHERE is excluded as a path,
even if the same line also contains a display sink. Strings must be >= 3 chars,
contain a letter, and not be pure format fragments.
"""
import re, json, io, os

SRC = r"C:\Users\ADMINI~1\AppData\Local\Temp\eran_decomp\Assembly-CSharp.decompiled.cs"
OUT = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n', 'dll_candidates.json')

src = io.open(SRC, encoding='utf-8', errors='replace').read()
lines = src.split('\n')

STR_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')

# strings used as path/lookup arguments anywhere
PATH_ARG = re.compile(
    r'(?:\.Find|\.FindChild|GameObject\.Find|FindGameObjectsWithTag|'
    r'Resources\.Load(?:<[^>]*>)?|LoadCard\(|LoadAvatar\(|LoadAudio|'
    r'GetComponent(?:InChildren)?(?:<[^>]*>)?\(|PlayerPrefs\.\w+|Directory\.\w+|File\.\w+|Path\.\w+|\.ContainsKey\(|'
    r'AddComponent(?:<[^>]*>)?\(|Instantiate\(|SetTrigger\(|Play\(|\.name\s*=)\s*\(\s*"((?:[^"\\\n]|\\.)*)"')
path_args = set()
for m in PATH_ARG.finditer(src):
    s = m.group(1)
    if s: path_args.add(s)
# also Find patterns written as Find("X")
for m in re.finditer(r'\.Find\("((?:[^"\\\n]|\\.)*)"\)', src):
    path_args.add(m.group(1))

DISPLAY_SINK = re.compile(
    r'\.text\s*=|DialogBox\.instance\.|\.SetText\(|\.SetTitle\(|SetDescription\(|SetTooltip\(|placeholder')
RISKY = re.compile(
    r'==\s*"|!=\s*"|case\s+"|\.Contains\(|ContainsKey\(|PlayerPrefs\.|Resources\.Load|'
    r'\.Find\(|Directory\.|File\.|Path\.|SendMessage|CompareTo\(|\.Equals\(|StartsWith|EndsWith|'
    r'\.Replace\(|\.Split\(|switch|\.tag|\.name|Sort\(|\?\?\s*"')

cands = {}
for i, line in enumerate(lines):
    if not DISPLAY_SINK.search(line):
        continue
    for m in STR_RE.finditer(line):
        s = m.group(1)
        if s.strip():
            cands.setdefault(s, []).append(i + 1)

def is_fragment(s):
    if len(s) < 3: return True
    if not re.search(r'[A-Za-z]{2}', s): return True
    # pure format/rich-text fragment: no letters outside tags/placeholders
    t = re.sub(r'\{[^}]*\}|<[^>]*>|\\n|[^\w\s]', '', s)
    if not re.search(r'[A-Za-z]{2}', t): return True
    return False

result = {}
for s, first in cands.items():
    if s in path_args:
        result[s] = {'verdict': 'path', 'sinks': first, 'risky': [], 'other': []}
        continue
    if is_fragment(s):
        result[s] = {'verdict': 'fragment', 'sinks': first, 'risky': [], 'other': []}
        continue
    rx = re.compile('"' + re.escape(s) + '"')
    sinks, risky, other = [], [], []
    for i, line in enumerate(lines):
        if rx.search(line):
            if DISPLAY_SINK.search(line): sinks.append(i + 1)
            elif RISKY.search(line): risky.append(i + 1)
            else: other.append(i + 1)
    verdict = 'safe' if not risky and not other else 'mixed'
    result[s] = {'verdict': verdict, 'sinks': sinks, 'risky': risky, 'other': other}

io.open(OUT, 'w', encoding='utf-8').write(json.dumps(result, ensure_ascii=False, indent=1))
from collections import Counter
c = Counter(v['verdict'] for v in result.values())
print(c)
print('--- SAFE (final) ---')
for s in sorted(k for k, v in result.items() if v['verdict'] == 'safe'):
    print(repr(s))
