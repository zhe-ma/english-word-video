"""词库浏览、已用词、统计、期目录文件：给工作台管理页用。"""
from . import lexicon, progress
from .config import EPISODES, LEVELS
from .script import ep_dir

SOURCE_NAMES = {"plan.json", "drafts.md", "script.json"}
MEDIA_EXT = {".wav", ".mp4", ".png", ".json", ".md"}


def word_index():
    """word -> [{id, theme, published, review, meaning}]，含未入库的期。"""
    out = {}
    for i, s in progress.all_scripts():
        published = bool(s.get("published_at"))
        for w in s.get("words") or []:
            word = (w.get("word") or "").lower()
            if not word:
                continue
            out.setdefault(word, []).append({
                "id": i, "theme": s.get("theme", ""), "published": published,
                "review": bool(w.get("review")), "meaning": w.get("meaning", ""),
            })
    return out


def _level_match(tag, cfg):
    tags = set((tag or "").split())
    return bool(tags & set(cfg["include"])) and not tags & set(cfg["exclude"])


def remaining_by_level():
    used = progress.used_words()
    lex = lexicon.connect()
    rows = lex.execute("SELECT word, tag FROM words WHERE frq > 0").fetchall()
    out = {}
    for key, cfg in LEVELS.items():
        n = 0
        for r in rows:
            if len(r["word"]) < 3 or r["word"] in used:
                continue
            if _level_match(r["tag"], cfg):
                n += 1
        out[key] = n
    return out


def stats():
    lex = lexicon.connect()
    n_lex = lex.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    used = progress.used_words()
    published = progress.published()
    eps = list(EPISODES.iterdir()) if EPISODES.exists() else []
    eps = [p for p in eps if p.is_dir()]
    videos = sum(1 for p in eps if (p / "out.mp4").exists())
    return {
        "lexicon": n_lex,
        "usedWords": len(used),
        "episodes": len(eps),
        "published": len(published),
        "videos": videos,
        "remaining": remaining_by_level(),
    }


def usage():
    """已出现过的单词（含未入库），按最近使用倒序。"""
    idx = word_index()
    items = []
    for word, refs in idx.items():
        last = refs[-1]
        items.append({
            "word": word, "times": len(refs), "reviewTimes": sum(1 for r in refs if r["review"]),
            "published": any(r["published"] for r in refs),
            "meaning": next((r["meaning"] for r in reversed(refs) if r["meaning"]), ""),
            "episodes": refs, "lastId": last["id"], "lastTheme": last["theme"],
        })
    items.sort(key=lambda x: (x["lastId"], x["word"]), reverse=True)
    return items


def browse(q="", level="cet4", used="", page=1, limit=40):
    """浏览 ECDICT。used: '' 全部 / used 已用 / new 未用。"""
    cfg = LEVELS.get(level) or LEVELS["cet4"]
    used_set = progress.used_words()
    idx = word_index()
    lex = lexicon.connect()
    q = (q or "").strip()
    if q.isascii() and q:
        rows = lex.execute(
            "SELECT * FROM words WHERE word LIKE ? ORDER BY frq = 0, frq, word LIMIT 2000",
            (q.lower() + "%",),
        ).fetchall()
    elif q:
        rows = lex.execute(
            "SELECT * FROM words WHERE translation LIKE ? ORDER BY frq = 0, frq, word LIMIT 2000",
            (f"%{q}%",),
        ).fetchall()
    else:
        rows = lex.execute("SELECT * FROM words ORDER BY frq = 0, frq, word").fetchall()

    hits = []
    for r in rows:
        tags = set((r["tag"] or "").split())
        in_level = bool(tags & set(cfg["include"]))
        is_used = r["word"] in used_set or r["word"] in idx
        if used == "used" and not is_used:
            continue
        if used == "new" and is_used:
            continue
        if not q and not in_level:
            continue
        hits.append({
            "word": r["word"], "ipa": lexicon.ipa(r),
            "senses": lexicon.short_senses(r["translation"], 2),
            "tag": r["tag"] or "", "frq": r["frq"],
            "inLevel": in_level, "used": is_used,
            "episodes": idx.get(r["word"], []),
        })

    page = max(1, int(page or 1))
    limit = max(1, min(100, int(limit or 40)))
    start = (page - 1) * limit
    return {
        "total": len(hits), "page": page, "limit": limit,
        "level": cfg["label"], "items": hits[start:start + limit],
    }


def episode_files(ep, media_url):
    d = ep_dir(ep)
    files = []
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(d)).replace("\\", "/")
        st = p.stat()
        files.append({
            "path": rel, "name": p.name, "size": st.st_size, "mtime": int(st.st_mtime),
            "kind": "source" if p.name in SOURCE_NAMES else "artifact",
            "url": media_url(d, rel) if p.suffix.lower() in MEDIA_EXT else None,
        })
    return files
