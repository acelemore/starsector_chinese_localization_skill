---
name: starsector-l10n
description: >-
  Localize the game Starsector (远行星号) and its mods into Simplified Chinese:
  CSV, lenient JSON, loose Java sources, and jars. Use when translating
  Starsector, 远行星号, starsector-core, rules.csv, starfarer.api.jar,
  starfarer_obf.jar, or a mod under mods/. Translations must follow
  glossary.tsv in this skill.
---

# 远行星号汉化

译文必须遵循同目录 [glossary.tsv](glossary.tsv)（英文、中文、来源，制表符分隔）。势力名另见 [factions.tsv](factions.tsv)。表中已有译名不得另起炉灶。表里没有的舰船、武器、船体插件、技能，先按表内同类构词翻译，并追加到表中。

目标版本以 `starfarer_obf.jar` 里的版本串为准（本工作流针对 0.98.5a 这一支）。游戏目录是 `starsector-core`。只覆盖玩家能看见的文本。

## 两种起点

流程相同。先看有没有上一版记忆或一份旧版译文可以对照。

- 有上一版记忆：走下面的增量对照。英文没变的沿用记忆里的中文。英文改过或新出现的才翻译。记忆和 glossary.tsv 冲突时，以 glossary 为准。
- 有旧版译文、还没有记忆：先做一次快照，以后按增量对照。也可以用对齐脚本按稳定 id、JSON 路径、方法内字符串序号套用，对不上的才翻译。
- 从零翻译：不运行对齐脚本，也不套记忆。按字段表抽出全部玩家可见句子，按 glossary 翻译。表里没有的专名先按同类构词译出并写入 glossary，再译句子。某个模组第一次做，先按「模组清点」交规模清单，用户确认后再改文件。

日志、异常、键名、路径三种情况下都不译。

## 增量翻译

原版和每个模组分开存放，记忆不能混用。

- 原版：`l10n_work/projects/vanilla/`
- 模组：`l10n_work/projects/mods/<mod id>/`

每个项目有 `memory/<版本>.jsonl`（该版英文和已经写出的中文）、`incoming/<版本>.jsonl`（新版英文）、`diff/<版本>/`（对照结果）。`l10n_work/chunks/` 和 `l10n_work/state/` 是 0.98.5a-RC7 的工作档案，新版本写进项目目录，不要追加到那里。

更新前先快照。英文目录必须是纯英文（更新前的 `starsector-core.backup`），中文目录是已经汉化的那一版。0.98.5a-RC7 的原版记忆已经写好。游戏更新后 `starsector-core` 会变成新版纯英文，那时再抽取、对照。

```
python l10n_work\tools\snapshot_memory.py --project vanilla --version 0.98.5a-RC7 --kind vanilla --en-root starsector-core.backup --zh-root starsector-core
python l10n_work\tools\extract_catalog.py --root starsector-core --cache l10n_work\projects\vanilla\cache\新版本 --out l10n_work\projects\vanilla\incoming\新版本.jsonl
python l10n_work\tools\diff_catalog.py --old l10n_work\projects\vanilla\memory\0.98.5a-RC7.jsonl --new l10n_work\projects\vanilla\incoming\新版本.jsonl --out l10n_work\projects\vanilla\diff\新版本
```

模组把 `--project` 设为 `mod_info.json` 的 `id`，`--kind mod`，`--en-root` / `--root` 指向该模组根目录。版本号用 `mod_info.json` 的 `version` 拼出来，并记下其中的 `gameVersion`。这次抽取只覆盖原版字段表，不含模组 jar，也不含模组自有的列和键。jsonl 的行数不是待译条数。做法见「模组清点」。

对照按条目进行，不是看到相同英文就全局套用：

- CSV：分组是「文件 + 键 + 列」。同一 id 出现多次时，按该文件里的出现顺序做序列对照。
- JSON：分组是「文件 + 字段路径」。
- Java、txt、jar：分组是同一个文件，或同一个方法（类 + 方法 + 描述符）里的字符串序列。方法内序号跨版本会变，所以用序列对照。同一版本的中英文 jar 仍按序号配对，因为中文 jar 是在那一版英文 jar 上替换出来的。

四类结果：

