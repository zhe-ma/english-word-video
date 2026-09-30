import json
import random
import re

from . import lexicon, progress
from .config import EPISODES, LEVELS, SERIES
from .script import save_json

HANZI_RUN = re.compile(r"[\u4e00-\u9fff]+")


def theme_keywords(theme):
    """从主题里拆出可查词的中文片段，例如「外卖选择困难症」→ 外卖、选择、困难。"""
    out, seen = [], set()
    for chunk in HANZI_RUN.findall(theme or ""):
        pieces = [chunk]
        if len(chunk) >= 2:
            for n in (2, 3):
                pieces += [chunk[i:i + n] for i in range(len(chunk) - n + 1)]
        for w in pieces:
            if len(w) >= 2 and w not in seen:
                seen.add(w)
                out.append(w)
    return out


def auto_pick(level, theme, ep=None, n=6):
    """按主题从词库挑 n 个未用词，不够再从高频候选补；最多带 2 个复习词。"""
    n = max(4, min(8, int(n or 6)))
    used = progress.used_words(exclude=ep)
    chosen, seen = [], set()

    def take(word, allow_used=False):
        w = (word or "").lower()
        if not w or w in seen or len(w) < 3:
            return False
        if w in used and not allow_used:
            return False
        seen.add(w)
        chosen.append(w)
        return True

    for w in progress.review_due(exclude=ep)[:2]:
        take(w, allow_used=True)
    for kw in theme_keywords(theme):
        if len(chosen) >= n:
            break
        for h in search_data(kw, level, 12):
            if h["in_level"] and not h["used"]:
                take(h["word"])
            if len(chosen) >= n:
                break
    if len(chosen) < n:
        _, cands, _ = candidates(level, 40, exclude=ep)
        for r in cands:
            take(r["word"])
            if len(chosen) >= n:
                break
    return chosen


def candidates(level, n, seed=None, exclude=None):
    cfg = LEVELS[level]
    lex = lexicon.connect()
    used = progress.used_words(exclude)
    rows = lex.execute("SELECT * FROM words WHERE frq > 0 ORDER BY frq").fetchall()
    pool = []
    for r in rows:
        tags = set((r["tag"] or "").split())
        if not tags & set(cfg["include"]) or tags & set(cfg["exclude"]):
            continue
        if r["word"] in used or len(r["word"]) < 3:
            continue
        pos = lexicon.main_pos(r["translation"])
        if not pos & {"n.", "v.", "vt.", "vi."}:
            continue
        pool.append(r)
    # 取高频的前 400 个未用词，随机抽 n 个，避免每期都是同一批
    head = pool[:400]
    rnd = random.Random(seed)
    picked = rnd.sample(head, min(n, len(head)))
    picked.sort(key=lambda r: r["frq"])
    return lex, picked, len(pool)


def search_data(keyword, level, limit=15):
    """按中文释义或英文前缀找词：[{word, ipa, senses, in_level, used}]。"""
    cfg = LEVELS[level]
    lex = lexicon.connect()
    used = progress.used_words()
    kw = keyword.strip()
    if kw.isascii():
        rows = lex.execute("SELECT * FROM words WHERE word LIKE ? ORDER BY frq = 0, frq LIMIT 200",
                           (kw.lower() + "%",)).fetchall()
    else:
        rows = lex.execute("SELECT * FROM words WHERE translation LIKE ? ORDER BY frq = 0, frq LIMIT 400",
                           (f"%{kw}%",)).fetchall()
    hits = []
    for r in rows:
        tags = set((r["tag"] or "").split())
        if tags & set(cfg["exclude"]) and not kw.isascii():
            continue
        hits.append({"word": r["word"], "ipa": lexicon.ipa(r), "senses": lexicon.short_senses(r["translation"], 2),
                     "in_level": bool(tags & set(cfg["include"])), "used": r["word"] in used})
        if len(hits) >= limit:
            break
    return hits


def search(keywords, level, limit):
    for kw in keywords:
        hits = search_data(kw, level, limit)
        print(f"「{kw}」({len(hits)})  ✓=在 {LEVELS[level]['label']} 词表")
        for h in hits:
            mark = ("✓" if h["in_level"] else " ") + ("用过" if h["used"] else "  ")
            print(f"  {mark} {h['word']:<16}{h['senses']}")
        if not hits:
            print("  （无）")


def build(ep, level, theme, n, seed=None):
    """生成 plan.json 的内容；ep 已存在时保留之前勾选的 picked。"""
    lex, picked, remaining = candidates(level, n, seed, exclude=ep)
    review = [r for r in (lexicon.lookup(lex, w) for w in progress.review_due(exclude=ep)) if r]

    def item(r):
        return {"word": r["word"], "ipa": lexicon.ipa(r), "senses": lexicon.short_senses(r["translation"], 3)}

    return {
        "id": ep, "series": SERIES, "level": LEVELS[level]["label"], "level_key": level,
        "theme": theme or "", "remaining_new_words": remaining,
        "candidates": [item(r) for r in picked],
        "review_due": [item(r) for r in review],
        "recent": progress.recent_episodes(exclude=ep),
        "picked": [],
    }


def run(level, theme, n, seed, ep=None):
    """新建一期（ep=None）或给已有期重新抽候选词。返回期号。"""
    if level not in LEVELS:
        raise SystemExit(f"未知 level：{level}，可选 {', '.join(LEVELS)}")
    EPISODES.mkdir(exist_ok=True)
    if ep:
        d = EPISODES / ep
        if not d.exists():
            raise SystemExit(f"找不到期目录：{d}")
        old = json.loads((d / "plan.json").read_text(encoding="utf-8")) if (d / "plan.json").exists() else {}
    else:
        ep = progress.next_episode_id()
        d = EPISODES / ep
        d.mkdir()
        old = {}
    plan = build(ep, level, theme or old.get("theme", ""), n, seed)
    plan["picked"] = old.get("picked") or []
    save_json(d / "plan.json", plan)

    print(f"{'刷新' if old else '新建'}第 {ep} 期 → {d}/plan.json")
    print(f"级别 {plan['level']}，剩余未学新词 {plan['remaining_new_words']} 个；主题：{plan['theme'] or '（未指定，自选）'}")
    print(f"\n候选新词（{len(plan['candidates'])}）：")
    for c in plan["candidates"]:
        print(f"  {c['word']:<16}{c['senses']}")
    if plan["review_due"]:
        print(f"\n到期复习词（可选 ≤2 个，words 里标 \"review\": true）：")
        for c in plan["review_due"]:
            print(f"  {c['word']:<16}{c['senses']}")
    if plan["recent"]:
        print("\n最近几期（避免主题和结尾雷同）：")
        for r in plan["recent"][:10]:
            print(f"  {r['id']} {r['theme']}｜{r['genre']}｜{r['ending']}")
    return ep
