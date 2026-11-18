# -*- coding: utf-8 -*-
"""Align new Starsector CSVs with the previous Chinese pack and emit leftovers."""
import json
import re
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path

JAVA = r"d:\Game\Starsector\jre\bin\java.exe"
CP = r"d:\Game\Starsector\l10n_work\classes;d:\Game\Starsector\starsector-core\json.jar"
NEW_ROOT = Path(r"d:\Game\Starsector\starsector-core\data")
OLD_ZIP = Path(r"d:\Game\Starsector\local_old") 
# resolved below
WORK = Path(r"d:\Game\Starsector\l10n_work")
OLD_DIR = WORK / "old_csv"
NEW_DUMP = WORK / "dump"
STATE = WORK / "state"

# columns that are player-facing prose or names
SPECS = {
    "campaign/abilities.csv": {"key": ["id"], "cols": ["name", "desc"]},
    "campaign/commodities.csv": {"key": ["id"], "cols": ["name", "desc"]},
    "campaign/industries.csv": {"key": ["id"], "cols": ["name", "desc"]},
    "campaign/market_conditions.csv": {"key": ["id"], "cols": ["name", "desc"]},
    "campaign/special_items.csv": {"key": ["id"], "cols": ["name", "tech/manufacturer", "desc"]},
    "campaign/submarkets.csv": {"key": ["id"], "cols": ["name", "desc"]},
    "campaign/reports.csv": {"key": ["event_type", "event_stage", "channels", "target_rel"], "cols": ["subject", "summary", "assessment"]},
    "campaign/rules.csv": {"key": ["id"], "mode": "rules"},
    "campaign/rules/askoniaCrisis2.csv": {"key": ["id"], "mode": "rules"},
    "characters/personalities.csv": {"key": ["id"], "cols": ["name", "desc"]},
    "characters/skills/aptitude_data.csv": {"key": ["id"], "cols": ["name", "desc", "description"]},
    "characters/skills/skill_data.csv": {"key": ["id"], "cols": ["name", "description", "author"]},
    "hullmods/hull_mods.csv": {"key": ["id"], "cols": ["name", "tech/manufacturer", "uiTags", "desc", "short", "sModDesc"]},
    "hulls/ship_data.csv": {"key": ["id"], "cols": ["name", "designation", "tech/manufacturer", "logistics n/a reason"]},
    "hulls/wing_data.csv": {"key": ["id"], "cols": ["role desc"]},
    "shipsystems/ship_systems.csv": {"key": ["id"], "cols": ["name"]},
    "strings/descriptions.csv": {"key": ["id", "type"], "cols": ["text1", "text2", "text3", "text4", "text5"]},
    "weapons/weapon_data.csv": {"key": ["id"], "cols": ["name", "tech/manufacturer", "primaryRoleStr", "customPrimary", "customPrimaryHL", "customAncillary", "customAncillaryHL"]},
}

NAME_COLS = {
    "name", "designation", "tech/manufacturer", "uiTags", "primaryRoleStr", "role desc",
    "author",
}

TOKEN_RE = re.compile(
    r"\$[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
    r"|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[a-zA-Z%]"
    r"|\\[ntr]"
)
UI_WORDS = {
    "Yes", "No", "OK", "Ok", "Cancel", "Continue", "Accept", "Refuse", "Leave",
    "Back", "More", "Next", "Exit", "Close", "Done", "Confirm", "Never", "Always",
}


def find_old_zip():
    hits = list(Path(r"d:\Game\Starsector\local_old").glob("*.zip"))
    if not hits:
        raise SystemExit("old zip missing")
    return hits[0]


