# -*- coding: utf-8 -*-
import json, os, re, sys

SRC = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Tales"
LIST = r"C:\Users\Administrator\AppData\Local\Temp\eran_l10n\tales_group_1.txt"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\eran_l10n\tales_out_1"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

os.makedirs(OUT, exist_ok=True)

SP = " "  # explicit trailing space marker

T = {
    "Innate Skills.json": {
        "Title": "动用你的超自然之力",
        "Narrative": "你可以消耗 7 点行动点，从 4 个种族行动中挑选并抽取 1 个。",
        "Choice_1": "[Human / -7 行动点] 准备",
        "Choice_2": "[Vampire / -7 行动点] 准备",
        "Choice_3": "[Lycanthrope / -7 行动点] 准备",
        "Choice_4": "[Demon / -7 行动点] 准备",
        "Choice_5": "[Nephilim / -7 行动点] 准备",
        "Choice_6": "[Undine / -7 行动点] 准备",
        "Choice_7": "[Sylph / -7 行动点] 准备",
        "Choice_8": "[Ifrit / -7 行动点] 准备",
        "Choice_9": "[Nymph / -7 行动点] 准备",
        "Choice_10": "[Runecaster / -7 行动点] 准备",
        "Choice_11": "继续",
    },
    "The Inquisition Pyre.json": {
        "Title": "审判庭的火刑堆",
        "Narrative": "穿过一座小聚落时，一小簇人群的欢呼声攫住了你的目光。看样子，有个男人即将被送上审判庭的火刑堆。你走近时，他用一双哀求的眼睛望着你。",
        "Choice_1": "朝他啐一口唾沫，然后留下来观看净化仪式。",
        "Choice_1_Outcome": "你满含轻蔑地朝他啐了一口，随人群一同观看净化仪式。大审判官低声念了句简短祷文，随即近乎敷衍地朝行刑者点了点头。欢呼声、尖叫声与硫磺的气味充斥空气。<i>正义得到了伸张。</i>" + SP,
        "Choice_2": "默默为他的灵魂祈祷，并留下来观看净化仪式",
        "Choice_2_Outcome": "对这个男人你已无能为力，唯有为他的灵魂祈祷。大审判官低声念了句简短祷文，随即近乎敷衍地朝行刑者点了点头。欢呼声、尖叫声与硫磺的气味充斥空气。没有什么值得欢呼的。一条生命就此消逝。<i>也许在来世，他能寻得此生未得的安宁。</i>" + SP,
        "Choice_3": "一小队审判官外加一群庄稼汉，应该拦不住我救人。",
        "Choice_3_Outcome": "你没有再三犹豫。此时此刻，分秒必争。你攻其不备，一把夺下行刑者手中的火把，用它烧断了捆缚那人的绳索。随之而来的混乱令围观的人群四散而去。剩下的只有审判官和她的手下——他们迅速拔剑将你围住。“把这两个异端统统给我架上火刑堆，立刻！”她朝手下嘶吼道。审判官们狂热地朝你冲来。你救下的那人手持火把，站到了你身旁与你并肩作战。",
        "Choice_4": "我不忍再看。还是去镇上的旅店吧……",
    },
    "Puppeteer.json": {
        "Title": "接下来会发生什么？",
        "Narrative": "<i>将光标滚动至选项区域，可查看更多选项。\n\n或按“空格”键跳过本选项。</i>",
        "Choice_1": "[普通遭遇] 与一群敌人战斗。",
        "Choice_2": "[精英遭遇] 与一群精英敌人战斗。",
        "Choice_3": "[随机事件] 我也说不准，但正想去看看！",
        "Choice_4": "[扎营，口粮 -1，10% 遭遇几率] 我真的需要休息了。",
        "Choice_5": "[商人] 远处有一支罗姆人的商队。",
        "Choice_6": "[城镇，口粮 -1，10% 遭遇几率] 我要回城补给。",
        "Choice_7": "[训练] 我要演练新的战斗技巧。",
    },
    "Prologue VIII.json": {
        "Title": "序章",
        "Narrative": "“Calista 和我会引开他们。你先过去布好伏击！这是救出她的唯一机会！”Rysa 说道，特意在“她”字上加重了语气。\n\n“她？”Trevor 嘿然一笑，却没有深究。那位先知说的话，他其实一个字也不信。\n\nTrevor 隐入阴影之中。\n\n“Red……要是我们回不来了……”Calista 欲言又止。",
        "Choice_1": "[安抚她]",
        "Choice_1_Outcome": "“要是你们回不来，我就亲手宰了你。”Rysa 的语气斩钉截铁，却又露出一个温暖的笑容，惹得 Calista 心头一颤。也许一切还来得及——只要她们能活过这一劫。\n\n<i>不，我们会活下去的。</i>Calista 在心里给自己打气。<i>我们必须活下去。</i>\n\nCalista 周身泛起一层大地的光环，藤蔓在她手中凝聚成形，朝着不断壮大的亡灵大军疾冲而去……",
        "Choice_2": "[无视她]",
        "Choice_2_Outcome": "<i>也许对我们来说真的太迟了</i>，Calista 心想，一阵绝望压得她喘不过气来。\n\n而在战场的另一头，Rysa 正被不断壮大的亡灵大军重重围困……",
    },
    "The Well.json": {
        "Title": "你遇到一口水井。",
        "Narrative": "井水看起来清新澄澈、晶莹透亮！",
        "Choice_1": "喝上几口",
        "Choice_1_Outcome": "你喝了几口，只觉精神恢复了几分。",
        "Choice_2": "把水袋灌满",
        "Choice_2_Outcome": "这正是把水袋灌满的好机会！",
        "Choice_3": "往井里抛一枚硬币",
        "Choice_3_Outcome": "也许是因为自己无法饮用井水而心存怨气，又或只是单纯好奇——想看看这是不是传说中那类许愿井。但结果是：什么也没发生。",
        "Choice_4": "[Undine] 跳进去！",
        "Choice_4_Outcome": "井水当真清凉提神。你化为水生形态，向着地下洞窟一路深潜。难得能做一回真正的自己，这感觉真好……\n\n片刻之后你再度浮出水面，环顾这座小巧而舒适的地下洞穴。<i>这里将是完美的藏身之所！</i>",
    },
    "Mausoleum II.json": {
        "Title": "你身处一座陵墓之中",
        "Narrative": "你的吸血鬼视觉很快适应了彻底的黑暗。东侧的小架上陈列着许多盛满骨灰与骸骨的骨灰瓮；除此之外，你还相中了一具不错的石棺——只需将原先的主人请去别处安放，它便是一张完美的床。\n\n这里将是完美的藏身之所！",
        "Choice_1": "[口粮 -1] 在石棺中陷入沉眠，直至伤势痊愈",
        "Choice_1_Outcome": "你将遗骸移入一只空骨灰瓮，随后陷入深沉无梦的睡眠。几天后你醒来，身体康健，却饥渴地渴望着鲜血。\n\n上路之前，你饮下了一瓶随身携带的瓶装鲜血……",
        "Choice_2": "在石棺中陷入沉眠，直至伤势痊愈",
        "Choice_2_Outcome": "你将遗骸移入一只空骨灰瓮，随后陷入深沉无梦的睡眠。几天后你醒来，身体康健，却饥渴地渴望着鲜血。\n\n得赶紧找点“吃的”才行！",
    },
    "The Dancing Nymphs II.json": {
        "Title": "起舞的宁芙",
        "Narrative": "三个巫婆朝着站在你面前那位容颜不老、青春绝艳的女子嘶嘶低吼。她身上仅以藤蔓蔽体。至少眼下如此。\n\n<i>“Rysa？”</i>你怎么会在这里？\n\n藤蔓仿佛拥有自己的意志，游移滑落，令她彻底赤裸，随即在她手中化作一张简易的弓。\n\n“真正的宁芙长这样。”她指着此刻一览无余的曼妙曲线，揶揄那三个巫婆。她们愈发恼怒地嘶叫着扑了上来……\n\n“你到底醒了没有？”她再度朝你喊道，同时朝巫婆们松弦放箭。",
        "Choice_1": "[意志] 抵抗巫婆的魅惑",
        "Choice_1_Outcome": "现实的景象缓缓重新聚焦，你终于看清了这三个邪恶生物的真实面目。",
    },
    "A Rescue Mission I.json": {
        "Title": "营救任务",
        "Narrative": "“谢谢你！你把我们从必死之局里救了出来。”被囚者们含着泪说道。\n\n有人急忙从倒下的审判官身旁牵过马匹，只求逃得越远越好；但也有些人，看起来满心渴望加入你对抗光明教团的战斗……",
        "Choice_1": "唔。你可以跟我走……",
        "Choice_2": "……你也是……",
        "Choice_3": "……其余的人，各自珍重，平安去吧！",
    },
    "The Herbalist and the Wolves.json": {
        "Title": "草药师与狼群",
        "Narrative": "“退后！退后！”你听到一个男人在喊叫。赶去查看时，只见一位老人正挥舞火把，竭力挡开三头饿狼。他看上去已筋疲力尽。\n\n“求求你！救救我！”他哀求道。当然，这件事由不得你选择。被激起兴致的狼群此刻转而绕着你打转，掂量着你是不是更容易下口的猎物……",
        "Choice_1": "[挑衅] 还愣着干什么？",
        "Choice_1_Outcome": "狼群首领低吼一声，朝你猛扑过来……",
    },
    "Pumpkin Patch III.json": {
        "Title": "胜利！",
        "Narrative": "那个女巫实在构不成什么真正的挑战，你顺利取胜——只不过大多数南瓜到头来还是被毁了个干净。",
        "Choice_1": "[Witch] 搜查女巫的小屋",
        "Choice_1_Outcome": "小屋里凡是有用的东西，你都毫不客气地取用了。反正她也没法再反对了。",
        "Choice_2": "搜查女巫的小屋",
        "Choice_2_Outcome": "你在她的小屋里四处翻找，却没发现什么特别有用的东西。或许除了小屋东墙边那只木箱。",
    },
    "Treasure Map.json": {
        "Title": "藏宝图",
        "Narrative": "你分毫不差地按地图指引前行，来到一处隐蔽得极好的洞窟。",
        "Choice_1": "[开始挖掘] 一定就是这里了！",
        "Choice_1_Outcome": "一番挖掘之后，你挖出了一只埋在地下的箱子！",
        "Choice_2": "[离开] 唔，这地方好像不对！",
    },
    "The Dancing Nymphs.json": {
        "Title": "起舞的宁芙",
        "Narrative": "苍翠繁茂的树林，你走得越深，景致便越发明媚动人。不知怎的，你的目光再也无法从那三个翩翩起舞、嬉戏玩乐的曼妙身影上移开。她们的身姿美得纯粹，嗓音抚慰人心，令人迷醉。\n\n“快给我醒醒，你这个蠢货！”那原本悦耳动听的声音，将你从昏睡一般的恍惚中唤醒。",
        "Choice_1": "Erannorth 之上究竟怎么了……",
    },
    "Destroyed Village.json": {
        "Title": "你远远望见一座被毁村庄的残迹",
        "Narrative": "在第一次 Ulniir 入侵期间，许多村庄毁于战火。少数得到重建，但大多数已被地下世界的罪犯占据。\n\n更有一些村庄，至今仍被不得安宁的亡者所萦绕……\n\n<i>接近村庄废墟后，当前阶段将新增 4 至 8 个可探索的节点。</i>",
        "Choice_1": "我这就握紧武器，小心靠近。",
        "Choice_1_Outcome": "你谨慎地向前行进。",
    },
    "Prologue VIIIb.json": {
        "Title": "序章",
        "Narrative": "Trevor 再也听不到战斗的声响了，这是好事。绝不能让光明教团的车队察觉到任何异样。<i>但异样确实是存在的……</i>",
        "Choice_1": "继续",
    },
    "Backpack.json": {
        "Title": "你发现了一只冒险者的背包",
        "Narrative": "这只背包看起来还算完好，而它的主人肯定也不会再惦记它了！",
        "Choice_1": "把背包里的东西搜刮一空。",
        "Choice_1_Outcome": "你在背包里细细翻寻一切用得上的东西。",
    },
}

