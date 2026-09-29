import json
import random

from . import lexicon, progress
from .config import EPISODES, LEVELS, SERIES
from .script import save_json


def candidates(level, n, seed=None):
    cfg = LEVELS[level]
    lex = lexicon.connect()
    used = progress.used_words(progress.connect())
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


def search(keywords, level, limit):
    """按中文释义或英文前缀找词，标出是否在级别词表、是否用过。"""
    cfg = LEVELS[level]
    lex = lexicon.connect()
    used = progress.used_words(progress.connect())
    for kw in keywords:
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
            mark = ("✓" if tags & set(cfg["include"]) else " ") + ("用过" if r["word"] in used else "  ")
            hits.append(f"  {mark} {r['word']:<16}{lexicon.short_senses(r['translation'], 2)}")
            if len(hits) >= limit:
                break
        print(f"「{kw}」({len(hits)})  ✓=在 {cfg['label']} 词表")
        print("\n".join(hits) or "  （无）")


def run(level, theme, n, seed):
    if level not in LEVELS:
        raise SystemExit(f"未知 level：{level}，可选 {', '.join(LEVELS)}")
    con = progress.connect()
    EPISODES.mkdir(exist_ok=True)
    ep = progress.next_episode_id(con, [d.name for d in EPISODES.iterdir() if d.is_dir()])
    d = EPISODES / ep
    d.mkdir()

    lex, picked, remaining = candidates(level, n, seed)
    review = []
    for w in progress.review_due(con):
        r = lexicon.lookup(lex, w)
        if r:
            review.append(r)

    def item(r):
        return {"word": r["word"], "ipa": lexicon.ipa(r), "senses": lexicon.short_senses(r["translation"], 3)}

    plan = {
        "id": ep, "series": SERIES, "level": LEVELS[level]["label"], "level_key": level,
        "theme": theme or "", "remaining_new_words": remaining,
        "candidates": [item(r) for r in picked],
        "review_due": [item(r) for r in review],
        "recent": [dict(r) for r in progress.recent_episodes(con)],
    }
    save_json(d / "plan.json", plan)

    print(f"新建第 {ep} 期 → {d}/plan.json")
    print(f"级别 {plan['level']}，剩余未学新词 {remaining} 个；主题：{theme or '（未指定，自选）'}")
    print(f"\n候选新词（{len(picked)}）：")
    for c in plan["candidates"]:
        print(f"  {c['word']:<16}{c['senses']}")
    if review:
        print(f"\n到期复习词（可选 ≤2 个，words 里标 \"review\": true）：")
        for c in plan["review_due"]:
            print(f"  {c['word']:<16}{c['senses']}")
    if plan["recent"]:
        print("\n最近几期（避免主题和结尾雷同）：")
        for r in plan["recent"][:10]:
            print(f"  {r['id']} {r['theme']}｜{r['genre']}｜{r['ending']}")
