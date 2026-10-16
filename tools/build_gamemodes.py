# -*- coding: utf-8 -*-
"""Create translated GameMode overrides in the Chinese localization mod."""
import json, io, os

SRC = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\GameModes"
MOD = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Mods\Chinese Localization\GameModes"
os.makedirs(MOD, exist_ok=True)

T = {
"Casual": "「休闲」模式是面向新手的极简难度，旨在作为入门引导，也是一个供你在学习游戏基础时练习和实验的安全环境。\n\n该模式共 3 个阶段，你将遇到低等级敌人和 D0 至 D2 的首领。完成该模式约可获得 20+ 代币与精通点数。\n\n<b>难度：</b>简单",
"Normal": "「普通」模式面向已掌握游戏基础、想要在比「休闲模式」稍严峻的环境中检验实力的玩家。\n\n该模式共 6 个阶段，你将遇到中等等级的敌人和 D0 至 D5 的首领。\n\n建议先用你选定的组合至少通关一次「休闲」模式，再来挑战「普通」。\n\n完成该模式约可获得 55+ 代币与精通点数。\n\n<b>难度：</b>普通",
"Ironman": "在你通关「普通」模式、准备好迎接 Erannorth 的首个类 Rogue 体验时，「铁人」就是你的下一站。原版铁人是一个「具有挑战性」的模式，需要你对游戏规则有充分理解并具备战术思维才能通关。\n\n如果你想要死亡即永久的完整类 Rogue 体验，请不使用存档栏位系统。每次推进节点时，进度仍会自动保存到唯一的续玩存档中。当你死亡或重新开始时，该存档将被销毁。\n\n铁人模式共 9 个阶段，你将遇到高等级敌人和 D0 至 D8 的首领。\n\n完成该模式约可获得 100+ 代币与精通点数。\n\n<b>难度：</b>具有挑战性",
"Mentalist": "「灵媒」模式共 6 个阶段，与「普通」模式类似，你将遇到中等等级的敌人和 D0 至 D5 的首领。与「普通」相比，「灵媒」的规则稍难，但你可以自选下一个节点：挑战精英？触发事件？开启宝箱？等等。\n\n踏上「灵媒」之旅前，建议先用你选定的组合至少通关一次「休闲」模式。\n\n完成该模式约可获得 55+ 代币与精通点数。\n\n<b>难度：</b>普通+",
"Seer": "「先知」模式共 9 个阶段，与「铁人」模式类似，你将遇到高等级敌人和 D0 至 D8 的首领。与「铁人」相比，「先知」的规则稍难，但你可以自选下一个节点：挑战精英？触发事件？开启宝箱？等等。\n\n踏上「先知」之旅前，建议先用你选定的组合至少通关一次「灵媒」模式。\n\n完成该模式约可获得 100+ 代币与精通点数。\n\n如果你想要死亡即永久的完整类 Rogue 体验，请不使用存档栏位系统。每次推进节点时，进度仍会自动保存到唯一的续玩存档中。当你死亡或重新开始时，该存档将被销毁。\n\n<b>难度：</b>具有挑战性+",
"Demigod": "「半神」模式共 12 个阶段，你将遇到比「先知」（或「铁人」）等级更高的敌人和 D0 至 D11 的首领。与「先知」类似，你可以自选下一个节点：挑战精英？触发事件？开启宝箱？等等。\n\n踏上「半神」之旅前，建议先用你选定的组合至少通关一次「先知」模式。\n\n完成该模式约可获得 160+ 代币与精通点数。\n\n如果你想要死亡即永久的完整类 Rogue 体验，请不使用存档栏位系统。每次推进节点时，进度仍会自动保存到唯一的续玩存档中。当你死亡或重新开始时，该存档将被销毁。\n\n<b>难度：</b>困难",
"Expert": "「专家」模式将「铁人」难度再提升几个档次并加入新机制。所有已解锁技能都可以在 1 级使用，且你的收藏中每一张已解锁的一阶卡牌都会获得一张，让你可以完全自定义起始牌库。\n\n这是一个无尽模式，唯有死亡或隐退才是你的出路。\n\n<b>你能走多远？</b>\n\n<b>难度：</b>困难+",
"Draft": "在轮抽模式中，你开局没有任何技能、牌库或专长，需要通过轮抽卡牌来组建初始牌库。\n\n你无法将卡牌转化为技能，也无法购买任何专长。\n\n<b>难度：</b>普通",
"Adventure": "探索 Erannorth 的世界，在沙盒/冒险模式中自由漫游。收集所有学科的卡牌，构筑不同的牌库，征服不断变化的魔法灵脉。在战术地图上自由选择探索哪些区域以及何时探索。\n\n<b>半动态世界：</b>\n每次开始（或续玩）该模式时，区域奖励都会改变。",
"Drifter": "探索 Erannorth 的世界，在这个沙盒/冒险模式的变体中自由漫游。开局拥有一个（最多）60 张卡牌的随机卡牌库，但没有起始牌库，也没有种族与职业技能卡。一路上收集更多学科的卡牌，构筑不同的牌库，征服不断变化的魔法灵脉。\n\n<b>动态世界：</b>\n每次开始（或续玩）该模式时，区域奖励与敌人等级都会改变。",
}

for mode, desc in T.items():
    src_f = os.path.join(SRC, mode + ".json")
    d = json.load(io.open(src_f, encoding="utf-8-sig"))
    assert d["Mode"] == mode, f"Mode 字段不匹配: {d['Mode']} != {mode}"
    d["ModeDescription"] = desc
    out_f = os.path.join(MOD, mode + ".json")
    with io.open(out_f, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print("written:", mode + ".json")

# refresh ModLoaderUser.conf with GameModes section
conf = ">> Language\n简体中文\n>> GameModes\n" + "\n".join(T.keys()) + "\n"
conf_path = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\StreamingAssets\Content\Mods\Chinese Localization\ModLoaderUser.conf"
with io.open(conf_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(conf)
print("ModLoaderUser.conf updated")
