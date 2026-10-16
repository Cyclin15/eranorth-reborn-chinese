# -*- coding: utf-8 -*-
"""Merge all translation chunk outputs into unified mappings and validate globally.
Applies collisions_fix.json (from the dedup agent) when present."""
import json, os, re, glob, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
OUT = os.path.join(WORK, 'names', 'out')

FORBIDDEN = set(',:;#@*<>=/"\\\n\r\t')
VARIANT_MARKER = re.compile(r' \([A-Za-z0-9]{1,2}\)$')  # " (F)", " (M)", " (Wk)", " (An)"

def check_forbidden(v):
    return [c for c in v if c in FORBIDDEN]

problems = []

# --- 1. merge names ---
names = {}
for p in sorted(glob.glob(os.path.join(OUT, 'names_*.json'))):
    with open(p, encoding='utf-8-sig') as f:
        d = json.load(f)
    for k, v in d.items():
        if k in names:
            problems.append(f'dup key across chunks: {k} ({os.path.basename(p)})')
        if not isinstance(v, str) or not v.strip():
            problems.append(f'empty value: {k}')
            continue
        bad = check_forbidden(v)
        if bad:
            problems.append(f'forbidden chars {bad} in {k!r} -> {v!r}')
        if v != v.strip():
            problems.append(f'ws in {k!r} -> {v!r}')
        names[k] = v

# --- 2. apply collision fixes (if the dedup agent has produced them) ---
fix_path = os.path.join(WORK, 'collisions_fix.json')
if os.path.exists(fix_path):
    with open(fix_path, encoding='utf-8-sig') as f:
        fixes = json.load(f)
    for k, v in fixes.items():
        if k not in names:
            problems.append(f'fix key not in names: {k}')
            continue
        bad = check_forbidden(v)
        if bad:
            problems.append(f'fix forbidden chars in {k!r} -> {v!r}')
        names[k] = v
    print(f'applied {len(fixes)} collision fixes')
else:
    print('NOTE: collisions_fix.json not present yet')

# --- 2b. apply perk name fixes (missed by the original extraction) ---
for fix_name in ('perk_names_fix.json',):
    fp = os.path.join(WORK, fix_name)
    if os.path.exists(fp):
        with open(fp, encoding='utf-8-sig') as f:
            fixes = json.load(f)
        for k, v in fixes.items():
            # a leading '*' is part of the perk's literal name in the tdb
            # (e.g. '*Psychic, 0'), not a decoration marker
            vv = v[1:] if k.startswith('*') and v.startswith('*') else v
            bad = check_forbidden(vv)
            if bad:
                problems.append(f'{fix_name} forbidden chars in {k!r} -> {v!r}')
            names[k] = v
        perk_name_fix_keys = set(fixes)
        print(f'applied {len(fixes)} {fix_name} entries')
    else:
        print(f'NOTE: {fix_name} not present yet')

