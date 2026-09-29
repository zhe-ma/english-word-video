import re

from . import lexicon, progress
from .config import (BANNED, HANZI_RANGE, HETERONYMS, LEVELS, MAX_ENDING_HANZI, MAX_HANZI_PER_SENTENCE,
                     MAX_MEANING_LEN, MAX_WORDS_PER_SENTENCE, REVIEW_KEYS, REVIEW_PASS, SENTENCES_RANGE,
                     WORDS_RANGE)
from .script import ep_dir, full_text, hanzi_count, load, save_json, sentence_text, word_tokens

ALLOWED_POS = {"n.", "v.", "vt.", "vi.", "adj.", "a."}


def check(ep):
    s = load(ep)
    errors, warnings = [], []
    E, W = errors.append, warnings.append

    for key in ("id", "level", "theme", "genre", "sentences", "words", "review"):
        if key not in s:
            E(f"缺少字段 {key}")
    if errors:
        return s, errors, warnings

    sents = s["sentences"]
    words = s["words"]
    text = full_text(s)

    # 结构
    if not SENTENCES_RANGE[0] <= len(sents) <= SENTENCES_RANGE[1]:
        E(f"句数 {len(sents)}，要求 {SENTENCES_RANGE[0]}–{SENTENCES_RANGE[1]}")
    n_hanzi = hanzi_count(text)
    if not HANZI_RANGE[0] <= n_hanzi <= HANZI_RANGE[1]:
        E(f"汉字数 {n_hanzi}，要求 {HANZI_RANGE[0]}–{HANZI_RANGE[1]}")
    for i, sent in enumerate(sents, 1):
        n_w = sum(1 for tk in sent if "w" in tk)
        if n_w > MAX_WORDS_PER_SENTENCE:
            E(f"第 {i} 句有 {n_w} 个单词，最多 {MAX_WORDS_PER_SENTENCE}")
        h = hanzi_count(sentence_text(sent))
        if h > MAX_HANZI_PER_SENTENCE:
            W(f"第 {i} 句 {h} 个汉字，建议 ≤ {MAX_HANZI_PER_SENTENCE}（读起来更像口语）")
    last = sents[-1] if sents else []
    if any("w" in tk for tk in last):
        E("最后一句不能放单词")
    ending = sentence_text(last)
    if hanzi_count(ending) > MAX_ENDING_HANZI:
        W(f"结尾句 {hanzi_count(ending)} 字，建议 ≤ {MAX_ENDING_HANZI}")
    if re.search(r"[A-Za-z]", "".join(tk.get("t", "") for sent in sents for tk in sent)):
        E("中文片段 t 里出现了英文字母，英文单词必须放进 w")
    if re.search(r"[,.!?;:]", text.replace("...", "")):
        W("出现半角标点，请用中文全角标点")

    # 单词
    toks = word_tokens(s)
    listed = [w["word"] for w in words]
    if toks != listed:
        E(f"sentences 中单词顺序 {toks} 与 words 列表 {listed} 不一致")
    if len(set(listed)) != len(listed):
        E("words 里有重复单词")
    if not WORDS_RANGE[0] <= len(listed) <= WORDS_RANGE[1]:
        E(f"单词数 {len(listed)}，要求 {WORDS_RANGE[0]}–{WORDS_RANGE[1]}")

    lex = lexicon.connect()
    pcon = progress.connect()
    used = progress.used_words(pcon)
    level_key = next((k for k, v in LEVELS.items() if v["label"] == s["level"]), None)
    n_review = 0
    for w in words:
        word = w["word"]
        row = lexicon.lookup(lex, word)
        if row is None:
            E(f"{word}：词库里查不到（拼写错误或非原形）")
            continue
        if not w.get("pos") or w["pos"] not in ALLOWED_POS:
            E(f"{word}：词性 {w.get('pos')!r} 不合法，用 n./v./vt./vi./adj.")
        meaning = w.get("meaning", "")
        if not meaning or len(meaning) > MAX_MEANING_LEN:
            E(f"{word}：释义 {meaning!r} 为空或超过 {MAX_MEANING_LEN} 字")
        dict_text = "".join(t for _, t in lexicon.senses(row["translation"]))
        if meaning and not any(ch in dict_text for ch in re.sub(r"[，,；;、\s]", "", meaning)):
            W(f"{word}：释义「{meaning}」与词典义项差异较大，请核对：{lexicon.short_senses(row['translation'], 3)}")
        if w.get("review"):
            n_review += 1
            if word not in used:
                W(f"{word}：标了 review，但之前没用过")
        elif word in used:
            E(f"{word}：往期已经用过，要么换词，要么标 \"review\": true")
        if level_key:
            tags = set((row["tag"] or "").split())
            if not tags & set(LEVELS[level_key]["include"]):
                W(f"{word}：不在 {s['level']} 词表里（tag: {row['tag'] or '无'}）")
        if word in HETERONYMS:
            W(f"{word}：多音词，TTS 可能读错，建议换词")
    if sum(1 for w in words if w.get("pos") in ("adj.", "a.")) > 1:
        E("形容词最多 1 个")
    if n_review > 2:
        E(f"复习词 {n_review} 个，最多 2 个")

    # 烂梗 / 敏感词
    if BANNED.exists():
        for line in BANNED.read_text(encoding="utf-8").splitlines():
            p = line.strip()
            if p and not p.startswith("#") and p in text:
                E(f"命中黑名单：{p}")

    # 去重
    for r in progress.recent_episodes(pcon):
        if r["id"] == s["id"]:
            continue
        if r["theme"] == s["theme"]:
            E(f"主题和第 {r['id']} 期重复：{r['theme']}")
        if r["ending"] and r["ending"] == ending:
            E(f"结尾句和第 {r['id']} 期重复")

    # 评审分
    rv = s.get("review") or {}
    missing = [k for k in REVIEW_KEYS if not isinstance(rv.get(k), (int, float))]
    if missing:
        E(f"review 缺少评分项：{missing}（先让毒舌评审打分）")
    else:
        total = sum(rv[k] for k in REVIEW_KEYS)
        if total < REVIEW_PASS["total"]:
            E(f"评审总分 {total} < {REVIEW_PASS['total']}")
        low = [k for k in REVIEW_KEYS if rv[k] < REVIEW_PASS["min"]]
        if low:
            E(f"评审单项低于 {REVIEW_PASS['min']}：{low}")
        for k in ("hook", "punchline"):
            if rv[k] < REVIEW_PASS[k]:
                E(f"评审 {k} = {rv[k]}，要求 ≥ {REVIEW_PASS[k]}")

    return s, errors, warnings


def run(ep):
    s, errors, warnings = check(ep)
    report = {"ok": not errors, "errors": errors, "warnings": warnings,
              "hanzi": hanzi_count(full_text(s)) if "sentences" in s else None,
              "text": full_text(s) if "sentences" in s else None}
    save_json(ep_dir(ep) / "report.json", report)
    status = "通过" if not errors else "未通过"
    print(f"第 {s.get('id', ep)} 期校验{status}（汉字 {report['hanzi']}）")
    for e in errors:
        print(f"  ✗ {e}")
    for w in warnings:
        print(f"  ! {w}")
    return 0 if not errors else 1
