"""可视化工作台的本地 API：./vv serve

- 读写只落在 episodes/<id>/ 的文件上，命令行、工作台、Cursor 对话三种方式可以混用。
- 快操作（校验、预览时间轴、查词）进程内直接调流水线；慢操作（配音、渲染、抽帧、入库）起 ./vv 子进程，
  日志按行推给前端轮询。同一时间只跑一个任务：edge-tts 和渲染都不适合并发。
"""
import json
import mimetypes
import os
import re
import signal
import subprocess
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import yaml

from . import bootstrap, catalog, lexicon, plan, produce, progress, tts, validate
from .config import (DATA, EPISODES, HANZI_RANGE, LEVELS, RATE, READING_RANGE, REVIEW_KEYS, REVIEW_PASS, ROOT,
                     VIDEO, VOICE, WORDS_RANGE, WORKBENCH)
from .script import full_text, save_json

WORKBENCH_DIST = WORKBENCH / "dist"
VOICES = [
    ("zh-CN-XiaoxiaoNeural", "晓晓 · 女声（默认）"),
    ("zh-CN-XiaoyiNeural", "晓伊 · 女声，活泼"),
    ("zh-CN-YunxiNeural", "云希 · 男声，年轻"),
    ("zh-CN-YunjianNeural", "云健 · 男声，浑厚"),
    ("zh-CN-YunyangNeural", "云扬 · 男声，播音"),
    ("zh-CN-YunxiaNeural", "云夏 · 男声，少年"),
]
JOB_CMDS = {"validate", "tts", "qa-audio", "render", "frames", "commit"}
EP_ID = re.compile(r"^[\w-]+$")


