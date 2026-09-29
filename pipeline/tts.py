import asyncio
import hashlib
import json
import re
import time
import wave

import edge_tts
import pyphen

from . import lexicon, media
from .config import (CACHE, COLORS, FPS, LEAD_IN, RATE, SENTENCE_GAP, SUMMARY_GAP, SUMMARY_HOLD,
                     VIDEO, VOICE)
from .script import ep_dir, load, save_json, sentence_text

SR = 24000
HYPH = pyphen.Pyphen(lang="en_US")


async def _synth(text, voice, rate, mp3_path):
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


def synth_cached(text, voice, rate):
    """返回 (wav_path, marks)。按 文本+音色+语速 缓存，同一句只合成一次。"""
    d = CACHE / "tts"
    d.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    wav, meta = d / f"{key}.wav", d / f"{key}.json"
    if wav.exists() and meta.exists():
        return wav, json.loads(meta.read_text())
    mp3 = d / f"{key}.mp3"
    for attempt in range(5):
        try:
            marks = asyncio.run(_synth(text, voice, rate, mp3))
            if mp3.stat().st_size == 0:
                raise RuntimeError("空音频")
            break
        except Exception as e:  # 网络抖动 / 限流
            if attempt == 4:
                raise SystemExit(f"edge-tts 合成失败：{e}")
            time.sleep(2 ** attempt)
    media.to_wav(mp3, wav, SR)
    meta.write_text(json.dumps(marks, ensure_ascii=False))
    return wav, marks


def read_pcm(path):
    with wave.open(str(path)) as w:
        return w.readframes(w.getnframes())


def write_pcm(path, pcm):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)


def silence(sec):
    return b"\x00\x00" * int(round(sec * SR))


def syllables(word):
    return HYPH.inserted(word).replace("-", " · ")


def syllable_count(word):
    return max(1, len(re.findall(r"[aeiouy]+", word.lower())))


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def map_words(tokens, marks, dur):
    """给句内每个英文单词找时间：优先用 WordBoundary，找不到就按字数权重插值。"""
    weights = []
    for tk in tokens:
        if "w" in tk:
            weights.append(syllable_count(tk["w"]) * 0.7)
        else:
            weights.append(len(re.findall(r"[\u4e00-\u9fff]", tk.get("t", ""))) + 0.3)
    total = sum(weights) or 1
    cursor, acc, out = 0, 0.0, []
    for tk, wgt in zip(tokens, weights):
        if "w" in tk:
            hit = None
            for j in range(cursor, len(marks)):
                if norm(marks[j]["text"]) == norm(tk["w"]):
                    hit, cursor = marks[j], j + 1
                    break
            if hit:
                out.append((hit["start"], max(hit["end"], hit["start"] + 0.2), "boundary"))
            else:
                s = dur * acc / total
                out.append((s, s + dur * wgt / total, "interp"))
        acc += wgt
    return out


def run(ep, voice=VOICE, rate=RATE):
    d = ep_dir(ep)
    s = load(ep)
    lex = lexicon.connect()

    pcm = bytearray(silence(LEAD_IN))
    t = LEAD_IN
    sentences, word_times = [], []
    for i, tokens in enumerate(s["sentences"]):
        text = sentence_text(tokens, tts=True)
        wav, marks = synth_cached(text, voice, rate)
        data = read_pcm(wav)
        dur = len(data) / 2 / SR
        times = map_words(tokens, marks, dur)
        out_tokens, k = [], 0
        for tk in tokens:
            if "w" in tk:
                st, en, src = times[k]
                word_times.append({"start": round(t + st, 3), "end": round(t + en, 3), "source": src})
                out_tokens.append({"w": len(word_times) - 1})
                k += 1
            else:
                out_tokens.append({"t": tk["t"]})
        sentences.append({"start": round(t, 3), "end": round(t + dur, 3), "tokens": out_tokens})
        pcm += data
        t += dur
        if i < len(s["sentences"]) - 1:
            pcm += silence(SENTENCE_GAP)
            t += SENTENCE_GAP

    reading_end = t
    summary_start = reading_end + SUMMARY_GAP
    summary_end = summary_start + 0.8 + 0.08 * len(s["words"]) + SUMMARY_HOLD
    pcm += silence(summary_end - t)

    voice_wav = d / "voice.wav"
    write_pcm(voice_wav, bytes(pcm))
    mix(voice_wav, d / "audio.wav")

    words = []
    for i, (w, tm) in enumerate(zip(s["words"], word_times)):
        row = lexicon.lookup(lex, w["word"])
        words.append({
            "word": w["word"], "ipa": lexicon.ipa(row), "syllables": syllables(w["word"]),
            "pos": w["pos"], "meaning": w["meaning"], "color": COLORS[i % len(COLORS)],
            "review": bool(w.get("review")), **tm,
        })

    timeline = {
        "meta": {"id": s["id"], "series": s.get("series", ""), "level": s["level"], "theme": s["theme"]},
        "layout": s.get("layout", {}),
        "fps": FPS,
        "durationInFrames": int(round(summary_end * FPS)),
        "reading": {"start": LEAD_IN, "end": round(reading_end, 3)},
        "summary": {"start": round(summary_start, 3), "end": round(summary_end, 3)},
        "sentences": sentences,
        "words": words,
        "voice": voice, "rate": rate,
    }
    save_json(d / "timeline.json", timeline)
    interp = [w["word"] for w in words if w["source"] == "interp"]
    print(f"配音完成：朗读 {reading_end - LEAD_IN:.1f}s，视频总长 {summary_end:.1f}s → {d}/audio.wav")
    print(f"单词时间来自 WordBoundary：{len(words) - len(interp)}/{len(words)}"
          + (f"，插值兜底：{', '.join(interp)}" if interp else ""))


def mix(voice_wav, out_wav):
    """有 BGM 就垫在下面，最后做响度归一。"""
    bgm = sorted((VIDEO / "public" / "bgm").glob("*.mp3")) if (VIDEO / "public" / "bgm").exists() else []
    if bgm:
        media.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice_wav), "-stream_loop", "-1", "-i", str(bgm[0]),
                   "-filter_complex",
                   "[1:a]volume=0.05[b];[0:a][b]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5",
                   "-ar", "48000", str(out_wav)])
    else:
        media.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice_wav),
                   "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "48000", str(out_wav)])
