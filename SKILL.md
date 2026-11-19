---
name: starsector-l10n
description: >-
  Localize the game Starsector (远行星号) into Simplified Chinese: CSV, lenient
  JSON, loose Java sources, and jars. Use when translating Starsector, 远行星号,
  starsector-core, rules.csv, starfarer.api.jar, or starfarer_obf.jar. Translations
  must follow glossary.tsv in this skill.
---

# 远行星号汉化

译文必须遵循同目录 [glossary.tsv](glossary.tsv)（英文、中文、来源，制表符分隔）。势力名另见 [factions.tsv](factions.tsv)。表中已有译名不得另起炉灶。表里没有的舰船、武器、船体插件、技能，先按表内同类构词翻译，并追加到表中。

目标版本以 `starfarer_obf.jar` 里的版本串为准（本工作流针对 0.98.5a 这一支）。游戏目录是 `starsector-core`。只覆盖玩家能看见的文本。

## 两种起点

流程相同。先看有没有上一版记忆或一份旧版译文可以对照。

- 有上一版记忆：走下面的增量对照。英文没变的沿用记忆里的中文。英文改过或新出现的才翻译。记忆和 glossary.tsv 冲突时，以 glossary 为准。
- 有旧版译文、还没有记忆：先做一次快照，以后按增量对照。也可以用对齐脚本按稳定 id、JSON 路径、方法内字符串序号套用，对不上的才翻译。
- 从零翻译：不运行对齐脚本，也不套记忆。按字段表抽出全部玩家可见句子，按 glossary 翻译。表里没有的专名先按同类构词译出并写入 glossary，再译句子。

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

模组把 `--project` 设为模组 id，`--kind mod`，`--en-root` / `--root` 指向该模组根目录。

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
5. 只改这两个 jar 里玩家能看见的字符串：`starfarer.api.jar`、`starfarer_obf.jar`。日志、异常、键名、路径不译。
6. `data` 下的 `.java` 与任务/法典 `.txt` 由游戏运行时编译或直接显示，改源码，不要自己编进 jar。
7. 成品镜像游戏相对路径，放到覆盖目录。安装脚本先整份备份 `starsector-core`，再覆盖。
8. JSON 字符串替换完成后再把 `data/config/settings.json` 里的 `"cjkMode"` 设为 `true`（中日韩折行）。字体见下面的「字体」。

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
| tools/catalog.py | 从游戏或模组目录抽出可对照的字符串，并按分组做序列对照 |
| tools/snapshot_memory.py | 把同一版本的纯英文目录和已汉化目录配成 `memory/<版本>.jsonl` |
| tools/extract_catalog.py | 从新版纯英文目录抽出 `incoming/<版本>.jsonl` |
| tools/diff_catalog.py | 对照记忆和新版英文，写出 unchanged / modified / added / removed |

编译与调用：

```
javac -encoding UTF-8 -cp starsector-core\json.jar -d l10n_work\classes tools\SsCsv.java
java -cp "l10n_work\classes;starsector-core\json.jar" SsCsv dump 输入.csv 输出.json
java -cp "l10n_work\classes;starsector-core\json.jar" SsCsv write 输入.json 输出.csv
javac -encoding UTF-8 -cp asm-9.7.jar;asm-tree-9.7.jar -d l10n_work\classes tools\SsJar.java
java -cp "l10n_work\classes;asm-9.7.jar;asm-tree-9.7.jar" SsJar dump 某.jar 输出.jsonl
java -cp "l10n_work\classes;asm-9.7.jar;asm-tree-9.7.jar" SsJar patch 某.jar 补丁.jsonl 输出.jar
```

## JAR

`starfarer_obf.jar` 已混淆，不能靠反编译后再编译还原，栈图和名字都会坏。

正确流程：

1. 用 CFR 反编译**需要判断的类**，看字符串是界面、提示、异常，还是日志、键、路径。
2. 只改确认要显示的 `LDC` 字符串。用 ASM `ClassNode` 改 `LdcInsnNode.cst`，再用 `ClassWriter(0)` 写回，最后按原条目重打 jar。不要重算栈图。同一常量池项被多处引用且译文不同时，必须拆成两条常量，不能整池替换。
3. 中文在基本多文种平面内，class 文件的 modified UTF-8 与普通 UTF-8 相同。单条常量不要超过 65535 字节。
4. `starfarer.api.jar` 未混淆，同样用常量替换。反编译只用于判断，不作为写回手段。
5. 判断：跟随其后的调用若是 `addPara`、`setTooltip`、`addMessage`、按钮文字，则翻译。日志、`getId`、资源路径、异常类名不译。

## 写回前检查

- 每条译文的名词类 `$变量` 与 `%` 占位符集合与原文一致。
- CSV 重新读入后列数与原文一致，`rules.csv` 为 7 列。
- JSON 扫描器能再次走完，`cjkMode` 为 true。
- 抽一个已改 class，用 CFR 反编译，确认中文位于界面方法而不是日志。

字段级清单、rules 列和不要碰的文件见 [reference.md](reference.md)。
