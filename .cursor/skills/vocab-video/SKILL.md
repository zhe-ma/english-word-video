---
name: vocab-video
description: 生产「荧光笔手帐」中英混读单词短视频（选词、写文案、毒舌评审、配音、渲染、看图质检、入库）。当用户说"做 N 期视频""出一期单词视频""生成 CET-4/考研/雅思视频"或提到 episodes、vv 命令时使用。
---
# 单词视频生产流程

所有命令在项目根目录执行。每期目录：`episodes/<id>/`。

## 单期流程

复制这份清单并逐项勾选：

```
- [ ] 1. plan：./vv plan --level <level> --theme "<主题>"
- [ ] 2. 写 3 稿 → drafts.md
- [ ] 3. 毒舌评审（子代理）→ 选稿精修 → script.json
- [ ] 4. ./vv validate <id> 通过
- [ ] 5. ./vv tts <id> + ./vv qa-audio <id> 通过
- [ ] 6. ./vv render <id>
- [ ] 7. ./vv frames <id>，逐张看图质检
- [ ] 8. ./vv commit <id>
```

### 1. 选题和选词

- 主题：用户没指定时，从 `data/themes.yaml` 选一个没用过的（`plan` 会打印最近几期）；也可以结合当周节日或热点（可用网页搜索）。
- 运行 `./vv plan`，得到候选新词和到期复习词。
- 候选词不贴合主题时，用 `./vv words <中文关键词…>` 找词。只要 validate 通过（在词库里、没用过），不必局限于候选列表。
- 选 6–8 个词（对话体等特殊形态可以 4–5 个），以名词和动词为主，最多 2 个复习词。

### 2. 写 3 稿

- 先读 `data/hall_of_fame.md` 找感觉，遵守 `.cursor/rules/copywriting.mdc`。
- 用**3 种不同形态**各写一稿（吐槽小剧场、朋友圈 vs 现实、伪官方通知、灵魂拷问对话、拟人视角、反鸡汤、伪新闻、说明书体、节日热点，或自创）。
- 写入 `episodes/<id>/drafts.md`，每稿标明形态和所用单词。

### 3. 毒舌评审

用 Task 工具开一个子代理（generalPurpose），prompt 里包含：3 份稿全文、下面的评分表，以及 `data/published_scripts.md` 最近 30 期的主题和结尾句。要求它：

- 以挑剔的短视频编辑身份，按 6 项分别给每稿打 1–5 分：hook（钩子）、relatable（共鸣）、punchline（笑点/反转）、fresh（新鲜度）、natural（单词自然度）、accurate（准确性）。
- 指出每稿最弱的一句，并给出具体修改建议。
- 只输出评分和意见，不替你重写。

过稿线：总分 ≥ 24，单项 ≥ 3，hook 和 punchline ≥ 4。

取最高分稿，按意见精修，**再评一次**（可以复用同一个子代理）。3 轮都不过就换形态或换选题。把评分和意见追加到 `drafts.md`。

定稿写成 `script.json`：

```json
{
  "id": "001", "series": "一分钟情景单词", "level": "CET-4",
  "theme": "猫主子的一天", "genre": "拟人视角",
  "review": {"hook": 4, "relatable": 5, "punchline": 5, "fresh": 4, "natural": 4, "accurate": 5},
  "sentences": [
    [{"t": "我是一只猫，每天的"}, {"w": "routine"}, {"t": "很简单。"}],
    [{"t": "人类真好教，三天就学会了。"}]
  ],
  "words": [{"word": "routine", "pos": "n.", "meaning": "日常惯例"}]
}
```

- `sentences` 是句子数组，每句由 `t`（中文片段）和 `w`（英文单词）组成；英文单词前后不要加空格。
- `words` 与 `sentences` 里单词顺序一致；复习词加 `"review": true`。
- 释义取本文语境下的意思，≤ 8 字，从 `plan.json` 或 `./vv words` 给出的义项里选。

### 4. 校验

`./vv validate <id>`：✗ 必须修；! 是提醒，要判断是否需要改（例如释义与词典差异大、多音词）。修改 script.json 后重跑。

### 5. 配音

- `./vv tts <id>`（默认 zh-CN-XiaoxiaoNeural、语速 +5%；可用 `--voice`、`--rate` 调整）。网络失败会自动重试。
- `./vv qa-audio <id>`：朗读时长必须在 16–21s，超了删字，短了加细节，然后回到第 4 步。

### 6–7. 渲染和看图质检

- `./vv render <id>`（约 1–3 分钟）。
- `./vv frames <id>`，然后用 Read 工具**逐张查看** `frames/*.png`，检查：
  - 正文是否溢出纸张，释义标签是否互相遮挡或压到上一行文字；
  - 是否有标点落在行首，单词是否被截断；
  - 聚焦词卡、汇总词卡文字是否超宽；
  - 高亮颜色和进度条是否正常。
- 正文太挤时，在 script.json 里加 `"layout": {"fontScale": 0.94}`，然后重新执行 tts（会用缓存，很快）和 render。

### 8. 入库

`./vv commit <id>`。最后向用户汇报：期号、主题、形态、单词、评审分、朗读时长、成片路径，并附上一张关键帧。

## 批量

- N ≥ 3 期时：给每期开一个子代理并行完成第 1–4 步（每个子代理负责一期，并告知它其他期的主题和形态，避免撞车）；主 Agent 再串行执行第 5–8 步（CPU 和 edge-tts 都不适合并发）。
- 同一批里同一种形态最多出现 2 次，主题不能重复。
- 结束时输出汇总表。

## 禁止

- 跳过评审或校验直接配音、渲染。
- 手写音标、手改 `timeline.json` 或 `props.json`。
- 为了过校验而删掉笑点；应该换词或重写。
