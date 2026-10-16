# -*- coding: utf-8 -*-
"""In-place equal-length UTF-16 patch of the #US heap in Assembly-CSharp.dll.

Two tables:
  SINGLE: plain string literals (one heap blob each).
  CHUNKS: literal chunks of interpolated strings ($"...{x}..."); each chunk is
          itself one heap blob. Only chunks vetted as display-only.
Every translation is padded with trailing spaces to the exact original length
(UTF-16 code units), so blob sizes and all metadata offsets stay untouched.

Run with --check to only report (length/miss/occurrence audit), no write.
"""
import sys, os, io, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usheap

DLL = usheap.DLL
SRC = r"C:\Users\ADMINI~1\AppData\Local\Temp\eran_decomp\Assembly-CSharp.decompiled.cs"

SINGLE = {
    # ---- buttons / labels ----
    'Choose & Draw': '选择并抽牌',
    'Choose & Play': '选择并打出',
    'End Turn': '结束回合',
    'Start': '开始',
    'Start!': '开始！',
    'Enter': '进入',
    'Travel': '旅行',
    'Travel to ': '前往 ',
    'Enter the Settlement of ': '进入聚落：',
    'Explore - ': '探索 - ',
    'Got it!': '明白了！',
    'Accept': '接受',
    'Decline': '拒绝',
    'Continue': '继续',
    'Locked': '已锁定',
    'Refill': '补货',
    'Minimum Deck': '最小牌库',
    'Add to Inventory': '加入物品栏',
    'Search Perks': '搜索专长',
    'Search for Cards, Effects or Disciplines': '搜索卡牌、效果或学科',
    'Search for Enemies or Archetypes': '搜索敌人或原型',
    'Click on a Race or Class Icon (or use the Search field) to get started!': '点击种族或职业图标（或使用搜索框）开始！',
    # ---- notices / log ----
    'Ambushed!': '遭遇伏击！',
    'Deck Reshuffled!': '牌库已重洗！',
    'Killed all Enemies!': '歼灭所有敌人！',
    'Enemy Reinforcements!': '敌方增援！',
    'Cards Left: ': '剩余卡牌：',
    'Cards in Deck: ': '牌库中卡牌：',
    'Cards in View: ': '视野中卡牌：',
    'Deck Size: ': '牌库数量：',
    'Cards: ': '卡牌：',
    'Starting Cards: ': '起始卡牌：',
    'Level ': '等级 ',
    ', Lvl ': '，等级 ',
    'Only ': '仅 ',
    'Players ': '玩家 ',
    'Portraits: ': '头像：',
    'Organization: ': '组织：',
    ' Expertise: ': ' 专长：',
    ' Influence: ': ' 影响力：',
    ' Mastery: ': ' 精通：',
    ' Mastery: +': ' 精通：+',
    'Mastery ': '精通 ',
    ' Mastery modified by ': ' 精通修改自 ',
    ' Mastery. Total: ': ' 精通，总计：',
    ' Mastery.': ' 精通。',
    ' modified by ': ' 修改自 ',
    # ---- '>' log family ----
    '>Health: ': '>生命：',
    '>Actions: ': '>行动：',
    '>Casting: ': '>施法：',
    '>Discarded: ': '>弃牌：',
    '>Equipped: ': '>装备：',
    '>Farthings: ': '>铜币：',
    '>Farthings: +': '>铜币：+',
    '>Ingredient: ': '>原料：',
    '>Karma: ': '>业力：',
    '>Karma: +': '>业力：+',
    '>LevelUp Points: ': '>升级点数：',
    '>LevelUp Points: +': '>升级点数：+',
    '>Mastery: ': '>精通：',
    '>Mastery: +': '>精通：+',
    '>Order: ': '>教团声望：',
    '>Order: +': '>教团声望：+',
    '>Perk Points: ': '>专长点数：',
    '>Perk Points: +': '>专长点数：+',
    '>Rations: ': '>口粮：',
    '>Rations: +': '>口粮：+',
    '>Received Action: ': '>获得卡牌：',
    '>Received Equipment: ': '>获得装备：',
    '>Received: ': '>获得：',
    '>Recipe Result: ': '>配方结果：',
    '>Recipe: ': '>配方：',
    '>Time Advances: +': '>时间推进：+',
    '>Tokens: ': '>代币：',
    '>Tokens: +': '>代币：+',
    '>Used: ': '>已使用：',
    '>You can carry ': '>你最多携带 ',
    '>You can carry +': '>你最多携带 +',
    '>You gain: +': '>获得：+',
    '>You lose: ': '>失去：',
    '>You receive: ': '>你获得：',
    ">You can't carry any more rations!</color></i></size>": '>口粮已达携带上限！</color></i></size>',
    ">You don't have enough coin!</color></i></size>": '>铜币不足！</color></i></size>',
    ">You don't have enough rations to fully benefit from rest!</color></i></size>": '>口粮不足，无法充分休息！</color></i></size>',
    '>You purchase Rations x1. You spend 25 Farthings.</color></i></size>': '>你购买了 1 份口粮，花费 25 铜币。</color></i></size>',
    '> Rest restores 15 HP & 15 AP. All Ailments and Debuffs are removed. You spend 1 Rations. </color></i></size>': '> 休息恢复 15 HP 和 15 AP，移除所有症状与减益，消耗 1 份口粮。</color></i></size>',
    '>Rest restores 5 HP & 5 AP.</color></i></size>': '>休息恢复 5 HP 和 5 AP。</color></i></size>',
    '>Feeding restores 15 HP, 15 AP and removes Bleeding. </color></i></size>': '>进食恢复 15 HP、15 AP 并移除流血。</color></i></size>',
    '>Ingredients Consumed. </color></i></size>': '>已消耗原料。</color></i></size>',
    '>Insufficient Ingredients. </color></i></size>': '>原料不足。</color></i></size>',
    ">It's Daybreak.</color></i></size>": '>天亮了。</color></i></size>',
    ">It's Nightfall.</color></i></size>": '>天黑了。</color></i></size>',
    # ---- suffixes ----
    ' AP.</color></i></size>': ' AP。</color></i></size>',
    ' Cards.</color></i></size>': ' 张卡牌。</color></i></size>',
    ' Days.</color></i></size>': ' 天。</color></i></size>',
    ' Farthings.</color></i></size>': ' 铜币。</color></i></size>',
    ' HP.</color></i></size>': ' HP。</color></i></size>',
    ' Hours.</color></i></size>': ' 小时。</color></i></size>',
    ' Rations.</color></i></size>': ' 口粮。</color></i></size>',
    ' XP.</color></i></size>': ' XP。</color></i></size>',
    '!</color></i></size>': '！</color></i></size>',
    ' added to your Inventory!': ' 已加入你的物品栏！',
    ' is already in your Inventory!': ' 已在你的物品栏中！',
    ' is locked!': ' 已锁定！',
    ' gained: ': ' 获得：',
    ' xp.': ' 经验。',
    ' iterations.': ' 次迭代。',
    ' : Stage ': ' ：阶段 ',
    ' Cards: ': ' 卡牌：',
    ' Card Set.': ' 卡牌套装。',
    ' Card already exists. Use <b>ReDefine</b> to replace.': ' 卡牌已存在。使用 <b>ReDefine</b> 替换。',
    " Couldn't find a card <b>": ' 找不到卡牌 <b>',
    " Couldn't find an Enemy <b>": ' 找不到敌人 <b>',
    " from the Action Database! Make sure it's not used in your Run!": ' 来自行动数据库！请确保它未在你的运行中使用！',
    ' in Deck (Reshuffle when done adding Cards)': ' 张在牌库中（加完卡牌后重洗）',
    '*Starting Deck Cards are also Skills': '*起始牌库卡牌同时也是技能',
    # ---- dialogs / info ----
    "You don't have enough Tokens. Clear a few stages to gather more!": '代币不足。多通关几个阶段来获取更多代币！',
    'All the fields are required!': '所有字段均为必填！',
    'Enforce Full Artwork Cards is On': '强制启用全卡面：开',
    'Enforce Full Artwork Cards is Off': '强制启用全卡面：关',
    '<size=24>Action Effect</size>\n\n': '<size=24>卡牌效果</size>\n\n',
    '<size=24>Gameplay Basics</size>\n\n': '<size=24>游戏基础</size>\n\n',
    '<size=24>Status</size>\n\n': '<size=24>状态</size>\n\n',
    '<b><size=15>Something is different!</size></b>\n<i>Looks like I can no longer do this!</i>': '<b><size=15>有什么东西不一样了！</size></b>\n<i>看来我已经无法这样做了！</i>',
    '[<b>Combat Result:</b> Victory!]\n': '[<b>战斗结果：</b>胜利！]\n',
    ' (Class)</b>\n': '（职业）  </b>\n',
    ' (Race)</b>\n': '（种族）  </b>\n',
    '(Class)</b>\n': '（职业）</b>\n',
    '(Race)</b>\n': '（种族）</b>\n',
    ' (Settlement)</color>': '（聚落）</color>',
    ' (You are denied entry)</color>': '（你被拒绝入内）</color>',
    '</b> <i>(Card Names are Case Sensitive.)</i>': '</b> <i>（卡牌名区分大小写。）</i>',
    '</b> <i>(Enemy Names are Case Sensitive.)</i>': '</b> <i>（敌人名区分大小写。）</i>',
    '</b>: Updating...': '</b>：更新中……',
    '<color=white><b>Farthings: </b></color>': '<color=white><b>铜币：</b></color>',
    '<color=white><b>Rations: </b></color>': '<color=white><b>口粮：</b></color>',
    '(Already in Inventory)': '（已在物品栏中）',
    "(Can't Sell Equipped Items)": '（无法出售已装备物品）',
    "(Can't own more Copies)": '（已达持有上限）',
    "(Can't sell Equipped Items)": '（无法出售已装备物品）',
    'Beautify ON': '美化：开',
    'Beautify OFF': '美化：关',
    'Beautify (DoF transparency support is ON)': '美化（景深透明支持：开）',
    'Beautify (Dof transparency support is OFF)': '美化（景深透明支持：关）',
    "Console Commands are available during the Player's Turn only": '控制台命令仅可在玩家回合使用',
    'Hold on! This may take a while...': '请稍候！这可能需要一点时间……',
    'Processing Request...': '正在处理请求……',
    'Connecting to Steam...': '正在连接 Steam……',
    'Creating Mods Directory...': '正在创建 Mods 目录……',
    'Unpacking...': '解包中……',
    'Uninstalling Mod...': '正在卸载 Mod……',
    'Sucessfully submitted item to Steam': '已成功提交至 Steam',
    'Steam Workshop Mods are <b>Active</b>': 'Steam 创意工坊 Mod：<b>已启用</b>',
    'Steam Workshop Mods are <b>Inactive</b>': 'Steam 创意工坊 Mod：<b>已停用</b>',
    'Steam Workshop appears offline. Try again a bit later!': 'Steam 创意工坊当前离线，请稍后再试！',
    'You are currently disconnected from Steam. Please login and try again!': '当前未连接到 Steam，请登录后重试！',
    'You already have a Steam Workshop item with that name.': '你已拥有同名 Steam 创意工坊物品。',
    'You have exceeded your Steam Cloud quota. Remove some items and try again!': '已超出 Steam 云配额，请移除部分物品后重试！',
    'You need to accept the Steam Workshop Agreement before uploading any items there!': '上传前需先接受 Steam 创意工坊协议！',
    'Your account appears currently restricted from uploading in the Workshop. Please contact Steam Support.': '你的账户似乎被限制在创意工坊上传内容，请联系 Steam 客服。',
    'Your account appears restricted from uploading content due to a hub ban, account lock, or community ban. Please contact Steam Support.': '你的账户因枢纽封禁、账户锁定或社区封禁而被限制上传内容，请联系 Steam 客服。',
    'One of the submission fields contains something not being accepted by that field. Check them and try again!': '某个提交字段包含不被接受的内容，请检查后重试！',
    'Operation timed out. Check that all fields are set correctly and try again!': '操作超时。请确认所有字段填写正确后重试！',
    'There was a problem trying to save the title and description. Access was denied. Check them and try again!': '保存标题和描述时出错，访问被拒绝，请检查后重试！',
    'The item update is committing all changes.': '正在提交物品的所有更改。',
    'The item update is processing configuration data.': '正在处理物品的配置数据。',
    'The item update is reading and processing content files.': '正在读取并处理物品的内容文件。',
    'The item update is uploading content changes to Steam.': '正在向 Steam 上传物品的内容更改。',
    'The item update is uploading new preview file image.': '正在上传物品的新预览图。',
    'The item update handle was invalid, the job might be finished, a SubmitItemUpdateResult_t call result should have been returned for it.': '物品更新句柄无效，任务可能已完成，应已返回 SubmitItemUpdateResult_t 调用结果。',
    "Steam Uploader wasn't properly initialized. Try restarting your Mod Manager!": 'Steam 上传器未正确初始化，请重启 Mod 管理器！',
    "Couldn't create a new item! Error Code: ": '无法创建新物品！错误码：',
    "Couldn't submit the item to Steam. Error Code: ": '无法提交至 Steam。错误码：',
    'Something went wrong! Error Code: ': '出错了！错误码：',
    'Something went wrong! Make sure Steam is Active & that all fields are properly set!': '出错了！请确认 Steam 处于运行状态且所有字段均已正确填写！',
    'Duplicate request. File was already successfully uploaded!': '重复请求。文件已成功上传！',
    'Step 0/2: Check if Item exists.': '步骤 0/2：检查物品是否存在。',
    'Step 1/2: Creating Steam Workshop Item.': '步骤 1/2：创建创意工坊物品。',
    'Step 2/2: Setting Item Details.': '步骤 2/2：设置物品详情。',
    'Step 2/2: Updating Item Details.': '步骤 2/2：更新物品详情。',
    'Detected an older version of <b>': '检测到旧版本 <b>',
    'A mod with this title already exists: <b>': '已存在同名 Mod：<b>',
    'Hmm... Something is not right. It would be better to Uninstall this Mod Manually!': '嗯……有哪里不对。建议手动卸载此 Mod！',
    "This file doesn't seem to exist! Did you pasted the path correctly?": '文件似乎不存在！请检查粘贴的路径是否正确。',
    'You need to specify a filename without the json extension. ': '请指定不带 json 扩展名的文件名。',
    'You need to specify the Game Mode Name without the json extension. ': '请指定不带 json 扩展名的游戏模式名。',
    'Need a number between 1 & ': '需要 1 到 ',
    'Template Retrieved! Edit at least the Cardname!': '已获取模板！请至少修改卡牌名！',
    'Template Retrieved! Enter to confirm any changes to Cardname!': '已获取模板！按回车确认卡牌名的修改！',
    'Card Added Temporarily in Actions Database!': '已临时将卡牌加入行动数据库！',
    'Card Creation Result: Error in Definition': '卡牌创建结果：定义有误',
    'Duplicate Entry Result: a ': '重复条目结果：',
    'Added Card: ': '已添加卡牌：',
    'Received Card: ': '获得卡牌：',
    'Added a new Node and set it to: ': '已添加新节点并设为：',
    'Current Node set to: ': '当前节点设为：',
    'Current Stage set to: ': '当前阶段设为：',
    'Next Node set to: ': '下一节点设为：',
    'Starting Event with ID: ': '正在启动事件，ID：',
    'No Event found with ID: ': '未找到 ID 如下的事件：',
    'Progress Loaded from ': '进度读取自 ',
    'Progress Saved as ': '进度保存为 ',
    'Fetched ': '已获取 ',
    'Removed ': '已移除 ',
    'Conquest Mode Requires either the War for Roverford or Canticum Noctem DLCs': '征服模式需要 War for Roverford 或 Canticum Noctem 资料片',
    "<b>Expansion Activated:</b> It's recommended to restart the ModManager.": '<b>资料片已启用：</b>建议重启 Mod 管理器。',
    "<b>Expansion Deactivated:</b> It's recommended to restart the ModManager.": '<b>资料片已停用：</b>建议重启 Mod 管理器。',
    "<b>Mod Activated:</b> It's recommended to restart the ModManager.": '<b>Mod 已启用：</b>建议重启 Mod 管理器。',
    "<b>Mod Deactivated:</b> It's recommended to restart the ModManager.": '<b>Mod 已停用：</b>建议重启 Mod 管理器。',
    "<b>Mod Installed:</b> It's recommended to restart the ModManager.": '<b>Mod 已安装：</b>建议重启 Mod 管理器。',
    "<b>Mod Uninstalled:</b> It's recommended to restart the ModManager.": '<b>Mod 已卸载：</b>建议重启 Mod 管理器。',
    # ---- string.Format single-blob tooltips ----
    '{0} Card Set.<size=16><color=white> New Tiers unlock when <i>{0}</i> Mastery ({1}) reaches: 15,30,60,90 & 120. </color></size>': '{0} 卡牌套装。<size=16><color=white>当 <i>{0}</i> 精通（{1}）达到 15、30、60、90、120 时解锁新阶级。</color></size>',
    '{0}/{1} Card Set.<size=16><color=white> New Tiers unlock when <i>{0}</i> Mastery ({2}) reaches: 15,30,60,90 & 120. </color></size>': '{0}/{1} 卡牌套装。<size=16><color=white>当 <i>{0}</i> 精通（{2}）达到 15、30、60、90、120 时解锁新阶级。</color></size>',
    # ---- stage / event buttons (GenerateEvent 3rd arg: display-only) ----
    'Search': '搜索',
    'Read': '阅读',
    'Leave': '离开',
    'Set Camp': '扎营',
    'Approach bandit camp': '接近强盗营地',
    'Steal from his Strongbox': '撬开他的保险箱',
    'Enter the dungeon': '进入地牢',
    'Look at his Wares': '看看他的货物',
    'Ignore the alternative path': '无视岔路',
    'Stop by the nearby Town': '在附近小镇停留',
    'Purchase ( 25F )': '购买（25F）',
    'Explore the cave': '探索洞穴',
    'Explore the alternative path': '探索岔路',
    # ---- exploration / rest log lines ----
    'You decide to explore the old Ruins.': '你决定探索古老的废墟。',
    'You decide to explore the Destroyed Village.': '你决定探索被毁的村庄。',
    'You decide to explore the old ruins.': '你决定探索古老的废墟。',
    'You decide to explore the destroyed village.': '你决定探索被毁的村庄。',
    'You decide to explore the old temple.': '你决定探索古老的神庙。',
    'You decide to explore the old Temple.': '你决定探索古老的神庙。',
    "You don't have enough rations to rest!": '口粮不足，无法休息！',
    "You don't have enough coin!": '铜币不足！',
    "You can't carry any more rations!": '口粮已达携带上限！',
    '<b>You can\'t save your progress while enemies are present!</b>': '<b>存在敌人时无法保存进度！</b>',
    "You don't have enough Actions Points to use: ": '行动点不足，无法使用：',
    "You don't have any consumables left in your Drawpile.": '抽牌堆中已没有可用的消耗品。',
    ">Your Hand is full (20+ Cards). You can't create or draw new Cards!</color>": '>手牌已满（20+ 张），无法创建或抽取新卡牌！</color>',
    'Enemy will summon Reinforcements.': '敌人将召唤增援。',
    'Expansion: {0}': '资料片：{0}',
    # ---- game-mode description fragments ----
    '\n\n<b>Recommended For:</b> Characters with <b>0</b> Race and Class Mastery.': '\n\n<b>推荐：</b>种族与职业精通为 <b>0</b> 的角色。',
    '\n\n<b>Recommended For:</b> Characters with at least <b>30+</b> Race and Class Mastery.': '\n\n<b>推荐：</b>种族与职业精通至少为 <b>30+</b> 的角色。',
    '\n\n<b>Recommended For:</b> Characters with at least <b>90+</b> Race and Class Mastery.': '\n\n<b>推荐：</b>种族与职业精通至少为 <b>90+</b> 的角色。',
    '\n\n<b>Recommended For:</b> Characters with at least <b>120+</b> Race and Class Mastery.': '\n\n<b>推荐：</b>种族与职业精通至少为 <b>120+</b> 的角色。',
    '\n\n<b>Recommended For:</b> Characters with at least <b>120+</b> Race and Class Mastery or more.': '\n\n<b>推荐：</b>种族与职业精通达 <b>120+</b> 或更高的角色。',
    "it's permanent, and you'll have to restart with a new character.\n\n": '本模式为永久死亡，需以新角色重新开始。\n\n',
    'you may choose to retain your savefile at no penalty.\n\n': '可选择保留存档且不受惩罚。\n\n',
    'you may choose to retain your savefile losing ': '可选择保留存档，但将失去 ',
    ' Tokens per Stage Cleared.\n\n': ' 个代币（每通过一个阶段）。\n\n',
    '\n\n<b>Completion Bonus:</b>\n': '\n\n<b>通关奖励：</b>\n',
    '\n\n<b>Stages:</b> ': '\n\n<b>阶段：</b> ',
    '\n\n<b>Stages:</b> Endless': '\n\n<b>阶段：</b>无尽',
    '\n\n<b>Stages:</b> Endless ': '\n\n<b>阶段：</b>无尽 ',
    ' Tokens & ': ' 代币与 ',
    " Difficulty:</b> If your character dies ": ' 难度：</b>若你的角色死亡 ',
    ' Farthings.': ' 铜币。',
    ' HP. ': ' HP。',
    ' Actions per turn without incurring a Fatigue Penalty.': ' 个行动/回合，且不会产生疲劳惩罚。',
    '\n\n<b>Fatigue:</b>You can use ': '\n\n<b>疲劳：</b>每回合可使用 ',
    ' extra XP to spend in Perks. ': ' 点额外经验用于专长。',
    '% XP & starts with ': '% 经验，且起始 ',
    '<b>Special Rules:</b>Your character gains ': '<b>特殊规则：</b>你的角色获得 ',
    'You start at Level ': '你起始等级为 ',
    'And your initial Wealth is set to ': '你的初始财富为 ',
    '<b>Invalid Character Combination</b>\nYou should choose two different Archetypes!': '<b>无效的角色组合</b>\n你应选择两个不同的原型！',
    '\nMax Reinforcement Waves: <b>{0}</b> ': '\n最大增援波数：<b>{0}</b> ',
    '\nMax Reinforcement Waves: <b>Endless</b> ': '\n最大增援波数：<b>无尽</b> ',
}

