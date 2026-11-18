# -*- coding: utf-8 -*-
"""Compare SsCsv dump against Python's csv module on the hybrid-decoded text."""
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

JAVA = r"d:\Game\Starsector\jre\bin\java.exe"
CP = r"d:\Game\Starsector\l10n_work\classes;d:\Game\Starsector\starsector-core\json.jar"
ROOT = Path(r"d:\Game\Starsector\starsector-core\data")
DUMP = Path(r"d:\Game\Starsector\l10n_work\dump")

CP1252 = {
    i: chr(c) for i, c in enumerate([
        0x20AC, 0x0081, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021,
        0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x008D, 0x017D, 0x008F,
        0x0090, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014,
        0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x009D, 0x017E, 0x0178
    ], start=0x80)
}

def decode(data: bytes) -> str:
    out = []
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b < 0x80:
            out.append(chr(b))
            i += 1
            continue
        if b >= 0xF0:
            need = 4
        elif b >= 0xE0:
            need = 3
        elif b >= 0xC2:
            need = 2
        else:
            need = 0
        if need and i + need <= n and all((data[i + k] & 0xC0) == 0x80 for k in range(1, need)):
            try:
                out.append(data[i:i + need].decode("utf-8"))
                i += need
                continue
            except UnicodeDecodeError:
                pass
        if 0x80 <= b <= 0x9F:
            out.append(CP1252[b])
        else:
            out.append(chr(b))
        i += 1
    if out and out[0] == "\ufeff":
        out = out[1:]
    return "".join(out)

def py_rows(path: Path):
    text = decode(path.read_bytes())
    return list(csv.reader(io.StringIO(text, newline="")))

def main():
    files = sorted(ROOT.rglob("*.csv"))
    bad = 0
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        out = DUMP / (rel + ".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([JAVA, "-cp", CP, "SsCsv", "dump", str(p), str(out)], capture_output=True, text=True)
        if r.returncode != 0:
            print("JAVA FAIL", rel, r.stderr[-400:])
            bad += 1
            continue
        doc = json.loads(out.read_text(encoding="utf-8"))
        jrows = doc["rows"]
        prows = py_rows(p)
        if len(jrows) != len(prows):
            print(f"COUNT {rel} java={len(jrows)} py={len(prows)} badBytes={doc['badBytes']}")
            bad += 1
            continue
        diffs = 0
        for i, (a, b) in enumerate(zip(jrows, prows)):
            if a != b:
                diffs += 1
                if diffs <= 2:
                    print(f"DIFF {rel} row {i}")
                    print(" J", a[:6])
                    print(" P", b[:6])
        if diffs:
            print(f"DIFFS {rel} {diffs}")
            bad += 1
        else:
            print(f"OK {len(jrows):6} bad={doc['badBytes']:3} {rel}")
    print("failures", bad)

if __name__ == "__main__":
    main()
