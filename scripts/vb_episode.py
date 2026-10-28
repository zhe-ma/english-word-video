"""读取文案文件，规范化为每期的 episode 数据并校验。

正文里直接写中英混读：学习词写成 `英文 (词性. 释义)`；其余位置再出现的同一个词
（含屈折词形，recalled → recall，通过 ECDICT 的 exchange 字段还原）会自动算作该学习项。
"""
import functools
import re
import sqlite3
from pathlib import Path

import yaml

from vb_config import (DEFAULTS, ECDICT_DB, HETERONYMS, ITEMS_RANGE, LEVEL_TAGS, MAX_GLOSS_LEN, MAX_TEXT_WEIGHT)
from vb_errors import BatchError

HANZI = re.compile(r"[\u4e00-\u9fff]")
EN_RUN = re.compile(r"[A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*)*")
SAFE_ID = re.compile(r"[^\w-]+")
PHRASE_POS = {"", "短语", "phrase", "phr.", "词组"}


# ---------- 词典 ----------

@functools.lru_cache(maxsize=1)
def _db():
    if not ECDICT_DB.exists():
        return None
    con = sqlite3.connect(ECDICT_DB)
    con.row_factory = sqlite3.Row
    return con


@functools.lru_cache(maxsize=None)
def dict_row(word):
    con = _db()
    if con is None:
        return None
    return con.execute(
        "SELECT word, phonetic, tag, exchange, translation FROM words WHERE word = ? COLLATE NOCASE",
        (word,)).fetchone()


def find_words(query, level=None, limit=12):
    """查词：英文精确查，查不到按前缀；中文在释义里搜。level 只保留该级别词表里的词。"""
    con = _db()
    if con is None:
        return []
    tag = LEVEL_TAGS.get(level, level) if level else None
    order = "ORDER BY CASE WHEN frq = 0 THEN 1 ELSE 0 END, frq LIMIT ?"
    if re.fullmatch(r"[A-Za-z' -]+", query):
        q = query.lower().strip()
        rows = con.execute("SELECT * FROM words WHERE word = ?", (q,)).fetchall()
        if not rows:
            rows = con.execute(f"SELECT * FROM words WHERE word LIKE ? {order}", (q + "%", limit)).fetchall()
    else:
        sql, args = "SELECT * FROM words WHERE translation LIKE ?", [f"%{query}%"]
        if tag:
            sql += " AND (' ' || tag || ' ') LIKE ?"
            args.append(f"% {tag} %")
        rows = con.execute(f"{sql} {order}", (*args, limit)).fetchall()
    return rows


IPA_FIX = str.maketrans({"'": "ˈ", ",": "ˌ", ".": "ˌ", ":": "ː", "ә": "ə", "g": "ɡ", "ε": "ɛ", "є": "ɛ"})
# 词库用的是金山风格的音标（i = ɪ，ei = eɪ，әu = əʊ）。只做有把握的规范化：复合元音，以及后面跟辅音的短 i。
_DIPHTHONGS = [("ei", "eɪ"), ("ai", "aɪ"), ("ɔi", "ɔɪ"), ("au", "aʊ"), ("əu", "əʊ"), ("iə", "ɪə"), ("uə", "ʊə")]
_SHORT_I = re.compile(r"i(?=[ˈˌ]?[^aeiouæɑɒɔəɛɜʌʊɪɚːˈˌ/\s]+)")


def normalize_ipa(p):
    p = p.translate(IPA_FIX)
    for a, b in _DIPHTHONGS:
        p = p.replace(a, b)
    return _SHORT_I.sub("ɪ", p)


def ipa(word):
    row = dict_row(word)
    p = (row["phonetic"] or "").strip() if row else ""
    return f"/{normalize_ipa(p)}/" if p else ""


_POS_ALIAS = {"adj": "a", "a": "a", "n": "n", "v": "v", "vt": "v", "vi": "v", "adv": "adv"}


