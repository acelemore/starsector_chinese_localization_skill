# 远行星号汉化技能

给 Cursor 用的远行星号（Starsector）简体中文汉化工作流。它指导代理翻译玩家能看见的文本，并提供解析、对齐、校验和写回脚本。

当前流程针对 0.98.5a 这一支。游戏目录是 `starsector-core`。

## 安装

把本目录放到 Cursor 的个人技能目录，文件夹名使用技能名：

```
%USERPROFILE%\.cursor\skills\starsector-l10n\
```

其中需要有 `SKILL.md`。术语表、字段说明和脚本都放在同一层。

## 目录

| 文件 | 作用 |
|---|---|
| [SKILL.md](SKILL.md) | 译法、两种起点、jar 补丁方式和写回前检查 |
| [glossary.tsv](glossary.tsv) | 英文、中文、来源。已有译名不得另起炉灶 |
| [factions.tsv](factions.tsv) | 势力名 |
| [reference.md](reference.md) | CSV 列、JSON 键、源码和安装包布局 |
| [tools](tools) | 解析和写回脚本 |

## 两种起点

流程相同，差别只在有没有旧版译文。

- 有旧版译文：英文与语境都相同的句子沿用。CSV 按稳定 id 对齐，JSON 按路径对齐，jar 按方法内字符串序号对齐。对不上的才新译。与术语表冲突时以术语表为准。
- 从零翻译：不运行对齐脚本。按字段表抽出玩家可见句子，按术语表翻译。表里没有的专名先写入术语表，再译句子。

日志、异常、键名、路径两种情况下都不译。jar 只改 `starfarer.api.jar` 和 `starfarer_obf.jar` 里玩家能看见的字符串。

## 脚本

脚本顶部写死了本机工作目录 `d:\Game\Starsector\l10n_work`。换机器时只改这一处。

游戏自带 JDK 为 Java 17。CSV 写出依赖游戏的 `starsector-core\json.jar`。JAR 补丁依赖 ASM 9.7。反编译只用 CFR 看上下文，不作为写回。

以 `#` 开头的 CSV 单元格不要加引号。游戏把行首为 `#` 的行当作注释；加引号后会变成正式记录。
