"""学习进度：不单独存库，全部从 episodes/*/script.json 推算。

一期入库后 script.json 里会有 "published_at"；已用词、复习调度、最近几期都由已入库的期算出来，
data/published_scripts.md 也由这里整体重新生成。数据跟着 git 走，多台机器合并不会冲突。
"""
import datetime as dt
import json

from .config import EPISODES, PUBLISHED
from .script import full_text, save_json, sentence_text


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def all_scripts():
    """[(期号, script)]，按期号排序；没有 script.json 的期跳过。"""
    out = []
    if not EPISODES.exists():
        return out
    for d in sorted(p for p in EPISODES.iterdir() if p.is_dir()):
        f = d / "script.json"
        if f.exists():
            try:
                out.append((d.name, json.loads(f.read_text(encoding="utf-8"))))
            except json.JSONDecodeError:
                continue
    return out


def published(exclude=None):
    """已入库的期，按入库时间升序。exclude：排除的期号（校验当前期时不和自己比）。"""
    eps = [(i, s) for i, s in all_scripts() if s.get("published_at") and i != exclude]
    return sorted(eps, key=lambda e: (e[1]["published_at"], e[0]))


def next_episode_id():
    nums = [int(d.name) for d in EPISODES.iterdir() if d.is_dir() and d.name.isdigit()] if EPISODES.exists() else []
    return f"{(max(nums) + 1) if nums else 1:03d}"


def used_words(exclude=None):
    return {w["word"].lower() for _, s in published(exclude) for w in s.get("words", [])}


def review_due(limit=6, exclude=None):
    """出现过的词，距上次出现已隔 ≥3 期、总出现 <3 次，按最久未复习排序。"""
    eps = published(exclude)
    seen = {}
    for seq, (_, s) in enumerate(eps, 1):
        for w in s.get("words", []):
            n, _ = seen.get(w["word"].lower(), (0, 0))
            seen[w["word"].lower()] = (n + 1, seq)
    due = [(last, word) for word, (n, last) in seen.items() if n < 3 and len(eps) - last >= 3]
    return [word for _, word in sorted(due)[:limit]]


def recent_episodes(limit=30, exclude=None):
    out = []
    for i, s in reversed(published(exclude)):
        sents = s.get("sentences") or [[]]
        out.append({"id": i, "theme": s.get("theme", ""), "genre": s.get("genre", ""),
                    "ending": sentence_text(sents[-1])})
    return out[:limit]


def commit(d, script):
    """标记入库并重新生成 published_scripts.md。"""
    script["published_at"] = script.get("published_at") or now()
    save_json(d / "script.json", script)
    write_published()


def write_published():
    blocks = ["# 已发布文案\n\n由 `./vv commit` 根据 episodes/*/script.json 自动生成，用于去重和新鲜度检查，不要手改。\n"]
    for i, s in published():
        words = "、".join(w["word"] for w in s["words"])
        blocks.append(f"\n## {i} · {s['theme']}（{s.get('genre', '')}，{s['level']}）\n\n"
                      f"> {full_text(s)}\n\n单词：{words}\n")
    PUBLISHED.write_text("".join(blocks), encoding="utf-8")
