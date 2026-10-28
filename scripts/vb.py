#!/usr/bin/env python3
"""中英混读单词短视频：文案 YAML → 配音 → 竖屏成片 + 封面。

  python scripts/vb.py setup [--upgrade]      准备运行环境（首次必须，之后几秒返回）
  python scripts/vb.py words <词或中文> [--level ielts]   查词典：音标、级别、释义
  python scripts/vb.py check  <文案.yaml>     解析 + 校验 + 估算时长 + 写对照稿 review.md，不联网
  python scripts/vb.py stills <文案.yaml>     按估算时间轴渲染质检静帧和封面，不联网
  python scripts/vb.py build  <文案.yaml>     校验 → 配音 → 渲染成片和封面 → 汇总

产物在 <文案所在目录>/<文案文件名>/：summary.md、review.md、result.json，每期一个 <id>/ 目录（video.mp4、cover.png、stills/）。
"""
import argparse
import json
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from lib.config import BODY_RANGE, PYDEPS, SR, TOTAL_RANGE  # noqa: E402  只用标准库，可在 setup 之前导入
from lib.errors import BatchError  # noqa: E402


def libs():
    """依赖装在用户目录里；环境没准备好就提示先 setup。"""
    from lib import setup
    if not setup.is_ready():
        print("环境还没准备好（或 skill 已更新），先运行：python scripts/vb.py setup")
        sys.exit(2)
    sys.path.insert(0, str(PYDEPS))
    from lib import episode, media, render, tts
    return episode, media, render, tts


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def timing_warnings(tl):
    out = []
    st = tl["stats"]
    lo, hi = BODY_RANGE
    if not lo <= st["body"] <= hi:
        out.append(f"正文 {st['body']:.1f}s，建议 {lo:.0f}–{hi:.0f}s")
    lo, hi = TOTAL_RANGE
    if not lo <= st["total"] <= hi:
        out.append(f"总长 {st['total']:.1f}s，建议 {lo:.0f}–{hi:.0f}s")
    if st["interp"]:
        out.append(f"这些学习项没拿到 TTS 时间戳，高亮时间是估算的：{', '.join(st['interp'])}")
    return out


def print_report(ep, errors, warnings, tl=None):
    head = f"[{ep['id']}] {ep.get('title', '')}"
    if tl:
        st = tl["stats"]
        est = "≈" if tl["estimated"] else ""
        head += f"  学习项 {len(tl['items'])}｜正文 {est}{st['body']:.1f}s｜复习 {est}{st['review']:.1f}s｜总长 {est}{st['total']:.1f}s"
    print(head)
    for e in errors:
        print(f"  ✗ {e}")
    for w in warnings:
        print(f"  ! {w}")


def batch_dir(path, out=None):
    return (Path(out).resolve() if out else path.parent) / path.stem


def write_review(root, path, eps, restore):
    """对照稿：每段正文旁边放「还原中文」（英文换回释义），给人或 AI 审稿用。"""
    lines = [f"# {path.name} 对照稿\n",
             "「还原」是把正文里的英文换成释义后的纯中文：它必须通顺自然，没有被英文释义误导的歧义。\n"]
    for ep, errors, _ in eps:
        if errors:
            continue
        lines += [f"## [{ep['id']}] {ep['title']}", "",
                  "学习项：" + " · ".join(f"{it['en']} {it['pos']} {it['gloss']}".replace("  ", " ") for it in ep["items"]), ""]
        for n, p in enumerate(ep["pages"], 1):
            lines += [f"### 第 {n} 段", f"- 正文：{p['text'].strip()}", f"- 还原：{restore(p, ep['items'])}", ""]
    root.mkdir(parents=True, exist_ok=True)
    out = root / "review.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ---------- 命令 ----------

def cmd_setup(args):
    from lib import setup
    return setup.setup(upgrade=args.upgrade)


def cmd_words(args):
    episode, *_ = libs()
    for q in args.query:
        rows = episode.find_words(q, args.level)
        print(f"# {q}" + (f"（{args.level}）" if args.level else ""))
        if not rows:
            print("  查不到")
        for r in rows:
            first = [x.strip() for x in (r["translation"] or "").split("\n") if x.strip()][:3]
            print(f"  {r['word']}  /{r['phonetic'] or ''}/  [{r['tag'] or '无级别'}]  " + " | ".join(first))
    return 0


def cmd_check(args):
    episode, _, _, tts = libs()
    path, eps = episode.load_episodes(args.file, args.only)
    bad = 0
    for ep, errors, warnings in eps:
        tl = None if errors else tts.assemble(ep, estimated=True)[0]
        print_report(ep, errors, warnings + (timing_warnings(tl) if tl else []), tl)
        bad += bool(errors)
    print(f"\n共 {len(eps)} 期，{len(eps) - bad} 期可以生成" + (f"，{bad} 期有 ✗ 必须修" if bad else ""))
    print(f"对照稿 → {write_review(batch_dir(path, args.out), path, eps, episode.restore)}")
    return 1 if bad else 0