- `unchanged.jsonl`：英文没变，沿用 `zh`。
- `modified.jsonl`：同一位置的英文被改过，哪怕没有新增行。`old_zh` 只作参考。
- `added.jsonl`：新句子，按术语表翻译。
- `removed.jsonl`：新版已没有，不要写回。

`starfarer_obf.jar` 的类名和方法名会随版本重新混淆。按容器名直接对照，会把没改的句子看成上万条新增和删除。先按「同一个方法里的英文字符串序列」做指纹配对：指纹相同就整段沿用旧译文，指纹不同再用序列对照。`starfarer.api.jar` 的类名稳定，可以按类名和方法名对照。同一版本的中英文 jar 仍按方法内序号配对，因为中文 jar 是在那一版英文 jar 上替换出来的。

写回：

- `unchanged` 按新版的位置写入记忆里的中文。
- 正文有改动时按新英文重译。英文只是错字、旧中文已经是修正后的意思时，沿用旧中文。
- `script` 以新版脚本为底，只译引号里的自然语言。不要用旧脚本整段覆盖，否则会退回旧逻辑。
- `options` 保留新版选项 id，只译最后一个冒号后面的显示文字。
- 句子挪到新的规则 id、原来的格子被清空时，空格子保持空白，译文写到新位置。
- 版本号保持新版英文，不要把旧版本号写回去。
- 日志、异常、键名、路径、类名、音效 id、市场 id，以及 `DEV` 调试行，即使落在 `modified` 或 `added` 里也不译。

写回会盖掉纯英文目录。下一版记忆用写回前保存的 `incoming` 英文目录，配上写回后再抽出的中文目录。

## 工作流

1. 用 Java 读入全部 CSV（见 [reference.md](reference.md)）。不要用只认 UTF-8 的解析器：`rules.csv` 含 Windows-1252 字节（`0x92` 右单引号、`0x94` 右双引号）。
2. 用宽松 JSON 扫描器处理 `.json` `.faction` `.skill` `.variant`。游戏文件允许 `#` 与 `//` 注释、尾逗号、无引号键、单引号字符串、数字后的 `f`、个别分号当逗号。
3. 按下面的字段表抽出句子。同一英文在已确认语境里只有一个译文时，可以复用。
4. 翻译新句子。写回时保持文件还能被游戏解析。
5. 原版只改这两个 jar 里玩家能看见的字符串：`starfarer.api.jar`、`starfarer_obf.jar`。日志、异常、键名、路径不译。模组 jar 见「模组源码」。
6. `data` 下的 `.java` 与任务/法典 `.txt` 由游戏运行时编译或直接显示，改源码，不要自己编进 jar。
7. 原版成品镜像游戏相对路径，放到覆盖目录。安装脚本先整份备份 `starsector-core`，再覆盖。模组成品见「模组清点」，不要备份或覆盖 `starsector-core`。
8. JSON 字符串替换完成后再把游戏本体 `starsector-core/data/config/settings.json` 里的 `"cjkMode"` 设为 `true`（中日韩折行）。字体见下面的「字体」。模组自己的 `settings.json` 多半是数值覆盖，不要往里面写 `cjkMode`。

## 字体

汉字要正常显示，游戏里必须有这些文件，否则界面只剩方框：

- `graphics/fonts` 下的 `.fnt`、`.png`，以及其中的 `dyn_font`
- `native/windows/ss_dyn_font.dll`

没有特殊情况时，这份动态字体 DLL 可以一直沿用，不必随小版本更换。本机已经备好时，放在技能目录的 `fonts/` 下，相对路径与游戏内一致，安装时覆盖到 `starsector-core`。

动手写回或安装之前先检查这些文件在不在。缺任何一个，就停下来告诉用户：到远行星号中文站 <https://www.fossic.org/> 下载「覆盖压缩包」版本的汉化，把下载到的 zip 交给代理。不要自己去下载。用户交出 zip 之后，从包里取出上面的字体和 `ss_dyn_font.dll`，覆盖进 `starsector-core` 的对应位置，并放到技能目录的 `fonts/` 里供以后使用。

## 必须遵守的译法

