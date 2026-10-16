# -*- coding: utf-8 -*-
"""Revert localization: restore backed-up dirs, then remove files the
localization added (staged paths not present in backup)."""
import os, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
STAGE = os.path.join(WORK, 'stage')
BACKUP = os.path.join(WORK, 'backup')
CONTENT = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content"

if not os.path.exists(os.path.join(BACKUP, '.done')):
    print('no backup found, nothing to revert')
    sys.exit(1)

# 1. remove everything the staging tree added/modified, then restore backup
removed = restored = 0
for root, dirs, files in os.walk(STAGE):
    rel = os.path.relpath(root, STAGE)
    dstroot = os.path.join(CONTENT, rel) if rel != '.' else CONTENT
    for f in files:
        d = os.path.join(dstroot, f)
        if os.path.isfile(d):
            os.remove(d)
            removed += 1
# remove now-empty dirs staged under Content (bottom-up, never remove Content itself)
for root, dirs, files in os.walk(STAGE, topdown=False):
    rel = os.path.relpath(root, STAGE)
    dstroot = os.path.join(CONTENT, rel) if rel != '.' else CONTENT
    if os.path.isdir(dstroot):
        try:
            os.rmdir(dstroot)  # only removes if empty
        except OSError:
            pass
for rel in ['Actions', 'Perks', 'Encounter',
            os.path.join('Archetypes', 'Classes'), os.path.join('Archetypes', 'Races'),
            'Locations',
            os.path.join('Mods', 'Chinese Localization', 'Tales'),
            os.path.join('CustomArtworks', 'Actions')]:
    src = os.path.join(BACKUP, rel)
    dst = os.path.join(CONTENT, rel)
    if not os.path.isdir(src):
        continue
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    restored += 1
print(f'removed {removed} staged files, restored {restored} dirs from backup')
print('NOTE: this reverts to the state at apply time (Phase-1 UI/Tales mod included).')
