# 荧光笔手帐 · 中英混读单词视频流水线

一句话出一期竖屏单词短视频：Agent 写文案和做判断，本地脚本负责查词、校验、配音、渲染。
流程细节见 `.cursor/skills/vocab-video/SKILL.md`，文案规范见 `.cursor/rules/copywriting.mdc`，
整体设计见 `中英混读单词视频-技术调研.md`。

## 命令（在项目根目录运行）

| 命令 | 作用 |
|---|---|
| `./vv plan --level cet4 --theme "主题"` | 新建一期 `episodes/<id>/`，输出候选新词、到期复习词、最近几期 |
| `./vv words 减肥 奶茶 --level cet4` | 按中文释义或英文前缀查词（✓ 表示在该级别词表） |
| `./vv validate <id>` | 校验 `script.json`，结果写 `report.json`；有 ✗ 必须修 |
| `./vv tts <id>` | edge-tts 逐句配音，生成 `audio.wav` + `timeline.json` |
| `./vv qa-audio <id>` | 检查朗读时长（16–21s）、单词时间戳、异常静音 |
| `./vv render <id>` | Remotion 渲染 `out.mp4` + `cover.png` |
| `./vv frames <id>` | 抽 4 张关键帧到 `frames/`，供 Agent 看图质检 |
| `./vv commit <id>` | 入库：记录已用词，文案追加到 `data/published_scripts.md` |
| `./vv status` | 各期进度 |

`level` 可选：`gk cet4 cet6 ky ielts toefl`。

## 目录

- `pipeline/`：Python CLI（`.venv` 里运行，依赖 edge-tts、pyphen）
- `video/`：Remotion 工程，模板在 `video/src/MarkerNotes/`；`npm run studio` 可预览
- `data/`：`ecdict.db` 词库、`progress.db` 学习记录、`themes.yaml` 选题库、`hall_of_fame.md` 范文、`banned_phrases.txt` 黑名单
- `episodes/<id>/`：每期产物（`plan.json` → `drafts.md` → `script.json` → `timeline.json` → `out.mp4`）
- `design/mockup.html`：视觉设计稿

## 约定

- Agent 只写 `drafts.md` 和 `script.json`；`timeline.json`、`props.json` 由脚本生成，不要手改。
- 音标、音节、颜色由脚本从 ECDICT 和 pyphen 补全，不要手写。
- 模板改动后先用 `npx remotion still` 出单帧确认，再批量渲染。
- 需要联网的命令：`tts`（edge-tts）。首次 `render` 会下载 Chrome Headless Shell。
