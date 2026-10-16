# -*- coding: utf-8 -*-
"""Context-aware replacement engine for Erannorth Reborn Chinese localization.
Copies affected game data to a staging tree, applies name replacements with
namespace-safe rules, and emits a validation report. originals untouched."""
import json, os, re, glob, shutil, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'eran_l10n')
CONTENT = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content"
STAGE = os.path.join(WORK, 'stage')
REPORT = []

def log(msg):
    REPORT.append(msg)
    print(msg)

# ---------------- mappings ----------------
NAMES = json.load(open(os.path.join(WORK, 'mapping_names.json'), encoding='utf-8'))
PERKDESC = json.load(open(os.path.join(WORK, 'mapping_perkdesc.json'), encoding='utf-8'))
ARCHDESC = json.load(open(os.path.join(WORK, 'mapping_archdesc.json'), encoding='utf-8'))
# longest-first replacement pairs for display text
PAIRS = sorted(NAMES.items(), key=lambda kv: -len(kv[0]))
DISPLAY_RE = [
    (re.compile(r'(?<![A-Za-z0-9])' + re.escape(en) + r'(?![A-Za-z0-9])'), ch)
    for en, ch in PAIRS
]

def display_replace(text):
    n = 0
    for rx, ch in DISPLAY_RE:
        text, k = rx.subn(ch, text)
        n += k
    return text, n

# ---------------- prefix config ----------------
# payload is a card/perk reference; bare mapped fragments get renamed
BARE_RENAME = sorted([
    'SynergyAllyAbility', 'OnDrawCastFirstEnemy', 'OnDrawCreate', 'OnDrawCastSelf',
    'AllyAbility', 'Spellcraft', 'Afterimage', 'ChooseOne', 'LootOne', 'PlayOne',
    'Gambit', 'PurchaseFrom', 'PurchaseOne', 'StockPile', 'Discovery', 'AddSkill',
    'LockPerk', 'AddStash', 'AddInventory', 'Mutate', 'ShowRelated',
    'AddAllySpecial', 'ChangeAllySpecial',
], key=len, reverse=True)
# payload is an effect-key/keycard composite; bare fragments are keywords (kept),
# only marker-decorated (@, #, >, *) or nested-prefixed fragments are card refs
KEYWORD_BARE = sorted([
    'AddEffect', 'DiscardEffect', 'ContingencyEffect', 'UnravelEffect', 'BloodTribute',
], key=len, reverse=True)
# buff/status namespace: only " <card> +*" active-card references get renamed
BUFF_PREFIXES = ['OnCasterStatus', 'OnEnemyStatus', 'WhileCaster']
MARKERS = '@#>*'
# perk-tree grouping labels (dropdown display; pure equality-grouping)
PERKTREE_LABELS = {
    'Psychic': '灵能异术', 'Additional Disciplines': '额外传承',
    'Grace': '优雅', 'Witchcraft': '巫术', 'Faith': '信仰',
    'Summoning Mastery': '召唤精通', 'Necromancy': '死灵法术',
    'Alter Self': '自我蜕变', 'Water Magic': '水系魔法', 'Fire Magic': '火系魔法',
    'Air Magic': '气系魔法', 'Light Magic': '光系魔法', 'Earth Magic': '土系魔法',
    'Dark Magic': '暗系魔法', 'Astral Magic': '星界魔法', 'Assassin': '刺杀',
    'Alchemy': '炼金术', 'Background': '背景', 'Ranged-Weapons': '远程武器',
    'Blunt-Weapons': '钝击武器', 'Bladed-Weapons': '利刃武器',
    'Hermetic Studies': '赫尔墨斯研究', 'Eldritch Arcana': '邪能奥术',
    'Vampiric Nature': '吸血鬼天性', 'Arcana': '奥术', 'Leadership': '领导力',
    'Coat of Arms': '家族纹章',
}

# ---------------- key decomposition ----------------
def try_rename_core(core):
    """core (markers/=N stripped) → renamed or None."""
    if core in NAMES:
        return NAMES[core]
    for pre in BARE_RENAME + KEYWORD_BARE:
        if core.startswith(pre):
            sub = decompose(core[len(pre):], pre in KEYWORD_BARE)
            if sub is not None:
                return pre + sub
            return None
    return None

