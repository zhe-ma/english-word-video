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

整个目录打成 zip（不含 `.git`、`.workbuddy`）即可，当前约 2.0MB（WorkBuddy 上限 3MB，改字体或词库前先量一下）。打包命令：`git ls-files | grep -v '^.workbuddy' | zip -9 ../english-word-video.zip -@`。`SKILL.md` 的 frontmatter 已按开放平台规范填写。
