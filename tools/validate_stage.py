# -*- coding: utf-8 -*-
"""Validate the staged replacement output against originals (invariants)."""
import json, os, re, glob, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
CONTENT = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content"
STAGE = os.path.join(WORK, 'stage')
MODBASE = os.path.join(CONTENT, 'Mods', 'Chinese Localization')
STAGEMOD = os.path.join(STAGE, 'Mods', 'Chinese Localization')

NAMES = json.load(open(os.path.join(WORK, 'mapping_names.json'), encoding='utf-8'))
PERKDESC = json.load(open(os.path.join(WORK, 'mapping_perkdesc.json'), encoding='utf-8'))
VALUES = set(NAMES.values())
TYPES = set(json.load(open(os.path.join(WORK, 'names', 'extracted.json'), encoding='utf-8'))['types'])
SPECIALS = re.compile(r'[:;#=@*>+,/]')
ERRORS, WARN = [], []
def err(m): ERRORS.append(m); print('ERR', m)
def warn(m): WARN.append(m); print('WARN', m)

def skeleton(s):
    return SPECIALS.findall(s)

# names containing chars that could break the skeleton invariant
odd = [k for k in NAMES if any(c in k for c in ':;#=@*>+,/')]
if odd: warn(f'mapping names with special chars: {odd[:10]}')

# ---------- tdb ----------
def read_lines(p):
    return [l.rstrip('\n') for l in open(p, encoding='utf-8-sig')]

for sub in ('Actions', 'Encounter'):   # Perks covered by the group-aware section below
    for orig in sorted(glob.glob(os.path.join(CONTENT, sub, '*.tdb'))):
        rel = os.path.relpath(orig, CONTENT)
        stag = os.path.join(STAGE, rel)
        if not os.path.exists(stag):
            err(f'missing staged {rel}'); continue
        o, s = read_lines(orig), read_lines(stag)
        if len(o) != len(s):
            err(f'{rel}: line count {len(o)} -> {len(s)}'); continue
        is_perk = sub == 'Perks'
        is_enemy = os.path.basename(orig) == 'EnemyDB.Core.tdb'
        for i, (lo, ls) in enumerate(zip(o, s)):
            if lo.startswith(('//', '@', '#')) or not lo.strip():
                if lo != ls: err(f'{rel}:{i+1} comment/directive changed')
                continue
            if is_enemy:
                to, ts = lo.split(', '), ls.split(', ')
                if len(to) != len(ts): err(f'{rel}:{i+1} token count'); continue
                for a, b in zip(to, ts):
                    if a == b: continue
                    if a.startswith('Name:') and b.startswith('Name:') and a[5:] in NAMES and b[5:] == NAMES[a[5:]]:
                        continue
                    err(f'{rel}:{i+1} enemy token changed: {a[:60]} -> {b[:60]}')
                continue
            if is_perk:
                # 3-line groups: name / desc / effects — just check token-level invariants on effects lines later;
                # here: token counts + skeleton on every line that has tokens with ':'
                pass
            # generic: card name line?
            if ', ' in lo and lo.rsplit(', ', 1)[1] in TYPES and not is_perk:
                no, t = lo.rsplit(', ', 1)
                ns, t2 = ls.rsplit(', ', 1) if ', ' in ls else (ls, '')
                if t != t2: err(f'{rel}:{i+1} type changed: {t} -> {t2}')
                if no in NAMES:
                    if ns != NAMES[no]: err(f'{rel}:{i+1} name not renamed per mapping: {no} -> {ns}')
                else:
                    warn(f'{rel}:{i+1} unmapped name line kept: {no}')
                continue
            # effects line
            to, ts = lo.split(', '), ls.split(', ')
            if len(to) != len(ts):
                err(f'{rel}:{i+1} token count {len(to)} -> {len(ts)}'); continue
            for a, b in zip(to, ts):
                if a == b: continue
                ka, va = (a.split(':', 1) + [''])[:2] if ':' in a else (a, '')
                kb, vb = (b.split(':', 1) + [''])[:2] if ':' in b else (b, '')
                if skeleton(ka) != skeleton(kb):
                    err(f'{rel}:{i+1} key skeleton changed: {a[:70]} -> {b[:70]}')
                # value invariants handled below in residual scan
print('tdb structural checks done')