# full string.Format blobs (what $-interpolations compile to); each is ONE heap
# blob with {0}/{1} placeholders kept verbatim. All vetted display-only.
# NOTE: '{0} - Lv {1}' is deliberately NOT here — it builds enemy lookup keys.
FMT = {
    'You searched for: {0} // {1} Cards Found.': '搜索：{0} // 共找到 {1} 张卡牌。',
    '<b>Active Filter: </b> {0}': '<b>激活筛选：</b>{0}',
    '<b>Active Filter: </b> Only {0}': '<b>激活筛选：</b>仅 {0}',
    'Buy {0}F': '购买 {0}F',
    'Sell {0}F': '出售 {0}F',
    'You can pick up to {0} Cards.': '你最多可以选择 {0} 张卡牌。',
    'Score: <b>{0}</b>': '评分：<b>{0}</b>',
    'New Value Set: {0} => {1}. (Feel free to modify a different value)': '新值已设置：{0} => {1}。（可继续修改其他值）',
    'You can spend up to <b>{0}</b> PP & give extra Perks to your Character.': '你最多可以使用 <b>{0}</b> 点专长点数，为角色添加额外专长。',
    'Active Perks ({0})': '已激活专长（{0}）',
    '<b>Archetype {0}</b>\n\n{1}': '<b>原型 {0}</b>\n\n{1}',
    '{0} - {1}/{2} - Lv {3} @{4}': '{0} - {1}/{2} - 等级 {3} @{4}',
    '{0}/{1} Lv {2}': '{0}/{1} 等级 {2}',
    '(-{0} Tokens)': '（-{0} 代币）',
    '<color=red>-{0} Tokens</color> {1}': '<color=red>-{0} 代币</color> {1}',
    '<b>Reward:</b> Pick 2 Card(s) out of {0} random choices.': '<b>奖励：</b>从 {0} 个随机选项中挑选 2 张卡牌。',
    '<b>Reward:</b> Pick {0} Card(s) out of {1} random choices.': '<b>奖励：</b>从 {1} 个随机选项中挑选 {0} 张卡牌。',
    'Requires <b>{0}</b> DLC.\nOr a mod implementing {1}.json.': '需要 <b>{0}</b> 资料片。\n或需实现 {1}.json 的 Mod。',
    'Enemy Reinforcements!\nWave {0}/{1}': '敌方增援！\n第 {0}/{1} 波',
    '<color=black>Abandon this run & Retire your character to the Book of Heroes?</color>\n<b>Cost</b>: <i>{0}</i> Farthings & <i>{1}</i> Rations.': '<color=black>放弃本次冒险并让角色荣退至英雄之书？</color>\n<b>花费</b>：<i>{0}</i> 铜币与 <i>{1}</i> 口粮。',
    '<b>{0}</b> (Expansion)': '<b>{0}</b>（资料片）',
    'Add to Deck (Owned x{0})': '加入牌库（已有 x{0}）',
    'Add to Stash (Owned x{0})': '加入仓库（已有 x{0}）',
    'Retire {0}?': '让 {0} 退役？',
}