- 简体中文，科幻军事书面语。中文之间不加空格。
- `$变量`、`$变量.方法` 原样保留，大小写不变。名词类变量（势力、市场、舰船、人名、金额）一个都不能丢。
- 纯语法变量可以删或挪位置：以 `AOrAn`、`IsOrAre` 结尾的，以及 `$heOrShe` `$HeOrShe` `$hisOrHer` `$HisOrHer` `$himOrHer` `$hesOrShes`。势力文件里的 `personNamePrefixAOrAn`、`displayNameIsOrAre` 中文版留空字符串。
- `printf` 占位符个数与类型必须与原文一致。数值高亮写成 `{%s}`（游戏先 `String.format`，再把 `{...}` 高亮）。不要调换 `%s` 的含义；语序必须变时改用 `%1$s` 这类序号，并确认该调用点走的是 `String.format`。
- `rules.csv` 的 `text` 用单独一行的 `OR` 分备用句（文件里是 `\r\nOR\r\n`）。只译各段，保留 `OR`。
- `options` 形如 `选项id:显示文字` 或 `序号:选项id:显示文字`。只译最后一个冒号之后的显示文字。
- `script` 只译引号里的自然语言。不译 `ESCAPE`、颜色名、记忆键、音效 id、类名、路径、`snake_case`。
- 描述里的 `%s` 在中文两侧可以加空格，方便高亮：`提高 {%s} 的转向速度`。
- 不要翻译：`id`、类名、插件、`tags`、图标路径、音效 id、`hullId`、`variantId`、舰名前缀（如 `HSS`）、`name_gen_data.csv` 里的神话专名、`person_names.csv`。
- `uiTags` 是界面分类，要译（护盾、相位）。`tags` 是逻辑标签，不译。
- 任务难度 `EASY`/`MEDIUM`/`HARD` 是枚举，不译。

## 核心专名

以下为强制译名。完整舰船、武器、插件、技能表以 glossary.tsv 为准。

| 英文 | 中文 |
|---|---|
| Hegemony | 霸主 |
| Tri-Tachyon | 速子科技 |
| Luddic Church | 银河救赎教会 |
| Luddic Path | 卢德左径 |
| Knights of Ludd | 卢德骑士团 |
| Lion's Guard | 狮心卫队 |
| Sindrian Diktat | 辛达强权 |
| Persean League | 英仙座联盟 |
| Persean Sector | 英仙座星域 |
| Remnant / Remnants | 余辉 |
| pirates | 海盗 |
| independent | 非势力团体 |
| Dweller | 渊幕原种 |
| Threat | 威胁 |
| Omega | 欧米伽 |
| scavengers | 拾荒者 |
| Human Domain / the Domain | 人之领 |
| the Collapse | 大崩塌 |
| hyperspace | 超空间 |
| flux / hard flux / soft flux | 幅能 / 硬幅能 / 软幅能 |
| shield / armor / hull | 护盾 / 装甲 / 船体 |
| combat readiness / CR | 战斗准备度 |
| burn | 燃烧等级 |
| ordnance points | 弹药点 |
| story point | 故事点 |
| fighter / frigate / destroyer / cruiser / capital | 战机 / 护卫舰 / 驱逐舰 / 巡洋舰 / 主力舰 |
| phase | 相位 |
| Low Tech / High Tech / Midline | 低端技术 / 高新技术 / 中线技术 |
| nanoforge | 纳米锻炉 |
| transponder | 应答器 |
| slipstream | 滑流 |
| jump point | 跳跃点 |
| credits | 星币 |
| variant Custom | 特装 |

## 人名与星球

人物、氏族、军官一律保留拉丁拼写，不要音译。glossary.tsv 里中文与英文相同的行就是这条规则。星球、星系、空间站若表中没有中文，也保留英文（Galatia、Volturn、Kazeron、Sindria、Askonia、Chicomoztoc、Tseen Ke）。

由普通英文词拼出来、会显示给玩家的生成名称要译。只用来拼空间站名的词，按上面的空间站规则先留英文，在规模清单里单独一档。

已锁定、容易译错的称呼：

