# 批量生成中英混读单词视频

用 AI 一次写一批文案到 `batch/scripts/<名字>.yaml`，再用脚本批量配音、渲染。不依赖工作台，也不依赖 `episodes/`。

## 准备

项目根目录先跑过 `scripts/setup.sh`（`.venv`、`data/ecdict.db`），然后：

```bash
batch/setup.sh
```

## 命令

```bash
batch/vb check  example      # 解析 + 校验 + 估算时长（不联网，几秒）
batch/vb stills example      # 按估算时间轴渲染质检静帧和封面（不联网，每张约 1 秒）
batch/vb build  example      # 校验 → 配音 → 渲染成片和封面 → 抽帧 → 汇总
```

- 文件名可以写路径，也可以只写 `batch/scripts/` 下的文件名。
- `--only id1,id2` 只处理部分期；`build --force` 忽略缓存；`build --no-video` 只配音。
- `build` 有缓存：文案和音色没变就不重新配音；时间轴和 `video/src` 模板都没变就不重新渲染。改模板后直接重跑，会重新渲染整批。
- `build` 需要联网（edge-tts）。

产物在 `batch/out/<文件名>/`：

| 文件 | 说明 |
|---|---|
| `summary.md` | 整批汇总：时长、状态、所有 ✗ 和 ! |
| `<id>/video.mp4`、`<id>/cover.png` | 成片、封面 |
| `<id>/frames/` | 成片质检帧：第一帧、每段读完、每组复习读完、结尾全文帧 |
| `<id>/stills/` | `stills` 命令的静帧（估算时间，不是成片截图） |
| `<id>/timeline.json`、`audio.wav` | 时间轴和配音，由脚本生成，不要手改 |

`✗` 必须修，否则这一期不生成；`!` 是提醒，照常生成。

## 文案格式

```yaml
defaults:                 # 可选，对整批生效，每期也可以单独覆盖
  level: 考研             # 高考 / CET-4 / CET-6 / 考研 / 雅思 / 托福
  series: 中英混读单词     # 左上角系列名
  source: 出自考研真题     # 纸张右下角的出处小字
  # voice: zh-CN-XiaoxiaoNeural   正文音色；review_voice 复习英文音色（默认 en-US-AriaNeural）
  # rate: "+5%"

episodes:
  - id: search-illusion   # 可选，默认 01、02…；用作输出目录名
    vol: "005"            # 可选，左上角 Vol. 徽章
    title: 搜到答案，就算懂了吗？
    cover: [搜到答案，, 就算懂了吗？]     # 可选，封面大标题分行，默认用 title
    pages:                # 全文一页显示完；这里的每一段是朗读单位，读到时由暗变亮
      - 搜到一篇explanation，就以为懂了？have access to资料，不等于掌握知识。
      - 怎么evaluate？隔一会儿，不看原文，试着recall。
    items:                # 学习项：[英文, 词性, 语境释义]；短语的词性写「短语」
      - [explanation, n., 解释]
      - [have access to, 短语, 能够获取]
      - [evaluate, v., 评估]
      - [recall, v., 回忆]
```

- 正文里直接写中英混读，英文前后不加空格、不加标记。连续英文会自动匹配学习项；屈折变化（recalled、had access to）自动认出，查不到的词形可在学习项第 4 位写出：`[recall, v., 回忆, [recalled]]`。
- 正文里不属于学习项的英文会原样显示、不高亮，校验时给提醒。
- 复习顺序就是 `items` 的顺序，建议和正文出现顺序一致。
- 音标、音节、高亮颜色由脚本补全，不要写。
- YAML 注意：`text` 不要以 `[`、`{`、`#` 开头；含英文冒号加空格（`: `）的内容要加引号。

## 给 AI 的写稿提示词

把下面这段连同上面的「文案格式」一起发给 AI：

> 按下面的格式写 N 期中英混读单词短视频文案，输出一个 YAML 文件。受众是大学生和考研学习者，level 统一为「考研」。
> 1. 内容取材于考研英语真题阅读常见的话题和观点（教育、科技、社会、心理、经济等）。先写出一段不插英文也值得读的中文，再挑 8–10 个考研词汇或短语自然放进去，短语算一个学习项。不要先抽词再硬编。
> 2. 每期 5–7 段，每段 1–2 句；全文约 120–150 个汉字（全文要在一屏内放下），第一句就进入正文。正文朗读约 30–40 秒。
> 3. 释义用这篇文章语境下的意思，不超过 8 个字，符合词典义项。避开 record、present 这类多音词。
> 4. 不写来源字段，统一用默认的「出自考研真题」。
> 5. 中文用全角标点。每期主题不同。

## 调整效果

| 想改的 | 位置 |
|---|---|
| 节奏（页间停顿、复习间隔、结尾停留） | `batch/config.py` 的 `PAGE_GAP`、`ITEM_GAP`、`OVERVIEW_HOLD` 等 |
| 字号、行距、字号自适应范围 | `batch/video/src/theme.ts` 的 `TEXT`（全文按纸张大小在 min–max 倍之间取最大能放下的字号） |
| 标题、卡片、纸张的位置 | `batch/video/src/theme.ts` 的 `LAYOUT` |
| 校验阈值（学习项数、时长、全文字数） | `batch/config.py` |
| 配色、字体 | `batch/video/src/theme.ts` |
| 版式和动画 | `batch/video/src/`：`Reading`（正文）、`Review`（词卡复习）、`Overview`（全文帧）、`Cover`（封面） |

改模板后先 `batch/vb stills <文件>` 看静帧，满意再 `build`。`cd batch/video && npm run studio` 可以交互预览（示例数据在 `src/sample.json`）。
