# -*- coding: utf-8 -*-
"""Align card/perk name references inside perk descriptions with the canonical
mapping_names translations.
- 'English' single-quoted refs left in Chinese text -> 『canonical』
- 『variant』 renderings (order-paired with original refs) -> 『canonical』
Writes mapping_perkdesc.json back. Idempotent."""
import json, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
NAMES = json.load(open(os.path.join(WORK, 'mapping_names.json'), encoding='utf-8'))
PD = json.load(open(os.path.join(WORK, 'mapping_perkdesc.json'), encoding='utf-8'))
PR = json.load(open(os.path.join(WORK, 'perks_reextracted.json'), encoding='utf-8'))

def extract_refs(text):
    """Quoted refs from ORIGINAL English text; merge inner apostrophes
    ('Raven' + 's Form') only when the merged form is a known name."""
    refs, i = [], 0
    while True:
        a = text.find("'", i)
        if a < 0: break
        b = text.find("'", a + 1)
        if b < 0: break
        ref = text[a + 1:b]
        # inner-apostrophe merge: try extending if next char is a lowercase letter
        if b + 1 < len(text) and text[b + 1].islower():
            nb = text.find("'", b + 1)
            if nb > 0:
                merged = text[a + 1:nb]
                if merged in NAMES and ref not in NAMES:
                    ref = merged
                    b = nb
        if ref.strip():
            refs.append(ref)
        i = b + 1
    return refs

stats = {'en_fixed': 0, 'cn_fixed': 0, 'unbalanced': []}

# 1) English leftovers -> canonical 『』 (exact quoted substrings)
for key in PD:
    td = PD[key]
    for e in NAMES:
        q = f"'{e}'"
        if q in td:
            td = td.replace(q, f"『{NAMES[e]}』")
            stats['en_fixed'] += 1
    PD[key] = td

# 2) variant renderings -> canonical, order-paired with ALL original refs
#    (originals quote keywords too: 'Dark' Ally cards -> 『黑暗』; pair
#    everything in order, fix only pairs whose English ref is a known name)
for key, od in ((k, v['desc']) for k, v in PR.items()):
    td = PD.get(key)
    if not td: continue
    en_refs = extract_refs(od)
    cn_refs = re.findall(r'『([^』]+)』', td)
    if len(en_refs) == len(cn_refs) and en_refs:
        changed = False
        for e, c in zip(en_refs, cn_refs):
            if e in NAMES and c != NAMES[e]:
                td = td.replace(f"『{c}』", f"『{NAMES[e]}』", 1)
                stats['cn_fixed'] += 1
                changed = True
        if changed:
            PD[key] = td
    else:
        missing = [e for e in en_refs if e in NAMES and f"『{NAMES[e]}』" not in td]
        if missing:
            stats['unbalanced'].append((key, en_refs, cn_refs))

print(f"english refs fixed: {stats['en_fixed']}")
print(f"chinese variants fixed: {stats['cn_fixed']}")
print(f"unbalanced: {len(stats['unbalanced'])}")
for k, r, c in stats['unbalanced'][:15]:
    print('  ', k, '| en:', r, '| cn:', c)
json.dump(PD, open(os.path.join(WORK, 'mapping_perkdesc.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
print('saved mapping_perkdesc.json')
