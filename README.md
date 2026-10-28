# english-word-video

WorkBuddy skill：把一段文字或一个主题做成竖屏「中英混读单词」短视频（配音、高亮注释、词卡复习、封面）。

本仓库根目录就是 skill 根目录，入口是 [SKILL.md](SKILL.md)。

```
SKILL.md              skill 定义与工作流（AI 读这个）
references/           写稿规范、文案格式与常见问题
scripts/vb.py         唯一命令行入口：setup / words / check / stills / build
scripts/vb_*.py       校验、配音（edge-tts）、渲染调度
scripts/ecdict-lite.db  内置词库（ECDICT 精简版）
templates/            画面模板（Remotion 源码）、内置字体、example.yaml 示例文案
```

## 本地试用

```bash
python scripts/vb.py setup                    # 首次：装依赖、下载浏览器（约 300MB）
python scripts/vb.py check  templates/example.yaml
python scripts/vb.py stills templates/example.yaml
python scripts/vb.py build  templates/example.yaml
```

要求 Python 3.9+、Node.js 18+，配音需要联网。Windows 用 `python` 或 `py -3`。依赖装在 `~/.english-word-video/`（`EWV_HOME` 可改），不会写入仓库。

## 发布

**开放平台限制：包内只能是「根目录/二级目录/文件」两级**，所以只有 `references/`、`scripts/`、`templates/` 三个子目录，里面不能再有目录（Python 模块、Remotion 模板都是平铺的）。新增文件时别建子目录。

先提交所有改动，再在仓库根目录打包（不含 `.git`、`.workbuddy`、`design/`、`AGENTS.md`、`.gitignore`）：

```bash
mkdir -p dist
EX="-- . :(exclude).workbuddy :(exclude)design :(exclude)AGENTS.md :(exclude).gitignore"
git archive --format=zip -9 --prefix=english-word-video/ -o dist/english-word-video.zip HEAD $EX   # 带一层技能目录
git archive --format=zip -9 -o dist/english-word-video-flat.zip HEAD $EX                           # SKILL.md 在压缩包根目录
```

当前约 2.0MB（上限 3MB，改字体或词库前先量一下）。先传第一个；如果平台提示找不到 SKILL.md 或目录层级，换第二个。

### 图标

`design/icon.html` 是 512×512 图标的源文件，字体复用模板里的内置字体。重新渲染（需先 `setup` 过，用到 Remotion 下载的 headless 浏览器）：

```bash
B=$(ls ~/.english-word-video/remotion/node_modules/.remotion/chrome-headless-shell/*/*/chrome-headless-shell)
"$B" --no-sandbox --hide-scrollbars --force-device-scale-factor=1 --allow-file-access-from-files --window-size=512,512 --virtual-time-budget=3000 --screenshot=dist/icon-512.png file://$PWD/design/icon.html
```
