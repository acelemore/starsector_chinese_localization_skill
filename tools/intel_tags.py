# -*- coding: utf-8 -*-
"""Check intel tag ids against tag_data.json names.

Intel panel buttons come from two places: the strings returned by
``getIntelTags()`` (the tag *ids*) and the ``name`` of the matching id in
``data/config/tag_data.json``.  Ids must stay English; Chinese lives only in
``name``.  Translating a tag id splits one category into two buttons.

Usage::

    python tools/intel_tags.py --dumps l10n_work\\tagscan
    python tools/intel_tags.py --dumps l10n_work\\tagscan --game D:\\Game\\Starsector

``--dumps`` is a directory of ``SsJar dump`` jsonl files.  The script reports:

* English-looking ids that have no ``name`` (would show English in the panel),
* ids that are still Chinese (only OK for mods that name their tag in Chinese),
* two ids sharing one Chinese name (would show two buttons with one label),
* tag ids declared in tag_data but never seen in the dumps (informational).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ssjson  # noqa: E402

# getIntelTags rows that are call markers, not tag ids
LOOKUP_KEYS = {
    "getString(...)",
    "getIntelTags(...)",
}


def cjk(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def load_factions(game: Path) -> dict[str, str]:
    """势力 id -> 文件名。势力 id 出现在 getIntelTags 里时由面板直接显示势力名。"""
    ids: dict[str, str] = {}
    patterns = [
        "starsector-core/data/world/factions/**/*.faction",
        "mods/*/data/world/factions/**/*.faction",
    ]
    for pattern in patterns:
        for path in game.glob(pattern):
            text = path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r'\bid\s*:\s*"([^"]+)"', text)
            if match:
                ids.setdefault(match.group(1), path.name)
    return ids


def load_names(game: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    files = [game / "starsector-core/data/config/tag_data.json"]
    files += sorted(game.glob("mods/*/data/config/tag_data.json"))
    names: dict[str, str] = {}
    seen: dict[str, list[str]] = defaultdict(list)
    for path in files:
        if not path.is_file():
            continue
        for json_path, value, *_ in ssjson.walk(path.read_text(encoding="utf-8")):
            parts = json_path.split(".")
            if len(parts) == 3 and parts[0] == "$" and parts[2] == "name":
                seen[parts[1]].append(value)
                names.setdefault(parts[1], value)
    conflicts = {tag: vals for tag, vals in seen.items() if len(set(vals)) > 1}
    return names, conflicts


def load_tags(dumps: Path) -> dict[str, set[str]]:
    seen: dict[str, set[str]] = defaultdict(set)
    for file in sorted(dumps.glob("*.jsonl")):
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("m") != "getIntelTags":
                continue
            text = row.get("t") or ""
            if text:
                seen[text].add(file.stem)
    return seen


def main() -> int:
    try:  # Windows 控制台默认不是 UTF-8，中文标签会变乱码
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", default=".", type=Path, help="游戏根目录，默认当前目录")
    parser.add_argument("--dumps", required=True, type=Path)
    args = parser.parse_args()

    names, conflicts = load_names(args.game)
    tags = load_tags(args.dumps)
    problems = 0

    if conflicts:
        problems += len(conflicts)
        print("== 同一个 id 在不同 tag_data.json 里译名不一致 ==")
        for tag, vals in conflicts.items():
            print(f"  {tag}: {', '.join(vals)}")

    missing = sorted(
        t for t in tags
        if t not in names and t not in LOOKUP_KEYS
        and not cjk(t) and t[:1].isupper()
    )
    if missing:
        problems += len(missing)
        print("== 没有中文名的标签 id（面板会显示英文）==")
        for tag in missing:
            print(f"  {tag:<28} {', '.join(sorted(tags[tag]))}")

    lower = sorted(
        t for t in tags
        if t not in names and t not in LOOKUP_KEYS
        and not cjk(t) and not t[:1].isupper()
    )
    if lower:
        print("== 小写 id：确认是势力 id 还是查找键，势力 id 不译 ==")
        for tag in lower:
            print(f"  {tag:<28} {', '.join(sorted(tags[tag]))}")

    chinese = sorted(t for t in tags if cjk(t))
    if chinese:
        print("== 仍是中文的 id（只有模组自有、无英文同名时允许）==")
        for tag in chinese:
            print(f"  {tag:<20} {', '.join(sorted(tags[tag]))}")

    rev: dict[str, list[str]] = defaultdict(list)
    for tag, name in names.items():
        rev[name].append(tag)
    # 中文 id 撞上了某个英文 id 的中文名 => 同一类情报被拆成两个标签
    # （中文键自己的 name 也是中文，属于正常，排除）
    split = []
    for tag in chinese:
        others = [x for x in rev.get(tag, []) if x != tag]
        if others:
            split.append((tag, others))
    if split:
        problems += len(split)
        print("== 中文 id 与英文 id 的译名相同，说明同一类情报被拆开 ==")
        for tag, ids in split:
            print(f"  {tag}: 中文 id 仍在，另有 {', '.join(ids)}")

    factions = load_factions(args.game)
    on_faction = sorted(tag for tag in names if tag in factions)
    if on_faction:
        problems += len(on_faction)
        print("== 给势力 id 写了 tag_data（会盖掉面板显示的势力名与势力色）==")
        for tag in on_faction:
            print(f"  {tag}（{factions[tag]}）: {names[tag]} —— 删掉这条，面板会自动显示势力名")
    dup = {name: ids for name, ids in rev.items() if len(ids) > 1}
    if dup:
        problems += len(dup)
        print("== 多个 id 共用同一个中文名（会出现两个同名按钮）==")
        for name, ids in dup.items():
            print(f"  {name}: {', '.join(ids)}")

    unused = sorted(set(names) - set(tags))
    if unused:
        print("== tag_data 里有、dump 里没见到的 id（可能是硬编码常量或数据驱动，仅供核对）==")
        print("  " + ", ".join(unused))

    print(f"\n共 {len(tags)} 个字符串、{len(names)} 个译名、{problems} 个问题")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