def decompose_frag(frag, keyword_bare):
    """single ';'-fragment → renamed or None(keep)."""
    if frag == '':
        return ''
    if '++' in frag:          # CustomBuff marker → buff namespace, never rename
        return None
    m = re.match(r'^(.*?)(=-?\d+)?$', frag)
    body, mag = m.group(1), m.group(2) or ''
    # strip markers from both ends
    lead = ''
    while body and body[0] in MARKERS:
        lead += body[0]; body = body[1:]
    trail = ''
    while body and body[-1] in MARKERS:
        trail = body[-1] + trail; body = body[:-1]
    marked = bool(lead or trail)
    if body == '':
        return None
    if marked:
        new = try_rename_core(body)
        return None if new is None else lead + new + trail + mag
    if keyword_bare:
        return None           # bare fragment in keyword family: effect keyword
    new = try_rename_core(body)
    return None if new is None else new + mag

def decompose_part(part, keyword_bare):
    """'#'-alternative → renamed or None(keep)."""
    frags = part.split(';')
    out = []
    for f in frags:
        r = decompose_frag(f, keyword_bare)
        if r is None:
            out.append(f)
        else:
            out.append(r)
    return ';'.join(out)

def decompose(payload, keyword_bare):
    parts = payload.split('#')
    return '#'.join(decompose_part(p, keyword_bare) for p in parts)

def process_key(key):
    """full effect key → renamed key or None (leave unchanged)."""
    # Morph meta-key: Morph=>N=><inner effect key>
    m = re.match(r'^Morph=>-?\d+=>(.+)$', key)
    if m:
        inner = m.group(1)
        r = process_key(inner)
        return None if r is None else 'Morph=>' + key[len('Morph=>'):-len(inner)-2] + '=>' + r
    # ModifyEffect wraps a card effect key: the game strips the prefix and
    # matches the rest EXACTLY against card cEffects keys (4567/51935) — the
    # wrapped key must go through the same renaming as the card's own key
    if key.startswith('ModifyEffect') and len(key) > len('ModifyEffect'):
        r = process_key(key[len('ModifyEffect'):])
        return None if r is None else 'ModifyEffect' + r
    # buff prefixes: only active-card " +*" refs
    for pre in BUFF_PREFIXES:
        if key.startswith(pre):
            payload = key[len(pre):]
            if payload.endswith(' +*') and payload[:-3] in NAMES:
                return pre + NAMES[payload[:-3]] + ' +*'
            return None
    # name-bearing prefixes
    for pre in BARE_RENAME:
        if key.startswith(pre):
            return pre + decompose(key[len(pre):], False)
    for pre in KEYWORD_BARE:
        if key.startswith(pre):
            return pre + decompose(key[len(pre):], True)
    return None

VALUE_EXACT_KEYS = {'Artwork', 'ReUseArtwork', 'Commodity', 'UniqueName'}
VALUE_DISPLAY_KEYS = {'Flavor', 'OverrideDesc'}

def process_value(key, value, artrefs):
    """effect value → possibly renamed."""
    if key in ('Artwork', 'ReUseArtwork'):
        # slash refs "A/B" stay unchanged; art exporter emits nested
        # CustomArtworks/Actions/A/B.png so the file-based lookup resolves.
        if '/' in value:
            artrefs.add(value)
            return value
        return NAMES.get(value, value)
    if key == 'PerkTree':
        # grouping label shown in the perk-tree filter dropdown; rename is a
        # pure function of the label so equality-grouping stays consistent
        v = NAMES.get(value)
        if v: return v
        return PERKTREE_LABELS.get(value, value)
    if key in VALUE_EXACT_KEYS:
        return NAMES.get(value, value)
    if key in VALUE_DISPLAY_KEYS:
        return display_replace(value)[0]
    return value

# ---------------- tdb processing ----------------
TYPES = set(json.load(open(os.path.join(WORK, 'names', 'extracted.json'), encoding='utf-8'))['types'])

