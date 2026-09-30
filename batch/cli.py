"""批量生成中英混读单词视频。

  batch/vb check  <批量文件>            解析 + 校验 + 估算时长，不联网
  batch/vb stills <批量文件>            估算时间轴，渲染质检静帧和封面，不联网
  batch/vb build  <批量文件>            校验 → 配音 → 渲染成片和封面 → 抽帧 → 汇总

批量文件可以写路径，也可以只写 batch/scripts/ 下的文件名。产物在 batch/out/<文件名>/<id>/。
"""
import argparse
import json
import sys
import wave

from . import media, render, tts
from .config import BODY_RANGE, OUT, SR, TOTAL_RANGE
from .episode import BatchError, load_episodes


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


def batch_dir(path):
    return OUT / path.stem


def cmd_check(args):
    path, eps = load_episodes(args.file, args.only)
    bad = 0
    for ep, errors, warnings in eps:
        tl = None if errors else tts.assemble(ep, estimated=True)[0]
        print_report(ep, errors, warnings + (timing_warnings(tl) if tl else []), tl)
        bad += bool(errors)
    print(f"\n共 {len(eps)} 期，{len(eps) - bad} 期可以生成" + (f"，{bad} 期有 ✗ 必须修" if bad else ""))
    return 1 if bad else 0


def cmd_stills(args):
    path, eps = load_episodes(args.file, args.only)
    jobs = []
    for ep, errors, warnings in eps:
        if errors:
            print_report(ep, errors, warnings)
            continue
        tl, _ = tts.assemble(ep, estimated=True)
        print_report(ep, [], warnings + timing_warnings(tl), tl)
        d = batch_dir(path) / ep["id"] / "stills"
        for name, t in render.key_times(tl):
            jobs.append({"kind": "still", "composition": "Episode", "props": tl,
                         "frame": render.frame_at(tl, t), "out": str(d / f"{name}.png")})
        jobs.append({"kind": "still", "composition": "Cover", "props": tl, "frame": 0, "out": str(d / "cover.png")})
    render.run_jobs(jobs)
    if jobs:
        print(f"\n静帧（估算时间轴，非成片截图）→ {batch_dir(path)}/<id>/stills/")
    return 0


def cmd_build(args):
    path, eps = load_episodes(args.file, args.only)
    root = batch_dir(path)
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
            save_json(tl_path, tl)
        warnings = warnings + timing_warnings(tl)
        print_report(ep, [], warnings, tl)
        save_json(d / "report.json", {"errors": [], "warnings": warnings, "stats": tl["stats"]})
        row = {"id": ep["id"], "title": ep["title"], "stats": tl["stats"], "items": len(tl["items"]),
               "warnings": warnings, "status": "配音完成"}
        rows.append(row)
        if args.no_video:
            continue

        key = f"{tl['hash']}-{tpl}"
        done = d / "render.json"
        video = d / "video.mp4"
        if not args.force and video.exists() and done.exists() and json.loads(done.read_text()).get("key") == key:
            row["status"] = "✓ 成片（未变化，跳过渲染）"
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
        render.extract_frames(d / "video.mp4", tl, d / "frames")
        save_json(d / "render.json", {"key": key})
        row["status"] = f"✓ 成片 {media.duration(d / 'video.mp4'):.1f}s"
    render.clear_audio()

    write_summary(root, path, rows)
    print(f"\n汇总 → {root / 'summary.md'}")
    return 1 if any(r["status"].startswith("✗") for r in rows) else 0


def write_summary(root, path, rows):
    lines = [f"# {path.name} 生成汇总\n", "| id | 标题 | 学习项 | 正文 | 复习 | 总长 | 状态 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        st = r.get("stats") or {}
        fmt = lambda k: f"{st[k]:.1f}s" if k in st else "-"
        lines.append(f"| {r['id']} | {r['title']} | {r.get('items', '-')} | {fmt('body')} | {fmt('review')} "
                     f"| {fmt('total')} | {r['status']} |")
    for r in rows:
        notes = [f"- ✗ {e}" for e in r.get("errors", [])] + [f"- ! {w}" for w in r.get("warnings", [])]
        if notes:
            lines += ["", f"## {r['id']} {r['title']}", "", *notes]
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="batch/vb", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "stills", "build"):
        p = sub.add_parser(name)
        p.add_argument("file", help="批量文案文件（路径或 batch/scripts/ 下的文件名）")
        p.add_argument("--only", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                       help="只处理这些 id，逗号分隔")
        if name == "build":
            p.add_argument("--force", action="store_true", help="忽略缓存，重新配音和渲染")
            p.add_argument("--no-video", action="store_true", help="只配音，不渲染")
            p.add_argument("--concurrency", type=int, help="Remotion 渲染并发数，默认 CPU 核数一半")
    args = ap.parse_args(argv)
    try:
        return {"check": cmd_check, "stills": cmd_stills, "build": cmd_build}[args.cmd](args)
    except BatchError as e:
        print(f"✗ {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
