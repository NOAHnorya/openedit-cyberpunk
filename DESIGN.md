# 设计记录

开源前定下的决定和理由，2026-11-17。D1–D4 由仓库作者拍板；默认决定是开工时定下的，没有逐条再问。以后改了哪条，就在这里改，并写上新的理由。

前提：零付费。open-edit 里所有走 VEED 或 fal 付费服务的功能都换成本机方案，规则写在 `AGENTS.md` 的「硬规则」一节。

## 拍板的决定

| 编号 | 决定 | 理由 | 落在哪 |
|---|---|---|---|
| D1 | 公开仓库 `NOAHnorya/openedit-cyberpunk`，任何人都能 clone。README 以中文为主，末尾附英文摘要 | skill、agent 指令和默认字幕都是中文，主要读者是做中文口播的人。英文摘要让 open-edit 社区一眼看懂这是什么 | `README.md` |
| D2 | 只放合成样片。作者真人出镜的片子（脸、文案、分段配置）都不进仓库 | 保护隐私。合成样片也能完整走一遍流程：配音、转写、素材、贴纸、页面、渲染、混音。任何人 clone 后都能复现同一条，不需要真人素材 | `examples/demo/`、`docs/preview.jpg`；`.gitignore` 忽略 `runs/` 和 `local/` |
| D3 | 日常剪片的工作区就是这个仓库。称呼、素材盘路径、代理这些个人设置放进不进仓库的 `LOCAL.md`，日常用法不变 | 模板只有一份，改完直接提交，不用在工作区和仓库之间来回同步。个人设置单独放一个文件，公开的内容里就没有本机路径 | `LOCAL.example.md`；`AGENTS.md` 和 SKILL.md 开头写着「先读 LOCAL.md」；`.gitignore` |
| D4 | 仓库只带合成底乐，不带第三方曲子 | 完全自带，不依赖外网。合成的底乐授权清楚；下载的曲库音乐拿不到可以再分发的授权全文。代价是听感和用真曲子做的成片不一样 | `templates/cyberpunk/mix.py` 默认合成底乐；想用自己的曲子，放进 `local/`，再用 `--music` 或 `scenes.json` 的 `music` 指定 |

## 默认决定

| 决定 | 理由 |
|---|---|
| 代码用 MIT，字体附 SIL OFL 1.1 | MIT 最宽松，也能和 open-edit 的 Apache-2.0 一起用。字体本身是 OFL，只能按 OFL 再分发，所以附上原文和四套字体的版权声明（`templates/cyberpunk/fonts/OFL.txt`） |
| 只支持 macOS | 抠像靠 macOS Vision，免费、在本机跑，经 JXA 调用不用编译。样片配音用 `say`，启动器是 AppleScript。要支持别的平台，得重写抠像这一层 |
| 转写用仓库自带的小 `.venv`，同时兼容已装的 OpenMontage | 没装 OpenMontage 也能用：`./setup.sh` 会建 `.venv`。已经装了的人不用再装一遍 faster-whisper。查找顺序是 `WHISPER_PY` → 仓库 `.venv` → `~/OpenMontage/.venv`。OpenMontage 是 AGPL-3.0，本仓库不含它的代码，只调用它环境里的 Python |
| `剪视频.applescript` 放进 `extras/` | 桌面启动器可有可无，不属于主流程。源码里的仓库路径用 `__REPO__` 占位，编译时再替换，所以不含本机路径 |
| open-edit 锁在 0.10.0 | 零付费规则是按 0.10.0 的付费入口写的。升级前要先核对新版本有没有新的付费入口，所以只在用户同意后升级（见 `AGENTS.md`「网络」一节） |