def process_card_tdb(path):
    stats = {'name': 0, 'name_miss': [], 'keys': 0, 'vals': 0, 'disp': 0}
    artrefs = set()
    out = []
    for line in open(path, encoding='utf-8-sig'):
        line = line.rstrip('\n')
        if not line or line.startswith('//') or line.startswith('@'):
            out.append(line); continue
        # name line?
        if ', ' in line and line.rsplit(', ', 1)[1] in TYPES:
            name, typ = line.rsplit(', ', 1)
            if name in NAMES:
                out.append(NAMES[name] + ', ' + typ)
                stats['name'] += 1
            else:
                out.append(line)
                stats['name_miss'].append(name)
            continue
        # effect line
        toks = line.split(', ')
        nt = []
        for tok in toks:
            if ':' not in tok:
                nt.append(tok); continue
            k, v = tok.split(':', 1)
            nk = process_key(k)
            if nk is not None:
                stats['keys'] += 1
                k = nk
            v2 = process_value(k, v, artrefs)
            if v2 != v:
                stats['vals'] += 1
                if k in VALUE_DISPLAY_KEYS:
                    stats['disp'] += 1
            nt.append(k + ':' + v2)
        if len(nt) != len(toks):
            log(f'!! TOKEN COUNT MISMATCH {path}: {len(toks)} -> {len(nt)}')
        out.append(', '.join(nt))
    return out, stats, artrefs

def process_perk_tdb(path):
    stats = {'name': 0, 'desc': 0, 'desc_miss': [], 'keys': 0, 'req': 0}
    out = []
    lines = [l.rstrip('\n') for l in open(path, encoding='utf-8-sig')]
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line.startswith('/') or line.startswith('#') or line.startswith('\ufeff/'):
            out.append(line); i += 1; continue
        # group: name line / desc line / effects line
        if i + 2 < len(lines) or i + 1 < len(lines):
            pass
        name_line = line
        parts = name_line.split(', ')
        if parts[0] in NAMES:
            parts[0] = NAMES[parts[0]]
            stats['name'] += 1
        if len(parts) >= 3 and parts[-1] in NAMES:   # required perk
            parts[-1] = NAMES[parts[-1]]
            stats['req'] += 1
        out.append(', '.join(parts))
        i += 1
        if i < len(lines):
            desc = lines[i]
            orig_name = name_line.split(', ')[0]
            if orig_name in PERKDESC:
                out.append(PERKDESC[orig_name])
                stats['desc'] += 1
            else:
                out.append(desc)
                if desc.strip():
                    stats['desc_miss'].append(orig_name)
            i += 1
        if i < len(lines):
            eff = lines[i]
            toks = eff.split(', ')
            nt = []
            for tok in toks:
                if ':' not in tok:
                    nt.append(tok); continue
                k, v = tok.split(':', 1)
                nk = process_key(k)
                if nk is not None:
                    stats['keys'] += 1
                    k = nk
                v2 = process_value(k, v, set())
                nt.append(k + ':' + v2)
            if len(nt) != len(toks):
                log(f'!! PERK TOKEN COUNT MISMATCH {path}')
            out.append(', '.join(nt))
            i += 1
    return out, stats

def process_enemy_tdb(path):
    stats = {'name': 0, 'miss': []}
    out = []
    for line in open(path, encoding='utf-8-sig'):
        line = line.rstrip('\n')
        if not line or line.startswith(('//', '@', '#')):
            out.append(line); continue
        toks = line.split(', ')
        nt = []
        for tok in toks:
            if tok.startswith('Name:'):
                v = tok[5:]
                if v in NAMES:
                    nt.append('Name:' + NAMES[v]); stats['name'] += 1
                else:
                    nt.append(tok); stats['miss'].append(v)
            else:
                nt.append(tok)
        out.append(', '.join(nt))
    return out, stats

# ---------------- json processing ----------------
def map_exact(s):
    return NAMES.get(s, s)

