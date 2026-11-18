# -*- coding: utf-8 -*-
import re
import zipfile
from pathlib import Path

zpath = next(Path(r"d:\Game\Starsector\local_old").glob("*.zip"))
z = zipfile.ZipFile(zpath)
out = []
for info in z.infolist():
    if info.filename.endswith(".faction") and "factions/" in info.filename:
        text = z.read(info).decode("utf-8")
        m = re.search(r'"displayName"\s*:\s*"([^"]*)"', text)
        m2 = re.search(r'"id"\s*:\s*"([^"]*)"', text) or re.search(r'\bid\s*:\s*"([^"]*)"', text)
        out.append(f"{info.filename.split('/')[-1]}\t{m2.group(1) if m2 else ''}\t{m.group(1) if m else ''}")
Path(r"d:\Game\Starsector\l10n_work\state\factions.tsv").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
