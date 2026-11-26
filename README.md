# 远行星号汉化技能

给代理 harness 用的远行星号（Starsector）简体中文汉化工作流。它指导代理翻译玩家能看见的文本，并提供解析、对齐、校验和写回脚本。

当前流程针对 0.98.5a 这一支。游戏目录是 `starsector-core`。

## 安装

把本目录放到 Cursor 的个人技能目录，文件夹名使用技能名：

```
%USERPROFILE%\.cursor\skills\starsector-l10n\
```

其中需要有 `SKILL.md`。术语表、字段说明和脚本都放在同一层。

其余 harness 工具：把本项目放进你的 harness 工作区，让它自行安装 skill。

## 目录

| 文件 | 作用 |
|---|---|
| [SKILL.md](SKILL.md) | 译法、两种起点、jar 补丁方式和写回前检查 |
| [glossary.tsv](glossary.tsv) | 英文、中文、来源。已有译名不得另起炉灶 |
| [intel_tags.tsv](intel_tags.tsv) | 情报面板标签的 id 与中文译名对照。同一标签只许一种中文 |
| [factions.tsv](factions.tsv) | 势力名 |
| [reference.md](reference.md) | CSV 列、JSON 键、源码和安装包布局 |
| [tools](tools) | 解析、对照和写回脚本 |
| `fonts/` | 字体文件，不进仓库。缺了就按 SKILL.md 请用户提供汉化 zip |

## 两种起点

流程相同，差别只在有没有旧版译文。

- 有旧版译文：英文与语境都相同的句子沿用。CSV 按稳定 id 对齐，JSON 按路径对齐，jar 按方法内字符串序号对齐。对不上的才新译。与术语表冲突时以术语表为准。
- 从零翻译：不运行对齐脚本。按字段表抽出玩家可见句子，按术语表翻译。表里没有的专名先写入术语表，再译句子。

日志、异常、键名、路径两种情况下都不译。jar 只改 `starfarer.api.jar` 和 `starfarer_obf.jar` 里玩家能看见的字符串。

## 增量翻译

原版放在 `l10n_work/projects/vanilla/`，每个模组放在 `l10n_work/projects/mods/<mod id>/`。更新前用 `snapshot_memory.py` 把纯英文目录和已汉化目录配成记忆。更新后用 `extract_catalog.py` 抽出新英文，再用 `diff_catalog.py` 逐条对照。

英文没变的沿用旧译文。同一位置英文被改过的记为 modified，按新英文重译；只是错字、旧中文已经表达修正后的意思时，沿用旧中文。新增和删除单独列出。不要因为别处出现过相同英文就套用。

`starfarer_obf.jar` 的类名会重新混淆。先按方法内的英文字符串序列配对，再做序列对照，否则没改的句子会被看成大量新增和删除。`script` 以新版脚本为底，只译引号里的话。`options` 只译最后一个冒号后的显示文字。版本号保持新版英文。写回后用保存下来的英文目录和写回后的中文目录做下一版记忆。

## 模组源码

翻译模组时先找源码。模组自带 `src/` 或 `source/` 就直接读。没有的话看 `mod_info.json` 的 `source`，以及 README、更新说明里的仓库地址，浅克隆到 `l10n_work/projects/mods/<mod id>/upstream`。源码用来区分界面文字、日志和注释，也用来确认文案是在 CSV、JSON 里，还是在 jar 里。

能在命令行编译的普通 Java 模组，可以译完源码后重新打包替换 jar。Kotlin 或只能用 IDE 构建时，用源码选定句子，再用 ASM 改现有 jar。游戏自己编译的 `data/scripts` 源码直接改，不打进 jar。

## 情报标签

情报面板的筛选按钮分两层：`getIntelTags()` 返回的是标签 **id**，中文名写在 `data/config/tag_data.json` 的 `name` 里。id 必须保持英文原串；把 id 当正文译掉，同一类情报就会裂成两个按钮。原版总表要覆盖全部原版 id，模组专属 id 写进模组自己的 `data/config/tag_data.json`，势力 id 不写（面板直接显示势力名）。译名表见 [intel_tags.tsv](intel_tags.tsv)，检查脚本是 `tools/intel_tags.py`。

## 字体

汉字要正常显示，需要 `graphics/fonts`（含 `.fnt`、`.png` 和 `dyn_font`）以及 `native/windows/ss_dyn_font.dll`。没有特殊情况时，这份 DLL 可以一直沿用。文件放在本目录的 `fonts/`，相对路径与游戏内一致，`fonts/` 不进仓库。

缺少这些文件时，请用户到远行星号中文站 <https://www.fossic.org/> 下载「覆盖压缩包」版本的汉化，把 zip 交给代理处理。代理不要自己下载。

## 脚本

脚本开头写死了工作目录（`l10n_work`，个别脚本写成绝对路径）。换机器时只改这一处。

游戏自带 JDK 为 Java 17。CSV 写出依赖游戏的 `starsector-core\json.jar`。JAR 补丁依赖 ASM 9.7。反编译只用 CFR 看上下文，不作为写回。

以 `#` 开头的 CSV 单元格不要加引号。游戏把行首为 `#` 的行当作注释；加引号后会变成正式记录。
