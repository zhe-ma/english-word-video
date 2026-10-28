---
name: english-word-video
display_name: 中英混读单词视频
display_name_en: English Word Video Maker
description: 把一段文字或一个主题做成竖屏「中英混读单词」短视频（1080x1920，含配音、高亮注释、词卡复习和封面）。当用户要求做单词视频、背单词短视频、中英混读视频、雅思/考研/四六级词汇视频、把文章或一段话做成学英语短视频，或给了主题让 AI 写文案并出视频时使用。
description_zh: 输入一段文字或主题，自动写成中英混读文案、配音并渲染成竖屏单词短视频和封面。
description_en: Turn a passage or a topic into a vertical Chinese-English mixed-reading vocabulary video with voiceover, highlighted annotations, flashcard review and cover image.
examples_zh:
  - "把这段话做成一条雅思单词短视频：……"
  - "帮我写一条吐槽周一通勤的单词视频，用雅思词汇"
  - "这篇文章太长了，拆成 3 期考研单词视频"
examples_en:
  - "Turn this paragraph into an IELTS vocabulary short video"
  - "Write and render a funny Monday-commute vocabulary video"
  - "Split this long article into 3 vocabulary episodes"
version: 1.0.0
author: 马哲
---

# 中英混读单词视频

正文以中文叙述，5–7 个英文学习词原位嵌入句子，配音读到时高亮并在词下方显示「词性 + 释义」，结尾逐个复习词卡。输出 1080×1920 竖屏 mp4 和封面 png，约 40–70 秒。

你负责**写文案**，脚本负责**校验、配音、渲染**。脚本不会替你写稿，也不会翻译。

`<SKILL_DIR>` 指本文件所在目录。命令统一写成 `python scripts/vb.py …`（在 `<SKILL_DIR>` 下运行；macOS / Linux 用 `python3`，Windows 用 `python` 或 `py -3`）。路径含空格要加引号。

## 开始之前

- 需要本机已装 **Python 3.9+** 和 **Node.js 18+**，配音要能访问 `speech.platform.bing.com`（edge-tts，免费、无需 key）。
- 首次使用要先 `setup`，会下载约 300MB（npm 依赖和渲染用浏览器），耗时 2–5 分钟。**运行前先告诉用户**。装好后再次运行立即返回。
- 所有依赖和缓存放在 `~/.english-word-video/`，skill 目录不会被写入。

## 流程

按顺序做，不要跳步。

### 1. 弄清要做什么

| 用户给了 | 你做 |
|---|---|
| 一段文字（文章、笔记、短文） | 以它为素材改写。内容只来自原文，不添加原文没有的信息。篇幅长就拆成多期 |
| 只有主题 | 自己写一条有共鸣的短文案 |
| 已写好的 yaml | 跳到第 3 步 |

缺少信息时才问，不要一上来盘问。默认值：词汇等级「雅思」，一期一条视频。需要确认的只有：用户是否指定了等级（高考 / CET-4 / CET-6 / 考研 / 雅思 / 托福）、栏目名（画面左上角）。

### 2. 准备环境

```bash
python scripts/vb.py setup
```

失败时看 @references/script-format.md 的「常见问题」。

### 3. 写文案

在当前工作目录建 `vocab-video/<名字>.yaml`。**先读 @references/copywriting.md**，格式见 @references/script-format.md，可参考 `examples/sample.yaml`。

核心要求：

- 每期 3–6 段，全文约 150–200 个汉字，一屏手机放得下；5–7 个学习词。
- 学习词写成 `英文 (词性. 释义)`，释义必须是被换掉的那个中文词。
- 选词前可以用 `python scripts/vb.py words <英文或中文> --level 雅思` 核对词典义项和级别。

### 4. 校验

```bash
python scripts/vb.py check vocab-video/<名字>.yaml
```

- `✗` 必须修，否则这一期不生成；`!` 是提醒，判断后决定改不改。
- 读 `vocab-video/<名字>/review.md` 里每段的「还原」（英文换回释义后的纯中文）：必须通顺，意思不能被改。有问题就改 yaml，再 check，直到干净。

### 5. 看静帧

```bash
python scripts/vb.py stills vocab-video/<名字>.yaml
```

用看图能力检查 `vocab-video/<名字>/<id>/stills/` 里的 `cover.png`、`01-first.png`、最后一张 `02-page*.png`、`03-review1.png`：文字有没有溢出卡片、注释有没有互相遮挡、换行是否别扭。有问题回第 3 步缩短文案。静帧只用估算时间，不联网。

### 6. 出片

```bash
python scripts/vb.py build vocab-video/<名字>.yaml
```

配音和渲染需联网，一期约 1 分钟。结果写在 `vocab-video/<名字>/result.json`，每期有 `video`、`cover` 的绝对路径。

- 只重跑某一期：加 `--only <id>`。强制重做：加 `--force`。
- 文案没变不会重新配音；改了文案只重配改动的部分。

### 7. 交付

用 `present_files` 交付每期的 `video.mp4` 和 `cover.png`（mp4 在前）。回复里写清：做了几期、每期时长、学习词列表，以及仍存在的 `!` 提醒。

## 原则

- **忠实**：用户给了素材就不编造事实、人名、数据。拿不准的内容告诉用户，不要凭记忆补全。
- **自查再交付**：没做 check 和还原检查，不要 build。
- **不改模板**：画面样式固定。用户要改风格或版式，说明目前不支持，不要去改 `templates/`。
- **不手改产物**：`timeline.json`、`audio.wav` 由脚本生成。
- 文案、说明一律用用户的语言（默认中文）。

## 目录

```
SKILL.md              本文件
references/           写稿规范、文案格式与常见问题
scripts/vb.py         唯一入口：setup / words / check / stills / build
scripts/lib/          校验、配音、渲染逻辑
scripts/data/         内置词库（ECDICT 精简版，MIT）
templates/remotion/   画面模板（Remotion）与内置字体（OFL）
examples/sample.yaml  示例文案
```
