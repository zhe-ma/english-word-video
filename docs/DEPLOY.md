# 部署文档：荧光笔手帐单词视频工作流

本文说明如何在一台新机器上部署这条工作流，并在 Cursor 里一句话生产单词视频。
工作流设计见 `docs/中英混读单词视频-技术调研.md`，日常命令见 `AGENTS.md`。工作台：`./vv serve`。

---

## 1. 工作流概览

```
Cursor Agent 或工作台（./vv serve）
  ├─ ./vv plan / words        选题、查词（ECDICT 词库）
  ├─ 写 drafts.md → 毒舌评审子代理打分 → script.json
  ├─ ./vv validate            规则校验（Hook 在改完 script.json 后自动触发）
  ├─ ./vv tts / qa-audio      edge-tts 逐句配音（可选音色 / 语速）→ timeline.json
  ├─ ./vv render / frames     Remotion 渲染 out.mp4，抽帧质检
  └─ ./vv commit              script.json 写 published_at，重写 published_scripts.md
```

| 组件 | 技术 | 位置 |
|---|---|---|
| 流水线 CLI / API | Python 3.10+（edge-tts、pyphen） | `pipeline/`，入口 `./vv` |
| 工作台 | Vite + React | `workbench/`，`./vv serve` |
| 视频模板 | Remotion 4 + React 18（Node 18+） | `video/` |
| 词库 | ECDICT（MIT） | `data/ecdict.csv` → `data/ecdict.db`（本机缓存，不进 git） |
| 学习进度 | 已入库的 `episodes/*/script.json` | 有 `published_at` 即入库 |
| Agent 配置 | Cursor Skill / Rule / Hook | `.cursor/`、`AGENTS.md` |
| 字体 | 思源黑体 Noto Sans SC、Poppins（OFL） | `video/public/fonts/` |

不需要 GPU，也不需要任何付费 API。文案由 Cursor Agent 写，消耗的是 Cursor 订阅额度。

---

## 2. 环境要求

### 2.1 系统和软件