def map_colon(s):
    """'Name:N' → renamed name part."""
    if ':' in s:
        n, suf = s.rsplit(':', 1)
        if re.fullmatch(r'-?\d+', suf):
            return map_exact(n) + ':' + suf
    return map_exact(s)

def rename_perk_ref(name):
    """Perk name reference — exact lookup; a leading '*' is part of the name."""
    return NAMES.get(name, name)

def rename_perk_tree_entry(e):
    """PerksTree entry (C# parses: 'N>AutoGrant>Name', 'Cond>>Name:lvl',
    'Name:lvl'). Only the perk NAME is renamed; conditions/levels are
    internal keys (gender/race/class/discipline) and stay untouched."""
    if '>AutoGrant>' in e:
        pre, name = e.split('>AutoGrant>', 1)
        return pre + '>AutoGrant>' + rename_perk_ref(name)
    if '>>' in e:
        cond, rest = e.split('>>', 1)
        if ':' in rest:
            n, lvl = rest.rsplit(':', 1)
            return cond + '>>' + rename_perk_ref(n) + ':' + lvl
        return cond + '>>' + rename_perk_ref(rest)
    if ':' in e:
        n, t = e.rsplit(':', 1)
        return rename_perk_ref(n) + ':' + t
    return e

def process_archetype(path):
    d = json.load(open(path, encoding='utf-8-sig'))
    stem = os.path.splitext(os.path.basename(path))[0]
    stats = {'deck': 0, 'tree': 0, 'perktree': 0, 'desc': 0}
    for k in ('StartingDeck', 'StartingEquipment', 'StartingStash', 'AdditionalActions'):
        if k in d and isinstance(d[k], list):
            d[k] = [map_exact(x) for x in d[k]]
    if isinstance(d.get('AI'), list):
        d['AI'] = [map_colon(x) for x in d['AI']]
    for k in ('MainWeapon', 'MainShield'):
        if isinstance(d.get(k), str) and d[k]:
            d[k] = map_exact(d[k])
    if isinstance(d.get('SkillTree'), list):
        d['SkillTree'] = [map_colon(x) for x in d['SkillTree']]
    if isinstance(d.get('PerksTree'), list):
        out = []
        for e in d['PerksTree']:
            out.append(rename_perk_tree_entry(e))
        d['PerksTree'] = out
    dkey = ('职业 ' if 'Classes' in path else '种族 ') + stem
    for fk, dk in (('ClassDescription', '职业 ' + stem), ('RaceDescription', '种族 ' + stem)):
        if d.get(fk) and dk in ARCHDESC:
            d[fk] = ARCHDESC[dk]; stats['desc'] += 1
    return d, stats

def process_location(path):
    d = json.load(open(path, encoding='utf-8-sig'))
    for k in list(d.keys()):
        if re.match(r'Area_\d+_Rewards$', k) and isinstance(d[k], list):
            d[k] = [map_exact(x) for x in d[k]]
    return d

# ---------------- tale processing ----------------
def tale_token(tok):
    """one reward/requirement token → possibly renamed."""
    m = re.match(r'^Encounter:(.*?)( - Lv \d+)?$', tok)
    if m:
        name, lv = m.group(1), m.group(2) or ''
        return 'Encounter:' + map_exact(name) + lv
    for pre in ('Craft', 'Cast'):
        if tok.startswith(pre + ':'):
            return pre + ':' + map_exact(tok[len(pre)+1:])
    for pre in ('LootOne', 'ChooseOne'):
        if tok.startswith(pre + ':'):
            return pre + ':' + '#'.join(map_exact(x) for x in tok[len(pre)+1:].split('#'))
    m = re.match(r'^Chance>(-?\d+)>(.*)$', tok)
    if m:
        return 'Chance>' + m.group(1) + '>' + tale_token(m.group(2))
    if tok.startswith('Not:'):
        return 'Not:' + tale_token(tok[4:])
    if '>' in tok or ':' in tok:
        return tok                     # NextNode, XP, HasDiscipline, Race, Class...
    return map_exact(tok)              # bare card/enemy name

