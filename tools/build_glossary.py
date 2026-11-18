# -*- coding: utf-8 -*-
import json
from pathlib import Path

seed = Path(r"d:\Game\Starsector\l10n_work\state\glossary_seed.tsv")
rows = []
for line in seed.read_text(encoding="utf-8").splitlines():
    parts = line.split("\t")
    if len(parts) < 3:
        continue
    en, zh, src = parts[0], parts[1], parts[2]
    if en == zh:
        continue
    if not any("\u4e00" <= c <= "\u9fff" for c in zh):
        continue
    rows.append((en, zh, src))

# prefer name columns, shorter, first seen
best = {}
prio = {
    "hulls/ship_data.csv:name": 0,
    "weapons/weapon_data.csv:name": 1,
    "shipsystems/ship_systems.csv:name": 2,
    "hullmods/hull_mods.csv:name": 3,
    "characters/skills/skill_data.csv:name": 4,
    "campaign/commodities.csv:name": 5,
    "campaign/industries.csv:name": 6,
    "campaign/market_conditions.csv:name": 7,
    "campaign/abilities.csv:name": 8,
    "campaign/special_items.csv:name": 9,
    "hulls/ship_data.csv:designation": 10,
    "hulls/ship_data.csv:tech/manufacturer": 11,
    "weapons/weapon_data.csv:tech/manufacturer": 11,
    "hullmods/hull_mods.csv:tech/manufacturer": 11,
    "weapons/weapon_data.csv:primaryRoleStr": 12,
    "hulls/wing_data.csv:role desc": 12,
    "characters/personalities.csv:name": 13,
}
for en, zh, src in rows:
    rank = prio.get(src, 50)
    prev = best.get(en)
    if prev is None or rank < prev[0]:
        best[en] = (rank, zh, src)

lines = [f"{en}\t{zh}\t{src}" for en, (rank, zh, src) in sorted(best.items(), key=lambda kv: (kv[1][0], kv[0].lower()))]
out = Path(r"d:\Game\Starsector\l10n_work\state\glossary.tsv")
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("terms", len(lines))
# print high priority
for en, (rank, zh, src) in sorted(best.items(), key=lambda kv: (kv[1][0], kv[0].lower())):
    if rank <= 11 and len(en) <= 40:
        print(f"{en} = {zh}")
