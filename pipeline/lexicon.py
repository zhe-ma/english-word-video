import csv
import re
import sqlite3
import sys

from .config import ECDICT_CSV, ECDICT_DB

POS_RE = re.compile(r"^(n|v|vt|vi|a|adj|adv|prep|conj|pron|num|int|art|abbr)\.", re.I)


def init_db():
    if not ECDICT_CSV.exists():
        sys.exit(f"缺少 {ECDICT_CSV}，先下载 ECDICT：https://github.com/skywind3000/ECDICT")
    ECDICT_DB.unlink(missing_ok=True)
    con = sqlite3.connect(ECDICT_DB)
    con.execute("""CREATE TABLE words(
        word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, tag TEXT,
        collins INT, oxford INT, bnc INT, frq INT, exchange TEXT)""")
    csv.field_size_limit(sys.maxsize)
    rows = []
    with open(ECDICT_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            w = r["word"]
            if not re.fullmatch(r"[a-z]+", w):
                continue
            if not (r["tag"] or r["oxford"] == "1" or (r["collins"] or "0") != "0"):
                continue
            rows.append((w, r["phonetic"], r["translation"].replace("\\n", "\n"), r["tag"],
                         int(r["collins"] or 0), int(r["oxford"] or 0),
                         int(r["bnc"] or 0), int(r["frq"] or 0), r["exchange"]))
    con.executemany("INSERT OR IGNORE INTO words VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    print(f"已导入 {len(rows)} 个词 → {ECDICT_DB}")


def connect():
    if not ECDICT_DB.exists():
        sys.exit("词库未初始化，先运行：./vv init-db")
    con = sqlite3.connect(ECDICT_DB)
    con.row_factory = sqlite3.Row
    return con


def lookup(con, word):
    return con.execute("SELECT * FROM words WHERE word = ?", (word.lower(),)).fetchone()


def senses(translation):
    """把 ECDICT 的 translation 拆成 [(pos, 释义), ...]，去掉 [网络] 等杂项。"""
    out = []
    for line in (translation or "").split("\n"):
        line = line.strip()
        if not line or line.startswith("["):
            continue
        m = POS_RE.match(line)
        pos = (m.group(0).lower() if m else "")
        text = line[m.end():].strip() if m else line
        out.append((pos, text))
    return out


def main_pos(translation):
    return {p for p, _ in senses(translation)}


IPA_FIX = str.maketrans({"'": "ˈ", ",": "ˌ", ".": "ˌ", ":": "ː", "ә": "ə", "g": "ɡ"})


def ipa(row):
    p = (row["phonetic"] or "").strip() if row else ""
    return f"/{p.translate(IPA_FIX)}/" if p else ""


def short_senses(translation, limit=2):
    parts = []
    for pos, text in senses(translation)[:limit]:
        text = re.sub(r"\s+", "", text)
        parts.append(f"{pos} {text[:18]}".strip())
    return "；".join(parts)
