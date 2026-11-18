# -*- coding: utf-8 -*-
"""Fill the short JSON strings the previous pack did not already cover."""
import json
from pathlib import Path

from ssjson import walk

ROOT = Path(r"d:\Game\Starsector\l10n_work\state\json_staged")
NEW = Path(r"d:\Game\Starsector\starsector-core\data")
PENDING = Path(r"d:\Game\Starsector\l10n_work\state\pending_json.jsonl")

ZH = {
    "Local Comms": "本地通讯",
    "Comms": "通讯",
    "Secure Comm Channel": "加密通讯频道",
    "Analysis & Projections": "分析与推演",
    "Intelligence Assessment": "情报评估",
    "Intel": "情报",
    "Comm Sniffer Program": "通讯嗅探程序",
    "Comm Data Feed": "通讯数据流",
    "Data": "数据",
    "Local Bulletin": "本地公告",
    "News Report": "新闻报道",
    "News": "新闻",
    "Hegemony Broadcast Service": "霸主广播服务",
    "Hegemony Intelligence": "霸主情报",
    "Intelligence Report": "情报报告",
    "Tri-Tachyon Network": "速子科技网络",
    "Tri-Tachyon Intelligence": "速子科技情报",
    "Sindrian Diktat Security": "辛达强权安保",
    "Asteroid Base": "小行星基地",
    "asteroid base": "小行星基地",
    "You can change the frequency of tips by adding a json object instead of a string, like so. For example, this tip has a frequency of 0 and will never show up. The default freq value is 1.": "可以把提示从字符串改成 json 对象来调整出现频率。例如这条提示的频率是 0，因此不会出现。默认频率为 1。",
    "Percentage increases are additive. Percentage reductions are generally multiplicative.": "百分比加成相互累加。百分比减益通常彼此相乘。",
    "Buy this %s for %s credits.": "购买此 {%s}，价格为 {%s} 星币。",
    "Sell this %s for %s credits.": "出售此 {%s}，价格为 {%s} 星币。",
    "Mercenary": "雇佣兵",
    "Custom": "特装",
    "Advanced": "高级",
    "Classified": "机密",
    "Restricted": "受限",
    "Command": "指挥",
    "Executive": "高管",
    "Artificial Intelligence": "人工智能",
    "Criminal": "罪犯",
    "Fugitive": "逃犯",
    "Personnel Officer": "人事军官",
    "Underworld Boss": "地下头目",
    "Associate Academician": "副院士",
    "Assistant Academician": "助理院士",
    "Exile": "流放者",
    "Sindrian Reformers": "辛达改革派",
    "the Reformed Sindrian Diktat": "改革后的辛达强权",
    "Supreme Executor": "最高执行官",
    "Leader of Executive Guard": "执行卫队领袖",
    "Controller-General": "总监",
    "No description yet.": "暂无描述。",
    "Fleet": "舰队",
    "Some of the ships in your fleet are in danger of suffering accidents due to having 0% combat readiness.\n\nAccidents may damage or even destroy a ship.\n\nIt's recommended that you either mothball those ships or let them recover combat readiness as soon as possible.": "你的舰队中有些舰船战斗准备度为 0%，有发生事故的危险。\n\n事故可能损坏甚至摧毁舰船。\n\n建议封存这些舰船，或尽快让它们恢复战斗准备度。",
}

# difficulty enums and the acronym DEM stay English
SKIP = {"MEDIUM", "HARD", "DEM"}


def escape(text, quote):
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == quote:
            out.append("\\" + quote)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            continue
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


def main():
    rows = [json.loads(l) for l in PENDING.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_file = {}
    for r in rows:
        if r["en"] in SKIP:
            continue
        zh = ZH.get(r["en"])
        if not zh:
            print("MISSING", r["en"][:80])
            continue
        by_file.setdefault(r["file"], []).append((r["path"], r["en"], zh))
    for rel, items in by_file.items():
        staged = ROOT / rel
        src = staged if staged.exists() else NEW / rel
        text = src.read_text(encoding="utf-8")
        leaves = {(p, v): (a, b, q) for p, v, a, b, q in walk(text)}
        repls = []
        for path, en, zh in items:
            hit = leaves.get((path, en))
            if not hit:
                # value may already be translated
                print("NO SPAN", rel, path)
                continue
            a, b, q = hit
            repls.append((a, b, escape(zh, q)))
        buf = text
        for a, b, body in sorted(repls, reverse=True):
            buf = buf[:a] + body + buf[b:]
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(buf, encoding="utf-8")
        print(rel, len(repls))


if __name__ == "__main__":
    main()
