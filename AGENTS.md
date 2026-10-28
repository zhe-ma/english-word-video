# english-word-video（WorkBuddy skill）

仓库根目录就是 skill 根目录，工作流见 `SKILL.md`，写稿规范见 `references/`。

## 约定

- 唯一入口 `scripts/vb.py`（setup / words / check / stills / build）；业务逻辑在 `scripts/vb_*.py`，只用 Python 标准库 + `requirements.txt` 里的三个包。
- 必须同时支持 macOS 和 Windows：路径用 `pathlib`，不写 bash 脚本，调用外部程序用 `shutil.which` 解析，终端输出统一 UTF-8。
- skill 目录只读。依赖、模板副本、配音缓存放在 `~/.english-word-video/`（`EWV_HOME`）。
- **目录层级硬限制**：开放平台只允许「根目录/二级目录/文件」，包内只能有 `references/`、`scripts/`、`templates/` 三个子目录，里面不能再嵌套目录。所以 Python 模块和 Remotion 模板都是平铺的（Python 模块带 `vb_` 前缀）；`setup` 会把模板按类型还原成 Remotion 要的 `src/`、`public/fonts/` 结构，放到 `~/.english-word-video/remotion/`。
- 画面模板在 `templates/`（`.ts`/`.tsx`/`sample.json` → src，`.woff2` → public/fonts，其余根目录文件原样）。改模板后运行 `python scripts/vb.py setup`（会同步到运行目录），再 `stills` 看静帧确认，满意后才 `build`。
- `timeline.json` 等产物由脚本生成，不手改。
- 改 `SKILL.md` frontmatter 要符合 WorkBuddy 技能规范（name、display_name、display_name_en、description、description_zh、description_en、version、author 必填）。
- 清理前的旧版本（真题对照、旧版单期流水线、工作台）在 git 标签 `pre-skill-cleanup` 里。
