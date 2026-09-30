"""创建一期的默认流水线：选题 → 选词 → 三稿底稿 → 定稿。

人只在这版底稿上改。配音和渲染仍要手动点（或以后批量串起来），因为要联网、要时间。
"""
import json
import re
import yaml

from . import lexicon, plan, progress
from .config import DATA, EPISODES, LEVELS, RATE, SERIES, VOICE
from .script import save_json

TOKEN_RE = re.compile(r"([A-Za-z]+)|([^A-Za-z]+)")
SPLIT_SENSE = re.compile(r"[，,；;、]")
ALLOWED_POS = {"n.", "v.", "vt.", "vi.", "adj.", "a."}

GENRES_FALLBACK = ["吐槽小剧场", "伪官方通知", "拟人视角"]

TEMPLATES = {
    "吐槽小剧场": [
        "{theme}又来了，我还在{w0}。",
        "眼前一堆{w1}，旁边的人一直{w2}另一边。",
        "我来回{w3}，身体已经开始{w4}。",
        "最后我{w5}了眼前这个。",
        "结果和上次一模一样。",
    ],
    "伪官方通知": [
        "关于{theme}，本人决定{w0}。",
        "备选{w1}很多，同事纷纷{w2}。",
        "方案来回{w3}，群里开始{w4}。",
        "散会前我{w5}了其中一个。",
        "纪要写着：下次再议。",
    ],
    "拟人视角": [
        "我是{theme}，每天都在{w0}。",
        "人类给我的{w1}太多，还爱{w2}。",
        "他们来回{w3}，接着{w4}。",
        "终于有人{w5}了我。",
        "其实我什么都没答应。",
    ],
    "反鸡汤": [
        "都说面对{theme}要勇敢{w0}。",
        "我准备了几个{w1}，朋友还{w2}我。",
        "计划来回{w3}，心情开始{w4}。",
        "夜里我{w5}了最省事的那个。",
        "成功学没写这一段。",
    ],
    "朋友圈 vs 现实": [
        "朋友圈里的{theme}，我还在{w0}。",
        "照片外全是{w1}，评论都在{w2}。",
        "我来回{w3}，镜头后面已经{w4}。",
        "发出去之前我{w5}了最能看的一张。",
        "配文两个字：真实。",
    ],
    "灵魂拷问对话": [
        "有人问我{theme}，我开始{w0}。",
        "他说{w1}很多，建议我{w2}。",
        "我来回{w3}，对方开始{w4}。",
        "最后我{w5}了最不像回答的一句。",
        "他回了一个句号。",
    ],
    "伪新闻": [
        "现场报道，{theme}让当事人持续{w0}。",
        "记者看到多个{w1}，路人不断{w2}。",
        "情况来回{w3}，围观开始{w4}。",
        "截止发稿，他{w5}了其中一个。",
        "本台将继续跟踪。",
    ],
    "说明书体": [
        "使用{theme}前，请先{w0}。",
        "备选{w1}见附件，勿随意{w2}。",
        "若反复{w3}，机体可能{w4}。",
        "确认无误后{w5}默认项。",
        "保修不含心情损坏。",
    ],
}


def used_themes():
    seen = set()
    for _, s in progress.all_scripts():
        if s.get("theme"):
            seen.add(s["theme"])
    if EPISODES.exists():
        for d in EPISODES.iterdir():
            p = d / "plan.json"
            if p.exists():
                try:
                    t = json.loads(p.read_text(encoding="utf-8")).get("theme")
                except Exception:
                    t = None
                if t:
                    seen.add(t)
    return seen


def theme_catalog():
    raw = yaml.safe_load((DATA / "themes.yaml").read_text(encoding="utf-8")) or {}
    items = []
    for group, lst in raw.items():
        for it in lst or []:
            if it.get("theme"):
                items.append({"group": group, **it})
    return items


def next_theme(exclude=None):
    taken = used_themes()
    if exclude:
        taken = set(taken) | {exclude}
    unused = [it for it in theme_catalog() if it["theme"] not in taken]
    return dict(unused[0] if unused else theme_catalog()[0])


def defaults(level="cet4"):
    t = next_theme()
    return {
        "level": level if level in LEVELS else "cet4",
        "theme": t["theme"],
        "genre": t.get("genre") or "吐槽小剧场",
        "words": 6,
        "voice": VOICE,
        "rate": RATE,
    }


