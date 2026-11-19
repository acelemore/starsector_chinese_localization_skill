# -*- coding: utf-8 -*-
"""Diff a new English catalog against a previous memory.

Unchanged English keeps its old translation.
Modified English (same container, text edited) is listed even when nothing was
added. The old translation is kept only as a reference and is not applied.
Added containers and inserted strings are listed separately.

    python diff_catalog.py --old memory/0.98.5a-RC7.jsonl --new incoming/RC8.jsonl --out diff/RC8
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import diff, diff_stats, read_jsonl, write_jsonl


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = diff(read_jsonl(Path(args.old)), read_jsonl(Path(args.new)))
    out = Path(args.out)
    for name, rows in result.items():
        write_jsonl(out / f"{name}.jsonl", rows)
    stats = diff_stats(result)
    (out / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
