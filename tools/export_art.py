# -*- coding: utf-8 -*-
"""Export embedded card artworks as mod-level flat PNGs (Chinese card names)
plus content-level nested ref PNGs, into the staging tree."""
import json, os, re, glob, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
CONTENT = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content"
# after apply.py the live tdb is translated - read originals from backup
BACKUP = os.path.join(WORK, 'backup')
TDB_SRC = os.path.join(BACKUP, 'Actions') if os.path.isdir(os.path.join(BACKUP, 'Actions')) else os.path.join(CONTENT, 'Actions')
ARTSTAGE = os.path.join(WORK, 'artstage')
STAGE = os.path.join(WORK, 'stage')
FLAT = os.path.join(STAGE, 'Mods', 'Chinese Localization', 'CustomArtworks', 'Actions')
NESTED = os.path.join(STAGE, 'CustomArtworks', 'Actions')

NAMES = json.load(open(os.path.join(WORK, 'mapping_names.json'), encoding='utf-8'))
TYPES = set(json.load(open(os.path.join(WORK, 'names', 'extracted.json'), encoding='utf-8'))['types'])

# ---- index artstage (folder lowercase -> {filename lower: path}) ----
idx = {}
for d in os.listdir(ARTSTAGE):
    dp = os.path.join(ARTSTAGE, d)
    if not os.path.isdir(dp): continue
    m = {}
    for f in os.listdir(dp):
        if f.lower().endswith('.png'):
            m[os.path.splitext(f)[0].lower()] = os.path.join(dp, f)
    idx[d.lower()] = m

def sprite(folder, name):
    m = idx.get(folder.lower())
    if not m: return None
    return m.get(name.lower())

# ---- parse original card tdb for name/type/reuse refs ----
cards = []   # (name, type, ref)
for p in sorted(glob.glob(os.path.join(TDB_SRC, '*.tdb'))):
    lines = [l.rstrip('\n').lstrip('\ufeff') for l in open(p, encoding='utf-8-sig')]
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line.startswith(('//', '@')):
            i += 1; continue
        if ', ' in line and line.rsplit(', ', 1)[1] in TYPES:
            name, typ = line.rsplit(', ', 1)
            ref = ''
            if i + 1 < len(lines):
                for tok in lines[i+1].split(', '):
                    if tok.startswith('ReUseArtwork:'):
                        ref = tok[len('ReUseArtwork:'):]
                        break
            cards.append((name, typ, ref))
            i += 2
        else:
            i += 1

print(f'cards parsed: {len(cards)}')
own_ok = ref_ok = unresolved_own = unresolved_ref = 0
unresolved_list, ref_unresolved = [], []
os.makedirs(FLAT, exist_ok=True)

for name, typ, ref in cards:
    chn = NAMES.get(name)
    if chn is None:
        print(f'!! card not in mapping: {name}'); continue
    if ref:
        a, b = ref.split('/', 1)
        art = sprite(a, b)
        if art:
            shutil.copyfile(art, os.path.join(FLAT, chn + '.png'))
            d = os.path.join(NESTED, a)
            os.makedirs(d, exist_ok=True)
            shutil.copyfile(art, os.path.join(d, b + '.png'))
            ref_ok += 1
        else:
            ref_unresolved.append((name, ref))
            # fall back to own sprite if present (vanilla would show blank, but
            # own sprite is the closest match; keep vanilla-faithful: skip)
    else:
        art = sprite(typ, name)
        if art:
            shutil.copyfile(art, os.path.join(FLAT, chn + '.png'))
            own_ok += 1
        else:
            unresolved_own += 1
            unresolved_list.append((name, typ))

print(f'own-sprite exports: {own_ok}')
print(f'ref exports (flat + nested): {ref_ok}')
print(f'own unresolved (no art, stays blank like vanilla): {unresolved_own}')
print(f'ref unresolved (dangling, stays blank like vanilla): {len(ref_unresolved)}')
for x in ref_unresolved[:20]: print('   dangling:', x)
if unresolved_own:
    print('sample unresolved:', unresolved_list[:15])
json.dump({'unresolved_own': unresolved_list, 'ref_unresolved': ref_unresolved},
          open(os.path.join(WORK, 'art_unresolved.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('flat files:', len(os.listdir(FLAT)))