def process_tale(path):
    d = json.load(open(path, encoding='utf-8-sig'))
    stats = {'mech': 0, 'disp': 0}
    for k in list(d.keys()):
        v = d[k]
        if not isinstance(v, str) or not v:
            continue
        if k == 'Requirements' or re.match(r'^Choice_\d+_Requirements$', k):
            toks = v.split(', ') if v else []
            d[k] = ', '.join(tale_token(t) for t in toks)
        elif 'Reward' in k:
            toks = v.split(', ')
            nt = []
            for t in toks:
                r = tale_token(t)
                if r != t: stats['mech'] += 1
                nt.append(r)
            d[k] = ', '.join(nt)
        elif k in ('Title', 'Narrative', 'Log') or re.match(r'^Choice_\d+$', k) or re.match(r'^Choice_\d+_Outcome$', k):
            nv, n = display_replace(v)
            if n: stats['disp'] += n
            d[k] = nv
    return d, stats

# ---------------- main ----------------
def main():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)

    targets = []
    for sub in ('Actions', 'Perks', 'Encounter'):
        targets += glob.glob(os.path.join(CONTENT, sub, '*.tdb'))
    arch = glob.glob(os.path.join(CONTENT, 'Archetypes', 'Classes', '*.json')) + \
           glob.glob(os.path.join(CONTENT, 'Archetypes', 'Races', '*.json'))
    locs = glob.glob(os.path.join(CONTENT, 'Locations', '*.json'))
    modt = os.path.join(CONTENT, 'Mods', 'Chinese Localization', 'Tales')
    tales = glob.glob(os.path.join(modt, '*.json'))
    modbase = os.path.join(CONTENT, 'Mods', 'Chinese Localization')

    all_artrefs = set()
    total = {'name': 0, 'keys': 0, 'vals': 0, 'enemy': 0, 'deck': 0, 'mech': 0, 'disp': 0, 'desc': 0}
    for p in targets:
        rel = os.path.relpath(p, CONTENT)
        dst = os.path.join(STAGE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.basename(p) == 'EnemyDB.Core.tdb':
            out, st = process_enemy_tdb(p)
            total['enemy'] += st['name']
            if st['miss']:
                log(f'enemy name miss ({len(st["miss"])}): {st["miss"][:10]}')
        elif os.path.dirname(rel) == 'Perks':
            out, st = process_perk_tdb(p)
            total['name'] += st['name']; total['desc'] += st['desc']; total['keys'] += st['keys']
            if st['desc_miss']:
                log(f'perk desc miss {os.path.basename(p)}: {st["desc_miss"][:10]}')
        else:
            out, st, arts = process_card_tdb(p)
            total['name'] += st['name']; total['keys'] += st['keys']; total['vals'] += st['vals']
            all_artrefs |= arts
            if st['name_miss']:
                log(f'card name miss {os.path.basename(p)} ({len(st["name_miss"])}): {st["name_miss"][:10]}')
        with open(dst, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
    for p in arch:
        rel = os.path.relpath(p, CONTENT)
        dst = os.path.join(STAGE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        d, st = process_archetype(p)
        json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
        total['deck'] += st['tree'] + 0
    for p in locs:
        rel = os.path.relpath(p, CONTENT)
        dst = os.path.join(STAGE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        json.dump(process_location(p), open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    for p in tales:
        rel = os.path.relpath(p, modbase)
        dst = os.path.join(STAGE, 'Mods', 'Chinese Localization', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        d, st = process_tale(p)
        json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
        total['mech'] += st['mech']; total['disp'] += st['disp']

    log('=== totals ===')
    log(f"card/perk names renamed: {total['name']}, enemy names: {total['enemy']}")
    log(f"effect keys renamed: {total['keys']}, effect values renamed: {total['vals']}")
    log(f"perk descriptions: {total['desc']}, tale mech tokens: {total['mech']}, tale display replacements: {total['disp']}")
    log(f"art slash refs kept (need nested export): {len(all_artrefs)}")
    json.dump(sorted(all_artrefs), open(os.path.join(WORK, 'stage_artrefs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    with open(os.path.join(WORK, 'engine_report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(REPORT))

if __name__ == '__main__':
    main()
