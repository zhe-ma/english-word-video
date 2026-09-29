#!/bin/bash
# afterFileEdit：改完 episodes/<id>/script.json 自动校验，结果写入同目录 report.json
input=$(cat)
file=$(echo "$input" | /usr/bin/jq -r '.file_path // empty')
if [[ "$file" =~ episodes/([0-9]+)/script\.json$ ]]; then
  ./vv validate "${BASH_REMATCH[1]}" > /dev/null 2>&1
fi
exit 0
