# -*- coding: utf-8 -*-
"""One-command rollback: restore the original Assembly-CSharp.dll from backup."""
import shutil, os, sys, hashlib

BAK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n', 'dll_backup', 'Assembly-CSharp.dll.orig')
DLL = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\Managed\Assembly-CSharp.dll"

md5 = lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()

if not os.path.exists(BAK):
    print("no backup found"); sys.exit(1)
cur = md5(DLL) if os.path.exists(DLL) else None
if cur == md5(BAK):
    print("already original, nothing to do"); sys.exit(0)
shutil.copyfile(BAK, DLL)
print("restored:", DLL)
print("md5:", md5(DLL))
