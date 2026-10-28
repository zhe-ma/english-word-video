# english-word-video

WorkBuddy skill：把一段文字或一个主题做成竖屏「中英混读单词」短视频（配音、高亮注释、词卡复习、封面）。

本仓库根目录就是 skill 根目录，入口是 [SKILL.md](SKILL.md)。

```
SKILL.md              skill 定义与工作流（AI 读这个）
references/           写稿规范、文案格式与常见问题
scripts/vb.py         唯一命令行入口：setup / words / check / stills / build
scripts/lib/          校验、配音（edge-tts）、渲染调度
scripts/data/         内置词库（ECDICT 精简版）
templates/remotion/   画面模板（Remotion）和内置字体
examples/sample.yaml  示例文案
```

## 本地试用

```bash
python scripts/vb.py setup                    # 首次：装依赖、下载浏览器（约 300MB）
python scripts/vb.py check  examples/sample.yaml
python scripts/vb.py stills examples/sample.yaml
python scripts/vb.py build  examples/sample.yaml
```

要求 Python 3.9+、Node.js 18+，配音需要联网。Windows 用 `python` 或 `py -3`。依赖装在 `~/.english-word-video/`（`EWV_HOME` 可改），不会写入仓库。

## 发布

压缩包只含 skill 本身，不含 `.git`、`.workbuddy`、`design/`。先提交所有改动，再在仓库根目录运行：

```bash
mkdir -p dist
git archive --format=zip -9 --prefix=english-word-video/ -o dist/english-word-video.zip HEAD -- . ':(exclude).workbuddy' ':(exclude)design'
```

当前约 2.0MB（WorkBuddy 上限 3MB，改字体或词库前先量一下）。包内是 `english-word-video/SKILL.md` 的目录结构，与开放平台文档的技能基础结构一致；如果平台解析失败，试试不带 `--prefix` 的版本（`SKILL.md` 放在压缩包根目录）。

### 图标

`design/icon.html` 是 512×512 图标的源文件，字体复用模板里的内置字体。重新渲染（需先 `setup` 过，用到 Remotion 下载的 headless 浏览器）：

```bash
B=$(ls ~/.english-word-video/remotion/node_modules/.remotion/chrome-headless-shell/*/*/chrome-headless-shell)
"$B" --no-sandbox --hide-scrollbars --force-device-scale-factor=1 --allow-file-access-from-files --window-size=512,512 --virtual-time-budget=3000 --screenshot=dist/icon-512.png file://$PWD/design/icon.html
```
