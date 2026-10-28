# 文案格式与常见问题

## 文案文件

```yaml
defaults:                      # 可选；对所有期生效，单期里同名字段可覆盖
  level: CET-6                 # 可选：高考 / CET-4 / CET-6 / 考研 / 雅思 / 托福；不写 = 不限
  series: 每日一词              # 可选：画面左上角栏目名；不写则用「<level>单词」，level 也没写则用「中英混读单词」
  footer: 不熟悉的单词，评论区打出来   # 卡片下方的固定提示

episodes:
  - id: monday-1               # 输出目录名；只用字母、数字、短横线、下划线。不写则是 01、02…
    title: 周一早八，我的大脑还在加载    # 画面顶部标题，一行显示
    cover: [周一早八，, 我的大脑还在加载]  # 封面大标题，按行分开；不写则用 title
    text: |                    # 一行一段；学习词写成「英文 (词性. 释义)」
      周一闹钟响到第五遍，我的 motivation (n. 干劲) 还躺在被窝里跟自己 negotiate (v. 谈判)。
      地铁挤得像一场 competition (n. 竞赛)，我被 compress (v. 压缩) 成了一张照片。
```

- 括号只给脚本看，画面上不会出现在字的后面；正文在单词下方注两行小字：音标、「词性 + 第一条释义」。
- 更多释义用分号接在括号里，只出现在最后的词卡上：`(n. 低绩效；表现不佳)`。词卡还会补上词典里的其他义项。音标由脚本从词典补全，不用手写；词典里没有的词不显示音标。
- 词性写 `n` / `v` / `adj` / `adv`，短语写 `短语`。
- 空行会被忽略。括号用中英文均可：`(n. 干劲)` 或 `（n. 干劲）`。
- YAML 注意：含 `: ` 的值要加引号；`text` 用 `|` 块最稳。

### 可调字段（都写在 `defaults` 或单期里）

| 字段 | 默认 | 说明 |
|---|---|---|
| `level` | 空（不限） | 校验用：学习词的词典级别标注里没有它时提醒；也决定默认栏目名 |
| `series` | 自动 | 栏目名：「<level>单词」或「中英混读单词」 |
| `footer` | 不熟悉的单词，评论区打出来 | 卡片下方提示 |
| `voice` / `rate` | zh-CN-XiaoxiaoNeural / +5% | 正文中英混读的音色和语速 |
| `review_voice` / `review_rate` | en-US-AriaNeural / -10% | 复习段英文 |
| `gloss_voice` / `gloss_rate` | zh-CN-XiaoxiaoNeural / +0% | 复习段中文释义 |

常用中文音色：`zh-CN-XiaoxiaoNeural`（女，默认）、`zh-CN-YunxiNeural`（男）、`zh-CN-XiaoyiNeural`（女）。音色名必须是 edge-tts 支持的。

## 命令

| 命令 | 作用 | 联网 |
|---|---|---|
| `setup [--upgrade]` | 准备环境 | 首次需要 |
| `words <词…> [--level 考研]` | 查词：英文精确查（查不到按前缀），中文在释义里搜 | 否 |
| `check <文件> [--only id1,id2]` | 解析、校验、估算时长，写 `review.md` | 否 |
| `stills <文件> [--only …]` | 渲染静帧和封面（估算时间轴） | 否 |
| `build <文件> [--only …] [--force] [--no-video] [--concurrency N]` | 配音、渲染成片和封面 | 是 |

`check` / `stills` / `build` 可加 `--out <目录>` 改产物位置，默认放在文案文件旁边。

## 产物

`vocab-video/<名字>/`：

| 文件 | 说明 |
|---|---|
| `result.json` | 机器可读的结果：每期的状态、视频和封面绝对路径、提醒 |
| `summary.md` | 汇总表：时长、状态、所有 ✗ 和 ! |
| `review.md` | 对照稿（`check` 生成）：正文和「还原」逐段并排 |
| `<id>/video.mp4`、`<id>/cover.png` | 成片、封面 |
| `<id>/stills/` | 静帧（估算时间，不是成片截图） |
| `<id>/timeline.json`、`audio.wav` | 时间轴和配音，由脚本生成，不要手改 |

## 校验规则

`✗`（错误，这一期不生成）：缺标题；学习项重复；缺释义；学习项没有在正文出现；`id` 重复；`text` 里没有任何学习项。

`!`（提醒，照常生成）：学习项不在 5–7 个；释义超过 8 字；全文太长；中文段落里有半角标点；词典里查不到某个词；词库标注里没有目标等级；多音词；正文里有非学习项的英文；正文或总长超出建议区间。

## 常见问题

| 现象 | 处理 |
|---|---|
| `没有找到 Node.js` | Windows：`winget install OpenJS.NodeJS.LTS`；macOS：`brew install node`；或到 nodejs.org 下载，装完重开终端 |
| `setup` 卡在 npm | 设置镜像再试：`npm_config_registry=https://registry.npmmirror.com`（Windows PowerShell：`$env:npm_config_registry="…"`） |
| 浏览器下载失败 | 用本机 Chrome 或 Edge：设环境变量 `VB_BROWSER` 为它的可执行文件路径，再运行 `setup`（会跳过下载）。Windows 示例：`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| pip 装包慢 | 设置 `PIP_INDEX_URL`，如 `https://pypi.tuna.tsinghua.edu.cn/simple` |
| `edge-tts 合成失败` / 403 | 先 `setup --upgrade` 升级 edge-tts（微软服务端会更新校验）；再检查能否访问 `speech.platform.bing.com`，必要时配置代理 |
| 渲染失败 | 看上方 `[browser]` 日志；加 `--concurrency 1` 降低内存占用 |
| 学习词高亮时间不准 | `build` 输出里提到的「没拿到 TTS 时间戳」的词是按字数估算位置的，可接受；严重时换词或调整句子 |
| 想换位置存放依赖 | 设环境变量 `EWV_HOME` |
| 更新 skill 后提示重新 setup | 正常，再运行一次 `setup`，会同步新模板 |

## 词库来源与许可

- 词典：ECDICT（skywind3000/ECDICT，MIT），已精简为 `scripts/ecdict-lite.db`。
- 字体：Poppins、Noto Sans SC（SIL OFL 1.1，许可文件见 `templates/OFL-*.txt`），已裁剪为子集（中文只含 GB2312 一级常用字约 3700 个和常用标点，生僻字自动回退系统字体，Windows 为微软雅黑）。
- 渲染：Remotion。公司或团队商用请先查阅 remotion.dev/license 的授权条款。
- 配音：微软 Edge 在线语音（edge-tts），非官方接口，可用性可能随服务端变化。
