# -*- coding: utf-8 -*-
"""Extract an English catalog from a game or mod tree.

    python extract_catalog.py --root d:\\Game\\Starsector\\starsector-core --out incoming.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import extract, write_jsonl


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--cache", type=Path, required=True)
    args = p.parse_args()
    rows = extract(args.root, args.cache)
    write_jsonl(args.out, rows)
    print(len(rows))


if __name__ == "__main__":
    main()
