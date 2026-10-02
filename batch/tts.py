"""配音与时间轴：正文逐页合成，复习逐项合成（英文 → 中文释义），拼成一条音轨。

同一套 assemble 也用于不联网的估算时间轴（stills 预览），保证预览和成片结构一致。
"""
import array
import asyncio
import hashlib
import json
import math
import re
import time

import pyphen

from . import media
from .config import (CACHE, COLORS, EN_ZH_GAP, FPS, GROUP_LEAD, ITEM_GAP, LEAD_IN, OVERVIEW_HOLD, PAGE_GAP,
                     REVIEW_GAP, REVIEW_GROUP_MAX, SR)
from .episode import PHRASE_POS, ipa, review_senses

HANZI = re.compile(r"[\u4e00-\u9fff]")
HYPH = pyphen.Pyphen(lang="en_US")
TIMELINE_VERSION = 3


# ---------- 合成与缓存 ----------

async def _synth(text, voice, rate, mp3_path):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    marks = []
    with open(mp3_path, "wb") as f:
        async for c in comm.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                marks.append({"text": c["text"], "start": c["offset"] / 1e7,
                              "end": (c["offset"] + c["duration"]) / 1e7})
    return marks


def synth(text, voice, rate):
    """返回去掉首尾静音后的 (pcm, 时长, WordBoundary 列表)。按 文本+音色+语速 缓存原始音频。"""
    pcm, _, marks = synth_raw(text, voice, rate)
    pcm, lead = trim(pcm)
    dur = len(pcm) / 2 / SR
    marks = [{**m, "start": max(0.0, m["start"] - lead), "end": min(dur, max(0.0, m["end"] - lead))} for m in marks]
    return pcm, dur, marks


def synth_raw(text, voice, rate):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    wav, meta = CACHE / f"{key}.wav", CACHE / f"{key}.json"
    if not (wav.exists() and meta.exists()):
        mp3 = CACHE / f"{key}.mp3"
        for attempt in range(5):
            try:
                marks = asyncio.run(_synth(text, voice, rate, mp3))
                if mp3.stat().st_size == 0:
                    raise RuntimeError("空音频")
                break
            except Exception as e:  # 网络抖动 / 限流
                if attempt == 4:
                    raise SystemExit(f"edge-tts 合成失败（{voice}）：{text[:30]}… {e}")
                time.sleep(2 ** attempt)
        media.to_wav(mp3, wav, SR)
        meta.write_text(json.dumps(marks, ensure_ascii=False))
    import wave
    with wave.open(str(wav)) as w:
        pcm = w.readframes(w.getnframes())
    return pcm, len(pcm) / 2 / SR, json.loads(meta.read_text())


def silence(sec):
    return b"\x00\x00" * max(0, int(round(sec * SR)))


def rms(pcm):
    a = array.array("h", pcm)
    return math.sqrt(sum(x * x for x in a) / len(a)) if a else 0.0


def trim(pcm, threshold=500, margin=0.06):
    """去掉首尾静音（edge-tts 每段前后都带几百毫秒空白）。返回 (pcm, 开头裁掉的秒数)。"""
    a = array.array("h", pcm)
    loud = [i for i in range(0, len(a), 48) if abs(a[i]) > threshold]
    if not loud:
        return pcm, 0.0
    pad = int(margin * SR)
    s, e = max(0, loud[0] - pad), min(len(a), loud[-1] + pad)
    return a[s:e].tobytes(), s / SR


def gain(pcm, g):
    a = array.array("h", pcm)
    for i, x in enumerate(a):
        a[i] = max(-32768, min(32767, int(x * g)))
    return a.tobytes()


# ---------- 估算 ----------

def syllables(text):
    return sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in text.split())


def estimate_page(tokens):
    hanzi = sum(len(HANZI.findall(tk["t"])) for tk in tokens if "t" in tk)
    pauses = sum(len(re.findall(r"[，。？！；：、]", tk["t"])) for tk in tokens if "t" in tk)
    sylls = sum(syllables(tk.get("text") or tk.get("en")) for tk in tokens if "t" not in tk)
    return 0.2 + hanzi * 0.2 + sylls * 0.2 + pauses * 0.1


# ---------- 对齐 ----------

def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def find_span(marks, cursor, target):
    """在 marks[cursor:] 里找拼起来等于 target 的连续标记，返回 (起, 止) 下标。"""
    for j in range(cursor, len(marks)):
        first = norm(marks[j]["text"])
        if not first or not target.startswith(first):
            continue
        acc = ""
        for k in range(j, len(marks)):
            acc += norm(marks[k]["text"])
            if acc == target:
                return j, k
            if not target.startswith(acc):
                break
    return None


def page_text(tokens):
    parts = []
    for tk in tokens:
        parts.append(tk["t"] if "t" in tk else f" {tk.get('text') or tk.get('en')} ")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def align_items(tokens, marks, dur):
    """给页内每个学习项找时间：优先 WordBoundary，找不到按字数权重插值。"""
    weights = []
    for tk in tokens:
        if "t" in tk:
            weights.append(len(HANZI.findall(tk["t"])) + 0.3)
        else:
            weights.append(syllables(tk.get("text") or tk.get("en")) * 0.7)
    total = sum(weights) or 1
    cursor, acc, out = 0, 0.0, {}
    for n, (tk, wgt) in enumerate(zip(tokens, weights)):
        if "i" in tk:
            span = find_span(marks, cursor, norm(tk["text"])) if marks else None
            if span:
                a, b = span
                s, e = marks[a]["start"], marks[b]["end"]
                out[n] = (s, max(e, s + 0.2), "boundary")
                cursor = b + 1
            else:
                s = dur * acc / total
                out[n] = (s, s + dur * wgt / total, "interp")
        acc += wgt
    return out


