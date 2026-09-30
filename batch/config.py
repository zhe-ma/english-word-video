from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = HERE / "scripts"
OUT = HERE / "out"
VIDEO = HERE / "video"
PUBLIC_AUDIO = VIDEO / "public" / "audio"
CACHE = ROOT / ".cache" / "tts"
ECDICT_DB = ROOT / "data" / "ecdict.db"

FPS = 30
SR = 24000

# 批量文件里 defaults 可以覆盖这些
DEFAULTS = {
    "level": "考研",
    "series": "中英混读单词",
    "vol": "",                              # 画面左上角 Vol. 徽章，空则不显示
    "voice": "zh-CN-XiaoxiaoNeural",        # 正文中英混读
    "rate": "+5%",
    "review_voice": "en-US-AriaNeural",     # 复习段英文
    "review_rate": "-10%",
    "gloss_voice": "zh-CN-XiaoxiaoNeural",  # 复习段中文释义
    "gloss_rate": "+0%",
    "hint": "哪个词还不熟？评论区留个词",
    "source": "",                           # 纸张底部的出处小字；不写则用原文文件里的 source
    "passage": "",                          # 真题原文 + 参考译文文件（batch/passages/），相对批量文件所在目录
}
DEFAULT_SOURCE = "出自考研真题"               # 既没写 source、也没有原文文件时

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