| 英文 | 中文 |
|---|---|
| hypershunt | 星冕分流器 |
| Demarchon / Prime Demarchon | 民选统领 / 首席民选统领 |
| Council of Demarchons | 民选统领议会 |
| demarch | 统领 |
| Archon | 执政官 |
| Supreme Executor | 最高元首 |
| Executor（舰级） | 执行官 |
| Guard High Deputy Executor | 卫队最高副首长 |
| Grand Star Marshal / Deputy Star Marshal | 大星际元帅 / 副星际元帅 |
| Chief High Inspector-General | 最高检察长 |
| Reformed Sindrian Diktat | 革新辛达强权 |
| the Lion / Lion of Sindria | 辛达瑞亚之狮 |
| station king / portking | 空间站之王 / 港口之王 |
| Moloch | 摩洛克 |
| Curate Sacraria Standfast | 神龛祭司 Sacraria Standfast |
| pneuma | 圣灵 |

## 工具脚本

解析和写回用同目录 [tools](tools)，不要另写 CSV/JSON/JAR 解析器。脚本顶部写死了本机工作目录 `d:\Game\Starsector\l10n_work`；换机器时只改这一处路径。

游戏自带 JDK：`jre\bin\javac.exe` 与 `java.exe`（Java 17）。CSV 写出依赖游戏的 `starsector-core\json.jar`。JAR 补丁依赖 ASM 9.7（`asm-9.7.jar`、`asm-tree-9.7.jar`）。反编译看上下文用 CFR 0.152，只读，不作为写回。

| 脚本 | 用途 |
|---|---|
| tools/SsCsv.java | `dump` 把 CSV 读成 JSON；`write` 把 JSON 写回 CSV。混合 UTF-8/CP1252，RFC 4180，保留 `#` 行 |
| tools/ssjson.py | 宽松 JSON 扫描器。能处理 `#`、`//`、尾逗号、无引号键、单引号、`f` 后缀、分号当逗号 |
| tools/apply_csv.py | 有旧版译文时：按稳定 id 和 rules 结构套入，剩下的写入 `pending.jsonl`。从零翻译时不用 |
| tools/apply_json.py | 有旧版译文时同样处理 JSON、faction、skill、variant。从零翻译时只改抽出的句子。`cjkMode` 必须在替换字符串之后再改 |
| tools/apply_sources.py | 有旧版译文时，对齐未改动的 `.java` / `.txt` 引号字符串。从零翻译时直接改源码里的自然语言 |
| tools/split_chunks.py | 把待译唯一字符串切成每批 80 条的 `chunks/in/NNN.json` |
| tools/validate_chunk.py | `python validate_chunk.py NNN`。核对条数、`i`、名词类 `$变量`。百分号后的英文单词会被误报，代词类 `$变量` 可以省略 |
| tools/merge_chunks.py | 按 `pending.jsonl` 的位置，把 `chunks/out` 写回暂存 CSV 的副本。默认只统计；`--apply` 写到 `state/merged`，不改 `state/staged` |
| tools/align_jars.py | 类名稳定时，按方法内字符串序号把旧 jar 的中文对齐到新 jar。`starfarer_obf.jar` 类名会变，改用 catalog 的序列指纹。从零翻译时不用 |
| tools/SsJar.java | `dump` 导出 LDC；`patch` 用 ASM 改字符串并重打 jar。`ClassWriter(0)`，不重算栈图 |
| tools/compare_csv.py | 确认 Java 解析结果与同一套解码后的对照一致 |
| tools/build_glossary.py | 从种子表生成 glossary.tsv |
| tools/core_terms.py | 写出势力名表 |
| tools/manual_json.py | 把短 JSON 字符串的人工译文写回暂存 |
| tools/catalog.py | 从游戏或模组目录抽出可对照的字符串，并按分组做序列对照。只覆盖原版字段表；jar 只导出 `starfarer.api.jar` 和 `starfarer_obf.jar` |
| tools/snapshot_memory.py | 把同一版本的纯英文目录和已汉化目录配成 `memory/<版本>.jsonl` |
| tools/extract_catalog.py | 从新版纯英文目录抽出 `incoming/<版本>.jsonl` |
| tools/diff_catalog.py | 对照记忆和新版英文，写出 unchanged / modified / added / removed |

编译与调用：

