# -*- coding: utf-8 -*-
"""Pair jar string constants with the previous Chinese jars and write a patch list."""
import json
from collections import defaultdict
from pathlib import Path

from apply_csv import looks_player_text, tokens_ok

DUMP = Path(r"d:\Game\Starsector\l10n_work\jar_dump")
STATE = Path(r"d:\Game\Starsector\l10n_work\state")
MEM = json.loads((STATE / "memory.json").read_text(encoding="utf-8"))

PAIRS = [
    ("api.jsonl", "api_old.jsonl", "api"),
    ("obf.jsonl", "obf_old.jsonl", "obf"),
    ("common.jsonl", "common_old.jsonl", "common"),
    ("sound.jsonl", "sound_old.jsonl", "sound"),
]


def load(name):
    bags = defaultdict(list)
    for line in (DUMP / name).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        bags[(o["c"], o["m"], o["d"])].append(o)
    for k in bags:
        bags[k].sort(key=lambda x: x["i"])
    return bags


def cjk(s):
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def worth_pairing(en: str, zh: str) -> bool:
    """Trust the previous pack when it produced Chinese, including short words."""
    if not cjk(zh) or en == zh or not tokens_ok(en, zh):
        return False
    if looks_player_text(en):
        return True
    if any(ch in en for ch in "/\\.{}$"):
        return False
    return en.isalpha() and 2 <= len(en) <= 24


def main():
    patch = []
    pending = []
    for new_name, old_name, tag in PAIRS:
        new_b, old_b = load(new_name), load(old_name)
        reused = fresh = methods = 0
        for key, rows in new_b.items():
            old_rows = old_b.get(key)
            if old_rows and len(old_rows) == len(rows):
                methods += 1
                for n, o in zip(rows, old_rows):
                    en, zh = n["t"], o["t"]
                    if cjk(zh) and worth_pairing(en, zh):
                        patch.append({**{k: n[k] for k in ("c", "m", "d", "i")}, "zh": zh, "jar": tag})
                        reused += 1
                    elif zh == en or not looks_player_text(en):
                        continue
                    else:
                        hit = MEM.get(en)
                        if hit and cjk(hit) and tokens_ok(en, hit):
                            patch.append({**{k: n[k] for k in ("c", "m", "d", "i")}, "zh": hit, "jar": tag})
                            reused += 1
                        else:
                            pending.append({"jar": tag, "c": n["c"], "m": n["m"], "en": en})
                            fresh += 1
            else:
                for n in rows:
                    en = n["t"]
                    if not looks_player_text(en):
                        continue
                    hit = MEM.get(en)
                    if hit and cjk(hit) and tokens_ok(en, hit):
                        patch.append({**{k: n[k] for k in ("c", "m", "d", "i")}, "zh": hit, "jar": tag})
                        reused += 1
                    elif len(en) > 8 and " " in en:
                        pending.append({"jar": tag, "c": n["c"], "m": n["m"], "en": en})
                        fresh += 1
        print(f"{tag}: methods_aligned={methods} reused={reused} pending={fresh}")
    # one patch file per jar
    by = defaultdict(list)
    for item in patch:
        by[item["jar"]].append(item)
    for jar, items in by.items():
        path = STATE / f"jar_patch_{jar}.jsonl"
        path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in items) + "\n", encoding="utf-8")
        print(jar, "patch", len(items))
    (STATE / "pending_jar.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in pending) + ("\n" if pending else ""),
        encoding="utf-8",
    )
    print("pending", len(pending))


if __name__ == "__main__":
    main()
