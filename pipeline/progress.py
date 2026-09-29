import datetime as dt
import sqlite3

from .config import PROGRESS_DB, PUBLISHED

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes(
  id TEXT PRIMARY KEY, level TEXT, theme TEXT, genre TEXT, ending TEXT,
  status TEXT, created_at TEXT, committed_at TEXT,
  plays INT, likes INT, saves INT, completion REAL);
CREATE TABLE IF NOT EXISTS word_usage(
  word TEXT, episode_id TEXT, seq INT, is_review INT, used_at TEXT,
  PRIMARY KEY(word, episode_id));
"""


def connect():
    con = sqlite3.connect(PROGRESS_DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def next_episode_id(con, existing_dirs):
    nums = [int(r["id"]) for r in con.execute("SELECT id FROM episodes") if r["id"].isdigit()]
    nums += [int(d) for d in existing_dirs if d.isdigit()]
    return f"{(max(nums) + 1) if nums else 1:03d}"


def used_words(con):
    return {r["word"] for r in con.execute("SELECT DISTINCT word FROM word_usage")}


def committed_count(con):
    return con.execute("SELECT COUNT(*) FROM episodes WHERE status='committed'").fetchone()[0]


def review_due(con, limit=6):
    """出现过的词，距上次出现已隔 ≥3 期、总出现 <3 次，按最久未复习排序。"""
    seq_now = committed_count(con)
    rows = con.execute("""
        SELECT word, COUNT(*) AS n, MAX(seq) AS last_seq FROM word_usage
        GROUP BY word HAVING n < 3 AND ? - last_seq >= 3
        ORDER BY last_seq LIMIT ?""", (seq_now, limit)).fetchall()
    return [r["word"] for r in rows]


def recent_episodes(con, limit=30):
    return con.execute("""SELECT id, theme, genre, ending FROM episodes
        WHERE status='committed' ORDER BY committed_at DESC LIMIT ?""", (limit,)).fetchall()


def commit(con, script, ending):
    seq = committed_count(con) + 1
    con.execute("""INSERT OR REPLACE INTO episodes(id, level, theme, genre, ending, status, created_at, committed_at)
        VALUES (?,?,?,?,?, 'committed', COALESCE((SELECT created_at FROM episodes WHERE id=?), ?), ?)""",
                (script["id"], script["level"], script["theme"], script.get("genre", ""), ending,
                 script["id"], now(), now()))
    for w in script["words"]:
        con.execute("INSERT OR REPLACE INTO word_usage VALUES (?,?,?,?,?)",
                    (w["word"].lower(), script["id"], seq, int(bool(w.get("review"))), now()))
    con.commit()


def append_published(script, text):
    words = "、".join(w["word"] for w in script["words"])
    block = (f"\n## {script['id']} · {script['theme']}（{script.get('genre', '')}，{script['level']}）\n\n"
             f"> {text}\n\n单词：{words}\n")
    with open(PUBLISHED, "a", encoding="utf-8") as f:
        f.write(block)