def dump_csv(src: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [JAVA, "-cp", CP, "SsCsv", "dump", str(src), str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise SystemExit(f"dump failed {src}\n{r.stderr}")


def load_dump(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def header_index(rows):
    if not rows:
        return {}, []
    header = rows[0]
    return {name: i for i, name in enumerate(header) if name}, header


def is_comment(row):
    return bool(row) and row[0].startswith("#")


def looks_player_text(value: str) -> bool:
    if value is None:
        return False
    s = value.strip()
    if not s:
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    if re.fullmatch(r"[a-z0-9_./\\+\-]+", s):
        return False
    if s.startswith("graphics/") or s.startswith("com.") or s.startswith("data."):
        return False
    if s in {"TRUE", "FALSE", "true", "false", "NONE", "null"}:
        return False
    return True


def tokens(s: str):
    return [m.group(0) for m in TOKEN_RE.finditer(s or "")]


PRONOUNS = {
    "heOrShe", "HeOrShe", "hisOrHer", "HisOrHer", "himOrHer", "HimOrHer",
    "hesOrShes", "HesOrShes", "manOrWoman", "ManOrWoman",
    "sirOrMadam", "SirOrMadam", "boyOrGirl", "BoyOrGirl",
    "sonOrDaughter", "SonOrDaughter", "himselfOrHerself", "hisOrHers",
    "HisOrHers", "heOrSheIs", "HeOrSheIs",
}


def grammar_token(tok: str) -> bool:
    name = tok[1:] if tok.startswith("$") else tok
    base = name.split(".")[0]
    if base in PRONOUNS:
        return True
    return base.endswith("AOrAn") or base.endswith("IsOrAre")


def tokens_ok(en: str, zh: str) -> bool:
    et, zt = tokens(en), tokens(zh)
    # percent / escape tokens must match as a multiset
    def bucket(ts):
        perc, vars_, gram = [], [], []
        for t in ts:
            if t.startswith("$") and grammar_token(t):
                gram.append(t)
            elif t.startswith("$"):
                vars_.append(t)
            else:
                perc.append(t)
        return sorted(perc), sorted(vars_), gram
    ep, ev, _eg = bucket(et)
    zp, zv, _zg = bucket(zt)
    # Grammar tokens ($heOrShe, *AOrAn, *IsOrAre) may be dropped or added.
    # Name-bearing $tokens and printf placeholders must match.
    return ep == zp and ev == zv


def should_translate_script(s: str) -> bool:
    t = s.strip()
    if not looks_player_text(t):
        return False
    if re.search(r"\s", t) or re.search(r"[.,!?;:]", t):
        return True
    if t in UI_WORDS:
        return True
    if re.fullmatch(r"[A-Z][a-z]{2,}", t):
        return True
    return False


def scan_quotes(s: str):
    i, n = 0, len(s)
    while i < n:
        if s[i] != '"':
            i += 1
            continue
        j = i + 1
        buf = []
        while j < n:
            if s[j] == "\\" and j + 1 < n:
                buf.append(s[j:j + 2])
                j += 2
                continue
            if s[j] == '"':
                break
            buf.append(s[j])
            j += 1
        if j >= n:
            return
        yield i, j + 1, "".join(buf)
        i = j + 1


def split_or(text: str):
    if text == "":
        return []
    return re.split(r"(\r\nOR\r\n|\nOR\n)", text)


def split_options(text: str):
    """Return list of (prefix, display, suffix_nl) keeping exact separators."""
    if text == "":
        return []
    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        nl = ""
        body = line
        if body.endswith("\r\n"):
            nl, body = "\r\n", body[:-2]
        elif body.endswith("\n"):
            nl, body = "\n", body[:-1]
        elif body.endswith("\r"):
            nl, body = "\r", body[:-1]
        m3 = re.match(r"^(\d+:[^:\r\n]+:)(.*)$", body)
        m2 = re.match(r"^([^:\r\n]+:)(.*)$", body)
        if m3:
            out.append((m3.group(1), m3.group(2), nl, body))
        elif m2 and m2.group(2).strip():
            out.append((m2.group(1), m2.group(2), nl, body))
        else:
            out.append((None, None, nl, body))
    return out


def text_segments(text):
    return [p for p in split_or(text) if p not in ("\r\nOR\r\n", "\nOR\n") and p.strip()]


def script_quotes(script):
    return [inner for _a, _b, inner in scan_quotes(script)]


def blank_quotes(script):
    out = []
    last = 0
    for a, b, _inner in scan_quotes(script):
        out.append(script[last:a])
        out.append('"§"')
        last = b
    out.append(script[last:])
    return "".join(out)


def option_prefixes(text):
    prefs = []
    for prefix, display, nl, body in split_options(text):
        prefs.append(prefix if prefix is not None else body)
    return tuple(prefs)


def apply_rule_map(row, idx, repl):
    """repl maps (kind, ordinal) -> zh. Only player-facing English pieces are replaced."""
    text_i, opt_i, scr_i = idx["text"], idx["options"], idx["script"]
    ti = oi = si = 0
    parts = split_or(row[text_i])
    new_parts = []
    for part in parts:
        if part in ("\r\nOR\r\n", "\nOR\n") or not part.strip():
            new_parts.append(part)
            continue
        key = ("text", ti)
        ti += 1
        new_parts.append(repl.get(key, part))
    row[text_i] = "".join(new_parts)

    opt_bits = []
    for prefix, display, nl, body in split_options(row[opt_i]):
        if prefix is None:
            opt_bits.append(body + nl)
            continue
        key = ("option", oi)
        oi += 1
        shown = repl.get(key, display if display is not None else body)
        if prefix is not None and display is not None:
            opt_bits.append(prefix + shown + nl)
        else:
            opt_bits.append(body + nl)
    row[opt_i] = "".join(opt_bits)

    s = row[scr_i]
    out = []
    last = 0
    for a, b, inner in scan_quotes(s):
        out.append(s[last:a])
        key = ("script", si)
        si += 1
        if key in repl:
            out.append('"' + repl[key] + '"')
        else:
            out.append(s[a:b])
        last = b
    out.append(s[last:])
    row[scr_i] = "".join(out)


class Memory:
    def __init__(self):
        self.exact = {}
        self.conflict = set()

    def add(self, en, zh):
        en = en.strip("\r\n")
        # keep internal newlines; only reject empty
        if not en or not zh or en == zh:
            return
        if en in self.conflict:
            return
        prev = self.exact.get(en)
        if prev is None:
            self.exact[en] = zh
        elif prev != zh:
            self.conflict.add(en)
            self.exact.pop(en, None)

    def get(self, en):
        return self.exact.get(en)


def index_by_key(rows, key_cols):
    idx, header = header_index(rows)
    for k in key_cols:
        if k not in idx:
            return idx, {}
    bags = defaultdict(list)
    for r_i, row in enumerate(rows[1:], start=1):
        if is_comment(row):
            continue
        # pad
        if len(row) < len(header):
            row.extend([""] * (len(header) - len(row)))
        key = tuple(row[idx[k]] if idx[k] < len(row) else "" for k in key_cols)
        if all(not x for x in key):
            continue
        bags[key].append((r_i, row))
    return idx, bags


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    old_zip = find_old_zip()
    z = zipfile.ZipFile(old_zip)
    # extract old csvs that we know, plus any csv
    for info in z.infolist():
        name = info.filename
        if not name.endswith(".csv"):
            continue
        # localization/data/...
        marker = "localization/data/"
        if marker not in name:
            continue
        rel = name.split(marker, 1)[1]
        dest = OLD_DIR / rel
        if not dest.exists() or dest.stat().st_size != info.file_size:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(info))

    mem = Memory()
    glossary_rows = []
    pending = []
    stats = []

    ordered = sorted(SPECS.items(), key=lambda kv: (kv[1].get("mode") == "rules", kv[0]))
    for rel, spec in ordered:
        new_csv = NEW_ROOT / rel
        if not new_csv.exists():
            stats.append(f"MISSING {rel}")
            continue
        new_dump = NEW_DUMP / (rel + ".json")
        if not new_dump.exists():
            dump_csv(new_csv, new_dump)
        new_doc = load_dump(new_dump)
        new_rows = new_doc["rows"]
        # ensure mutable lists
        new_rows = [list(r) for r in new_rows]
        idx, new_bags = index_by_key(new_rows, spec["key"])

        old_csv = OLD_DIR / rel
        old_bags = {}
        old_idx = {}
        if old_csv.exists():
            old_dump = WORK / "old_dump" / (rel + ".json")
            dump_csv(old_csv, old_dump)
            old_doc = load_dump(old_dump)
            old_rows = [list(r) for r in old_doc["rows"]]
            old_idx, old_bags = index_by_key(old_rows, spec["key"])

        reused = fresh = 0
        if spec.get("mode") == "rules":
            reused, fresh = apply_rules(rel, new_rows, idx, new_bags, old_bags, mem, pending)
        else:
            reused, fresh = apply_columns(rel, spec, new_rows, idx, new_bags, old_idx, old_bags, mem, pending, glossary_rows)
        stats.append(f"{rel}: reused_segments={reused} pending_segments={fresh} keys={len(new_bags)}")
        # stash modified rows for a later write
        new_doc["rows"] = new_rows
        staged = STATE / "staged" / (rel + ".json")
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text(json.dumps(new_doc, ensure_ascii=False), encoding="utf-8")

    # second pass: fill pending from exact memory where possible
    still = []
    filled = 0
    for item in pending:
        hit = mem.get(item["en"])
        if hit and tokens_ok(item["en"], hit):
            item["zh"] = hit
            item["via"] = "memory"
            filled += 1
        else:
            still.append(item)
    stats.append(f"memory_filled={filled} still_pending={len(still)} memory={len(mem.exact)} conflicts={len(mem.conflict)}")

    (STATE / "stats.txt").write_text("\n".join(stats), encoding="utf-8")
    (STATE / "pending.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in still) + ("\n" if still else ""),
        encoding="utf-8",
    )
    # unique pending
    uniq = {}
    for item in still:
        key = item["en"] if len(item["en"]) > 24 else item["en"] + "\n@@" + item.get("kind", "")
        uniq.setdefault(key, item["en"])
    (STATE / "pending_unique.txt").write_text(
        "\n----\n".join(uniq.values()), encoding="utf-8"
    )
    (STATE / "glossary_seed.tsv").write_text(
        "\n".join(f"{a}\t{b}\t{c}" for a, b, c in glossary_rows),
        encoding="utf-8",
    )
    (STATE / "memory.json").write_text(
        json.dumps(mem.exact, ensure_ascii=False), encoding="utf-8"
    )
    print("\n".join(stats))
    print("unique_pending_keys", len(uniq))


def apply_columns(rel, spec, new_rows, idx, new_bags, old_idx, old_bags, mem, pending, glossary_rows):
    reused = fresh = 0
    cols = [c for c in spec["cols"] if c in idx]
    for key, items in new_bags.items():
        old_items = old_bags.get(key, [])
        for n, (r_i, row) in enumerate(items):
            old_row = old_items[n][1] if n < len(old_items) else None
            for col in cols:
                ci = idx[col]
                if ci >= len(row):
                    continue
                en = row[ci]
                if not looks_player_text(en):
                    continue
                zh = None
                if old_row is not None and col in old_idx and old_idx[col] < len(old_row):
                    cand = old_row[old_idx[col]]
                    if cand and cand != en and tokens_ok(en, cand) and re.search(r"[\u4e00-\u9fff]", cand):
                        zh = cand
                if zh:
                    row[ci] = zh
                    mem.add(en, zh)
                    reused += 1
                    if col in NAME_COLS or col == "name":
                        if len(en) <= 48:
                            glossary_rows.append((en, zh, rel + ":" + col))
                else:
                    pending.append({
                        "file": rel, "row": r_i, "col": col, "key": "|".join(key),
                        "kind": col, "en": en,
                    })
                    fresh += 1
    return reused, fresh


def apply_rules(rel, new_rows, idx, new_bags, old_bags, mem, pending):
    reused = fresh = 0
    needed = ["text", "options", "script", "trigger", "conditions"]
    if any(k not in idx for k in needed):
        return 0, 0
    for key, items in new_bags.items():
        old_items = old_bags.get(key, [])
        for n, (r_i, row) in enumerate(items):
            en_text = text_segments(row[idx["text"]])
            en_opts = split_options(row[idx["options"]])
            en_quotes = script_quotes(row[idx["script"]])
            repl = {}
            paired = False
            old_row = old_items[n][1] if n < len(old_items) else None
            learned = []
            if old_row is not None:
                same_code = (
                    row[idx["trigger"]] == old_row[idx["trigger"]]
                    and row[idx["conditions"]] == old_row[idx["conditions"]]
                    and blank_quotes(row[idx["script"]]) == blank_quotes(old_row[idx["script"]])
                    and option_prefixes(row[idx["options"]]) == option_prefixes(old_row[idx["options"]])
                    and len(text_segments(row[idx["text"]])) == len(text_segments(old_row[idx["text"]]))
                )
                if same_code:
                    zh_text = text_segments(old_row[idx["text"]])
                    zh_opts = split_options(old_row[idx["options"]])
                    zh_quotes = script_quotes(old_row[idx["script"]])
                    if len(zh_opts) == len(en_opts) and len(zh_quotes) == len(en_quotes):
                        paired = True
                        for i, (en, zh) in enumerate(zip(en_text, zh_text)):
                            if not looks_player_text(en):
                                if en != zh:
                                    paired = False
                                    break
                                continue
                            if not (tokens_ok(en, zh) and re.search(r"[\u4e00-\u9fff]", zh)):
                                paired = False
                                break
                            repl[("text", i)] = zh
                            learned.append((en, zh))
                        if paired:
                            for i, ((ep, ed, _nl, _b), (zp, zd, _znl, _zb)) in enumerate(zip(en_opts, zh_opts)):
                                if ep != zp:
                                    paired = False
                                    break
                                if ed is None:
                                    continue
                                if not looks_player_text(ed):
                                    if ed != zd:
                                        paired = False
                                        break
                                    continue
                                if not (tokens_ok(ed, zd or "") and re.search(r"[\u4e00-\u9fff]", zd or "")):
                                    paired = False
                                    break
                                repl[("option", i)] = zd
                                learned.append((ed, zd))
                        if paired:
                            for i, (en, zh) in enumerate(zip(en_quotes, zh_quotes)):
                                if not should_translate_script(en):
                                    if en != zh:
                                        paired = False
                                        break
                                    continue
                                if not (tokens_ok(en, zh) and re.search(r"[\u4e00-\u9fff]", zh)):
                                    paired = False
                                    break
                                repl[("script", i)] = zh
                                learned.append((en, zh))
                        if not paired:
                            repl = {}
                            learned = []
            if paired and (repl or not any(looks_player_text(t) for t in en_text)):
                for en, zh in learned:
                    mem.add(en, zh)
                apply_rule_map(row, idx, repl)
                reused += len(repl)
                continue
            # unchanged identifiers aside, queue English pieces and try memory per piece
            piece_repl = {}
            missed = []
            for i, en in enumerate(en_text):
                if not looks_player_text(en):
                    continue
                hit = mem.get(en)
                if hit and tokens_ok(en, hit):
                    piece_repl[("text", i)] = hit
                else:
                    missed.append(("text", en))
            for i, (ep, ed, _nl, _b) in enumerate(en_opts):
                if ed is None or not looks_player_text(ed):
                    continue
                hit = mem.get(ed)
                if hit and tokens_ok(ed, hit):
                    piece_repl[("option", i)] = hit
                else:
                    missed.append(("option", ed))
            for i, en in enumerate(en_quotes):
                if not should_translate_script(en):
                    continue
                hit = mem.get(en)
                if hit and tokens_ok(en, hit):
                    piece_repl[("script", i)] = hit
                else:
                    missed.append(("script", en))
            if piece_repl:
                apply_rule_map(row, idx, piece_repl)
                reused += len(piece_repl)
            for kind, en in missed:
                pending.append({
                    "file": rel, "row": r_i, "col": kind, "key": "|".join(key),
                    "kind": kind, "en": en,
                })
                fresh += 1
    return reused, fresh


if __name__ == "__main__":
    main()
