# -*- coding: utf-8 -*-
import json, re, sys, io

BASE = r"C:\Users\Administrator\AppData\Local\Temp\eran_l10n"
fix_path = BASE + r"\collisions_fix.json"
ctx_path = BASE + r"\collisions_ctx.txt"
vals_path = BASE + r"\all_values.txt"

errors = []

# (a) no BOM + parses
raw = open(fix_path, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"):
    errors.append("FAIL: file has BOM")
try:
    fix = json.loads(raw.decode("utf-8"))
except Exception as e:
    errors.append("FAIL: JSON parse error: %s" % e)
    print("\n".join(errors)); sys.exit(1)

FORBIDDEN = set(',:#@*<>=/"\\\n\r\t')
for k, v in fix.items():
    # (b) forbidden chars
    bad = [c for c in v if c in FORBIDDEN]
    if bad:
        errors.append("FAIL: forbidden chars %r in value of %r" % (bad, k))
    # trailing ASCII variant marker must be preserved from key
    m = re.search(r"(\s\([A-Za-z]+\))$", k)
    if m:
        if not v.endswith(m.group(1)):
            errors.append("FAIL: marker %r not preserved for %r -> %r" % (m.group(1), k, v))
    # length guideline 2-6 han chars (excluding marker)
    core = re.sub(r"\s\([A-Za-z]+\)$", "", v)
    if not (2 <= len(core) <= 6):
        errors.append("WARN: core length %d outside 2-6 for %r" % (len(core), k))

# (c) values mutually unique
vals = list(fix.values())
if len(vals) != len(set(vals)):
    from collections import Counter
    dups = [v for v, c in Counter(vals).items() if c > 1]
    errors.append("FAIL: duplicate new values: %r" % dups)

# (d) not in all_values.txt
used = set()
with io.open(vals_path, "r", encoding="utf-8-sig") as f:
    for line in f:
        used.add(line.rstrip("\n").rstrip("\r"))
for k, v in fix.items():
    if v in used:
        errors.append("FAIL: value %r (for %r) already in all_values.txt" % (v, k))

# parse groups from ctx
groups = []
cur = []
with io.open(ctx_path, "r", encoding="utf-8-sig") as f:
    for line in f:
        line = line.rstrip("\n").rstrip("\r")
        if line.startswith("###"):
            if cur: groups.append(cur); cur = []
        m = re.match(r"-\s(.+?)\s+\[.*?\]\s+当前译名：(.+)$", line)
        if m:
            cur.append((m.group(1), m.group(2)))
    if cur: groups.append(cur)

all_names = set(n for g in groups for n, _ in g)
# (f) keys come from ctx
for k in fix:
    if k not in all_names:
        errors.append("FAIL: key %r not found in collisions_ctx.txt" % k)

# (e) each group keeps >= 1 member unmodified; also each group's final names unique
for i, g in enumerate(groups, 1):
    names = [n for n, _ in g]
    modified = [n for n in names if n in fix]
    kept = [n for n in names if n not in fix]
    if len(kept) == 0:
        errors.append("FAIL: group %d fully modified (no keeper)" % i)
    final = {n: (fix[n] if n in fix else orig) for n, orig in g}
    fv = list(final.values())
    if len(fv) != len(set(fv)):
        errors.append("FAIL: group %d still has duplicate names: %r" % (i, fv))
    if modified:
        pass

n_groups = len(groups)
n_fix = len(fix)
print("groups parsed: %d" % n_groups)
print("fix entries: %d" % n_fix)
if errors:
    print("\n".join(errors)); sys.exit(1)
print("ALL CHECKS PASSED")