def dict_meanings(word, pos, limit=4):
    """词典里同一词性的其他义项，供词卡展示。正文仍只用文案里的那一条。"""
    row = dict_row(word)
    if not row or not row["translation"]:
        return []
    want = _POS_ALIAS.get(str(pos or "").lower().split("/")[0].rstrip("."), "")
    hit, rest = [], []
    for line in row["translation"].split("\n"):
        line = line.strip()
        if not line or line.startswith("["):
            continue
        m = re.match(r"^([a-z]+)\.\s*", line, re.I)
        line_pos = m.group(1).lower() if m else ""
        text = line[m.end():] if m else line
        matched = want and line_pos and (line_pos.startswith(want) or want.startswith(line_pos))
        (hit if matched or not line_pos else rest).append(text)
    lines = hit or rest
    out = []
    for text in lines:
        for part in re.split(r"[，,;；]", text):
            part = re.sub(r"\s+", "", part.strip())
            if part and part not in out and len(part) <= 12:
                out.append(part)
            if len(out) >= limit:
                return out
    return out


def review_senses(it, limit=3):
    """词卡上的更多释义：文案里分号后面的，再加上词典里不同的义项。"""
    gloss = it["gloss"]
    out = []
    for s in list(it.get("senses") or []):
        if s and s != gloss and s not in out:
            out.append(s)
    if it["kind"] == "word" and len(out) < limit:
        for s in dict_meanings(it["en"], it["pos"]):
            if s != gloss and gloss not in s and s not in gloss and s not in out:
                out.append(s)
            if len(out) >= limit:
                break
    return out[:limit]


@functools.lru_cache(maxsize=None)
def variants(word):
    """原形及其屈折变化（ECDICT exchange：过去式、分词、三单、复数、比较级等）。"""
    w = word.lower().replace("’", "'")
    out = {w}
    row = dict_row(w)
    if row and row["exchange"]:
        for part in row["exchange"].split("/"):
            kind, _, form = part.partition(":")
            if kind not in ("0", "1") and form:
                out.add(form.lower())
    return frozenset(out)


# ---------- 读取 ----------

def load_batch(path):
    """返回 (defaults, [原始条目])。文件可以是 {defaults, episodes} 或直接是列表。"""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise BatchError(f"YAML 解析失败：{e}") from e
    if isinstance(raw, list):
        return dict(DEFAULTS), raw
    if not isinstance(raw, dict) or not isinstance(raw.get("episodes"), list):
        raise BatchError("文案文件需要 episodes 列表")
    return {**DEFAULTS, **(raw.get("defaults") or {})}, raw["episodes"]


# ---------- 规范化 ----------

def split_gloss(gloss):
    """「低绩效；表现不佳」→ 正文用第一条，其余留给词卡。"""
    parts = [p.strip() for p in re.split(r"[；;]", str(gloss or "")) if p.strip()]
    return (parts[0] if parts else ""), parts[1:]


def parse_item(en, pos, gloss):
    en = re.sub(r"\s+", " ", str(en or "")).strip()
    pos = str(pos or "").strip()
    if pos not in PHRASE_POS and re.fullmatch(r"[A-Za-z][A-Za-z./]*", pos) and not pos.endswith("."):
        pos += "."
    gloss, extra = split_gloss(gloss)
    return {
        "en": en, "pos": "" if pos in PHRASE_POS else pos, "gloss": gloss, "senses": [s for s in extra if s != gloss],
        "kind": "phrase" if " " in en or pos in PHRASE_POS else "word",
    }


# 英文 (词性. 释义；更多释义)。词性可以是 n / adj / v / 短语。
MARK = re.compile(
    r"([A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*)*)\s*[（(]\s*([^()）.．]{1,12}?)\s*[.．]\s*([^()）]+?)\s*[)）]"
)


def parse_marked_text(text):
    """把带括号注释的正文拆成（纯正文行, 学习项）。一行一段。"""
    items, seen = [], {}
    pages = []

    def repl(m):
        en = re.sub(r"\s+", " ", m.group(1)).strip()
        key = en.lower()
        gloss = m.group(3).strip()
        if key in seen:
            if items[seen[key]]["gloss"] != split_gloss(gloss)[0]:
                raise BatchError(f"{en} 出现了两次，释义不一致")
        else:
            seen[key] = len(items)
            items.append(parse_item(en, m.group(2).strip(), gloss))
        return en

    for line in str(text or "").splitlines():
        line = line.strip()
        if line:
            pages.append(MARK.sub(repl, line))
    if not pages:
        raise BatchError("text 是空的")
    if not items:
        raise BatchError("text 里没有「英文 (词性. 释义)」，例如 baseline (n. 底线)")
    return pages, items


