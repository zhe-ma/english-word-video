"""音频转码和响度归一。用 Remotion 自带的 ffmpeg，不要求用户另装。"""
import os
import subprocess

from vb_config import RUNTIME


def ffmpeg_dir():
    """Remotion 的 ffmpeg 要在它自己的目录下运行才找得到动态库。"""
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    base = RUNTIME / "node_modules" / "@remotion"
    for d in sorted(base.glob("compositor-*")):
        if (d / exe).exists():
            return d, exe
    raise SystemExit("找不到 Remotion 自带的 ffmpeg，先运行：python scripts/vb.py setup")


def run(args):
    d, exe = ffmpeg_dir()
    r = subprocess.run([str(d / exe), "-v", "error", "-y", *map(str, args)], cwd=d, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败：{r.stderr.strip()[:300]}")


def to_wav(src, dst, rate):
    run(["-i", os.path.abspath(src), "-ac", "1", "-ar", rate, "-sample_fmt", "s16", os.path.abspath(dst)])


def loudnorm(src, dst):
    run(["-i", os.path.abspath(src), "-af", "loudnorm=I=-16:TP=-1.5", "-ar", 48000, os.path.abspath(dst)])
