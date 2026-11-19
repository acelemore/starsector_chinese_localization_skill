# -*- coding: utf-8 -*-
"""Player-visible string catalogs for vanilla and mods.

A catalog is JSONL. Each record:

    {"container", "slot", "en", "zh"}

`zh` may be omitted on a fresh English extract. `container` is the stable
group (a CSV id, a JSON path, a Java file, or one jar method). `slot` is the
position inside that group. Diffs compare English inside a container, so an
edited sentence is "modified" even when no row was added.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

JAVA = Path(r"d:\Game\Starsector\jre\bin\java.exe")
WORK = Path(r"d:\Game\Starsector\l10n_work")
CSV_CP = f"{WORK / 'classes'};{Path(r'd:\Game\Starsector\starsector-core\json.jar')}"
JAR_CP = f"{WORK / 'classes'};{WORK / 'lib' / 'asm-9.7.jar'};{WORK / 'lib' / 'asm-tree-9.7.jar'}"

# Columns that reach the player. Keys are paths relative to data/.
CSV_SPECS = {
    "campaign/abilities.csv": (["id"], ["name", "desc"]),
    "campaign/commodities.csv": (["id"], ["name", "desc"]),
    "campaign/industries.csv": (["id"], ["name", "desc"]),
    "campaign/market_conditions.csv": (["id"], ["name", "desc"]),
    "campaign/special_items.csv": (["id"], ["name", "tech/manufacturer", "desc"]),
    "campaign/submarkets.csv": (["id"], ["name", "desc"]),
    "campaign/reports.csv": (["event_type", "event_stage", "channels", "target_rel"], ["subject", "summary", "assessment"]),
    "characters/personalities.csv": (["id"], ["name", "desc"]),
    "characters/skills/aptitude_data.csv": (["id"], ["name", "description"]),
    "characters/skills/skill_data.csv": (["id"], ["name", "description", "author"]),
    "hullmods/hull_mods.csv": (["id"], ["name", "tech/manufacturer", "uiTags", "desc", "short", "sModDesc"]),
    "hulls/ship_data.csv": (["id"], ["name", "designation", "tech/manufacturer", "logistics n/a reason"]),
    "hulls/wing_data.csv": (["id"], ["role desc"]),
    "shipsystems/ship_systems.csv": (["id"], ["name"]),
    "weapons/weapon_data.csv": (["id"], ["name", "tech/manufacturer", "primaryRoleStr", "customPrimary", "customPrimaryHL", "customAncillary", "customAncillaryHL"]),
    "strings/descriptions.csv": (["id", "type"], ["text1", "text2", "text3", "text4", "text5"]),
}

JSON_KEYS = {
    "name", "displayName", "displayNameWithArticle", "desc", "description",
    "text", "title", "body", "tip", "short", "shortType", "defaultName", "shortName",
}
JSON_WHOLE = {
    "strings/strings.json",
    "strings/tips.json",
    "strings/tooltips.json",
    "world/factions/default_fleet_type_names.json",
}
PATH_SUFFIXES = (".png", ".fnt", ".ogg", ".csv", ".json", ".java", ".txt", ".vs", ".fs", ".wav")
LOWER_ID = re.compile(r"[a-z0-9_$.-]+")


def keep_slot(text: str) -> bool:
    """Drop only strings that stay English identifiers or paths after translation.

    The same slots must survive on the English tree and the Chinese tree.
    """
    if text is None:
        return False
    s = text.strip()
    if not s or s.startswith("#"):
        return False
    if "/" in s or "\\" in s or s.endswith(PATH_SUFFIXES):
        return False
    if LOWER_ID.fullmatch(s):
        return False
    return True
JAVA_STRING = re.compile(r'"((?:\\.|[^"\\])*)"')
JAVA_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
JARS = ("starfarer.api.jar", "starfarer_obf.jar")


def _java_unescape(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == "u" and i + 5 < len(text):
                try:
                    out.append(chr(int(text[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            out.append(JAVA_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def keep_text(text: str) -> bool:
    return keep_slot(text)


def rec(container: str, slot: str, en: str, zh: str | None = None) -> dict:
    row = {"container": container, "slot": slot, "en": en}
    if zh is not None:
        row["zh"] = zh
    return row


def dump_csv(src: Path, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [str(JAVA), "-cp", CSV_CP, "SsCsv", "dump", str(src), str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"SsCsv dump failed {src}\n{r.stderr}")
    return json.loads(dest.read_text(encoding="utf-8"))


def csv_records(root: Path, cache: Path) -> list[dict]:
    data = root / "data"
    out = []
    files = list(CSV_SPECS.items())
    rules = sorted((data / "campaign" / "rules").glob("*.csv")) if (data / "campaign" / "rules").is_dir() else []
    for rel, (keys, cols) in files:
        src = data / rel
        if src.is_file():
            out.extend(_csv_file(src, rel, keys, cols, cache))
    for src in rules:
        rel = src.relative_to(data).as_posix()
        out.extend(_csv_file(src, rel, ["id"], ["text", "options", "script"], cache))
    main_rules = data / "campaign" / "rules.csv"
    if main_rules.is_file():
        out.extend(_csv_file(main_rules, "campaign/rules.csv", ["id"], ["text", "options", "script"], cache))
    return out


def _csv_file(src: Path, rel: str, keys: list[str], cols: list[str], cache: Path) -> list[dict]:
    dumped = dump_csv(src, cache / (rel.replace("/", "__") + ".json"))
    rows = dumped["rows"]
    if not rows:
        return []
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}
    grouped: dict[tuple, list] = defaultdict(list)
    for row in rows[1:]:
        if not row or (row[0].startswith("#") if row[0] else False):
            continue
        ident_parts = []
        blank = True
        for k in keys:
            i = idx.get(k)
            val = row[i] if i is not None and i < len(row) else ""
            ident_parts.append(val)
            if val.strip() and not val.startswith("#"):
                blank = False
        if blank or ident_parts[0].startswith("#"):
            continue
        ident = "|".join(ident_parts)
        for col in cols:
            i = idx.get(col)
            if i is None or i >= len(row):
                continue
            grouped[(ident, col)].append(row[i] if row[i] is not None else "")
    records = []
    for (ident, col), texts in grouped.items():
        container = f"csv:{rel}:{ident}:{col}"
        for n, text in enumerate(texts):
            records.append(rec(container, str(n), text))
    return records


def json_records(root: Path) -> list[dict]:
    import sys
    sys.path.insert(0, str(WORK))
    from ssjson import Walker

    data = root / "data"
    out = []
    if not data.is_dir():
        return out
    for path in data.rglob("*"):
        if path.suffix.lower() not in {".json", ".faction", ".skill", ".variant"}:
            continue
        rel = path.relative_to(data).as_posix()
        if rel.startswith("config/sounds") or rel.startswith("campaign/econ"):
            continue
        whole = rel in JSON_WHOLE
        try:
            raw = path.read_bytes()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("cp1252")
            walker = Walker(text)
            walker.parse()
        except Exception:
            continue
        for leaf_path, value, *_rest in walker.leaves:
            if not isinstance(value, str):
                continue
            key = leaf_path.rsplit(".", 1)[-1]
            key = key.split("[", 1)[0]
            if not whole and key not in JSON_KEYS and not (rel.endswith("descriptor.json") and key == "title"):
                continue
            container = f"json:{rel}:{leaf_path}"
            out.append(rec(container, "0", value))
    return out


def java_records(root: Path) -> list[dict]:
    data = root / "data"
    out = []
    if not data.is_dir():
        return out
    for path in data.rglob("*"):
        if path.suffix not in {".java", ".txt"}:
            continue
        rel = path.relative_to(data).as_posix()
        if path.suffix == ".txt" and not (
            rel.startswith("codex/") or rel.endswith("mission_text.txt")
        ):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".java":
            parts = [_java_unescape(m) for m in JAVA_STRING.findall(text)]
        else:
            parts = [ln for ln in text.splitlines() if ln.strip()]
        container = f"src:{rel}"
        for n, part in enumerate(parts):
            out.append(rec(container, str(n), part))
    return out


def dump_jar(jar: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_mtime >= jar.stat().st_mtime:
        return
    r = subprocess.run(
        [str(JAVA), "-cp", JAR_CP, "SsJar", "dump", str(jar), str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"SsJar dump failed {jar}\n{r.stderr}")


def jar_records(root: Path, cache: Path) -> list[dict]:
    out = []
    for name in JARS:
        jar = root / name
        if not jar.is_file():
            continue
        dest = cache / (name + ".jsonl")
        dump_jar(jar, dest)
        grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for line in dest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            container = f"jar:{name}:{o['c']}:{o['m']}:{o['d']}"
            grouped[container].append((int(o["i"]), o.get("t", "")))
        for container, items in grouped.items():
            items.sort()
            for idx, text in items:
                out.append(rec(container, str(idx), text))
    return out


def extract(root: Path, cache: Path) -> list[dict]:
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    rows.extend(csv_records(root, cache / "csv"))
    rows.extend(json_records(root))
    rows.extend(java_records(root))
    rows.extend(jar_records(root, cache / "jar"))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def pair(en_rows: list[dict], zh_rows: list[dict]) -> list[dict]:
    """Same version: slot order matches. zh is the shipped translation."""
    zh_map: dict[tuple, list[str]] = defaultdict(list)
    for row in zh_rows:
        zh_map[(row["container"], row["slot"])].append(row["en"])
    used: dict[tuple, int] = defaultdict(int)
    out = []
    for row in en_rows:
        key = (row["container"], row["slot"])
        n = used[key]
        used[key] = n + 1
        choices = zh_map.get(key, [])
        zh = choices[n] if n < len(choices) else row["en"]
        out.append(rec(row["container"], row["slot"], row["en"], zh))
    return out


def diff(old_rows: list[dict], new_rows: list[dict]) -> dict[str, list[dict]]:
    """Compare English inside each container.

    equal   -> unchanged, keep the old zh
    replace -> modified (old zh is reference only)
    insert  -> added
    delete  -> removed
    """
    old_g: dict[str, list[dict]] = defaultdict(list)
    new_g: dict[str, list[dict]] = defaultdict(list)
    for row in old_rows:
        old_g[row["container"]].append(row)
    for row in new_rows:
        new_g[row["container"]].append(row)
    result = {"unchanged": [], "modified": [], "added": [], "removed": []}
    for container in sorted(set(old_g) | set(new_g)):
        old = sorted(old_g.get(container, []), key=_slot_key)
        new = sorted(new_g.get(container, []), key=_slot_key)
        sm = SequenceMatcher(a=[r["en"] for r in old], b=[r["en"] for r in new], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    prev, nxt = old[i1 + k], new[j1 + k]
                    result["unchanged"].append(rec(container, nxt["slot"], nxt["en"], prev.get("zh", prev["en"])))
            elif tag == "replace":
                span = min(i2 - i1, j2 - j1)
                for k in range(span):
                    prev, nxt = old[i1 + k], new[j1 + k]
                    result["modified"].append({
                        "container": container,
                        "slot": nxt["slot"],
                        "en": nxt["en"],
                        "old_en": prev["en"],
                        "old_zh": prev.get("zh", ""),
                    })
                for k in range(span, i2 - i1):
                    prev = old[i1 + k]
                    result["removed"].append(rec(container, prev["slot"], prev["en"], prev.get("zh", "")))
                for k in range(span, j2 - j1):
                    nxt = new[j1 + k]
                    result["added"].append(rec(container, nxt["slot"], nxt["en"]))
            elif tag == "delete":
                for k in range(i1, i2):
                    prev = old[k]
                    result["removed"].append(rec(container, prev["slot"], prev["en"], prev.get("zh", "")))
            elif tag == "insert":
                for k in range(j1, j2):
                    nxt = new[k]
                    result["added"].append(rec(container, nxt["slot"], nxt["en"]))
    return result


def _slot_key(row: dict):
    slot = row["slot"]
    return int(slot) if str(slot).isdigit() else slot


def diff_stats(result: dict[str, list[dict]]) -> dict[str, int]:
    return {name: len(rows) for name, rows in result.items()}
