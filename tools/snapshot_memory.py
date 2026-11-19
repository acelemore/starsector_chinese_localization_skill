# -*- coding: utf-8 -*-
"""Pair an English tree with its translated tree and write a memory JSONL.

    python snapshot_memory.py --project vanilla --version 0.98.5a-RC7 ^
        --en-root d:\\Game\\Starsector\\starsector-core.backup ^
        --zh-root d:\\Game\\Starsector\\starsector-core

The memory is the baseline for a later diff. Each record keeps the English
that was translated and the Chinese that shipped.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import extract, pair, write_jsonl

GAME = Path(r"d:\Game\Starsector")
WORK = Path(r"d:\Game\Starsector\l10n_work")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="vanilla or a mod id")
    p.add_argument("--version", required=True)
    p.add_argument("--en-root", type=Path, required=True)
    p.add_argument("--zh-root", type=Path, required=True)
    p.add_argument("--kind", default="vanilla", choices=["vanilla", "mod"])
    args = p.parse_args()
    base = WORK / "projects" / args.project
    cache = base / "cache" / args.version
    print("extract en", args.en_root)
    en_rows = extract(args.en_root, cache / "en")
    print("extract zh", args.zh_root, "en", len(en_rows))
    zh_rows = extract(args.zh_root, cache / "zh")
    print("zh", len(zh_rows))
    memory = pair(en_rows, zh_rows)
    translated = sum(1 for row in memory if row["zh"] != row["en"])
    dest = base / "memory" / f"{args.version}.jsonl"
    write_jsonl(dest, memory)
    meta = {
        "id": args.project,
        "kind": args.kind,
        "version": args.version,
        "en_root": str(args.en_root),
        "zh_root": str(args.zh_root),
        "records": len(memory),
        "translated": translated,
    }
    (base / "project.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