| 依赖 | 版本 | macOS | Ubuntu / Debian |
|---|---|---|---|
| Python | ≥ 3.10 | `brew install python@3.12` | `sudo apt install python3 python3-venv` |
| Node.js | ≥ 18（已在 20 上验证） | `brew install node@20` | 用 [nvm](https://github.com/nvm-sh/nvm) 安装 20 |
| ffmpeg / ffprobe | 任意较新版本 | `brew install ffmpeg` | `sudo apt install ffmpeg` |
| jq | 任意 | 系统自带 | `sudo apt install jq` |
| curl、git | 任意 | 系统自带 | `sudo apt install curl git` |
| Cursor | 支持 Skills 和 Hooks 的版本 | — | — |

Linux 上 Remotion 的 Chrome Headless Shell 还需要一些系统库，缺库时渲染会报错：

```bash
sudo apt install -y libnss3 libdbus-1-3 libatk1.0-0 libgbm-dev libasound2 \
  libxrandr2 libxkbcommon-dev libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libcups2
```

### 2.2 硬件

- CPU：4 核以上。当前开发机（Intel Mac）渲染一条约 25 秒的 1080×1920 视频大约需要 1 分钟。
- 内存：8GB 以上。
- 磁盘：约 1.5GB（node_modules 约 400MB、Chrome 约 200MB、词库约 70MB、字体 17MB，另加每期约 15MB 产物）。

### 2.3 网络

| 用途 | 域名 | 何时需要 |
|---|---|---|
| 词库、字体 | `raw.githubusercontent.com` | 安装时 |
| Python 包 | `pypi.org` | 安装时 |
| npm 包 | `registry.npmjs.org` | 安装时 |
| Chrome Headless Shell | `storage.googleapis.com` 等 | 安装时（`npx remotion browser ensure`） |
| **edge-tts 配音** | `speech.platform.bing.com` | **每次配音时** |

国内网络访问 GitHub 较慢时，可以通过环境变量换镜像（见第 3 节）。

---

## 3. 一键安装

```bash
git clone <仓库地址> vocab-video && cd vocab-video
./scripts/setup.sh
```

脚本按顺序完成以下步骤，可以重复执行（已完成的步骤会跳过）：

1. 检查 Python、Node、ffmpeg、jq 等依赖和版本。
2. 创建 `.venv`，安装 `requirements.txt`。
3. `video/` 下执行 `npm ci`。
4. 下载 ECDICT（约 63MB），生成 `data/ecdict.db`。
5. 下载字体到 `video/public/fonts/`。
6. 下载 Remotion 用的 Chrome Headless Shell。
7. 冒烟测试：`./vv status`、渲染一帧模板到 `.cache/stills/setup-check.png`、测试 edge-tts 连通性。

参数和环境变量：

```bash
./scripts/setup.sh --force        # 重新下载词库和字体，重建 ecdict.db
./scripts/setup.sh --skip-check   # 跳过冒烟测试
PYTHON=python3.12 ./scripts/setup.sh
GH_RAW=https://<你的 GitHub raw 镜像> ./scripts/setup.sh
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
npm_config_registry=https://registry.npmmirror.com ./scripts/setup.sh
```

网络不稳定时下载会自动断点续传，最多重试 10 次。

---

## 4. 手动安装（脚本失败时逐步排查）

```bash
# 1. Python
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Remotion
cd video && npm ci && npx remotion browser ensure && cd ..

# 3. 词库
curl -L -o data/ecdict.csv https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv
./vv init-db                       # 输出“已导入 17737 个词”

# 4. 字体
mkdir -p video/public/fonts && cd video/public/fonts
B=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -LO $B/poppins/Poppins-ExtraBold.ttf
curl -LO $B/poppins/Poppins-SemiBold.ttf
curl -L -o NotoSansSC.ttf "$B/notosanssc/NotoSansSC%5Bwght%5D.ttf"   # 约 17MB
cd -

# 5. 权限
chmod +x vv .cursor/hooks/*.sh
```

字体下载失败时渲染不会中断，会自动回退到系统字体（macOS 苹方）。但 Linux 上没有中文字体会出现方块字，而且发布前应当使用可商用字体，所以字体最好下载完整。

---

## 5. 验证部署

```bash
./vv status                                   # 能列出期目录即可
./vv words 选择 推荐 --limit 5                 # 词库可查
cd video && npx remotion still src/index.ts MarkerNotes /tmp/check.png --frame=225 && cd ..
.venv/bin/edge-tts --text "测试 hello" --voice zh-CN-XiaoxiaoNeural --write-media /tmp/t.mp3
```

完整链路测试（不入库）：

```bash
mkdir -p .cache/ep_test
# 写一份 script.json（格式见 .cursor/skills/vocab-video/SKILL.md），然后：
./vv validate .cache/ep_test && ./vv tts .cache/ep_test && ./vv qa-audio .cache/ep_test
./vv render .cache/ep_test --no-cover && ./vv frames .cache/ep_test
```

---

## 6. 在 Cursor 中使用

1. 用 Cursor 打开项目根目录。
2. 确认配置已加载：
   - **Skill**：设置里能看到 `vocab-video`（来源：`.cursor/skills/vocab-video/SKILL.md`）。
   - **Rule**：`copywriting.mdc` 在编辑 `episodes/**/script.json` 和 `drafts.md` 时自动生效。
   - **Hook**：设置 → Hooks 里能看到 `afterFileEdit → .cursor/hooks/validate-script.sh`。
3. 对 Agent 说：

   ```
   做 1 期 CET-4 单词视频，主题：外卖选择困难症
   做 3 期考研单词视频，主题你从选题库里挑
   ```

   Agent 会按 Skill 走完“选词 → 3 稿 → 毒舌评审 → 校验 → 配音 → 渲染 → 看图质检 → 入库”，最后汇报成片路径。
4. Agent 执行 `tts`（联网）和 `render`（写 node_modules 缓存）时，如果被 Cursor 沙箱拦截，需要允许它在沙箱外运行。

### 无人值守（可选）

安装 [Cursor CLI](https://cursor.com/cli) 后，可以定时批量生产（参数以 `cursor-agent --help` 为准）：

```bash
cd /path/to/vocab-video
cursor-agent -p "按 vocab-video skill 做 3 期 CET-4 单词视频，主题从 data/themes.yaml 里挑未用过的"
```

- macOS 用 `launchd`，Linux 用 `crontab` 定时执行上面的命令。
- 第一次必须先在对话模式下跑通，确认各步骤的权限都已放行。
- 产物都在 `episodes/<id>/`，由人工终审后再发布。

---

## 7. 数据与迁移

| 文件 | 内容 | 是否在 git 里 | 迁移方式 |
|---|---|---|---|
| `data/published_scripts.md` | 由 commit 根据 script.json 重写 | 是 | 派生文件，冲突以 script.json 为准 |
| `data/themes.yaml`、`hall_of_fame.md`、`banned_phrases.txt` | 选题库、范文、黑名单 | 是 | 随仓库同步 |
| `episodes/<id>/plan.json`、`drafts.md`、`script.json` | 每期文本；入库后 script 带 `published_at` | 是 | 随仓库同步，这就是进度源 |
| `episodes/<id>/audio.wav`、`out.mp4`、`cover.png` 等 | 每期产物 | 否 | 需要时拷贝，或本机 `./vv tts` + `./vv render` |
| `data/ecdict.db` | 词库查询缓存 | 否 | `./vv init-db` 重建 |

**多台机器同时生产时**：只同步文本。期号看 `episodes/` 目录，已用词看各期 `published_at`。两台机器不要同时 `plan` 同一期号。

备份：

```bash
tar czf backup-$(date +%F).tgz data/published_scripts.md episodes/
```

---

## 8. 配置项

主要参数在 `pipeline/config.py`：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `VOICE` | `zh-CN-XiaoxiaoNeural` | edge-tts 音色，也可以用 `./vv tts <id> --voice zh-CN-YunxiNeural` 临时指定 |
| `RATE` | `+5%` | 语速 |
| `HANZI_RANGE` | 45–62 | 每篇汉字数 |
| `READING_RANGE` | 16–21 秒 | 朗读时长要求 |
| `LEVELS` | gk / cet4 / cet6 / ky / ielts / toefl | 按 ECDICT tag 过滤的词表 |
| `REVIEW_PASS` | 总分 ≥ 24，单项 ≥ 3，钩子和笑点 ≥ 4 | 评审过稿线 |

BGM：把一首免版权 mp3 放到 `video/public/bgm/`，`./vv tts` 会自动垫在人声下面（音量约 5%）。

视觉模板：`video/src/MarkerNotes/`。修改后用 `cd video && npm run studio` 实时预览。

---

## 9. 常见问题

| 现象 | 原因和处理 |
|---|---|
| `edge-tts 合成失败` / 超时 / 403 | 网络访问不到微软接口，或接口协议有变更。先检查网络和代理，再执行 `.venv/bin/pip install -U edge-tts`。edge-tts 是非官方接口，长期商用建议换成官方 TTS |
| `朗读时长 xx s，要求 16–21s` | 文案太长或太短。删字或加细节，也可以微调 `RATE` |
| `这些词没拿到 WordBoundary` | 时间戳由插值估算，一般可用。如果画面明显不同步，换个说法或换词后重新配音 |
| 渲染报 `Failed to launch browser` | Linux 缺系统库（见 2.1），或 Chrome 没下载成功：`cd video && npx remotion browser ensure` |
| 画面中文是方块 | 字体没下载完整：`./scripts/setup.sh --force`，或检查 `video/public/fonts/NotoSansSC.ttf` 是否约 17MB |
| GitHub 下载很慢或中断 | 设置代理（`https_proxy=...`）或 `GH_RAW` 镜像后重跑脚本；脚本支持断点续传 |
| `词库未初始化` | 执行 `./vv init-db`（需要先有 `data/ecdict.csv`） |
| Hook 没生效 | 确认 `.cursor/hooks/validate-script.sh` 有执行权限、`jq` 已安装；在 Cursor 的 Hooks 输出面板查看日志 |
| 期号冲突 | 两台机器同时 `plan` 导致。删掉其中一个未入库的期目录，同步后重新 `plan` |

---

## 10. 目录结构

```
.
├── AGENTS.md / README.md
├── vv                            # CLI 入口
├── pipeline/                     # Python CLI + 工作台 API
├── workbench/                    # 可视化工作台
├── video/                        # Remotion 模板
├── data/                         # 选题库、范文、黑名单、词库缓存
├── episodes/<id>/                # 每期文本与产物
├── docs/                         # 部署、调研、设计稿
└── scripts/setup.sh
```
