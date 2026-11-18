# 字段与文件

路径都相对 `starsector-core/data/`。

## CSV 读取

用 Java 状态机，不要靠只认 UTF-8 的库。

- 字节流：合法 UTF-8 序列照常解码；单个非法字节按 Windows-1252（`0x92`→`’`，`0x94`→`”`）。写出时用 UTF-8。
- 记录：逗号分隔，双引号包裹，内部引号写成 `""`，引号内允许换行。`#` 开头的行是注释，原样保留。写出时这种单元格不要加引号，行首必须仍是 `#`，否则游戏会把它当成正式记录。
- 写出时，含逗号、引号、换行或首尾空格的单元格加引号。保持原文件的 `\r\n` 或 `\n`。
- 读完后每一数据行的列数必须等于表头。`rules.csv` 与 `rules/*.csv` 固定 7 列。

## 要译的 CSV 列

| 文件 | 键 | 翻译列 |
|---|---|---|
| campaign/abilities.csv | id | name, desc |
| campaign/commodities.csv | id | name, desc |
| campaign/industries.csv | id | name, desc |
| campaign/market_conditions.csv | id | name, desc |
| campaign/special_items.csv | id | name, tech/manufacturer, desc |
| campaign/submarkets.csv | id | name, desc |
| campaign/reports.csv | event_type+event_stage+channels+target_rel | subject, summary, assessment |
| campaign/rules.csv 与 campaign/rules/*.csv | id | text（按 OR 分段）, options（只译显示文字）, script（只译自然语言引号） |
| characters/personalities.csv | id | name, desc |
| characters/skills/aptitude_data.csv | id | name, description |
| characters/skills/skill_data.csv | id | name, description, author |
| hullmods/hull_mods.csv | id | name, tech/manufacturer, uiTags, desc, short, sModDesc |
| hulls/ship_data.csv | id | name, designation, tech/manufacturer, logistics n/a reason |
| hulls/wing_data.csv | id | role desc。`role` 列是枚举，不译 |
| shipsystems/ship_systems.csv | id | name |
| weapons/weapon_data.csv | id | name, tech/manufacturer, primaryRoleStr, customPrimary, customPrimaryHL, customAncillary, customAncillaryHL |
| strings/descriptions.csv | id+type | text1–text5 |

不译：`person_names.csv`、`name_gen_data.csv`（神话专名）、`bar_events.csv`、`factions.csv`、`sim_opponents.csv`、`drop_groups.csv` 以及各 procgen 数值表。`notes` 列是作者备忘，不进界面。

`shield type`、`hints`、`tags`、`plugin`、`script` 列里的类名不译。

## JSON 与类 JSON

扫描器要记录每个字符串值的路径和源码区间，替换时只改引号内的正文，保留注释和键顺序。

整份字符串值都要译：

- strings/strings.json
- strings/tips.json
- strings/tooltips.json
- world/factions/default_fleet_type_names.json

只译这些键：`name`、`displayName`、`displayNameWithArticle`、`desc`、`description`、`text`、`title`、`body`、`tip`、`short`、`shortType`、`defaultName`、`shortName`。

`type` 仅在 `campaign/channels.json` 里是显示文字。别处的 `type` 是代码。

还要处理：

- config/planets.json、custom_entities.json、tag_data.json、battle_objectives.json、contact_tag_data.json 的 name
- world/factions/*.faction 的显示名与官职 `name`。`shipNamePrefix`、颜色、舰船 id 不译
- characters/skills/*.skill 里的 `name`（如 Elite→精英）
- variants/**/*.variant 的 `displayName`（Custom→特装，Assault→突击，Strike→打击，Attack→进攻，Support→支援，Standard→标准）
- missions/*/descriptor.json 的 `title`。`difficulty` 保持 EASY/MEDIUM/HARD

不要译：`config/sounds.json`、`engine_styles.json`、`hull_styles.json`、`campaign/econ/*.json`、`events.json`、`pings.json`、`starmap.json`、`terrain.json`。`.skin` 没有玩家句子。

`settings.json` 只改 `cjkMode`，以及确实显示给玩家的字符串。有旧版译文且英文完全相同时可以沿用。不要改数值、路径、类名。

## 源码与 txt

`data/**/*.java` 里的自然语言字符串（船体插件提示、星系描述、任务简报、舰船系统状态名）要译。保留 Java 转义。代码、枚举、id 不译。这些文件由游戏里的 Janino 编译。

要译的 txt：

- codex/spacers_manual_*.txt、codex/game_mechanics.txt
- missions/*/mission_text.txt

## 安装包布局

```
output/
  starsector-core/...   # 只放改过的文件，相对路径与游戏一致
  安装汉化.bat
```

bat 的行为：若同级还没有 `starsector-core.backup`，先把整个 `starsector-core` 复制成备份；然后再把 `output/starsector-core` 覆盖进游戏目录。不要在备份已存在时删掉玩家后来的存档目录（存档不在 core 里）。
