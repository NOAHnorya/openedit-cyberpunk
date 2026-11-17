# LOCAL.md 模板

把这份复制成 `LOCAL.md`，按自己的情况填（`cp LOCAL.example.md LOCAL.md`）。`LOCAL.md` 在 `.gitignore` 里，不会进仓库。
Agent 开工前会先读 `LOCAL.md`，这里写的个人偏好优先于 `AGENTS.md` 和 `koubo-edit/SKILL.md` 里的默认值。
私人文件（自己的配乐、范例配置、封面素材）放 `local/`，同样不进仓库。用不上的条目删掉或留空即可。

## 用户和拍板方式

- 怎么称呼你：<名字>
- 方案怎么交给你拍板：<例如：写进某个在线文档的「待你决定」表 / 直接在对话里列>

## 路径

- 素材盘（每条视频一个项目目录，定稿封面拷到这里）：<例如 /Volumes/<盘名>/<素材目录>/<项目名>/>
- 待选版本（方案样图、封面候选）放：<例如 ~/Downloads/<片名>-xxx/>

## 网络

- 代理（下载字体、`openedit install-browser`、转写第一次下载模型时用；渲染不挂代理）：`HTTPS_PROXY=<http://host:port>`
- npm 镜像：<用国内镜像时，升级 openedit-cli 改用 registry.npmjs.org，见 AGENTS.md>

## 转写

- 带 faster-whisper 的 Python：<留空就按 WHISPER_PY → 仓库 .venv → ~/OpenMontage/.venv 的顺序找>
- 常用模型：<small / medium / large-v3>，已下载过的：<…>

## 默认配乐

- <留空就用 mix.py 合成的底乐。想用自己的曲子：放进 local/，然后写明「mix.py 加 `--music local/<曲子文件>`」>

## 个人偏好

- 和「默认风格规范」（SKILL.md 第 9 节）不一样的地方：<配色、字体、布局、配乐风格>
- 定稿记录（标题、封面版式选择）：<…>

## 范例

- 自己的范例片：<runs/<key>/>
- local/ 里的范例配置：<例如 local/<片名>.scenes.json、local/<片名>.cover.json、local/<片名>.fixes.json>

## 快捷方式

- 桌面启动器：<编译好的 .app 位置；源码 extras/剪视频.applescript，文件开头写了编译方法>
