# 中英混读单词视频流水线

本地脚本负责查词、校验、配音、渲染。批量生成是现在的主流程，见 `batch/README.md`。
文案规范见 `.cursor/rules/copywriting.mdc`。

## 批量生成

`batch/passages/<名字>.yaml` 放原文和逐句参考译文，`batch/scripts/<名字>.yaml` 放中英混读文案。
文案一行一段，学习词写成 `英文 (词性. 释义)`。换文案只改这个文件，然后 `batch/vb stills <名字>`，不用改画面代码。

| 命令 | 作用 |
|---|---|
| `batch/vb check <名字>` | 校验，并写对照稿 `batch/out/<名字>/review.md` |
| `batch/vb stills <名字>` | 按估算时间轴出静帧和封面 |
| `batch/vb build <名字>` | 配音并渲染到 `batch/out/<名字>/` |

格式、写稿提示词和调画面的位置见 `batch/README.md`。

## 旧版单期命令（在项目根目录运行）

| 命令 | 作用 |
|---|---|
| `./vv new` | 一键新建底稿：自动选题、选词、写三稿、生成 script.json |
| `./vv plan --level cet4 --theme "主题"` | 新建一期 `episodes/<id>/`，输出候选新词、到期复习词、最近几期 |
| `./vv words 减肥 奶茶 --level cet4` | 按中文释义或英文前缀查词（✓ 表示在该级别词表） |
| `./vv validate <id>` | 校验 `script.json`，结果写 `report.json`；有 ✗ 必须修 |
| `./vv tts <id>` | edge-tts 逐句配音，可用 `--voice`、`--rate` |
| `./vv qa-audio <id>` | 检查朗读时长（16–21s）、单词时间戳、异常静音 |
| `./vv render <id>` | Remotion 渲染 `out.mp4` + `cover.png` |
| `./vv frames <id>` | 抽 4 张关键帧到 `frames/`，供看图质检 |
| `./vv commit <id>` | 入库：在 `script.json` 写 `published_at`，重写 `data/published_scripts.md` |
| `./vv status` | 各期进度 |

`level` 可选：`gk cet4 cet6 ky ielts toefl`。
音色例如：`zh-CN-XiaoxiaoNeural`（默认）、`zh-CN-YunxiNeural`。语速默认 `+5%`。

## 目录

- `batch/`：批量流水线（文案、校验、配音、Remotion 模板）
- `pipeline/`：旧版单期 Python CLI（`.venv` 里运行）
- `video/`：旧版单期 Remotion 模板
- `data/`：词库缓存、选题库、范文、黑名单、已发布文案
- `episodes/<id>/`：旧版单期产物（`plan.json` → `drafts.md` → `script.json` → 配音/成片）
- `docs/`：部署说明、调研、设计稿

## 约定

- 批量文案只改 `batch/scripts/` 和 `batch/passages/`。`timeline.json` 由脚本生成，不要手改。
- 旧版单期：Agent 只写 `drafts.md` 和 `script.json`；`timeline.json`、`props.json` 由脚本生成。
- 学习进度不单独存库：已用词、复习调度从已入库的 `script.json`（有 `published_at`）推算。
- 音标、音节、颜色由脚本从 ECDICT 和 pyphen 补全，不要手写。
- 模板改动后先 `batch/vb stills <名字>` 出静帧确认，再 `build`。
- 需要联网的命令：配音（edge-tts）。首次渲染会下载 Chrome Headless Shell。