# ---------- 组装 ----------

def item_ipa(it):
    if it["en"].lower() == "competency":
        return "/ˈkɒmpɪtənsi/"
    if it["kind"] == "word":
        return ipa(it["en"])
    parts = [ipa(w).strip("/") for w in it["en"].split()]
    parts = [p for p in parts if p]
    return f"/{' '.join(parts)}/" if parts else ""


def item_view(it, n):
    word = it["kind"] == "word"
    pos = "phr." if it["pos"] in PHRASE_POS else it["pos"]
    return {"en": it["en"], "pos": pos, "gloss": it["gloss"], "senses": review_senses(it), "kind": it["kind"],
            "ipa": item_ipa(it),
            "syllables": HYPH.inserted(it["en"]).replace("-", " · ") if word else "",
            "color": COLORS[n % len(COLORS)]}


def review_groups(n):
    k = max(1, math.ceil(n / REVIEW_GROUP_MAX))
    base, extra = divmod(n, k)
    sizes = [base + (1 if g < extra else 0) for g in range(k)]
    out, start = [], 0
    for s in sizes:
        out.append(list(range(start, start + s)))
        start += s
    return out


def audio_hash(ep):
    key = json.dumps([TIMELINE_VERSION, [p["tokens"] for p in ep["pages"]],
                      [(it["en"], it["pos"], it["gloss"]) for it in ep["items"]],
                      ep["voice"], ep["rate"], ep["review_voice"], ep["review_rate"],
                      ep["gloss_voice"], ep["gloss_rate"],
                      [ep[k] for k in ("title", "cover", "source", "level", "series", "vol")]],
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def assemble(ep, estimated=False):
    """返回 (timeline, pcm)。estimated=True 时不联网，按字数估算、pcm 为空。"""
    pcm = bytearray(silence(LEAD_IN))
    t = LEAD_IN
    body_rms = []
    interp = []

    def body(tokens):
        if estimated:
            return b"", estimate_page(tokens), []
        return synth(page_text(tokens), ep["voice"], ep["rate"])

    pages = []
    for n, p in enumerate(ep["pages"]):
        data, dur, marks = body(p["tokens"])
        if data:
            body_rms.append(rms(data))
        times = align_items(p["tokens"], marks, dur)
        tokens = []
        for k, tk in enumerate(p["tokens"]):
            if k in times:
                s, e, src = times[k]
                if src == "interp" and not estimated:
                    interp.append(tk["text"])
                tokens.append({**tk, "start": round(t + s, 3), "end": round(t + e, 3)})
            else:
                tokens.append(tk)
        pages.append({"start": round(t, 3), "end": round(t + dur, 3), "tokens": tokens})
        pcm += data
        t += dur
        if n < len(ep["pages"]) - 1:
            pcm += silence(PAGE_GAP)
            t += PAGE_GAP
    body_end = t

    target = sum(body_rms) / len(body_rms) if body_rms else 0
    pcm += silence(REVIEW_GAP)
    t += REVIEW_GAP
    review_start = t
    groups = []
    for idxs in review_groups(len(ep["items"])):
        g = {"start": round(t, 3), "entries": []}
        pcm += silence(GROUP_LEAD)
        t += GROUP_LEAD
        for i in idxs:
            it = ep["items"][i]
            if estimated:
                en, en_dur = b"", 0.15 + syllables(it["en"]) * 0.25
                zh, zh_dur = b"", 0.3 + len(it["gloss"]) * 0.16
            else:
                en, en_dur, _ = synth(it["en"], ep["review_voice"], ep["review_rate"])
                zh, zh_dur, _ = synth(it["gloss"], ep["gloss_voice"], ep["gloss_rate"])
                if target and rms(en):
                    en = gain(en, min(3.0, target / rms(en)))
            entry = {"i": i, "start": round(t, 3)}
            pcm += en
            t += en_dur
            entry["enEnd"] = round(t, 3)
            pcm += silence(EN_ZH_GAP) + zh
            t += EN_ZH_GAP + zh_dur
            entry["end"] = round(t, 3)
            g["entries"].append(entry)
            pcm += silence(ITEM_GAP)
            t += ITEM_GAP
        g["end"] = round(t, 3)
        groups.append(g)
    review_end = t
    overview_end = t + OVERVIEW_HOLD
    pcm += silence(OVERVIEW_HOLD)

    timeline = {
        "id": ep["id"], "vol": ep["vol"], "series": ep["series"], "title": ep["title"], "cover": ep["cover"],
        "level": ep["level"], "source": ep["source"],
        "items": [item_view(it, n) for n, it in enumerate(ep["items"])],
        "pages": pages,
        "review": {"start": round(review_start, 3), "end": round(review_end, 3), "groups": groups},
        "overview": {"start": round(review_end, 3), "end": round(overview_end, 3)},
        "fps": FPS,
        "durationInFrames": int(math.ceil(overview_end * FPS)),
        "estimated": estimated,
        "stats": {"body": round(body_end - LEAD_IN, 2), "review": round(review_end - review_start, 2),
                  "total": round(overview_end, 2), "interp": interp},
        "hash": audio_hash(ep),
    }
    return timeline, bytes(pcm)
