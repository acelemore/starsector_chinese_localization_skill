# -*- coding: utf-8 -*-
"""Check a translated chunk against its source: count, ids, placeholders."""
import json
import re
import sys
from pathlib import Path

TOKEN = re.compile(
    r"\$[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
    r"|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[a-zA-Z%]"
)
PRONOUN = re.compile(r"\$(?:[A-Za-z]+(?:AOrAn|IsOrAre)|heOrShe|HeOrShe|hisOrHer|HisOrHer|himOrHer|hesOrShes)\b")


def toks(s):
    return [m.group(0) for m in TOKEN.finditer(s or "")]


def meaningful(ts):
    return sorted(t for t in ts if not t.startswith("%") and not PRONOUN.search(t) and not t.endswith("AOrAn") and "IsOrAre" not in t and t not in {
        "$heOrShe", "$HeOrShe", "$hisOrHer", "$HisOrHer", "$himOrHer", "$hesOrShes"
    } and not t.startswith("%"))


def main(n):
    src = json.loads(Path(rf"d:\Game\Starsector\l10n_work\chunks\in\{n}.json").read_text(encoding="utf-8"))
    outp = Path(rf"d:\Game\Starsector\l10n_work\chunks\out\{n}.jsonl")
    rows = [json.loads(l) for l in outp.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"chunk {n}: src {len(src)} out {len(rows)}")
    by = {r.get("i"): r.get("zh", "") for r in rows}
    missing = [s["i"] for s in src if s["i"] not in by or not str(by[s["i"]]).strip()]
    print(" missing", len(missing), missing[:8])
    bad = 0
    no_cjk = 0
    for s in src:
        zh = by.get(s["i"], "")
        if not zh:
            continue
        if not any("\u4e00" <= c <= "\u9fff" for c in zh):
            no_cjk += 1
        et = [t for t in toks(s["en"]) if t.startswith("$") and not PRONOUN.fullmatch(t) and not t[1:].endswith("AOrAn") and not t[1:].endswith("IsOrAre")]
        # percent counts
        ep = sorted(t for t in toks(s["en"]) if t.startswith("%"))
        zp = sorted(t for t in toks(zh) if t.startswith("%") or t.startswith("{%"))
        # normalize {%s} -> %s for compare
        zp_n = sorted(t.strip("{}") for t in zp)
        zt = [t for t in toks(zh) if t.startswith("$") and not PRONOUN.fullmatch(t) and not t[1:].endswith("AOrAn") and not t[1:].endswith("IsOrAre")]
        if sorted(et) != sorted(zt) or ep != zp_n:
            bad += 1
            if bad <= 6:
                print(" TOKEN", s["i"])
                print("  EN", s["en"][:160].replace("\n", " "))
                print("  ZH", zh[:160].replace("\n", " "))
                print("  ", et, zt, ep, zp_n)
    print(" token_mismatches", bad, "no_cjk", no_cjk)
    # samples
    for s in src[:2]:
        print("---", s["i"])
        print(s["en"][:180].replace("\n", " / "))
        print(by.get(s["i"], "")[:180].replace("\n", " / "))


if __name__ == "__main__":
    main(sys.argv[1])