```
javac -encoding UTF-8 -cp starsector-core\json.jar -d l10n_work\classes tools\SsCsv.java
java -cp "l10n_work\classes;starsector-core\json.jar" SsCsv dump 输入.csv 输出.json
java -cp "l10n_work\classes;starsector-core\json.jar" SsCsv write 输入.json 输出.csv
javac -encoding UTF-8 -cp l10n_work\lib\asm-9.7.jar;l10n_work\lib\asm-tree-9.7.jar -d l10n_work\classes tools\SsJar.java
java -cp "l10n_work\classes;l10n_work\lib\asm-9.7.jar;l10n_work\lib\asm-tree-9.7.jar" SsJar dump 某.jar 输出.jsonl
java -cp "l10n_work\classes;l10n_work\lib\asm-9.7.jar;l10n_work\lib\asm-tree-9.7.jar" SsJar patch 某.jar 补丁.jsonl 输出.jar
```

## JAR

`starfarer_obf.jar` 已混淆，不能靠反编译后再编译还原，栈图和名字都会坏。

正确流程：

1. 用 CFR 反编译**需要判断的类**，看字符串是界面、提示、异常，还是日志、键、路径。
2. 只改确认要显示的 `LDC` 字符串。用 ASM `ClassNode` 改 `LdcInsnNode.cst`，再用 `ClassWriter(0)` 写回，最后按原条目重打 jar。不要重算栈图。同一常量池项被多处引用且译文不同时，必须拆成两条常量，不能整池替换。
3. 中文在基本多文种平面内，class 文件的 modified UTF-8 与普通 UTF-8 相同。单条常量不要超过 65535 字节。
4. `starfarer.api.jar` 未混淆，同样用常量替换。反编译只用于判断，不作为写回手段。
5. 判断：跟随其后的调用若是 `addPara`、`setTooltip`、`addMessage`、按钮文字，则翻译。日志、`getId`、资源路径、异常类名不译。

这一节只用于原版的 `starfarer.api.jar` 和 `starfarer_obf.jar`。模组 jar 先看下面的「模组清点」和「模组源码」。

## 模组清点

某个模组第一次翻译，先交规模清单，等用户确认再改文件。清单用已经安装的模组目录做。记忆放在 `l10n_work/projects/mods/<mod id>/`。

```
python l10n_work\tools\extract_catalog.py --root mods\<模组目录> --cache l10n_work\projects\mods\<mod id>\cache\<版本> --out l10n_work\projects\mods\<mod id>\incoming\<版本>.jsonl
java -cp "l10n_work\classes;l10n_work\lib\asm-9.7.jar;l10n_work\lib\asm-tree-9.7.jar" SsJar dump mods\<模组目录>\jars\<mod_info 的 jars 所列 jar> l10n_work\projects\mods\<mod id>\cache\<版本>\jar\<jar 名>.jsonl
```

`extract_catalog.py` 的 jsonl 不是模组全文。行数里包含空单元格、注释、id、类名和路径。报数按玩家看见的句子，同时给出不重复条数和字符量。主数字包含两块：抽取器已经认出的句子，以及清点时自己找出来的玩家文本。大文件分开报：`strings.json`、规则正文、规则选项、规则脚本里的引号、`descriptions.csv`，其余已识别字段合成一档。

下面三档单列，不并进主数字，除非用户要求并进去：

- 按术语规则保留英文的名称碎片（空间站名生成词）
- 只有开了控制台才出现的帮助
- jar 里还没对照源码的句子

计数时这些情况容易数错：

- `strings.json`、`tips.json` 整份都是显示文字。值即使只有一个小写单词也要译。键不译。不要用「全小写、没有空格」把这些值滤掉。
- 规则 `text` 按 `OR` 分段，每段算一条，空段不算。`options` 只算最后一个冒号后面的显示文字。`script` 只算引号里的自然语言，一整格脚本不是一条。
- 单元格里的换行仍是同一条显示文字。
- 句子中间的斜杠不是路径。带空格或标点的句子要译。路径是 `graphics/`、`data/`、`sounds/`、带扩展名的文件，或没有空格的整段路径。
- 名称表只数数组里的值，不数对象的键。同一显示词写在多个文件里时，报不重复条数和写入处数。
- `#` 开头的行，以及被注释掉的调用，不译。
- 文件名里带 rules 不等于原版规则表。只有 `campaign/rules.csv` 和 `campaign/rules/*.csv` 按 7 列处理。旁边的表先读表头。

