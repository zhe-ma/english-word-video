import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from . import media
from .config import PUBLIC_AUDIO, VIDEO


def template_hash():
    """模板源码的哈希：改了 video/src 下的任何文件都会触发重新渲染。"""
    h = hashlib.sha1()
    for p in sorted((VIDEO / "src").rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(VIDEO)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


def key_times(tl):
    """质检帧：第一帧、每段读完、每组复习读完、结尾全文帧。"""
    shots = [("01-first", 0.0)]
    for n, p in enumerate(tl["pages"], 1):
        shots.append((f"02-page{n}", p["end"]))
    for n, g in enumerate(tl["review"]["groups"], 1):
        shots.append((f"03-review{n}", g["entries"][-1]["end"]))
    shots.append(("04-overview", tl["overview"]["end"] - 0.1))
    return shots


def frame_at(tl, t):
    return max(0, min(tl["durationInFrames"] - 1, int(round(t * tl["fps"]))))


def stage_audio(key, wav):
    """把音频放进 Remotion public 目录，返回 staticFile 路径。"""
    PUBLIC_AUDIO.mkdir(parents=True, exist_ok=True)
    dst = PUBLIC_AUDIO / f"{key}.wav"
    shutil.copy(wav, dst)
    return f"audio/{dst.name}"


def clear_audio():
    shutil.rmtree(PUBLIC_AUDIO, ignore_errors=True)


def run_jobs(jobs):
    if not jobs:
        return
    if not (VIDEO / "node_modules").exists():
        raise SystemExit("缺少 batch/video/node_modules，先运行 batch/setup.sh")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False)
        path = f.name
    try:
        if subprocess.run(["node", "render.mjs", path], cwd=VIDEO).returncode != 0:
            raise SystemExit("✗ Remotion 渲染失败，见上方输出")
    finally:
        os.unlink(path)


def default_concurrency():
    return max(1, (os.cpu_count() or 4) // 2)


def extract_frames(video, tl, out_dir):
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    for name, t in key_times(tl):
        media.extract_frame(video, max(0.0, t), out_dir / f"{name}.png")
