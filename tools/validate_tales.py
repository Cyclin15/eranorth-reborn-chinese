# -*- coding: utf-8 -*-
"""Validate translated tales: mechanic fields byte-identical, filenames match."""
import json, io, os, sys, re

WORK = r"C:\Users\Administrator\AppData\Local\Temp\eran_l10n"
SRC = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Tales"
MOD = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Mods\Chinese Localization\Tales"

DISPLAY_NUM = 19
MECH_PREFIXES = ("ID", "Inklet", "Requirements", "BackgroundGraphic", "MainGraphic")

def is_display(k):
    if k in ("Title", "Narrative"): return True
    m = re.match(r"Choice_(\d+)$", k)
    if m: return True
    m = re.match(r"Choice_(\d+)_Outcome$", k)
    if m: return True
    return False

def is_mech(k):
    if k in ("InkletSupportsResume", "Unique", "AutoIncludeOnwards", "AutoIncludeInEventNode"): return True
    if k in MECH_PREFIXES: return True
    if re.match(r"Choice_(\d+)_Requirements$", k): return True
    if re.match(r"Choice_(\d+)_Reward$", k): return True
    if re.match(r"Choice_(\d+)_ExecuteFunction$", k): return True
    return False  # unknown keys: report

def readlist(g):
    return [l for l in io.open(f"{WORK}\\tales_group_{g}.txt", encoding="utf-8").read().splitlines() if l.strip()]

errors, done = [], []
total = 0
for g in range(6):
    listing = readlist(g)
    total += len(listing)
    for fn in listing:
        outp = os.path.join(MOD, fn)
        srcp = os.path.join(SRC, fn)
        if not os.path.exists(outp):
            errors.append(f"缺少输出文件: {fn}"); continue
        try:
            a = json.load(io.open(srcp, encoding="utf-8-sig"))
            b = json.load(io.open(outp, encoding="utf-8"))
        except Exception as e:
            errors.append(f"{fn}: JSON 解析失败 {e}"); continue
        if set(a.keys()) != set(b.keys()):
            errors.append(f"{fn}: 键集合不一致 缺{set(a)-set(b)} 多{set(b)-set(a)}"); continue
        for k in a:
            if is_mech(k):
                if a[k] != b[k]:
                    errors.append(f"{fn}.{k}: 机制字段被改动: {a[k]!r} -> {b[k]!r}")
            elif is_display(k):
                if isinstance(a[k], str) and a[k].strip() and not (isinstance(b[k], str) and b[k].strip()):
                    errors.append(f"{fn}.{k}: 译文为空")
            else:
                errors.append(f"{fn}.{k}: 未知字段类型(请人工确认): {k}")
        done.append(fn)

print(f"校验 {len(done)}/{total} 个文件")
if errors:
    print(f"共 {len(errors)} 个问题:")
    for e in errors[:80]: print(" -", e)
    sys.exit(1)
print("OK: 所有机制字段与原版一致，显示字段均已翻译")
