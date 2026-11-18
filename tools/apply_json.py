# -*- coding: utf-8 -*-
"""Apply old-pack JSON/faction/variant/skill translations onto the new game files."""
import json
import zipfile
from pathlib import Path

from apply_csv import TOKEN_RE, looks_player_text, tokens_ok
from ssjson import JsonWalkError, walk

NEW = Path(r"d:\Game\Starsector\starsector-core\data")
OLD_ZIP = next(Path(r"d:\Game\Starsector\local_old").glob("*.zip"))
STATE = Path(r"d:\Game\Starsector\l10n_work\state")
OUT = STATE / "json_staged"
MEM = json.loads((STATE / "memory.json").read_text(encoding="utf-8"))

ALLOW_KEYS = {
    "name", "displayName", "displayNameWithArticle", "desc", "description",
    "text", "title", "body", "tip", "short", "shortType", "defaultName",
    "shortName", "difficulty", "type",
}
ALL_VALUE = {
    "strings/strings.json",
    "strings/tips.json",
    "strings/tooltips.json",
    "world/factions/default_fleet_type_names.json",
}
# type= is player-facing only in channels
TYPE_OK = {"campaign/channels.json"}
GRAMMAR_KEYS = {"personNamePrefixAOrAn", "displayNameIsOrAre"}
SKIP_FILES_PREFIX = ("config/sounds", "config/engine_styles", "config/hull_styles")


def last_key(path: str) -> str:
    path = path.rstrip("]")
    if "[" in path:
        path = path[: path.rfind("[")]
    return path.rsplit(".", 1)[-1]


def worth(en: str) -> bool:
    if not en or not en.strip():
        return False
    stripped = TOKEN_RE.sub(" ", en)
    return looks_player_text(stripped)


def should(rel: str, path: str, en: str) -> bool:
    if rel.startswith(SKIP_FILES_PREFIX):
        return False
    key = last_key(path)
    if key in GRAMMAR_KEYS:
        return False
    if rel in ALL_VALUE:
        return worth(en)
    if key == "type" and rel not in TYPE_OK:
        return False
    if key not in ALLOW_KEYS:
        return False
    return worth(en)


def escape(text: str, quote: str) -> str:
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == quote:
            out.append("\\" + quote)
        elif ch == "\r":
            continue
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


def cjk(s: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def old_text(z, rel: str):
    name = "localization/data/" + rel
    try:
        return z.read(name).decode("utf-8")
    except KeyError:
        return None


def apply_one(rel: str, new_text: str, old: str | None, pending: list):
    try:
        new_leaves = walk(new_text)
    except JsonWalkError as e:
        print("SKIP", rel, e)
        return new_text, 0
    old_map = {}
    if old:
        try:
            for path, val, *_ in walk(old):
                old_map[path] = val
        except JsonWalkError as e:
            print("OLD FAIL", rel, e)
            old_map = {}
    repls = []
    used = 0
    for path, en, start, end, quote in new_leaves:
        key = last_key(path)
        if key in GRAMMAR_KEYS:
            repls.append((start, end, ""))
            used += 1
            continue
        if not should(rel, path, en):
            continue
        zh = None
        cand = old_map.get(path)
        if cand and cand != en and cjk(cand) and tokens_ok(en, cand):
            zh = cand
        elif en in MEM and tokens_ok(en, MEM[en]) and cjk(MEM[en]):
            zh = MEM[en]
        if zh:
            repls.append((start, end, escape(zh, quote)))
            used += 1
        else:
            pending.append({"file": rel, "path": path, "en": en})
    # also force cjkMode in settings
    if not repls:
        buf = new_text
    else:
        buf = new_text
        for start, end, body in sorted(repls, key=lambda x: x[0], reverse=True):
            buf = buf[:start] + body + buf[end:]
    if rel == "config/settings.json":
        buf = buf.replace('"cjkMode":false', '"cjkMode":true', 1)
    return buf, used


def main():
    z = zipfile.ZipFile(OLD_ZIP)
    OUT.mkdir(parents=True, exist_ok=True)
    pending = []
    # targeted extensions, skip sounds and pure numeric configs we already skip by prefix
    exts = {".json", ".faction", ".skill", ".variant"}
    total_used = 0
    files = 0
    for p in NEW.rglob("*"):
        if p.suffix.lower() not in exts:
            continue
        rel = p.relative_to(NEW).as_posix()
        if rel.startswith(SKIP_FILES_PREFIX):
            continue
        # variants/skills/factions/selected json only — skip econ and campaign terrain
        if rel.startswith("campaign/econ") or rel in {"campaign/events.json", "campaign/pings.json", "campaign/starmap.json", "campaign/terrain.json"}:
            continue
        if rel.startswith("config/") and rel not in {
            "config/settings.json", "config/battle_objectives.json", "config/contact_tag_data.json",
            "config/custom_entities.json", "config/planets.json", "config/tag_data.json",
        }:
            continue
        text = p.read_text(encoding="utf-8")
        new_text, used = apply_one(rel, text, old_text(z, rel), pending)
        if new_text != text:
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(new_text, encoding="utf-8")
            files += 1
            total_used += used
    (STATE / "pending_json.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in pending) + ("\n" if pending else ""),
        encoding="utf-8",
    )
    print(f"rewritten_files={files} replacements={total_used} pending={len(pending)}")


if __name__ == "__main__":
    main()