MECH_BASE = {"ID", "Inklet", "InkletSupportsResume", "Requirements", "Unique",
             "AutoIncludeOnwards", "AutoIncludeInEventNode", "BackgroundGraphic", "MainGraphic"}

def kind(key):
    if key in MECH_BASE:
        return "mech"
    if re.fullmatch(r"Choice_\d+_Requirements", key):
        return "mech"
    if re.fullmatch(r"Choice_\d+_Reward", key):
        return "mech"
    if re.fullmatch(r"Choice_\d+_ExecuteFunction", key):
        return "mech"
    if key in ("Title", "Narrative"):
        return "disp"
    if re.fullmatch(r"Choice_\d+", key):
        return "disp"
    if re.fullmatch(r"Choice_\d+_Outcome", key):
        return "disp"
    return "other"

def enc(s):
    return json.dumps(s, ensure_ascii=False)

with open(LIST, "rb") as f:
    files = [ln.strip() for ln in f.read().decode("utf-8-sig").splitlines() if ln.strip()]
assert len(files) == len(set(files)), "duplicate entries in list"

errors = []

# ---- translate & write ----
for fn in files:
    with open(os.path.join(SRC, fn), "rb") as f:
        b = f.read()
    bom = b.startswith(b"\xef\xbb\xbf")
    raw = b.decode("utf-8-sig")
    data = json.loads(raw)
    tr = T.get(fn)
    if tr is None:
        errors.append("no translations for " + fn)
        continue
    for key, newval in tr.items():
        if key not in data:
            errors.append("key %s not found in %s" % (key, fn))
            continue
        pattern = '"%s": %s' % (key, enc(data[key]))
        repl = '"%s": %s' % (key, enc(newval))
        cnt = raw.count(pattern)
        if cnt != 1:
            errors.append("pattern count=%d for %s::%s" % (cnt, fn, key))
            continue
        raw = raw.replace(pattern, repl)
    out = raw.encode("utf-8")
    if bom:
        out = b"\xef\xbb\xbf" + out
    with open(os.path.join(OUT, fn), "wb") as f:
        f.write(out)

