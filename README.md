# 中英混读单词视频

本地用脚本生产竖屏中英混读单词短视频。文案放在 `batch/scripts/`，校验、静帧、配音和渲染都走命令行。

```bash
./scripts/setup.sh          # 首次安装
batch/setup.sh              # 批量渲染环境
batch/vb stills <名字>      # 出静帧
batch/vb build <名字>       # 配音并渲染
```

- 批量流程和文案格式：[batch/README.md](batch/README.md)
- 日常命令：[AGENTS.md](AGENTS.md)
- 部署与迁移：[docs/DEPLOY.md](docs/DEPLOY.md)
