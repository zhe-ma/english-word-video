import json
import re
import sys
from pathlib import Path

from .config import EPISODES

HANZI = re.compile(r"[\u4e00-\u9fff]")


def ep_dir(ep):
    p = Path(str(ep))
    d = p.resolve() if len(p.parts) > 1 else EPISODES / p.name
    if not d.exists():
        sys.exit(f"找不到期目录：{d}")
    return d


def load(ep):
    path = ep_dir(ep) / "script.json"
    if not path.exists():
        sys.exit(f"缺少 {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sentence_text(tokens, tts=False):
    """tts=True 时在英文单词两侧加空格，帮助 TTS 切分。"""
    parts = []
    for tk in tokens:
        if "w" in tk:
            parts.append(f" {tk['w']} " if tts else tk["w"])
        else:
            parts.append(tk.get("t", ""))
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def full_text(script):
    return "".join(sentence_text(s) for s in script["sentences"])


def hanzi_count(text):
    return len(HANZI.findall(text))


def word_tokens(script):
    return [tk["w"] for s in script["sentences"] for tk in s if "w" in tk]