# ---- verification ----
print("=== VERIFICATION ===")
allok = True
for fn in files:
    with open(os.path.join(SRC, fn), "rb") as f:
        o = json.loads(f.read().decode("utf-8-sig"))
    with open(os.path.join(OUT, fn), "rb") as f:
        n = json.loads(f.read().decode("utf-8-sig"))
    ok = True
    if list(o.keys()) != list(n.keys()):
        print("FAIL key order: " + fn)
        ok = False
    tr = T.get(fn, {})
    for k in o:
        if kind(k) in ("mech", "other"):
            if o[k] != n[k]:
                print("FAIL mech field %s::%s" % (fn, k))
                ok = False
        else:
            expect = tr.get(k, o[k])
            if n[k] != expect:
                print("FAIL disp field %s::%s" % (fn, k))
                ok = False
            if k in tr and isinstance(o[k], str):
                if o[k].count("\n") != tr[k].count("\n"):
                    print("FAIL newline count %s::%s" % (fn, k))
                    ok = False
    for k in n:
        if k not in o:
            print("FAIL extra key %s::%s" % (fn, k))
            ok = False
    print(("OK   " if ok else "FAIL ") + fn)
    if not ok:
        allok = False

outfiles = sorted(os.listdir(OUT))
if outfiles != sorted(files):
    print("FAIL output dir file list mismatch: %r" % outfiles)
    allok = False
else:
    print("OK   output file list matches input list (%d files)" % len(files))

if errors:
    print("ERRORS during processing:")
    for e in errors:
        print("  " + e)
    allok = False

print("RESULT:", "ALL PASS" if allok else "FAILED")