def item_keys(items):
    """[(每个位置可接受的词形集合, 学习项下标)]。"""
    return [(tuple(variants(w) for w in it["en"].split()), i) for i, it in enumerate(items)]


def split_english(run, keys):
    """把一段连续英文切成 [(文本, 学习项下标或 None)]，优先最长匹配。"""
    words = run.split()
    longest = max((len(k) for k, _ in keys), default=1)
    out, p = [], 0
    while p < len(words):
        hit = None
        for n in range(min(longest, len(words) - p), 0, -1):
            seg = words[p:p + n]
            low = [w.lower().replace("’", "'") for w in seg]
            idx = next((i for k, i in keys if len(k) == n and all(w in s for w, s in zip(low, k))), None)
            if idx is not None:
                hit = (" ".join(seg), idx, n)
                break
        if hit:
            out.append((hit[0], hit[1]))
            p += hit[2]
        else:
            out.append((words[p], None))
            p += 1
    return out


def tokenize(text, keys):
    """正文 → [{t: 中文} | {i: 学习项下标, text} | {en: 非学习项英文}]。"""
    text = re.sub(r"\s*\n\s*", "", text.strip())
    tokens, pos = [], 0
    for m in EN_RUN.finditer(text):
        if m.start() > pos:
            tokens.append({"t": text[pos:m.start()].strip(" ")})
        for seg, idx in split_english(m.group(0), keys):
            tokens.append({"i": idx, "text": seg} if idx is not None else {"en": seg})
        pos = m.end()
    if pos < len(text):
        tokens.append({"t": text[pos:].strip(" ")})
    merged = []
    for tk in tokens:
        if "en" in tk and merged and "en" in merged[-1]:
            merged[-1]["en"] += " " + tk["en"]
        elif "t" in tk and not tk["t"]:
            continue
        else:
            merged.append(tk)
    return merged


def normalize(raw, index, defaults):
    if not isinstance(raw, dict):
        raise BatchError(f"第 {index} 条不是对象")
    ep = {k: raw.get(k, v) for k, v in defaults.items()}
    ep["id"] = SAFE_ID.sub("-", str(raw.get("id") or f"{index:02d}")).strip("-") or f"{index:02d}"
    ep["level"] = str(ep["level"] or "").strip()
    ep["series"] = str(ep["series"] or "").strip() or (f"{ep['level']}单词" if ep["level"] else "中英混读单词")
    ep["title"] = str(raw.get("title") or "").strip()
    cover = raw.get("cover") or ep["title"]
    ep["cover"] = [str(c) for c in cover] if isinstance(cover, list) else [str(cover)]

    page_texts, ep["items"] = parse_marked_text(raw.get("text"))
    keys = item_keys(ep["items"])
    ep["pages"] = [{"text": t, "tokens": tokenize(t, keys)} for t in page_texts]
    return ep


def text_weight(tokens, items=None):
    """排版占位的粗略字数：汉字和标点计 1，英文字母计 0.55，每个英文片段再加 1；传入 items 时把释义也算上。"""
    w = 0.0
    for tk in tokens:
        w += len(tk["t"]) if "t" in tk else len(tk.get("text") or tk.get("en")) * 0.55 + 1
        if items is not None and "i" in tk:
            it = items[tk["i"]]
            w += len(it["gloss"]) * 0.8 + len(it["pos"]) * 0.45 + 1
    return w


def restore(page, items):
    """把正文里的英文学习项换回释义（第一个义项），得到纯中文：用来检查读起来通不通、意思对不对。"""
    out = []
    for tk in page["tokens"]:
        if "t" in tk:
            out.append(tk["t"])
        elif "i" in tk:
            out.append(items[tk["i"]]["gloss"])
        else:
            out.append(tk["en"])
    return "".join(out)


