"""读取批量文案文件，规范化为每期的 episode 数据并校验。

正文里直接写中英混读，不需要标记：连续的英文会自动匹配到 items 里的学习项，
屈折词形（recalled → recall）通过 ECDICT 的 exchange 字段还原。
"""
import functools
import re
import sqlite3
from pathlib import Path

import yaml

from .config import (DEFAULT_SOURCE, DEFAULTS, ECDICT_DB, HETERONYMS, ITEMS_RANGE, LEVEL_TAGS, MAX_GLOSS_LEN,
                     MAX_TEXT_WEIGHT, SCRIPTS)

HANZI = re.compile(r"[\u4e00-\u9fff]")
EN_RUN = re.compile(r"[A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*)*")
SAFE_ID = re.compile(r"[^\w-]+")
PHRASE_POS = {"", "短语", "phrase", "phr.", "词组"}


class BatchError(Exception):
    pass


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


IPA_FIX = str.maketrans({"'": "ˈ", ",": "ˌ", ".": "ˌ", ":": "ː", "ә": "ə", "g": "ɡ"})


def ipa(word):
    row = dict_row(word)
    p = (row["phonetic"] or "").strip() if row else ""
    return f"/{p.translate(IPA_FIX)}/" if p else ""


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

def resolve_path(arg):
    p = Path(arg)
    if p.exists():
        return p.resolve()
    for cand in (SCRIPTS / arg, SCRIPTS / f"{arg}.yaml", SCRIPTS / f"{arg}.yml"):
        if cand.exists():
            return cand.resolve()
    raise BatchError(f"找不到批量文件：{arg}")


def load_batch(path):
    """返回 (defaults, [原始条目])。文件可以是 {defaults, episodes} 或直接是列表。"""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise BatchError(f"YAML 解析失败：{e}") from e
    if isinstance(raw, list):
        return dict(DEFAULTS), raw
    if not isinstance(raw, dict) or not isinstance(raw.get("episodes"), list):
        raise BatchError("批量文件需要 episodes 列表")
    return {**DEFAULTS, **(raw.get("defaults") or {})}, raw["episodes"]


# ---------- 规范化 ----------

def split_gloss(gloss):
    """「低绩效；表现不佳」→ 正文用第一条，其余留给词卡。"""
    parts = [p.strip() for p in re.split(r"[；;]", str(gloss or "")) if p.strip()]
    return (parts[0] if parts else ""), parts[1:]


# 文案括号末尾可以写音标：gloss /ˈaɪpiːeɪ/。没有就继续用词典。
_IPA_TAIL = re.compile(r"\s*(/[^/\s][^/]*/)\s*$")


def peel_ipa(gloss):
    text = str(gloss or "").strip()
    m = _IPA_TAIL.search(text)
    if not m:
        return text, ""
    return text[: m.start()].strip(), m.group(1)


