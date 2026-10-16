# -*- coding: utf-8 -*-
"""Apply staged localization: backup originals -> copy staged files over Content.
Run once; safe to re-run (backup skipped if marker exists)."""
import os, shutil, sys, io, filecmp
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
STAGE = os.path.join(WORK, 'stage')
BACKUP = os.path.join(WORK, 'backup')
CONTENT = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content"

# relative dirs we touch (staged content mirrors these under STAGE)
TARGETS = [
    'Actions', 'Perks', 'Encounter',
    os.path.join('Archetypes', 'Classes'), os.path.join('Archetypes', 'Races'),
    'Locations',
    os.path.join('Mods', 'Chinese Localization', 'Tales'),
    os.path.join('CustomArtworks', 'Actions'),
]

if os.path.exists(os.path.join(BACKUP, '.done')):
    print('backup already exists, skipping backup step')
else:
    os.makedirs(BACKUP, exist_ok=True)
    n = 0
    for rel in TARGETS:
        src = os.path.join(CONTENT, rel)
        dst = os.path.join(BACKUP, rel)
        if not os.path.isdir(src):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            print(f'!! backup path exists, not overwriting: {dst}')
            sys.exit(1)
        shutil.copytree(src, dst)
        n += 1
    open(os.path.join(BACKUP, '.done'), 'w').write('ok')
    print(f'backed up {n} dirs -> {BACKUP}')

# apply staged files (merge: overwrite/add, never delete)
applied = skipped = 0
for root, dirs, files in os.walk(STAGE):
    rel = os.path.relpath(root, STAGE)
    dstroot = os.path.join(CONTENT, rel) if rel != '.' else CONTENT
    os.makedirs(dstroot, exist_ok=True)
    for f in files:
        s = os.path.join(root, f)
        d = os.path.join(dstroot, f)
        if os.path.exists(d) and filecmp.cmp(s, d, shallow=False):
            skipped += 1
            continue
        shutil.copyfile(s, d)
        applied += 1
print(f'applied {applied} files, unchanged {skipped}')