def cmd_stills(args):
    episode, _, render, tts = libs()
    path, eps = episode.load_episodes(args.file, args.only)
    root = batch_dir(path, args.out)
    jobs = []
    for ep, errors, warnings in eps:
        if errors:
            print_report(ep, errors, warnings)
            continue
        tl, _ = tts.assemble(ep, estimated=True)
        print_report(ep, [], warnings + timing_warnings(tl), tl)
        d = root / ep["id"] / "stills"
        for name, t in render.key_times(tl):
            jobs.append({"kind": "still", "composition": "Episode", "props": tl,
                         "frame": render.frame_at(tl, t), "out": str(d / f"{name}.png")})
        jobs.append({"kind": "still", "composition": "Cover", "props": tl, "frame": 0, "out": str(d / "cover.png")})
    render.run_jobs(jobs)
    if jobs:
        print(f"\n静帧（估算时间轴，非成片截图）→ {root}/<id>/stills/")
    return 0


def cmd_build(args):
    episode, media, render, tts = libs()
    path, eps = episode.load_episodes(args.file, args.only)
    root = batch_dir(path, args.out)
    tpl = render.template_hash()
    render.clear_audio()
    jobs, pending, rows = [], [], []

    for ep, errors, warnings in eps:
        d = root / ep["id"]
        if errors:
            print_report(ep, errors, warnings)
            rows.append({"id": ep["id"], "title": ep.get("title", ""), "status": "✗ 校验未通过", "errors": errors,
                         "warnings": warnings})
            continue
        save_json(d / "episode.json", ep)

        tl_path, audio = d / "timeline.json", d / "audio.wav"
        old = json.loads(tl_path.read_text(encoding="utf-8")) if tl_path.exists() else None
        if not args.force and old and old.get("hash") == tts.audio_hash(ep) and audio.exists():
            tl = old
        else:
            tl, pcm = tts.assemble(ep)
            voice = d / "voice.wav"
            with wave.open(str(voice), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(SR)
                w.writeframes(pcm)
            media.loudnorm(voice, audio)
            voice.unlink()
            save_json(tl_path, tl)
        warnings = warnings + timing_warnings(tl)
        print_report(ep, [], warnings, tl)
        row = {"id": ep["id"], "title": ep["title"], "stats": tl["stats"], "items": len(tl["items"]),
               "warnings": warnings, "status": "配音完成", "audio": str(audio)}
        rows.append(row)
        if args.no_video:
            continue

        key = f"{tl['hash']}-{tpl}"
        done = d / "render.json"
        video = d / "video.mp4"
        if not args.force and video.exists() and done.exists() and json.loads(done.read_text()).get("key") == key:
            row.update(status="✓ 成片（未变化，跳过渲染）", video=str(video), cover=str(d / "cover.png"))
            continue
        props = {**tl, "audioSrc": render.stage_audio(f"{root.name}__{ep['id']}", audio)}
        jobs.append({"kind": "video", "composition": "Episode", "props": props, "out": str(video),
                     "concurrency": args.concurrency or render.default_concurrency()})
        jobs.append({"kind": "still", "composition": "Cover", "props": props, "frame": 0, "out": str(d / "cover.png")})
        pending.append((d, tl, key, row))

    if jobs:
        print(f"\n开始渲染 {len(pending)} 期 …")
        render.run_jobs(jobs)
    for d, tl, key, row in pending:
        save_json(d / "render.json", {"key": key})
        row.update(status=f"✓ 成片 {tl['durationInFrames'] / tl['fps']:.1f}s", video=str(d / "video.mp4"),
                   cover=str(d / "cover.png"))
    render.clear_audio()

    write_summary(root, path, rows)
    save_json(root / "result.json", {"file": str(path), "out": str(root), "episodes": rows})
    print(f"\n汇总 → {root / 'summary.md'}")
    return 1 if any(r["status"].startswith("✗") for r in rows) else 0


def write_summary(root, path, rows):
    lines = [f"# {path.name} 生成汇总\n", "| id | 标题 | 学习项 | 正文 | 复习 | 总长 | 状态 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        st = r.get("stats") or {}

        def fmt(k):
            return f"{st[k]:.1f}s" if k in st else "-"
        lines.append(f"| {r['id']} | {r['title']} | {r.get('items', '-')} | {fmt('body')} | {fmt('review')} "
                     f"| {fmt('total')} | {r['status']} |")
    for r in rows:
        notes = [f"- ✗ {e}" for e in r.get("errors", [])] + [f"- ! {w}" for w in r.get("warnings", [])]
        if notes:
            lines += ["", f"## {r['id']} {r['title']}", "", *notes]
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vb.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("setup", help="准备运行环境")
    p.add_argument("--upgrade", action="store_true", help="强制重装 Python 和 npm 依赖")

    p = sub.add_parser("words", help="查词")
    p.add_argument("query", nargs="+", help="英文单词（精确，查不到按前缀）或中文释义关键词")
    p.add_argument("--level", help="只看某级别词表：高考 / CET-4 / CET-6 / 考研 / 雅思 / 托福；不写则不限")

    for name in ("check", "stills", "build"):
        p = sub.add_parser(name)
        p.add_argument("file", help="文案 YAML 文件路径")
        p.add_argument("--only", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                       help="只处理这些 id，逗号分隔")
        p.add_argument("--out", help="产物根目录，默认放在文案文件旁边")
        if name == "build":
            p.add_argument("--force", action="store_true", help="忽略缓存，重新配音和渲染")
            p.add_argument("--no-video", action="store_true", help="只配音，不渲染")
            p.add_argument("--concurrency", type=int, help="Remotion 渲染并发数，默认 CPU 核数一半")
    args = ap.parse_args(argv)

    handlers = {"setup": cmd_setup, "words": cmd_words, "check": cmd_check, "stills": cmd_stills, "build": cmd_build}
    try:
        return handlers[args.cmd](args)
    except BatchError as e:
        print(f"✗ {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
