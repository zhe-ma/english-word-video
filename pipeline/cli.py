import argparse
import sys

from .config import RATE, VOICE


def main():
    ap = argparse.ArgumentParser(prog="vv", description="荧光笔手帐单词视频流水线")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db", help="把 data/ecdict.csv 导入 data/ecdict.db")

    p = sub.add_parser("new", help="一键新建：自动选题、选词、写底稿")
    p.add_argument("--level", default="cet4")
    p.add_argument("--theme", default="")
    p.add_argument("--words", type=int, default=6)
    p.add_argument("--voice", default=VOICE)
    p.add_argument("--rate", default=RATE)
    p.add_argument("--ep", default=None, help="给已有期重做默认底稿")

    p = sub.add_parser("plan", help="新建一期，输出候选词")
    p.add_argument("--level", default="cet4")
    p.add_argument("--theme", default="")
    p.add_argument("--n", type=int, default=40, help="候选新词数量")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--ep", default=None, help="给已有的期重新抽候选词，不新建")

    p = sub.add_parser("words", help="按中文释义/英文前缀查词")
    p.add_argument("keywords", nargs="+")
    p.add_argument("--level", default="cet4")
    p.add_argument("--limit", type=int, default=15)

    for name, hlp in [("validate", "校验 script.json"), ("qa-audio", "检查配音"),
                      ("frames", "抽关键帧供质检"), ("commit", "入库：记录已用词和文案")]:
        sub.add_parser(name, help=hlp).add_argument("ep")

    p = sub.add_parser("tts", help="edge-tts 配音 + 生成 timeline.json")
    p.add_argument("ep")
    p.add_argument("--voice", default=VOICE)
    p.add_argument("--rate", default=RATE)

    p = sub.add_parser("render", help="Remotion 渲染 out.mp4 + cover.png")
    p.add_argument("ep")
    p.add_argument("--concurrency", type=int, default=None)
    p.add_argument("--no-cover", action="store_true")

    sub.add_parser("status", help="查看各期进度")

    p = sub.add_parser("serve", help="启动可视化工作台")
    p.add_argument("--port", type=int, default=8765, help="API 端口")
    p.add_argument("--ui-port", type=int, default=5173, help="前端端口")
    p.add_argument("--api-only", action="store_true", help="只启动 API，不启动前端")

    a = ap.parse_args()
    if a.cmd == "init-db":
        from . import lexicon
        lexicon.init_db()
    elif a.cmd == "new":
        from . import bootstrap
        r = bootstrap.run(a.level, a.theme, a.words, a.voice, a.rate, ep=a.ep)
        print(f"第 {r['id']} 期底稿已生成：{r['theme']}｜{r['genre']}｜{' '.join(r['picked'])}")
    elif a.cmd == "plan":
        from . import plan
        plan.run(a.level, a.theme, a.n, a.seed, a.ep)
    elif a.cmd == "words":
        from . import plan
        plan.search(a.keywords, a.level, a.limit)
    elif a.cmd == "validate":
        from . import validate
        sys.exit(validate.run(a.ep))
    elif a.cmd == "tts":
        from . import tts
        tts.run(a.ep, a.voice, a.rate)
    elif a.cmd == "qa-audio":
        from . import produce
        sys.exit(produce.qa_audio(a.ep))
    elif a.cmd == "render":
        from . import produce
        produce.render(a.ep, a.concurrency, not a.no_cover)
    elif a.cmd == "frames":
        from . import produce
        produce.frames(a.ep)
    elif a.cmd == "commit":
        from . import produce
        produce.commit(a.ep)
    elif a.cmd == "status":
        from . import produce
        produce.status()
    elif a.cmd == "serve":
        from . import server
        server.main(a.port, a.ui_port, not a.api_only)


if __name__ == "__main__":
    main()
