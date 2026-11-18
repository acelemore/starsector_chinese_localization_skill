# -*- coding: utf-8 -*-
"""Translate loose Java sources and txt by aligning with the previous pack."""
import json
import re
import zipfile
from pathlib import Path

from apply_csv import looks_player_text, tokens_ok

NEW = Path(r"d:\Game\Starsector\starsector-core\data")
ZIP = next(Path(r"d:\Game\Starsector\local_old").glob("*.zip"))
STATE = Path(r"d:\Game\Starsector\l10n_work\state")
OUT = STATE / "src_staged"
MEM = json.loads((STATE / "memory.json").read_text(encoding="utf-8"))

QUOTE = re.compile(r'"((?:\\.|[^"\\])*)"')


def decode_java(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            n = s[i + 1]
            out.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}.get(n, n))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def encode_java(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            continue
        else:
            out.append(ch)
    return "".join(out)


def cjk(s: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def blank(src: str) -> str:
    return QUOTE.sub('"§"', src)


def strings(src: str):
    return [(m.start(1), m.end(1), decode_java(m.group(1))) for m in QUOTE.finditer(src)]


def apply_java(new: str, old: str | None, rel: str, pending: list) -> str:
    news = strings(new)
    repl = {}
    if old and blank(new) == blank(old):
        olds = strings(old)
        if len(news) == len(olds):
            for (a, b, en), (_c, _d, zh) in zip(news, olds):
                if not looks_player_text(en):
                    continue
                if cjk(zh) and tokens_ok(en, zh):
                    repl[(a, b)] = zh
    if not repl:
        for a, b, en in news:
            if not looks_player_text(en):
                continue
            zh = MEM.get(en)
            if zh and cjk(zh) and tokens_ok(en, zh):
                repl[(a, b)] = zh
            else:
                pending.append({"file": rel, "en": en})
    if not repl:
        return new
    buf = new
    for (a, b), zh in sorted(repl.items(), reverse=True):
        buf = buf[:a] + encode_java(zh) + buf[b:]
    return buf


def apply_txt(new: str, old: str | None, rel: str, pending: list) -> str:
    if old is None:
        pending.append({"file": rel, "en": new[:200]})
        return new
    nlines = new.splitlines(keepends=True)
    olines = old.splitlines(keepends=True)
    if len(nlines) == len(olines):
        out = []
        for nl, ol in zip(nlines, olines):
            ns, os_ = nl.rstrip("\r\n"), ol.rstrip("\r\n")
            end = nl[len(ns):]
            if looks_player_text(ns) and cjk(os_) and tokens_ok(ns, os_):
                out.append(os_ + end)
            else:
                if looks_player_text(ns) and ns != os_:
                    zh = MEM.get(ns)
                    if zh and tokens_ok(ns, zh):
                        out.append(zh + end)
                    else:
                        pending.append({"file": rel, "en": ns})
                        out.append(nl)
                else:
                    out.append(nl)
        return "".join(out)
    # different shape: keep new, queue prose lines
    for nl in nlines:
        ns = nl.strip()
        if looks_player_text(ns) and len(ns) > 20:
            zh = MEM.get(ns)
            if not zh:
                pending.append({"file": rel, "en": ns})
    return new


def main():
    z = zipfile.ZipFile(ZIP)
    OUT.mkdir(parents=True, exist_ok=True)
    pending = []
    changed = 0
    for p in NEW.rglob("*"):
        if p.suffix.lower() not in {".java", ".txt"}:
            continue
        rel = p.relative_to(NEW).as_posix()
        if "graphics/" in rel:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            old = z.read("localization/data/" + rel).decode("utf-8")
        except KeyError:
            old = None
        if p.suffix.lower() == ".java":
            if old is None and not any(looks_player_text(s[2]) for s in strings(text)):
                continue
            new_text = apply_java(text, old, rel, pending)
        else:
            if rel.startswith("missions/") or rel.startswith("codex/"):
                new_text = apply_txt(text, old, rel, pending)
            else:
                continue
        if new_text != text:
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(new_text, encoding="utf-8")
            changed += 1
    (STATE / "pending_src.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in pending) + ("\n" if pending else ""),
        encoding="utf-8",
    )
    print(f"changed={changed} pending={len(pending)}")


if __name__ == "__main__":
    main()