# ---------- 校验 ----------

def check(ep):
    errors, warnings = [], []
    E, W = errors.append, warnings.append
    if not ep["title"]:
        E("缺少 title")

    seen = set()
    for it in ep["items"]:
        key = it["en"].lower()
        if key in seen:
            E(f"学习项重复：{it['en']}")
        seen.add(key)
        if not it["gloss"]:
            E(f"{it['en']}：缺少释义")
        elif len(it["gloss"]) > MAX_GLOSS_LEN:
            W(f"{it['en']}：释义「{it['gloss']}」超过 {MAX_GLOSS_LEN} 字，注释可能挤")

    used = {tk["i"] for p in ep["pages"] for tk in p["tokens"] if "i" in tk}
    for i, it in enumerate(ep["items"]):
        if i not in used:
            E(f"{it['en']}：正文里没有出现，检查拼写")
    extras = sorted({tk["en"] for p in ep["pages"] for tk in p["tokens"] if "en" in tk})
    if extras:
        W(f"正文里这些英文不是学习项，将按普通文字显示：{', '.join(extras)}")

    lo, hi = ITEMS_RANGE
    if not lo <= len(ep["items"]) <= hi:
        W(f"学习项 {len(ep['items'])} 个，建议 {lo}–{hi} 个")

    total = sum(text_weight(p["tokens"], ep["items"]) for p in ep["pages"])
    if total > MAX_TEXT_WEIGHT:
        W(f"全文约 {total:.0f} 字，超过 {MAX_TEXT_WEIGHT}，一页放下需要明显缩小字号，建议删减")
    for n, p in enumerate(ep["pages"], 1):
        if re.search(r"[,.!?;:]", "".join(tk["t"] for tk in p["tokens"] if "t" in tk)):
            W(f"第 {n} 段有半角标点，中文请用全角")

    if ep["level"] and ep["level"] not in LEVEL_TAGS:
        W(f"level「{ep['level']}」不在 {' / '.join(LEVEL_TAGS)} 里，不做词表校验")
    tag = LEVEL_TAGS.get(ep["level"])
    if _db() is None:
        W("找不到词库 scripts/ecdict-lite.db，跳过词典检查")
    else:
        for it in ep["items"]:
            missing = [w for w in it["en"].split() if dict_row(w) is None]
            if missing:
                W(f"{it['en']}：词典里查不到 {missing}，检查拼写（查不到不影响生成，但没有音标）")
            elif it["kind"] == "word" and tag:
                row = dict_row(it["en"])
                if tag not in (row["tag"] or "").split():
                    W(f"{it['en']}：词库标注里没有「{ep['level']}」（仅供参考，标注不全；tag: {row['tag'] or '无'}）")
            if it["kind"] == "word" and it["en"].lower() in HETERONYMS:
                W(f"{it['en']}：多音词，TTS 可能读错")
    return errors, warnings


def load_episodes(arg, only=None):
    """返回 (文案文件路径, [(episode, errors, warnings)])。"""
    path = Path(arg)
    if not path.exists():
        raise BatchError(f"找不到文案文件：{arg}")
    path = path.resolve()
    defaults, raws = load_batch(path)
    out, ids = [], set()
    for n, raw in enumerate(raws, 1):
        try:
            ep = normalize(raw, n, defaults)
        except BatchError as e:
            raw = raw if isinstance(raw, dict) else {}
            ep = {"id": SAFE_ID.sub("-", str(raw.get("id") or f"{n:02d}")), "title": str(raw.get("title", ""))}
            out.append((ep, [str(e)], []))
            continue
        errors, warnings = check(ep)
        if ep["id"] in ids:
            errors.append(f"id 重复：{ep['id']}")
        ids.add(ep["id"])
        out.append((ep, errors, warnings))
    if only:
        want = set(only)
        out = [x for x in out if x[0]["id"] in want]
        if not out:
            raise BatchError(f"--only 没有匹配到任何一期：{', '.join(only)}")
    return path, out