def main(check_only):
    buf = bytearray(open(DLL, 'rb').read())
    us_start, us_size, blobs = usheap.parse(bytes(buf))
    print(f"#US heap @{us_start:#x} size {us_size:#x}, {len(blobs)} blobs")

    # index: decoded string -> [(offset, prefix_len, size, data)]
    idx = {}
    for off, plen, size, data in blobs:
        s = usheap.decode(data)
        if s is not None:
            idx.setdefault(s, []).append((off, plen, size, data))

    problems, plan = [], []
    for table in (SINGLE, FMT):
        for orig, tr in table.items():
            # format-string safety: same placeholders, same order set
            for ph in re.findall(r'\{\d+\}', orig):
                if ph not in tr:
                    problems.append(f"PLACEHOLDER LOST {ph}: {orig!r}")
            if orig not in idx:
                problems.append(f"NOT IN HEAP: {orig!r}")
                continue
            if len(tr) > len(orig):
                problems.append(f"TOO LONG ({len(tr)}>{len(orig)}): {orig!r} -> {tr!r}")
                continue
            padded = tr + ' ' * (len(orig) - len(tr))
            for off, plen, size, data in idx[orig]:
                new_data = usheap.encode(padded, data)
                if len(new_data) != len(data):
                    problems.append(f"BYTE LEN MISMATCH {orig!r}")
                    continue
                plan.append((off, plen, size, data, new_data, orig, padded))

    print(f"plan: {len(plan)} blob patches, problems: {len(problems)}")
    for p in problems: print("  !", p)

    if check_only:
        return 0 if not problems else 1

    # apply
    assert len(plan) > 100, "suspiciously few patches"
    changed = set()
    for off, plen, size, data, new_data, orig, padded in plan:
        pos = us_start + off + plen
        buf[pos:pos+len(data)] = new_data
        changed.update(range(pos, pos + len(data)))
    # verify all changes inside #US region
    bad = [o for o in changed if not (us_start <= o < us_start + us_size)]
    assert not bad, f"changes outside #US heap: {bad[:5]}"

    # re-parse and validate
    us_start2, us_size2, blobs2 = usheap.parse(bytes(buf))
    assert (us_start2, us_size2) == (us_start, us_size)
    dec = [usheap.decode(d) for _, _, _, d in blobs2]
    assert all(s is not None for s in dec), "decode failure after patch"

    tmp = DLL + '.new'
    open(tmp, 'wb').write(buf)
    os.replace(tmp, DLL)
    print(f"patched {len(plan)} blobs, written {DLL}")
    return 0


if __name__ == '__main__':
    sys.exit(main(check_only='--check' in sys.argv))