def parse_item(raw):
    senses = []
    if isinstance(raw, (list, tuple)):
        vals = list(raw) + [None] * 4
        en, pos, gloss, forms = vals[0], vals[1], vals[2], vals[3]
    elif isinstance(raw, dict):
        en, pos, gloss, forms = raw.get("en"), raw.get("pos"), raw.get("gloss"), raw.get("forms")
        senses = list(raw.get("senses") or [])
    else:
        raise BatchError(f"学习项格式不对：{raw!r}，用 [英文, 词性, 释义] 或 {{en, pos, gloss}}")
    en = re.sub(r"\s+", " ", str(en or "")).strip()
    if not en:
        raise BatchError(f"学习项缺少英文：{raw!r}")
    pos = str(pos or "").strip()
    if pos not in PHRASE_POS and re.fullmatch(r"[A-Za-z][A-Za-z./]*", pos) and not pos.endswith("."):
        pos += "."
    gloss, extra = split_gloss(gloss)
    if isinstance(forms, str):
        forms = [forms]
    kind = "phrase" if " " in en or pos in PHRASE_POS else "word"
    more = []
    for s in list(senses) + extra:
        s = str(s).strip()
        if s and s != gloss and s not in more:
            more.append(s)
    return {
        "en": en, "pos": "" if pos in PHRASE_POS else pos, "gloss": gloss, "senses": more,
        "kind": kind, "forms": [re.sub(r"\s+", " ", str(f)).strip() for f in (forms or []) if f],
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
        pos = m.group(2).strip()
        gloss, ipa_text = peel_ipa(m.group(3).strip())
        key = en.lower()
        if key in seen:
            prev = items[seen[key]]
            if prev["gloss"] != split_gloss(gloss)[0]:
                raise BatchError(f"{en} 出现了两次，释义不一致")
            if ipa_text and not prev.get("ipa"):
                prev["ipa"] = ipa_text
        else:
            seen[key] = len(items)
            item = parse_item([en, pos, gloss])
            if ipa_text:
                item["ipa"] = ipa_text
            items.append(item)
        return en

    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        pages.append(MARK.sub(repl, line))
    if not pages:
        raise BatchError("text 是空的")
    if not items:
        raise BatchError("text 里没有「英文 (词性. 释义)」，例如 baseline (n. 底线)")
    return pages, items


def item_keys(items):
    """[(每个位置可接受的词形集合, 学习项下标)]。forms 里写的词形按原样精确匹配。"""
    keys = []
    for i, it in enumerate(items):
        keys.append((tuple(variants(w) for w in it["en"].split()), i))
        for form in it["forms"]:
            keys.append((tuple(frozenset([w.lower()]) for w in form.split()), i))
    return keys


def split_english(run, items, keys):
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


def tokenize(text, items, keys):
    """正文 → [{t: 中文} | {i: 学习项下标, text} | {en: 非学习项英文}]。"""
    text = re.sub(r"\s*\n\s*", "", text.strip())
    tokens, pos = [], 0
    for m in EN_RUN.finditer(text):
        if m.start() > pos:
            tokens.append({"t": text[pos:m.start()].strip(" ")})
        for seg, idx in split_english(m.group(0), items, keys):
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


@functools.lru_cache(maxsize=None)
def read_passage(path):
    """真题原文文件 → {source, ids: [句号], sents: {句号: {en, zh}}}。句号 = 段.句，如 3.2。"""
    p = Path(path)
    if not p.exists():
        raise BatchError(f"找不到原文文件：{p}")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise BatchError(f"原文文件 YAML 解析失败：{e}") from e
    if not isinstance(raw, dict) or not isinstance(raw.get("paragraphs"), list):
        raise BatchError(f"原文文件需要 paragraphs 列表：{p}")
    ids, sents = [], {}
    for pi, para in enumerate(raw["paragraphs"], 1):
        for si, s in enumerate(para or [], 1):
            sid = f"{pi}.{si}"
            en, zh = str((s or {}).get("en") or "").strip(), str((s or {}).get("zh") or "").strip()
            if not en or not zh:
                raise BatchError(f"原文 {sid} 缺少 en 或 zh：{p}")
            ids.append(sid)
            sents[sid] = {"en": en, "zh": zh}
    return {"source": str(raw.get("source") or "").strip(), "ids": ids, "sents": sents}


def parse_src(src, psg):
    """「3.1-3.2, 4」→ 句号列表；只写段号表示整段。"""
    if src is None or src == "":
        return []
    parts = src if isinstance(src, list) else re.split(r"[,，\s]+", str(src))
    ids, out = psg["ids"], []

    def expand(x):
        return [x] if x in ids else [i for i in ids if i.startswith(f"{x}.")] if "." not in x else []

    for part in (str(x).strip() for x in parts):
        if not part:
            continue
        a, _, b = part.partition("-")
        lo, hi = expand(a.strip()), expand((b or a).strip())
        if not lo or not hi:
            raise BatchError(f"src「{part}」在原文里找不到（写成 段.句，如 3.2；整段写段号）")
        out += ids[ids.index(lo[0]):ids.index(hi[-1]) + 1]
    return list(dict.fromkeys(out))


def normalize(raw, index, defaults, base=SCRIPTS):
    if not isinstance(raw, dict):
        raise BatchError(f"第 {index} 条不是对象")
    ep = {k: raw.get(k, v) for k, v in defaults.items()}
    ep["id"] = SAFE_ID.sub("-", str(raw.get("id") or f"{index:02d}")).strip("-") or f"{index:02d}"
    ep["vol"] = str(ep["vol"] or "")
    ep["title"] = str(raw.get("title") or "").strip()
    cover = raw.get("cover") or ep["title"]
    ep["cover"] = [str(c) for c in cover] if isinstance(cover, list) else [str(cover)]

    ep["passage"] = str((Path(base) / ep["passage"]).resolve()) if ep["passage"] else ""
    psg = read_passage(ep["passage"]) if ep["passage"] else None
    ep["source"] = str(ep["source"] or (psg and psg["source"]) or DEFAULT_SOURCE).strip()

    if raw.get("text"):
        page_texts, ep["items"] = parse_marked_text(raw.get("text"))
        raw_pages = [{"text": t} for t in page_texts]
    else:
        ep["items"] = [parse_item(it) for it in (raw.get("items") or [])]
        raw_pages = raw.get("pages") or []
    keys = item_keys(ep["items"])
    ep["pages"] = []
    for p in raw_pages:
        text, src = (p.get("text"), p.get("src")) if isinstance(p, dict) else (p, None)
        text = str(text or "")
        ep["pages"].append({"text": text, "tokens": tokenize(text, ep["items"], keys),
                            "src": parse_src(src, psg) if psg else []})
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
            out.append(re.split(r"[；;]", items[tk["i"]]["gloss"])[0])
        else:
            out.append(tk["en"])
    return "".join(out)


def passage_words(text):
    return [w.lower().replace("’", "'") for w in re.findall(r"[A-Za-z][A-Za-z'’]*", text)]


def in_passage(item, words):
    """学习项（任一屈折词形，或 forms 里写的词形）是否在原文里连续出现。"""
    for key, _ in item_keys([item]):
        n = len(key)
        if any(all(words[p + k] in key[k] for k in range(n)) for p in range(len(words) - n + 1)):
            return True
    return False


# ---------- 校验 ----------

def check(ep):
    errors, warnings = [], []
    E, W = errors.append, warnings.append
    if not ep["title"]:
        E("缺少 title")
    if not ep["pages"]:
        E("缺少 pages")
    if not ep["items"]:
        E("缺少 items")

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
            E(f"{it['en']}：正文里没有出现（检查拼写，或用 forms 写出文中的词形）")
    extras = sorted({tk["en"] for p in ep["pages"] for tk in p["tokens"] if "en" in tk})
    if extras:
        W(f"正文里这些英文不是学习项，将按普通文字显示：{', '.join(extras)}")

    lo, hi = ITEMS_RANGE
    if not lo <= len(ep["items"]) <= hi:
        W(f"学习项 {len(ep['items'])} 个，建议 {lo}–{hi} 个")

    if ep.get("passage"):
        psg = read_passage(ep["passage"])
        for n, p in enumerate(ep["pages"], 1):
            if not p["src"]:
                W(f"第 {n} 段没写 src（对应原文哪几句），没法和参考译文对照")
        for i, it in enumerate(ep["items"]):
            scope = [s for p in ep["pages"] if any(tk.get("i") == i for tk in p["tokens"]) for s in p["src"]]
            scope = scope or psg["ids"]
            words = passage_words(" ".join(psg["sents"][s]["en"] for s in scope))
            if not in_passage(it, words):
                W(f"{it['en']}：对应的原文句子里没有这个词，学习项要从原文里选")
            zh = "".join(psg["sents"][s]["zh"] for s in scope)
            senses = [s.strip().rstrip("的") for s in re.split(r"[；;，,、/]", it["gloss"]) if s.strip()]
            if senses and not any(s in zh for s in senses):
                W(f"{it['en']}：释义「{it['gloss']}」在对应的参考译文里找不到，确认和译文的译法一致")

    total = sum(text_weight(p["tokens"], ep["items"]) for p in ep["pages"])
    if total > MAX_TEXT_WEIGHT:
        W(f"全文约 {total:.0f} 字，超过 {MAX_TEXT_WEIGHT}，一页放下需要明显缩小字号，建议删减")
    for n, p in enumerate(ep["pages"], 1):
        if re.search(r"[,.!?;:]", "".join(tk["t"] for tk in p["tokens"] if "t" in tk)):
            W(f"第 {n} 段有半角标点，中文请用全角")

    tag = LEVEL_TAGS.get(ep["level"])
    if _db() is None:
        W("找不到 data/ecdict.db，跳过词典检查")
    else:
        for it in ep["items"]:
            words = it["en"].split()
            missing = [w for w in words if dict_row(w) is None]
            if missing:
                W(f"{it['en']}：词典里查不到 {missing}，检查拼写")
            elif it["kind"] == "word" and tag:
                row = dict_row(it["en"])
                if tag not in (row["tag"] or "").split():
                    W(f"{it['en']}：不在 {ep['level']} 词表（tag: {row['tag'] or '无'}）")
            if it["kind"] == "word" and it["en"].lower() in HETERONYMS:
                W(f"{it['en']}：多音词，TTS 可能读错")
    return errors, warnings


def load_episodes(arg, only=None):
    """返回 (批量文件路径, [(episode, errors, warnings)])。"""
    path = resolve_path(arg)
    defaults, raws = load_batch(path)
    out, ids = [], set()
    for n, raw in enumerate(raws, 1):
        try:
            ep = normalize(raw, n, defaults, path.parent)
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
