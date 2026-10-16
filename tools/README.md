# 汉化流水线工具

制作 Erannorth Reborn 简体中文汉化包用的全部脚本与翻译数据。
依赖 Python 3，脚本内路径指向本机的游戏安装目录，换机器需自行修改。

## 流程概览

```
反编译 (ilspycmd)  ──►  eran_decomp/Assembly-CSharp.decompiled.cs
                             │
   ┌─────────────────────────┼──────────────────────────────┐
   ▼                         ▼                              ▼
数据文件汉化            DLL 界面字符串                  Mod 资源
engine.py               usheap.py (#US 堆解析)           export_art.py (卡面图导出)
merge_names.py          curate_dll_strings.py (甄别)     stage_artrefs.json
align_desc_refs.py      patch_dll.py (等长原位补丁)      art_unresolved.json
apply.py (部署+备份)     revert_dll.py (还原)
   │                         │
   ▼                         ▼
merge_ui.py + out_*.json  build_gamemodes.py
(UI 本地化 JSON 合并)     (汉化游戏模式生成)
                             │
validate_stage.py / validate_tales.py / verify_fix.py (校验)
```

## 脚本说明

| 脚本 | 用途 |
|---|---|
| `usheap.py` | 解析 .NET 程序集 #US 字符串堆（等长 UTF-16 原位补丁的基础） |
| `curate_dll_strings.py` | 从反编译源提取 DLL 硬编码字符串，甄别显示用途 vs 逻辑键（路径/查找键/比较键） |
| `patch_dll.py` | DLL 界面字符串等长中文补丁（`--check` 干跑审计；含全部翻译表） |
| `revert_dll.py` | 从备份还原 Assembly-CSharp.dll |
| `engine.py` | 上下文感知替换引擎：把游戏数据复制到 staging 树做名词替换，不动原文件 |
| `merge_names.py` | 合并卡牌/敌人/地点等名称映射到 staging |
| `align_desc_refs.py` | 对齐描述文本中的名称引用（防止替换后引用断链） |
| `apply.py` | 把 staging 部署进游戏 Content（先备份原版） |
| `revert.py` | 从备份还原游戏 Content（配合 apply.py） |
| `merge_ui.py` | 由 out_*.json 重新生成 Mod 的 简体中文.json（1473 个 UI 字段） |
| `build_gamemodes.py` | 重新生成 Mod 的 10 个汉化游戏模式 + ModLoaderUser.conf |
| `export_art.py` | 卡面图导出/改名（为中文卡名生成 CustomArtworks 索引） |
| `translate_*.py` | 分批机器翻译跑批脚本 |
| `validate_stage.py` / `validate_tales.py` / `verify_fix.py` | 数据完整性校验 |

## 翻译数据

| 文件 | 内容 |
|---|---|
| `mapping_names.json` | 卡牌/敌人/地点名称映射（英 → 中） |
| `mapping_perkdesc.json` / `mapping_archdesc.json` | 专长描述 / 种族职业描述映射 |
| `perks_reextracted.json` / `perk_desc_fix.json` / `perk_names_fix.json` | 专长文本重提取与修正 |
| `out_0..5.json` | UI 本地化最终字段（merge_ui.py 的输入） |
| `dll_candidates.json` | DLL 字符串甄别结果（safe/fragment/path/mixed） |
| `collisions_fix.json` / `unclassified_*.json` / `desc_ref_mismatch.json` / `art_unresolved.json` / `stage_artrefs.json` | 各阶段修正与遗留问题清单 |

## 更新汉化的方法

1. Steam 更新游戏后：`revert.py`（或 Steam 验证完整性）还原原版。
2. 重新反编译（`ilspycmd`），重新生成 `us_strings.txt`（`usheap.py` 自带 dump）。
3. 跑 `curate_dll_strings.py` 复核安全清单 → 调整 `patch_dll.py` 翻译表 → `--check` 至 0 问题 → 应用。
4. `engine.py` → `merge_names.py` → `align_desc_refs.py` → `apply.py` 部署数据。
5. `merge_ui.py` / `build_gamemodes.py` / `export_art.py` 更新 Mod。
6. 打 Release zip：复制改动文件 + Mod 文件夹 + 补丁 DLL，覆盖层结构见主 README。