# --- 3. verify keys vs source chunk inputs (strip " || context" suffix) ---
src_keys = set()
for p in sorted(glob.glob(os.path.join(WORK, 'names', 'chunks', 'names_*.txt'))):
    with open(p, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line and not line.startswith('*'):
                src_keys.add(line.split(' || ')[0])
missing = src_keys - set(names)
extra = set(names) - src_keys - perk_name_fix_keys
if missing: problems.append(f'missing keys ({len(missing)}): {sorted(missing)[:10]}')
if extra: problems.append(f'extra keys ({len(extra)}): {sorted(extra)[:10]}')

# fix keys must all be real perks from the authoritative re-extraction
pr = json.load(open(os.path.join(WORK, 'perks_reextracted.json'), encoding='utf-8'))
real_perks = set(pr.keys())
pdfix = {}
pdfix_path = os.path.join(WORK, 'perk_desc_fix.json')
if os.path.exists(pdfix_path):
    pdfix = json.load(open(pdfix_path, encoding='utf-8-sig'))
bogus = (perk_name_fix_keys | set(pdfix)) - real_perks
if bogus: problems.append(f'fix keys not real perks: {sorted(bogus)[:10]}')

# --- 4. global value uniqueness ---
from collections import Counter
vc = Counter(names.values())
dups = {v: c for v, c in vc.items() if c > 1}
if dups:
    v2k = {}
    for k, v in names.items(): v2k.setdefault(v, []).append(k)
    for v in sorted(dups)[:25]:
        problems.append(f'value collision {v!r}: {v2k[v]}')

# --- 5. variant-marker preservation (short ASCII markers only) ---
for k, v in names.items():
    if VARIANT_MARKER.search(k) and not VARIANT_MARKER.search(v):
        problems.append(f'variant marker lost/changed: {k!r} -> {v!r}')

# --- 6. merge perkdesc & archdesc ---
def merge_simple(pattern):
    m = {}
    for p in sorted(glob.glob(os.path.join(OUT, pattern))):
        with open(p, encoding='utf-8-sig') as f:
            d = json.load(f)
        for k, v in d.items():
            if k in m: problems.append(f'dup in {pattern}: {k}')
            if isinstance(v, str) and v.strip():
                m[k] = v
            # empty values = source has no description; drop silently
    return m

perkdesc = merge_simple('perkdesc_*.json')
# apply perk description fixes
pfix = os.path.join(WORK, 'perk_desc_fix.json')
if os.path.exists(pfix):
    with open(pfix, encoding='utf-8-sig') as f:
        perkdesc.update(json.load(f))
    print(f'applied {len(json.load(open(pfix, encoding="utf-8-sig")))} perk_desc_fix entries')
else:
    print('NOTE: perk_desc_fix.json not present yet')
archdesc = merge_simple('archdesc_*.json')

# --- 7. verify perkdesc/archdesc coverage ---
def src_keys_of(pattern):
    """Key lines are 'KEY || value'; value may span continuation lines which
    contain no ' || ' separator (counts confirm: 71/289 key lines exactly)."""
    s = set()
    for p in sorted(glob.glob(os.path.join(WORK, 'names', 'chunks', pattern))):
        with open(p, encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if ' || ' in line:
                    s.add(line.split(' || ')[0])
    return s

psrc = src_keys_of('perkdesc_*.txt')
asrc = src_keys_of('archdesc_*.txt')
# archdesc: only keys whose source value was non-empty must be translated
asrc_nonempty = set()
for p in sorted(glob.glob(os.path.join(WORK, 'names', 'chunks', 'archdesc_*.txt'))):
    with open(p, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if ' || ' in line:
                k, _, v = line.partition(' || ')
                if v.strip():
                    asrc_nonempty.add(k)
if psrc - set(perkdesc): problems.append(f'perkdesc missing: {sorted(psrc - set(perkdesc))[:5]}')
if set(perkdesc) - psrc - set(pdfix): problems.append(f'perkdesc extra: {sorted(set(perkdesc) - psrc - set(pdfix))[:5]}')
if asrc_nonempty - set(archdesc): problems.append(f'archdesc missing (non-empty src): {sorted(asrc_nonempty - set(archdesc))[:5]}')
if set(archdesc) - asrc: problems.append(f'archdesc extra: {sorted(set(archdesc) - asrc)[:5]}')

print(f'names: {len(names)} entries (src {len(src_keys)}), distinct values: {len(set(names.values()))}')
print(f'perkdesc: {len(perkdesc)} (src {len(psrc)})')
print(f'archdesc: {len(archdesc)} (src {len(asrc)}, empties dropped)')
if problems:
    print(f'\n!!! {len(problems)} PROBLEMS:')
    for p in problems[:60]: print(' -', p)
    sys.exit(1)
print('ALL CHECKS PASSED')

with open(os.path.join(WORK, 'mapping_names.json'), 'w', encoding='utf-8') as f:
    json.dump(names, f, ensure_ascii=False, indent=0)
with open(os.path.join(WORK, 'mapping_perkdesc.json'), 'w', encoding='utf-8') as f:
    json.dump(perkdesc, f, ensure_ascii=False, indent=0)
with open(os.path.join(WORK, 'mapping_archdesc.json'), 'w', encoding='utf-8') as f:
    json.dump(archdesc, f, ensure_ascii=False, indent=0)
print('saved mapping_names.json / mapping_perkdesc.json / mapping_archdesc.json')
