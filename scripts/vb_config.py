"""路径与参数。

skill 目录只读；依赖、渲染模板副本、配音缓存都放在用户目录 ~/.english-word-video/（可用 EWV_HOME 改）。
"""
import os
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "templates"                  # 平铺的模板文件；setup 时按类型还原成 Remotion 的目录结构
ECDICT_DB = SKILL / "scripts" / "ecdict-lite.db"
REQUIREMENTS = SKILL / "scripts" / "requirements.txt"

HOME = Path(os.environ.get("EWV_HOME") or Path.home() / ".english-word-video")
PYDEPS = HOME / f"pydeps-{sys.version_info.major}.{sys.version_info.minor}"
RUNTIME = HOME / "remotion"          # 模板副本 + node_modules + 浏览器
PUBLIC_AUDIO = RUNTIME / "public" / "audio"
CACHE = HOME / "cache" / "tts"
STAMP = HOME / "setup.json"

FPS = 30
SR = 24000

# 文案文件里的 defaults 可以覆盖这些
DEFAULTS = {
    "level": "",                            # 高考 / CET-4 / CET-6 / 考研 / 雅思 / 托福；空 = 不限，不做词表校验
    "series": "",                           # 画面左上角栏目名；不写则用「<level>单词」，level 也没写则用「中英混读单词」
    "footer": "不熟悉的单词，评论区打出来",    # 卡片下方的固定提示
    "voice": "zh-CN-XiaoxiaoNeural",        # 正文中英混读
    "rate": "+5%",
    "review_voice": "en-US-AriaNeural",     # 复习段英文
    "review_rate": "-10%",
    "gloss_voice": "zh-CN-XiaoxiaoNeural",  # 复习段中文释义
    "gloss_rate": "+0%",
}

LEVEL_TAGS = {"高考": "gk", "CET-4": "cet4", "CET-6": "cet6", "考研": "ky", "雅思": "ielts", "托福": "toefl"}

# 节奏（秒）
LEAD_IN = 0.25        # 第一帧就有正文，声音稍后进入
PAGE_GAP = 0.45       # 页间静音，翻页动画落在这里
REVIEW_GAP = 0.7      # 正文结束到复习
GROUP_LEAD = 0.35     # 每组复习出现后再开口
EN_ZH_GAP = 0.25      # 英文与中文释义之间
ITEM_GAP = 0.45       # 复习项之间
OVERVIEW_HOLD = 1.8   # 结尾全文高亮帧停留

REVIEW_GROUP_MAX = 5

COLORS = ["yellow"]
# 全文占位字数（汉字和标点计 1，英文字母计 0.55，释义也算）超过这个值，一页放下就要明显缩小字号
MAX_TEXT_WEIGHT = 250

# 校验阈值：只产生提醒（!），不阻断生成
ITEMS_RANGE = (5, 7)
MAX_GLOSS_LEN = 8
BODY_RANGE = (30.0, 50.0)
TOTAL_RANGE = (50.0, 75.0)

HETERONYMS = {
    "record", "present", "content", "object", "desert", "produce", "permit", "project",
    "refuse", "subject", "conduct", "contract", "increase", "decrease", "export", "import",
    "insult", "minute", "wind", "lead", "tear", "bow", "close", "live", "read", "row", "wound",
}
