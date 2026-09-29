from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EPISODES = ROOT / "episodes"
VIDEO = ROOT / "video"
CACHE = ROOT / ".cache"

ECDICT_CSV = DATA / "ecdict.csv"
ECDICT_DB = DATA / "ecdict.db"
PROGRESS_DB = DATA / "progress.db"
BANNED = DATA / "banned_phrases.txt"
PUBLISHED = DATA / "published_scripts.md"

SERIES = "一分钟情景单词"
FPS = 30

# ECDICT tag 过滤：include 任一命中即入池，exclude 任一命中即剔除（太基础的词）
LEVELS = {
    "gk":    {"label": "高考",   "include": ["gk"],    "exclude": ["zk"]},
    "cet4":  {"label": "CET-4",  "include": ["cet4"],  "exclude": ["zk"]},
    "cet6":  {"label": "CET-6",  "include": ["cet6"],  "exclude": ["zk", "cet4"]},
    "ky":    {"label": "考研",   "include": ["ky"],    "exclude": ["zk", "cet4"]},
    "ielts": {"label": "雅思",   "include": ["ielts"], "exclude": ["zk"]},
    "toefl": {"label": "托福",   "include": ["toefl"], "exclude": ["zk"]},
}

COLORS = ["yellow", "green", "pink", "blue"]

# 朗读节奏
LEAD_IN = 0.6          # 纸张入场后开始朗读
SENTENCE_GAP = 0.35    # 句间静音
SUMMARY_GAP = 0.5      # 朗读结束到词卡页
SUMMARY_HOLD = 3.6     # 词卡全部出现后的停留

# 文案规则
HANZI_RANGE = (45, 62)
WORDS_RANGE = (4, 8)
SENTENCES_RANGE = (4, 7)
MAX_WORDS_PER_SENTENCE = 2
MAX_HANZI_PER_SENTENCE = 20
MAX_ENDING_HANZI = 15
MAX_MEANING_LEN = 8
READING_RANGE = (16.0, 21.0)
REVIEW_PASS = {"total": 24, "min": 3, "hook": 4, "punchline": 4}
REVIEW_KEYS = ["hook", "relatable", "punchline", "fresh", "natural", "accurate"]

HETERONYMS = {
    "record", "present", "content", "object", "desert", "produce", "permit", "project",
    "refuse", "subject", "conduct", "contract", "increase", "decrease", "export", "import",
    "insult", "minute", "wind", "lead", "tear", "bow", "close", "live", "read", "row", "wound",
}

VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+5%"