[reference.md](reference.md) 的字段表是原版的。模组多出来的玩家文本，抽取器会漏，清点时要自己找：

- 表头不在原版字段表里、单元格却是名称或描述的 CSV。先读表头，再决定哪些列要译。
- 原版键表没有、但值是给玩家看的说明的键。`tip` 在表里，`tooltip` 不在；同文件的 `name` 仍会被抽到，不要因此当成整份文件都已覆盖。
- 字段表以外、值是短语或句子的自定义键。值若是 id、类名或数值，不译。
- 名称数组里的显示词，以及会显示出来的序数后缀。这些是显示碎片，要译。
- 空间站名生成词按「人名与星球」留英文，先单列。
- `mod_info.json` 的 `name` 和 `description` 出现在模组列表里，要计入。`author` 和版本号不译。
- 控制台命令的 `help` 列。单列。

jar 的句子等源码。没有源码时，把像句子的常量分成三档再报：调试、测试、异常（不译）；版本更新这类玩家对话框（计入）；其余（待复核）。不要报常量总数。和 `strings.json` 完全相同的句子不要算两次。jar 里的短词多半是查表键，键不译。

模组成品放在 `output/mods/<mod id>/`，相对路径从模组根目录算。不要改模组的版本号。

## 模组源码

翻译模组时，先找源码，用它判断哪些字符串给玩家看，再决定写回方式。不要只对着 jar 里的常量翻译。

按这个顺序找：

1. 模组根目录里的 `src/` 或 `source/`。里面可以是 `.java`，也可以是 `.kt`。
2. `mod_info.json` 的 `source` 字段。
3. jar 旁边的 `src.txt`，以及 `jars/src.txt`。仓库地址可能写在这里，`mod_info.json` 未必有 `source` 字段。
4. 模组里的 README、更新说明、许可文件中的仓库地址。

数据文件的规模清单不依赖源码，先做。要判断 jar 里哪些常量给玩家看时，再浅克隆到 `l10n_work/projects/mods/<mod id>/upstream`，不要把仓库直接盖进已经安装的模组目录。克隆失败就告诉用户，不要换地址反复试。没有源码就不要开始改 jar。

源码用来做这些判断：

- `addPara`、`setTooltip`、`addMessage`、按钮文字要译。日志、异常、键名、路径不译。
- 注释和被注释掉的调用不是玩家文本，不要译。
- 一行字符串被加号拆成几段时，按源码里拼好的整句来译。
- 传给 `String.format` 或 `addPara` 的 `%%` 要保留，它显示出来是一个 `%`。
- Kotlin 字符串里的 `$名字` 是编译期拼接，不是规则文件里的 `$变量`。看源码确认它编译后变成哪几段常量。
- 源码如果从 CSV、JSON 读文案，就译那些文件。jar 里只留键名和日志时，不要为了凑字去改 jar。

写回：

- `data/scripts` 下由游戏自己编译的 `.java`，直接改源码，不要打进 jar。
- 玩家文字在 CSV、JSON 里时，改那些文件。
- 玩家文字编进了 `mod_info.json` 的 `jars` 所列 jar 时：源码是普通 Java，并且模组带有能在命令行跑的构建（Gradle、Maven，或依赖只是游戏和模组依赖 jar）时，译源码后重新编译，用新 jar 换掉原来的 jar。Kotlin、只能用 IDE 构建、或依赖凑不齐时，不要自己凑一套编译。用源码选定要改的常量，再用 ASM 改现有 jar。
- 原版 `starfarer_obf.jar` 仍然只做常量替换，不反编译重编。

## 写回前检查

- 每条译文的名词类 `$变量` 与 `%` 占位符集合与原文一致。
- CSV 重新读入后列数与原文一致，`rules.csv` 为 7 列。
- JSON 扫描器能再次走完，`cjkMode` 为 true。
- 抽一个已改 class，用 CFR 反编译，确认中文位于界面方法而不是日志。

字段级清单、rules 列和不要碰的文件见 [reference.md](reference.md)。