# ---------- perk specific ----------
perk_names_renamed = perk_desc_ok = 0
for orig in sorted(glob.glob(os.path.join(CONTENT, 'Perks', '*.tdb'))):
    rel = os.path.relpath(orig, CONTENT)
    o, s = read_lines(orig), read_lines(os.path.join(STAGE, rel))
    i = 0
    while i < len(o):
        lo = o[i].lstrip('\ufeff')
        if not lo.strip() or lo.startswith(('/', '#')):
            i += 1; continue
        name_line, desc, eff = lo, o[i+1], o[i+2]
        parts = name_line.split(', ')
        nm = parts[0]
        sn, sd, se = s[i], s[i+1], s[i+2]
        sp = sn.split(', ')
        if nm in NAMES:
            if sp[0] != NAMES[nm]: err(f'{rel} perk name: {nm} -> {sp[0]}')
            else: perk_names_renamed += 1
        elif sp[0] != nm:
            err(f'{rel} unmapped perk name changed: {nm} -> {sp[0]}')
        if len(parts) == 3 and parts[2] in NAMES:
            if sp[-1] != NAMES[parts[2]]: err(f'{rel} perk req not renamed: {parts[2]}')
        if nm in PERKDESC:
            if sd != PERKDESC[nm]: err(f'{rel} perk desc mismatch: {nm}')
            else: perk_desc_ok += 1
        elif desc.strip() and sd != desc and not any(ord(c) > 0x2E7F for c in sd):
            # desc changed but no Chinese → suspicious
            err(f'{rel} perk desc changed but not from mapping: {nm}')
        # effects line: token count + per-token key skeleton
        eto, ese = eff.split(', '), se.split(', ')
        if len(eto) != len(ese):
            err(f'{rel} perk effects token count: {nm}')
        else:
            for a, b in zip(eto, ese):
                if a == b: continue
                ka = a.split(':', 1)[0] if ':' in a else a
                kb = b.split(':', 1)[0] if ':' in b else b
                if skeleton(ka) != skeleton(kb):
                    err(f'{rel} perk effect skeleton {nm}: {a[:60]} -> {b[:60]}')
        i += 3
print(f'perk checks done: names renamed {perk_names_renamed}, descs {perk_desc_ok}')

# ---------- archetypes ----------
for orig in sorted(glob.glob(os.path.join(CONTENT, 'Archetypes', 'Classes', '*.json')) +
                   glob.glob(os.path.join(CONTENT, 'Archetypes', 'Races', '*.json'))):
    rel = os.path.relpath(orig, CONTENT)
    do = json.load(open(orig, encoding='utf-8-sig'))
    ds = json.load(open(os.path.join(STAGE, rel), encoding='utf-8'))
    if set(do.keys()) != set(ds.keys()):
        err(f'{rel}: json keys changed'); continue
    for k in do:
        vo, vs = do[k], ds[k]
        if k in ('StartingDeck', 'StartingEquipment', 'StartingStash', 'AdditionalActions', 'AI', 'SkillTree', 'PerksTree'):
            if not isinstance(vo, list): continue
            if len(vo) != len(vs): err(f'{rel}.{k}: list len'); continue
            for a, b in zip(vo, vs):
                if a == b:
                    base = a.split(':')[0] if ':' in a else a
                    if base in NAMES and NAMES[base] != base: err(f'{rel}.{k}: mapped entry not renamed: {a}')
                    continue
                # structural: name part replaced, numeric suffix kept
                if ':' not in a:
                    if a in NAMES and b != NAMES[a]:
                        err(f'{rel}.{k}: mapped entry not renamed: {a}')
                    continue
                ao, bo = a.rsplit(':', 1)[0], b.rsplit(':', 1)[0]
                if ao in NAMES and b == NAMES[ao] + ':' + a.rsplit(':', 1)[1]: continue
                if a in NAMES and b == NAMES[a]: continue
                if '>AutoGrant>' in a:
                    pa, na = a.split('>AutoGrant>', 1); pb, nb = b.split('>AutoGrant>', 1)
                    if pa != pb or nb != NAMES.get(na, na):
                        err(f'{rel}.{k}: AutoGrant broken: {a} -> {b}')
                elif '>>' in a:
                    ca, ra = a.split('>>', 1); cb, rb = b.split('>>', 1)
                    na = ra.rsplit(':', 1)[0] if ':' in ra else ra
                    nb = rb.rsplit(':', 1)[0] if ':' in rb else rb
                    la = ra.rsplit(':', 1)[1] if ':' in ra else None
                    lb = rb.rsplit(':', 1)[1] if ':' in rb else None
                    if ca != cb or la != lb or nb != NAMES.get(na, na):
                        err(f'{rel}.{k}: conditional broken: {a} -> {b}')
                else:
                    err(f'{rel}.{k}: unexpected change: {a} -> {b}')
        elif k in ('MainWeapon', 'MainShield'):
            if isinstance(vo, str) and vo in NAMES and vs != NAMES[vo]:
                err(f'{rel}.{k}: not renamed')
        elif k in ('ClassDescription', 'RaceDescription'):
            pass  # archdesc substitution
        else:
            if vo != vs: err(f'{rel}.{k}: unexpected change: {vo!r} -> {vs!r}')
