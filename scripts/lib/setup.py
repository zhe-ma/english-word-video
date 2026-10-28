"""运行环境准备：Python 依赖 → 渲染模板副本 → npm 依赖 → 浏览器 → 自检。只依赖标准库，可重复运行。

  python scripts/vb.py setup            准备环境（已就绪时立即返回）
  python scripts/vb.py setup --upgrade  强制重装 Python 依赖和 npm 依赖

可用环境变量：
  EWV_HOME            运行目录，默认 ~/.english-word-video
  PIP_INDEX_URL       pip 镜像
  npm_config_registry npm 镜像
  VB_BROWSER          用本机 Chrome / Edge 渲染（Remotion 浏览器下载失败时用）
"""
import filecmp
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .config import HOME, PYDEPS, REQUIREMENTS, RUNTIME, STAMP, TEMPLATE


def say(msg):
    print(f"\n==> {msg}", flush=True)


def die(msg):
    print(f"✗ {msg}", flush=True)
    raise SystemExit(1)


def _sha(*paths):
    h = hashlib.sha1()
    for p in paths:
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:12]


def read_stamp():
    try:
        return json.loads(STAMP.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def is_ready():
    st = read_stamp()
    return bool(st.get("ok")) and PYDEPS.exists() and (RUNTIME / "node_modules").exists() \
        and st.get("requirements") == _sha(REQUIREMENTS) and st.get("template") == template_sig()


def template_sig():
    h = hashlib.sha1()
    for p in sorted(TEMPLATE.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(TEMPLATE).as_posix().encode())
            h.update(str(p.stat().st_size).encode())
    return h.hexdigest()[:12]


def which(name):
    return shutil.which(name)


def run(cmd, cwd=None, env=None):
    cmd = [str(c) for c in cmd]
    if subprocess.run(cmd, cwd=cwd, env=env).returncode != 0:
        die(f"命令失败：{' '.join(cmd)}")


# ---------- 各步骤 ----------

def check_system():
    say("检查系统环境")
    if sys.version_info < (3, 9):
        die(f"需要 Python 3.9+，当前 {sys.version.split()[0]}")
    node = which("node")
    if not node:
        die("没有找到 Node.js（需要 18+）。Windows：winget install OpenJS.NodeJS.LTS；macOS：brew install node；"
            "或到 https://nodejs.org 下载。装好后重新打开终端再运行 setup")
    ver = subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip()
    if int(ver.lstrip("v").split(".")[0]) < 18:
        die(f"Node.js 需要 18+，当前 {ver}")
    if not which("npm") or not which("npx"):
        die("没有找到 npm / npx，请重新安装 Node.js")
    print(f"Python {sys.version.split()[0]}，Node {ver}，{sys.platform}")


def install_python_deps(upgrade):
    say("Python 依赖（edge-tts、pyphen、PyYAML）")
    want = _sha(REQUIREMENTS)
    if not upgrade and PYDEPS.exists() and read_stamp().get("requirements") == want:
        print("已安装")
        return
    shutil.rmtree(PYDEPS, ignore_errors=True)
    PYDEPS.mkdir(parents=True)
    run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--target", PYDEPS,
         "-r", REQUIREMENTS])


def sync_template():
    """skill 目录只读，渲染在用户目录里的副本中进行；node_modules 留在副本里。"""
    say("同步渲染模板")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json", "tsconfig.json", "render.mjs"):
        shutil.copy2(TEMPLATE / name, RUNTIME / name)
    shutil.rmtree(RUNTIME / "src", ignore_errors=True)
    shutil.copytree(TEMPLATE / "src", RUNTIME / "src")
    fonts = RUNTIME / "public" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    for f in (TEMPLATE / "public" / "fonts").iterdir():
        if not (fonts / f.name).exists() or not filecmp.cmp(f, fonts / f.name, shallow=True):
            shutil.copy2(f, fonts / f.name)
    print(f"→ {RUNTIME}")


def install_node_deps(upgrade):
    say("Remotion 依赖（npm）")
    want = _sha(TEMPLATE / "package-lock.json")
    if not upgrade and (RUNTIME / "node_modules").exists() and read_stamp().get("lock") == want:
        print("已安装")
        return
    run([which("npm"), "ci", "--no-audit", "--no-fund"], cwd=RUNTIME)


def ensure_browser():
    say("渲染用浏览器")
    if os.environ.get("VB_BROWSER"):
        print(f"使用 VB_BROWSER：{os.environ['VB_BROWSER']}")
        return
    run([which("npx"), "remotion", "browser", "ensure"], cwd=RUNTIME)


def self_check():
    say("自检")
    from . import media
    d, exe = media.ffmpeg_dir()
    r = subprocess.run([str(d / exe), "-version"], cwd=d, capture_output=True, text=True)
    if r.returncode != 0:
        die("Remotion 自带的 ffmpeg 无法运行：" + r.stderr[:200])
    print("ffmpeg：" + r.stdout.splitlines()[0])
    sys.path.insert(0, str(PYDEPS))
    try:
        import asyncio

        import edge_tts

        async def probe():
            n = 0
            async for c in edge_tts.Communicate("hello", "en-US-AriaNeural").stream():
                n += c["type"] == "audio"
            return n

        asyncio.run(asyncio.wait_for(probe(), 20))
        print("edge-tts：连通正常")
    except Exception as e:  # 只提醒，配音时才真正需要
        print(f"⚠ edge-tts 连不上（{type(e).__name__}）。配音需要能访问 speech.platform.bing.com；"
              "403 请运行 setup --upgrade；仍失败请检查网络或代理")


def setup(upgrade=False):
    HOME.mkdir(parents=True, exist_ok=True)
    if not upgrade and is_ready():
        print("环境已就绪（需要重装依赖时加 --upgrade）")
        return 0
    check_system()
    install_python_deps(upgrade)
    sync_template()
    install_node_deps(upgrade)
    ensure_browser()
    self_check()
    STAMP.write_text(json.dumps({"ok": True, "requirements": _sha(REQUIREMENTS),
                                 "lock": _sha(TEMPLATE / "package-lock.json"), "template": template_sig()}),
                     encoding="utf-8")
    say("环境就绪")
    return 0