def word_entry(word, review=False):
    row = lexicon.lookup(lexicon.connect(), word)
    pos, meaning = "n.", word
    if row:
        ss = lexicon.senses(row["translation"])
        if ss:
            pos, text = ss[0]
            meaning = SPLIT_SENSE.split(text)[0].strip()[:8]
        if pos not in ALLOWED_POS:
            pos = "n."
        if pos == "a.":
            pos = "adj."
    return {"word": word, "pos": pos, "meaning": meaning or word, "review": bool(review)}


def seed_text(theme, words, genre):
    lines = TEMPLATES.get(genre) or TEMPLATES["吐槽小剧场"]
    slots = list(words) + [words[-1]] * 6
    kw = {f"w{i}": slots[i] for i in range(6)}
    return "".join(line.format(theme=theme, **kw) for line in lines)


def text_to_sentences(text):
    out = []
    for sent in re.split(r"(?<=[。！？])", text):
        sent = sent.strip()
        if not sent:
            continue
        tokens = []
        for m in TOKEN_RE.finditer(sent):
            if m.group(1):
                tokens.append({"w": m.group(1)})
            elif m.group(2):
                tokens.append({"t": m.group(2)})
        out.append(tokens or [{"t": sent}])
    return out


def draft_genres(primary):
    extra = [g for g in GENRES_FALLBACK if g != primary]
    return [primary or "吐槽小剧场", extra[0], extra[1] if len(extra) > 1 else "反鸡汤"]


def write_drafts(ep, theme, level_label, words, genres):
    blocks = [f"# 第 {ep} 期 · {theme}（{level_label}）\n"]
    items = []
    for i, genre in enumerate(genres):
        text = seed_text(theme, words, genre)
        items.append({"genre": genre, "words": ", ".join(words), "text": text})
        blocks.append(f"## {chr(65 + i)} · {genre}\n\n单词：{', '.join(words)}\n\n> {text}\n")
    blocks.append("\n底稿由平台按模板生成，请改到有画面和笑点再配音。\n")
    (EPISODES / ep / "drafts.md").write_text("".join(blocks), encoding="utf-8")
    return items


def write_script(ep, theme, level, genre, words, used):
    text = seed_text(theme, words, genre)
    sentences = text_to_sentences(text)
    meta = {w.lower(): word_entry(w, review=w.lower() in used) for w in words}
    listed = []
    for sent in sentences:
        for tk in sent:
            if "w" in tk:
                listed.append(meta.get(tk["w"].lower(), word_entry(tk["w"])))
    script = {
        "id": ep, "series": SERIES, "level": LEVELS[level]["label"],
        "theme": theme, "genre": genre,
        "sentences": sentences, "words": listed,
    }
    save_json(EPISODES / ep / "script.json", script)
    return script


def run(level="cet4", theme="", words=6, voice=None, rate=None, seed=None, ep=None):
    """新建或给已有期重做默认底稿。返回 {id, theme, picked, genre}。"""
    if level not in LEVELS:
        level = "cet4"
    picked_theme = theme.strip()
    genre = "吐槽小剧场"
    if not picked_theme:
        nxt = next_theme()
        picked_theme, genre = nxt["theme"], nxt.get("genre") or genre
    else:
        hit = next((it for it in theme_catalog() if it["theme"] == picked_theme), None)
        if hit:
            genre = hit.get("genre") or genre

    if ep:
        plan.run(level, picked_theme, 40, seed, ep)
    else:
        ep = plan.run(level, picked_theme, 40, seed)

    picked = plan.auto_pick(level, picked_theme, ep, words)
    used = progress.used_words(exclude=ep)
    d = EPISODES / ep
    p = json.loads((d / "plan.json").read_text(encoding="utf-8"))
    p["picked"] = picked
    p["theme"] = picked_theme
    p["voice"] = voice or VOICE
    p["rate"] = rate or RATE
    save_json(d / "plan.json", p)

    genres = draft_genres(genre)
    write_drafts(ep, picked_theme, LEVELS[level]["label"], picked, genres)
    write_script(ep, picked_theme, level, genres[0], picked, used)
    return {"id": ep, "theme": picked_theme, "genre": genres[0], "picked": picked, "voice": p["voice"], "rate": p["rate"]}
