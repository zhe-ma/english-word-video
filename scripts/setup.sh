#!/usr/bin/env bash
# 一键安装：./scripts/setup.sh [--force] [--skip-check]
#   --force       重新下载词库和字体、重建 ecdict.db
#   --skip-check  跳过最后的冒烟测试
# 可选环境变量：
#   PYTHON=python3.12                 指定 Python
#   GH_RAW=https://raw.githubusercontent.com   GitHub raw 镜像地址
#   PIP_INDEX_URL / npm_config_registry        pip / npm 镜像
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
GH_RAW="${GH_RAW:-https://raw.githubusercontent.com}"
FORCE=0
CHECK=1
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --skip-check) CHECK=0 ;;
    *) echo "未知参数：$arg"; exit 1 ;;
  esac
done

say() { printf "\n\033[1;34m==> %s\033[0m\n" "$*"; }
die() { printf "\033[1;31m✗ %s\033[0m\n" "$*"; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "缺少 $1：$2"; }

# 下载到 .part，完成后再改名；失败自动断点续传重试
fetch() {
  local url="$1" dst="$2" min_bytes="$3"
  if [[ $FORCE -eq 0 && -f "$dst" && $(wc -c <"$dst") -ge $min_bytes ]]; then
    echo "已存在 $dst"
    return
  fi
  rm -f "$dst"
  for i in $(seq 1 10); do
    if curl -fSL -C - --retry 3 --connect-timeout 20 -o "$dst.part" "$url"; then
      [[ $(wc -c <"$dst.part") -ge $min_bytes ]] && { mv "$dst.part" "$dst"; return; }
    fi
    echo "  重试 $i/10 ..."
    sleep 3
  done
  die "下载失败：$url（可设置 GH_RAW 镜像或代理后重试）"
}

say "检查系统依赖"
need "$PY" "安装 Python 3.10+"
need node "安装 Node.js 18+"
need npm "安装 Node.js 18+"
need ffmpeg "macOS: brew install ffmpeg；Ubuntu: sudo apt install ffmpeg"
need ffprobe "随 ffmpeg 一起安装"
need curl "安装 curl"
need jq "macOS 自带；Ubuntu: sudo apt install jq（Cursor Hook 用）"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || die "Python 需要 ≥ 3.10（当前 $("$PY" -V)）"
node -e 'process.exit(+process.versions.node.split(".")[0] >= 18 ? 0 : 1)' || die "Node.js 需要 ≥ 18（当前 $(node -v)）"
echo "Python $("$PY" -V | cut -d' ' -f2)，Node $(node -v)，$(ffmpeg -version | head -1 | cut -d' ' -f1-3)"

say "Python 虚拟环境（.venv）"
[[ -d .venv ]] || "$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

say "Remotion 依赖（video/node_modules）"
(cd video && npm ci --no-audit --no-fund)

say "工作台依赖（workbench/node_modules）"
(cd workbench && npm ci --no-audit --no-fund)

say "下载 ECDICT 词库"
mkdir -p data
fetch "$GH_RAW/skywind3000/ECDICT/master/ecdict.csv" data/ecdict.csv 60000000
if [[ $FORCE -eq 1 || ! -f data/ecdict.db ]]; then
  ./vv init-db
else
  echo "已存在 data/ecdict.db"
fi

say "下载字体（OFL 可商用）"
mkdir -p video/public/fonts
fetch "$GH_RAW/google/fonts/main/ofl/poppins/Poppins-ExtraBold.ttf" video/public/fonts/Poppins-ExtraBold.ttf 100000
fetch "$GH_RAW/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf" video/public/fonts/Poppins-SemiBold.ttf 100000
fetch "$GH_RAW/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf" video/public/fonts/NotoSansSC.ttf 15000000

say "Remotion 渲染用浏览器（Chrome Headless Shell）"
(cd video && npx remotion browser ensure)

chmod +x vv .cursor/hooks/*.sh

if [[ $CHECK -eq 1 ]]; then
  say "冒烟测试"
  ./vv status
  mkdir -p .cache/stills
  (cd video && npx remotion still src/index.ts MarkerNotes ../.cache/stills/setup-check.png --frame=225 --log=error)
  echo "模板渲染正常 → .cache/stills/setup-check.png"
  if .venv/bin/edge-tts --text "测试 hello" --voice zh-CN-XiaoxiaoNeural --write-media .cache/stills/setup-check.mp3 >/dev/null 2>&1; then
    echo "edge-tts 连通正常"
  else
    echo "⚠ edge-tts 连不上（需要能访问 speech.platform.bing.com），配音步骤会失败"
  fi
fi

say "安装完成。启动工作台：./vv serve　　或对 Agent 说：做 1 期 CET-4 单词视频"
