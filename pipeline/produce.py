import json
import os
import shutil
import subprocess

from . import media, progress, validate
from .config import EPISODES, READING_RANGE, VIDEO
from .script import ep_dir, load, save_json


def load_timeline(d):
    p = d / "timeline.json"
    if not p.exists():
        raise SystemExit(f"缺少 {p}，先运行 ./vv tts {d.name}")
    return json.loads(p.read_text(encoding="utf-8"))


def qa_audio(ep):
    d = ep_dir(ep)
    tl = load_timeline(d)
    errors, warnings = [], []
    reading = tl["reading"]["end"] - tl["reading"]["start"]
    lo, hi = READING_RANGE
    if not lo <= reading <= hi:
        errors.append(f"朗读时长 {reading:.1f}s，要求 {lo:.0f}–{hi:.0f}s（{'删减' if reading > hi else '扩写'}文案）")
    interp = [w["word"] for w in tl["words"] if w["source"] == "interp"]
    if interp:
        warnings.append(f"这些词没拿到 WordBoundary，时间是插值估算的：{', '.join(interp)}")
    for a, b in media.silences(d / "voice.wav", min_dur=0.8):
        for s in tl["sentences"]:
            if s["start"] < a and b < s["end"]:
                warnings.append(f"句内出现 {b - a:.1f}s 长静音（{a:.1f}s–{b:.1f}s），可能有异常停顿")
    for w in tl["words"]:
        if not 0.2 <= w["end"] - w["start"] <= 1.5:
            warnings.append(f"{w['word']} 时长 {w['end'] - w['start']:.2f}s 异常")
    ok = not errors
    save_json(d / "qa_audio.json", {"ok": ok, "reading": round(reading, 2), "errors": errors, "warnings": warnings})
    print(f"音频检查{'通过' if ok else '未通过'}：朗读 {reading:.1f}s，总长 {tl['summary']['end']:.1f}s")
    for e in errors:
        print(f"  ✗ {e}")
    for w in warnings:
        print(f"  ! {w}")
    return 0 if ok else 1


def render(ep, concurrency=None, cover=True):
    d = ep_dir(ep)
    tl = load_timeline(d)
    pub = VIDEO / "public" / "episodes" / d.name
    pub.mkdir(parents=True, exist_ok=True)
    shutil.copy(d / "audio.wav", pub / "audio.wav")
    props = {**tl, "audioSrc": f"episodes/{d.name}/audio.wav"}
    props_path = d / "props.json"
    save_json(props_path, props)

    conc = concurrency or max(1, (os.cpu_count() or 4) // 2)
    out = d / "out.mp4"
    cmd = ["npx", "remotion", "render", "src/index.ts", "MarkerNotes", str(out),
           f"--props={props_path}", f"--concurrency={conc}", "--codec=h264", "--crf=20", "--log=error"]
    print("渲染中：", " ".join(cmd[2:5]), "...")
    subprocess.run(cmd, cwd=VIDEO, check=True)
    if cover:
        frame = int(tl["summary"]["start"] * tl["fps"]) - 2
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "MarkerNotes", str(d / "cover.png"),
                        f"--props={props_path}", f"--frame={frame}", "--log=error"], cwd=VIDEO, check=True)
    print(f"完成 → {out}（{media.duration(out):.1f}s）")


def frames(ep):
    d = ep_dir(ep)
    tl = load_timeline(d)
    video = d / "out.mp4"
    if not video.exists():
        raise SystemExit(f"缺少 {video}，先运行 ./vv render {d.name}")
    fd = d / "frames"
    shutil.rmtree(fd, ignore_errors=True)
    fd.mkdir()
    ws = tl["words"]
    mid = ws[len(ws) // 2]
    shots = [
        ("1-first-word", ws[0]["start"] + 0.5),
        ("2-middle", mid["start"] + 0.5),
        ("3-reading-end", tl["reading"]["end"] + 0.2),
        ("4-summary", tl["summary"]["end"] - 0.3),
    ]
    for name, t in shots:
        media.extract_frame(video, t, fd / f"{name}.png")
    print("已抽帧（请逐张查看）：")
    for name, t in shots:
        print(f"  {fd / (name + '.png')}  @ {t:.2f}s")


def commit(ep):
    d = ep_dir(ep)
    if validate.run(ep) != 0:
        raise SystemExit("校验未通过，不能入库")
    if not (d / "out.mp4").exists():
        raise SystemExit("还没有成片 out.mp4")
    s = load(ep)
    progress.commit(d, s)
    print(f"第 {d.name} 期已入库（published_at={s['published_at']}），已重新生成 data/published_scripts.md")


def steps(d):
    """一期目录已完成的步骤。"""
    out = []
    if (d / "plan.json").exists():
        out.append("plan")
    if (d / "drafts.md").exists():
        out.append("drafts")
    script = None
    if (d / "script.json").exists():
        out.append("script")
        try:
            script = json.loads((d / "script.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    rp = d / "report.json"
    if rp.exists() and json.loads(rp.read_text(encoding="utf-8")).get("ok"):
        out.append("valid")
    if (d / "timeline.json").exists():
        out.append("tts")
    qa = d / "qa_audio.json"
    if qa.exists() and json.loads(qa.read_text(encoding="utf-8")).get("ok"):
        out.append("qa")
    if (d / "out.mp4").exists():
        out.append("video")
    if (d / "frames").exists():
        out.append("frames")
    if script and script.get("published_at"):
        out.append("committed")
    return out, script


def status():
    if not EPISODES.exists():
        print("还没有任何一期")
        return
    print(f"{'期号':<6}{'主题':<14}{'状态'}")
    for d in sorted(p for p in EPISODES.iterdir() if p.is_dir()):
        st, script = steps(d)
        print(f"{d.name:<6}{(script or {}).get('theme', ''):<14}{' → '.join(st)}")
    print(f"\n已学单词 {len(progress.used_words())} 个，已入库 {len(progress.published())} 期")
