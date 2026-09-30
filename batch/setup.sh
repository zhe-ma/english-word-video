#!/usr/bin/env bash
# 批量生成环境：batch/setup.sh
# 依赖项目根目录已经跑过 scripts/setup.sh（.venv、data/ecdict.db）。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
cd "$HERE/video"

echo "==> Remotion 依赖（batch/video/node_modules）"
npm install --no-audit --no-fund

echo "==> Chrome Headless Shell"
if [[ -d "$ROOT/video/node_modules/.remotion" && ! -d node_modules/.remotion ]]; then
  cp -R "$ROOT/video/node_modules/.remotion" node_modules/.remotion
  echo "复用 video/ 里已下载的浏览器"
else
  npx remotion browser ensure
fi

echo "==> 字体"
mkdir -p public/fonts
if [[ -d "$ROOT/video/public/fonts" ]]; then
  cp -n "$ROOT/video/public/fonts/"*.ttf public/fonts/ || true
fi
ls public/fonts

echo "==> Python 依赖"
"$ROOT/.venv/bin/python" -c "import yaml, edge_tts" || "$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt"

chmod +x "$HERE/vb"
echo "完成。试一下：batch/vb check example"
