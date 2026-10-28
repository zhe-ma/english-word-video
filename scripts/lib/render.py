import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from .config import PUBLIC_AUDIO, RUNTIME, TEMPLATE


def template_hash():
    """模板源码的哈希：模板变了就重新渲染。"""
    h = hashlib.sha1()
    for p in sorted((TEMPLATE / "src").rglob("*")):
        if p.is_file():
            h.update(p.relative_to(TEMPLATE).as_posix().encode())
            h.update(p.read_bytes())
    for p in sorted((TEMPLATE / "public" / "fonts").glob("*.woff2")):
        h.update(p.name.encode())
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
    node = shutil.which("node")
    if not node or not (RUNTIME / "node_modules").exists():
        raise SystemExit("渲染环境没准备好，先运行：python scripts/vb.py setup")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False)
        path = f.name
    try:
        env = {**os.environ, "PYTHONUTF8": "1"}
        if subprocess.run([node, "render.mjs", path], cwd=RUNTIME, env=env).returncode != 0:
            raise SystemExit("✗ Remotion 渲染失败，见上方输出")
    finally:
        os.unlink(path)


def default_concurrency():
    return max(1, (os.cpu_count() or 4) // 2)
