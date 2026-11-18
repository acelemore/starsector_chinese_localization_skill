# -*- coding: utf-8 -*-
"""Apply chunks/out translations onto a copy of state/staged CSV rows.

Reads pending.jsonl locations and the unique-string chunks. Does not modify
state/staged. Default is a dry run. Pass --apply to write state/merged.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import apply_csv

WORK = Path(r"d:\Game\Starsector\l10n_work")
CHUNKS = WORK / "chunks"
STAGED = WORK / "state" / "staged"
MERGED = WORK / "state" / "merged"
PENDING = WORK / "state" / "pending.jsonl"
RULE_KINDS = {"text", "option", "script"}


def load_translations():
    en_by_i = {}
    for path in sorted((CHUNKS / "in").glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            en_by_i[row["i"]] = row["en"]
    zh_by_i = {}
    missing_files = []
    for path in sorted((CHUNKS / "in").glob("*.json")):
        outp = CHUNKS / "out" / (path.stem + ".jsonl")
        if not outp.exists():
            missing_files.append(path.stem)
            continue
        for line in outp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            zh_by_i[row["i"]] = row["zh"]
    trans = {}
    absent = []
    for i, en in en_by_i.items():
        zh = zh_by_i.get(i)
        if zh is None:
            absent.append(i)
        else:
            trans[en] = zh
    return trans, missing_files, len(en_by_i), len(zh_by_i), absent


def script_zh(zh):
    return zh.replace("\\", "\\\\").replace('"', '\\"')


def apply_rules_row(row, header, items, trans):
    idx = {name: i for i, name in enumerate(header)}
    wanted = defaultdict(set)
    for item in items:
        wanted[item["kind"]].add(item["en"])
    repl = {}
    missed = 0
    text = row[idx["text"]] if "text" in idx else ""
    ti = 0
    for part in apply_csv.split_or(text):
        if part in ("\r\nOR\r\n", "\nOR\n") or not part.strip():
            continue
        if part in wanted["text"]:
            zh = trans.get(part)
            if zh is None:
                missed += 1
            else:
                repl[("text", ti)] = zh
        ti += 1
    oi = 0
    for _prefix, display, _nl, _body in apply_csv.split_options(row[idx["options"]] if "options" in idx else ""):
        if display is None:
            continue
        if display in wanted["option"]:
            zh = trans.get(display)
            if zh is None:
                missed += 1
            else:
                repl[("option", oi)] = zh
        oi += 1
    si = 0
    for _a, _b, inner in apply_csv.scan_quotes(row[idx["script"]] if "script" in idx else ""):
        if inner in wanted["script"]:
            zh = trans.get(inner)
            if zh is None:
                missed += 1
            else:
                repl[("script", si)] = script_zh(zh)
        si += 1
    if repl:
        apply_csv.apply_rule_map(row, idx, repl)
    return len(repl), missed


def apply_column_row(row, header, items, trans):
    idx = {name: i for i, name in enumerate(header)}
    hits = missed = 0
    for item in items:
        zh = trans.get(item["en"])
        ci = idx.get(item["col"])
        if zh is None or ci is None or ci >= len(row):
            missed += 1
            continue
        if row[ci] == item["en"]:
            row[ci] = zh
            hits += 1
        elif row[ci] == zh:
            hits += 1
        else:
            missed += 1
    return hits, missed


def main():
    apply_mode = "--apply" in sys.argv
    trans, missing_files, n_en, n_zh, absent = load_translations()
    pending = [json.loads(l) for l in PENDING.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_file = defaultdict(lambda: defaultdict(list))
    for item in pending:
        by_file[item["file"]][item["row"]].append(item)

    total_hits = total_miss = 0
    for rel, rows_map in by_file.items():
        doc = json.loads((STAGED / (rel + ".json")).read_text(encoding="utf-8"))
        header = doc["rows"][0]
        file_hits = file_miss = 0
        for row_i, items in rows_map.items():
            row = doc["rows"][row_i]
            if items[0]["kind"] in RULE_KINDS:
                hits, missed = apply_rules_row(row, header, items, trans)
            else:
                hits, missed = apply_column_row(row, header, items, trans)
            file_hits += hits
            file_miss += missed
        total_hits += file_hits
        total_miss += file_miss
        print(f"{rel}: hit {file_hits} miss {file_miss}")
        if apply_mode:
            dest = MERGED / (rel + ".json")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    print(
        f"chunks_in {n_en} chunks_out {n_zh} missing_files {len(missing_files)} "
        f"untranslated_ids {len(absent)} pending {len(pending)} hit {total_hits} miss {total_miss}"
    )
    if missing_files:
        print("missing", ",".join(missing_files[:24]))


if __name__ == "__main__":
    main()
