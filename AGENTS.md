# 荧光笔手帐 · 中英混读单词视频流水线

一句话出一期竖屏单词短视频：Agent 写文案和做判断，本地脚本负责查词、校验、配音、渲染。
人也可以在工作台逐步操作。流程见 `.cursor/skills/vocab-video/SKILL.md`，文案规范见 `.cursor/rules/copywriting.mdc`，
整体设计见 `docs/中英混读单词视频-技术调研.md`。

## 命令（在项目根目录运行）

| 命令 | 作用 |
|---|---|
| `./vv serve` | 打开工作台（选题、写稿、选音色、预览、配音、渲染、词库管理） |
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

## 批量生成（新版，内容先行）

`batch/` 是独立的批量流水线：真题原文和逐句参考译文放 `batch/passages/<名字>.yaml`，AI 把参考译文按段落压缩成几期、嵌入原文单词写进 `batch/scripts/<名字>.yaml`，
`batch/vb check|stills|build <名字>` 校验、出静帧、配音并渲染到 `batch/out/<名字>/`。
格式、写稿提示词和调参位置见 `batch/README.md`。上面的 `./vv` 命令是旧版单期流程。

## 目录

- `pipeline/`：Python CLI 和工作台 API（`.venv` 里运行）
- `workbench/`：可视化工作台（Vite + React）
- `video/`：Remotion 模板，`video/src/MarkerNotes/`；`npm run studio` 可预览
- `data/`：词库缓存、选题库、范文、黑名单、已发布文案
- `episodes/<id>/`：每期产物（`plan.json` → `drafts.md` → `script.json` → 配音/成片）
- `docs/`：部署说明、调研、设计稿

## 约定

- Agent 只写 `drafts.md` 和 `script.json`；`timeline.json`、`props.json` 由脚本生成，不要手改。
- 学习进度不单独存库：已用词、复习调度从已入库的 `script.json`（有 `published_at`）推算。
- 音标、音节、颜色由脚本从 ECDICT 和 pyphen 补全，不要手写。
- 模板改动后先用 `npx remotion still` 出单帧确认，再批量渲染。
- 需要联网的命令：`tts`（edge-tts）。首次 `render` 会下载 Chrome Headless Shell。
