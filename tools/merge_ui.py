# -*- coding: utf-8 -*-
"""Merge translated chunks into the final localization JSON and validate."""
import json, re, sys, io

WORK = r"C:\Users\Administrator\AppData\Local\Temp\eran_l10n"
SRC = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Localization\English.json"
OUT = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Mods\Chinese Localization\Localization\简体中文.json"

def placeholders(s):
    return sorted(re.findall(r"\{\d+\}", s or ""))

def sprites(s):
    return sorted(re.findall(r'<sprite name="[^"]*">', s or ""))

def tags(s):
    # count opening/closing rich-text tags (excluding self-closing sprite)
    return sorted(re.findall(r"</?(?:b|i|u|s|nobr|br|color|size)[^>]*>", s or ""))

eng = json.load(io.open(SRC, encoding="utf-8-sig"))
meta = ["Language", "Compatibility", "HasUserModifications", "README//1"]
src_items = {k: v for k, v in eng.items() if k not in meta}

merged, errors = {}, []
for i in range(6):
    try:
        chunk = json.load(io.open(f"{WORK}\\out_{i}.json", encoding="utf-8"))
    except Exception as e:
        errors.append(f"out_{i}.json 无法解析: {e}")
        continue
    for k, v in chunk.items():
        if k in merged:
            errors.append(f"重复键 {k} (chunk {i})")
        merged[k] = v

# key set checks
missing = [k for k in src_items if k not in merged]
extra = [k for k in merged if k not in src_items]
for k in missing: errors.append(f"缺失键: {k}")
for k in extra: errors.append(f"多余键: {k}")

# per-key format checks
for k, orig in src_items.items():
    if k not in merged: continue
    tr = merged[k]
    if not isinstance(tr, str):
        errors.append(f"{k}: 译文不是字符串"); continue
    if placeholders(orig) != placeholders(tr):
        errors.append(f"{k}: 占位符不匹配 原{placeholders(orig)} 译{placeholders(tr)}")
    if sprites(orig) != sprites(tr):
        errors.append(f"{k}: sprite 标签不匹配 原{sprites(orig)} 译{sprites(tr)}")
    if len(tags(orig)) != len(tags(tr)):
        errors.append(f"{k}: 富文本标签数量不匹配 原{tags(orig)} 译{tags(tr)}")
    if isinstance(orig, str) and orig.strip() == "" and tr.strip() != "":
        errors.append(f"{k}: 原文为空但译文非空: {tr!r}")

# Translation-class-only fields that English.json lacks (kept English as empty default); nothing to do
if errors:
    print(f"共 {len(errors)} 个问题:")
    for e in errors[:80]: print(" -", e)
    sys.exit(1)

final = {
    "Language": "简体中文",
    "Compatibility": eng.get("Compatibility", ""),
    "README//1": "简体中文汉化。翻译值请勿改动键名；'HasUserModifications' 保持 'No'（未改动格式）。",
    "HasUserModifications": "No",
}
final.update(merged)
with io.open(OUT, "w", encoding="utf-8-sig", newline="\n") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)
print(f"OK: 写出 {OUT}")
print(f"字段数: {len(final)}（含 4 个头部字段）")