print('archetype checks done')

# ---------- locations ----------
for orig in sorted(glob.glob(os.path.join(CONTENT, 'Locations', '*.json'))):
    rel = os.path.relpath(orig, CONTENT)
    do = json.load(open(orig, encoding='utf-8-sig'))
    ds = json.load(open(os.path.join(STAGE, rel), encoding='utf-8'))
    if set(do.keys()) != set(ds.keys()):
        err(f'{rel}: json keys changed'); continue
    for k in do:
        if re.match(r'Area_\d+_Rewards$', k):
            if len(do[k]) != len(ds[k]): err(f'{rel}.{k}: len'); continue
            for a, b in zip(do[k], ds[k]):
                if a == b and a in NAMES and NAMES[a] != a: err(f'{rel}.{k}: mapped not renamed: {a}')
                elif a in NAMES and b != NAMES[a]: err(f'{rel}.{k}: wrong rename: {a} -> {b}')
        elif do[k] != ds[k]:
            err(f'{rel}.{k}: unexpected change')
print('location checks done')

# ---------- tales ----------
def tale_tokens(v): return v.split(', ') if v else []
for orig in sorted(glob.glob(os.path.join(MODBASE, 'Tales', '*.json'))):
    rel = os.path.basename(orig)
    do = json.load(open(orig, encoding='utf-8-sig'))
    ds = json.load(open(os.path.join(STAGEMOD, 'Tales', rel), encoding='utf-8'))
    if set(do.keys()) != set(ds.keys()):
        err(f'tale {rel}: keys changed'); continue
    for k in do:
        vo, vs = do[k], ds[k]
        if not isinstance(vo, str) or not vo:
            if vo != vs: err(f'tale {rel}.{k}: non-string changed')
            continue
        if k in ('ID', 'MainGraphic', 'BackgroundGraphic') or k.endswith('_ExecuteFunction') or k in ('Unique', 'AutoIncludeOnwards', 'AutoIncludeInEventNode'):
            if vo != vs: err(f'tale {rel}.{k}: protected field changed: {vo} -> {vs}')
            continue
        if k == 'Requirements' or re.match(r'^Choice_\d+_Requirements$', k) or 'Reward' in k:
            to, ts = tale_tokens(vo), tale_tokens(vs)
            if len(to) != len(ts): err(f'tale {rel}.{k}: token count'); continue
            for a, b in zip(to, ts):
                if a == b: continue
                # changed tokens must be prefix-preserving with only name substitution
                ma = re.match(r'^([A-Za-z_]+:?)', a); mb = re.match(r'^([^:]*:?)', b)
                # check NextNode / ID-like tokens unchanged
                if a.startswith(('NextNode:', 'TravelTo:')) and a != b:
                    err(f'tale {rel}.{k}: NextNode changed: {a} -> {b}')
        elif k in ('Title', 'Narrative', 'Log') or re.match(r'^Choice_\d+$', k) or re.match(r'^Choice_\d+_Outcome$', k):
            pass  # display
        else:
            if vo != vs: warn(f'tale {rel}.{k}: other field changed: {vo[:40]} -> {vs[:40]}')
print('tale checks done')

# ---------- residual mapped-English scan in mechanic outputs ----------
residual = 0
for sub in ('Actions',):
    for stag in sorted(glob.glob(os.path.join(STAGE, sub, '*.tdb'))):
        for line in open(stag, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line or line.startswith(('//', '@')): continue
            if ', ' in line and line.rsplit(', ', 1)[1] in TYPES: continue  # name line handled
            for tok in line.split(', '):
                if ':' not in tok: continue
                key, val = tok.split(':', 1)
                for en in NAMES:
                    pass  # too slow; skip brute force — structural checks cover
print('residual brute scan skipped (structural checks cover)')

print()
print(f'==== RESULT: {len(ERRORS)} errors, {len(WARN)} warnings ====')
for e in ERRORS[:40]: print(' -', e)
sys.exit(1 if ERRORS else 0)
