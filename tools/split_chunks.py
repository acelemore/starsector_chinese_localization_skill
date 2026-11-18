# -*- coding: utf-8 -*-
import json
from pathlib import Path

src = Path(r"d:\Game\Starsector\l10n_work\state\pending.jsonl")
rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
uniq = []
seen = set()
for r in rows:
    if r["en"] in seen:
        continue
    seen.add(r["en"])
    uniq.append(r["en"])

out_dir = Path(r"d:\Game\Starsector\l10n_work\chunks\in")
out_dir.mkdir(parents=True, exist_ok=True)
# clear old
for p in out_dir.glob("*.json"):
    p.unlink()
size = 80
n = 0
for i in range(0, len(uniq), size):
    chunk = [{"i": i + j, "en": s} for j, s in enumerate(uniq[i:i + size])]
    path = out_dir / f"{n:03d}.json"
    path.write_text(json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
    n += 1
print("unique", len(uniq), "chunks", n, "size", size)