class ApiError(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status = status


# ---------- 任务 ----------

class Jobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.jobs = {}
        self.current = None

    def start(self, ep, steps):
        with self.lock:
            if self.current and self.jobs[self.current]["status"] == "running":
                raise ApiError(409, f"已有任务在运行：{self.jobs[self.current]['title']}")
            jid = uuid.uuid4().hex[:8]
            job = {"id": jid, "ep": ep, "title": " → ".join(s[0] for s in steps), "steps": steps,
                   "status": "running", "lines": [], "started": time.time(), "ended": None, "failed_step": None}
            self.jobs[jid] = job
            self.current = jid
        threading.Thread(target=self._run, args=(job,), daemon=True).start()
        return job

    def _run(self, job):
        env = {**os.environ, "PYTHONUNBUFFERED": "1", "FORCE_COLOR": "0"}
        for cmd, *args in job["steps"]:
            job["lines"].append(f"$ ./vv {cmd} {job['ep']} {' '.join(args)}".rstrip())
            try:
                p = subprocess.Popen([str(ROOT / "vv"), cmd, job["ep"], *args], cwd=ROOT, env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in p.stdout:
                    job["lines"].append(line.rstrip("\n"))
                code = p.wait()
            except Exception as e:  # noqa: BLE001
                job["lines"].append(f"启动失败：{e}")
                code = -1
            if code != 0:
                job["status"], job["failed_step"] = "failed", cmd
                job["lines"].append(f"✗ {cmd} 退出码 {code}")
                break
        else:
            job["status"] = "done"
        job["ended"] = time.time()

    def get(self, jid, since=0):
        job = self.jobs.get(jid)
        if not job:
            raise ApiError(404, "任务不存在")
        return {**{k: v for k, v in job.items() if k != "lines"}, "lines": job["lines"][since:],
                "next": len(job["lines"])}

    def active(self):
        if self.current and self.jobs[self.current]["status"] == "running":
            return self.get(self.current)
        return None


JOBS = Jobs()


# ---------- 数据 ----------

def ep_path(ep):
    if not EP_ID.match(ep or ""):
        raise ApiError(400, f"期号不合法：{ep}")
    d = EPISODES / ep
    if not d.is_dir():
        raise ApiError(404, f"找不到第 {ep} 期")
    return d


def read_json(p):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def media_url(d, rel):
    f = d / rel
    if not f.exists():
        return None
    return f"media/{d.name}/{int(f.stat().st_mtime)}/{rel}"


def meta():
    return {
        "levels": [{"key": k, "label": v["label"]} for k, v in LEVELS.items()],
        "voices": [{"id": v, "label": label} for v, label in VOICES],
        "defaultVoice": VOICE, "defaultRate": RATE,
        "hanziRange": HANZI_RANGE, "wordsRange": WORDS_RANGE, "readingRange": READING_RANGE,
        "reviewKeys": REVIEW_KEYS, "reviewPass": REVIEW_PASS,
    }


def themes():
    raw = yaml.safe_load((DATA / "themes.yaml").read_text(encoding="utf-8")) or {}
    used = {}
    for d in sorted(EPISODES.iterdir()) if EPISODES.exists() else []:
        s = read_json(d / "script.json") or read_json(d / "plan.json") or {}
        if s.get("theme"):
            used.setdefault(s["theme"], d.name)
    return [{"group": g, "items": [{**it, "usedBy": used.get(it.get("theme"))} for it in items or []]}
            for g, items in raw.items()]


def episodes():
    out = []
    for d in sorted((p for p in EPISODES.iterdir() if p.is_dir()), reverse=True) if EPISODES.exists() else []:
        steps, s = produce.steps(d)
        p = read_json(d / "plan.json") or {}
        s = s or {}
        words = [w.get("word", "") for w in (s.get("words") or []) if w.get("word")]
        if not words:
            words = list(p.get("picked") or [])
        text = full_text(s) if s.get("sentences") else ""
        out.append({
            "id": d.name, "theme": s.get("theme") or p.get("theme", ""),
            "level": s.get("level") or p.get("level", ""), "genre": s.get("genre", ""),
            "steps": steps, "publishedAt": s.get("published_at"),
            "words": words, "text": text,
            "cover": media_url(d, "cover.png"), "video": media_url(d, "out.mp4"),
        })
    return out


def normalize_plan(p):
    if not p:
        return p
    p["picked"] = p.get("picked") or []
    p["review_due"] = p.get("review_due") or []
    p["candidates"] = p.get("candidates") or []
    return p


def episode(ep):
    d = ep_path(ep)
    steps, script = produce.steps(d)
    tl = read_json(d / "timeline.json")
    timeline = None
    if tl:
        timeline = {"reading": tl["reading"]["end"] - tl["reading"]["start"], "total": tl["summary"]["end"],
                    "voice": tl.get("voice"), "rate": tl.get("rate"),
                    "stale": bool(script) and tl.get("scriptHash") != tts.script_hash(script),
                    "interp": [w["word"] for w in tl["words"] if w.get("source") == "interp"]}
    frames = sorted((d / "frames").glob("*.png")) if (d / "frames").exists() else []
    return {
        "id": ep, "steps": steps,
        "plan": normalize_plan(read_json(d / "plan.json")),
        "script": script,
        "drafts": (d / "drafts.md").read_text(encoding="utf-8") if (d / "drafts.md").exists() else None,
        "report": read_json(d / "report.json"),
        "qa": read_json(d / "qa_audio.json"),
        "timeline": timeline,
        "files": {
            "audio": media_url(d, "audio.wav"),
            "video": media_url(d, "out.mp4"),
            "cover": media_url(d, "cover.png"),
            "frames": [{"name": f.stem, "url": media_url(d, f"frames/{f.name}")} for f in frames],
        },
    }


def create_episode(body):
    return bootstrap.run(
        level=body.get("level") or "cet4",
        theme=(body.get("theme") or "").strip(),
        words=int(body.get("words") or 6),
        voice=body.get("voice"),
        rate=body.get("rate"),
        seed=body.get("seed"),
    )


def autopick(ep, body):
    d = ep_path(ep)
    old = read_json(d / "plan.json") or {}
    level = body.get("level") or old.get("level_key") or "cet4"
    theme = (body.get("theme") or old.get("theme") or "").strip()
    if theme and theme != old.get("theme"):
        old["theme"] = theme
    old["picked"] = plan.auto_pick(level, theme, ep, int(body.get("n") or 6))
    save_json(d / "plan.json", old)
    return normalize_plan(old)


def replan(ep, body):
    d = ep_path(ep)
    old = read_json(d / "plan.json") or {}
    level = body.get("level") or old.get("level_key") or "cet4"
    plan.run(level, body.get("theme", old.get("theme", "")), int(body.get("n") or 40), None, ep)
    return read_json(d / "plan.json")


def save_plan_fields(ep, body):
    d = ep_path(ep)
    p = read_json(d / "plan.json")
    if p is None:
        raise ApiError(400, "这一期还没有 plan.json")
    for k in ("picked", "theme", "voice", "rate"):
        if k in body:
            p[k] = body[k]
    save_json(d / "plan.json", p)
    return p


def save_drafts(ep, body):
    d = ep_path(ep)
    text = body.get("text")
    if not isinstance(text, str):
        raise ApiError(400, "drafts 需要 text 字符串")
    (d / "drafts.md").write_text(text, encoding="utf-8")
    return {"ok": True, "bytes": len(text.encode())}


def clean_script(s):
    if not isinstance(s, dict) or not isinstance(s.get("sentences"), list):
        raise ApiError(400, "script 格式不对：缺少 sentences")
    return s


def save_script(ep, body):
    d = ep_path(ep)
    s = clean_script(body)
    s["id"] = ep
    old = read_json(d / "script.json") or {}
    if old.get("published_at") and not s.get("published_at"):
        s["published_at"] = old["published_at"]
    save_json(d / "script.json", s)
    report = validate.build_report(ep)
    save_json(d / "report.json", report)
    return {"report": report}


def check_script(ep, body):
    ep_path(ep)
    s = clean_script(body)
    s["id"] = ep
    return validate.build_report(ep, s)


def aligned(s):
    """words 和句子里的单词顺序对齐，缺的补空，保证模板不会因为编辑中途的不一致而崩。"""
    by_word = {w.get("word", "").lower(): w for w in s.get("words", [])}
    toks = [tk["w"] for sent in s["sentences"] for tk in sent if "w" in tk]
    return {**s, "words": [by_word.get(t.lower(), {"word": t, "pos": "", "meaning": "?"}) | {"word": t} for t in toks]}


def preview(ep, body):
    d = ep_path(ep)
    s = clean_script(body.get("script") or read_json(d / "script.json") or {})
    s = {"series": "", "level": "", "theme": "", **s, "id": ep}
    s = aligned(s)
    if not s["sentences"]:
        raise ApiError(400, "还没有句子")
    tl = read_json(d / "timeline.json")
    if tl and tl.get("scriptHash") == tts.script_hash(s) and (d / "audio.wav").exists() and not body.get("estimate"):
        return {"timeline": {**tl, "audioSrc": media_url(d, "audio.wav")}, "source": "tts"}
    return {"timeline": tts.estimate(s), "source": "estimate"}


def lookup(word, level):
    lex = lexicon.connect()
    r = lexicon.lookup(lex, word)
    if not r:
        return {"word": word, "found": False}
    tags = set((r["tag"] or "").split())
    cfg = LEVELS.get(level) or LEVELS["cet4"]
    return {"word": r["word"], "found": True, "ipa": lexicon.ipa(r), "tag": r["tag"],
            "inLevel": bool(tags & set(cfg["include"])), "used": r["word"] in progress.used_words(),
            "senses": [{"pos": p, "text": t} for p, t in lexicon.senses(r["translation"])][:6]}


def run_job(ep, body):
    ep_path(ep)
    steps = []
    for step in body.get("steps") or []:
        cmd, args = step.get("cmd"), step.get("args") or []
        if cmd not in JOB_CMDS or not all(isinstance(a, str) for a in args):
            raise ApiError(400, f"不支持的命令：{cmd}")
        steps.append([cmd, *args])
    if not steps:
        raise ApiError(400, "没有要执行的步骤")
    return JOBS.get(JOBS.start(ep, steps)["id"])


# ---------- HTTP ----------

ROUTES = [
    ("GET", r"/api/meta", lambda m, q, b: meta()),
    ("GET", r"/api/defaults", lambda m, q, b: bootstrap.defaults(q.get("level") or "cet4")),
    ("GET", r"/api/stats", lambda m, q, b: catalog.stats()),
    ("GET", r"/api/themes", lambda m, q, b: themes()),
    ("GET", r"/api/usage", lambda m, q, b: catalog.usage()),
    ("GET", r"/api/lexicon", lambda m, q, b: catalog.browse(q.get("q", ""), q.get("level", "cet4"),
                                                            q.get("used", ""), int(q.get("page", 1)),
                                                            int(q.get("limit", 40)))),
    ("GET", r"/api/episodes", lambda m, q, b: episodes()),
    ("POST", r"/api/episodes", lambda m, q, b: create_episode(b)),
    ("GET", r"/api/episodes/([\w-]+)", lambda m, q, b: episode(m[1])),
    ("GET", r"/api/episodes/([\w-]+)/files", lambda m, q, b: catalog.episode_files(m[1], media_url)),
    ("POST", r"/api/episodes/([\w-]+)/replan", lambda m, q, b: replan(m[1], b)),
    ("POST", r"/api/episodes/([\w-]+)/autopick", lambda m, q, b: autopick(m[1], b)),
    ("POST", r"/api/episodes/([\w-]+)/bootstrap", lambda m, q, b: bootstrap.run(
        level=b.get("level") or "cet4", theme=(b.get("theme") or "").strip(),
        words=int(b.get("words") or 6), voice=b.get("voice"), rate=b.get("rate"), ep=m[1])),
    ("PUT", r"/api/episodes/([\w-]+)/plan", lambda m, q, b: save_plan_fields(m[1], b)),
    ("PUT", r"/api/episodes/([\w-]+)/drafts", lambda m, q, b: save_drafts(m[1], b)),
    ("PUT", r"/api/episodes/([\w-]+)/script", lambda m, q, b: save_script(m[1], b)),
    ("POST", r"/api/episodes/([\w-]+)/check", lambda m, q, b: check_script(m[1], b)),
    ("POST", r"/api/episodes/([\w-]+)/preview", lambda m, q, b: preview(m[1], b)),
    ("POST", r"/api/episodes/([\w-]+)/run", lambda m, q, b: run_job(m[1], b)),
    ("GET", r"/api/words", lambda m, q, b: [
        {**h, "inLevel": h["in_level"]} for h in plan.search_data(
            q.get("q", ""), q.get("level", "cet4"), int(q.get("limit", 15)))
    ]),
    ("GET", r"/api/lookup", lambda m, q, b: lookup(q.get("word", ""), q.get("level", "cet4"))),
    ("GET", r"/api/jobs/active", lambda m, q, b: JOBS.active()),
    ("GET", r"/api/jobs/(\w+)", lambda m, q, b: JOBS.get(m[1], int(q.get("since", 0)))),
]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if not self.path.startswith("/api/jobs"):
            sys.stderr.write(f"[api] {self.command} {self.path} → {args[1] if len(args) > 1 else ''}\n")

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PUT(self):
        self.dispatch("PUT")

    def send_json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def dispatch(self, method):
        url = urlparse(self.path)
        path = unquote(url.path)
        if path.startswith("/media/"):
            return self.serve_media(path)
        if not path.startswith("/api/"):
            return self.serve_static(path) if method == "GET" else self.send_json(404, {"error": "not found"})
        q = {k: v[-1] for k, v in parse_qs(url.query).items()}
        body = {}
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            try:
                body = json.loads(self.rfile.read(n))
            except json.JSONDecodeError:
                return self.send_json(400, {"error": "请求体不是 JSON"})
        for m_, pattern, fn in ROUTES:
            m = re.fullmatch(pattern, path)
            if m and m_ == method:
                try:
                    return self.send_json(200, fn(m, q, body))
                except ApiError as e:
                    return self.send_json(e.status, {"error": str(e)})
                except SystemExit as e:
                    return self.send_json(400, {"error": str(e.code)})
                except Exception as e:  # noqa: BLE001
                    traceback.print_exc()
                    return self.send_json(500, {"error": f"{type(e).__name__}: {e}"})
        self.send_json(404, {"error": f"没有这个接口：{method} {path}"})

    def serve_media(self, path):
        # /media/<期号>/<版本号>/<相对路径>，版本号只用来破缓存
        parts = path.split("/")[2:]
        if len(parts) < 3 or not EP_ID.match(parts[0]):
            return self.send_json(404, {"error": "not found"})
        base = (EPISODES / parts[0]).resolve()
        f = (base / "/".join(parts[2:])).resolve()
        if base not in f.parents or not f.is_file():
            return self.send_json(404, {"error": "not found"})
        self.send_file(f)

    def serve_static(self, path):
        for root in (WORKBENCH_DIST, VIDEO / "public"):
            f = (root / path.lstrip("/")).resolve()
            if root.exists() and (f == root.resolve() or root.resolve() in f.parents) and f.is_file():
                return self.send_file(f)
        index = WORKBENCH_DIST / "index.html"
        if index.exists():
            return self.send_file(index)
        self.send_json(404, {"error": "前端未构建：用 ./vv serve 启动开发模式，或在 video/ 下 npm run workbench:build"})

    def send_file(self, f):
        size = f.stat().st_size
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        start, end = 0, size - 1
        rng = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
        if rng:
            if rng[1]:
                start = int(rng[1])
                end = int(rng[2]) if rng[2] else end
            else:
                start = max(0, size - int(rng[2]))
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with open(f, "rb") as fh:
            fh.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = fh.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass


def main(port=8765, ui_port=5173, with_ui=True):
    lexicon.connect()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    ui = None
    if with_ui:
        if not (WORKBENCH / "node_modules" / "vite").exists():
            raise SystemExit("缺少工作台依赖：cd workbench && npm install")
        env = {**os.environ, "VV_API": f"http://127.0.0.1:{port}"}
        ui = subprocess.Popen(["npx", "vite", "--port", str(ui_port), "--strictPort"], cwd=WORKBENCH, env=env)
        print(f"工作台：http://localhost:{ui_port}  （API：http://127.0.0.1:{port}）")
    else:
        print(f"API：http://127.0.0.1:{port}" + ("，前端已构建，直接打开这个地址" if WORKBENCH_DIST.exists() else ""))

    def stop(*_):
        if ui and ui.poll() is None:
            ui.terminate()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop()
        httpd.server_close()
