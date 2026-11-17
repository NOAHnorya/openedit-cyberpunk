# open-edit 口播剪辑工作区（赛博朋克模板）

仓库根目录有 LOCAL.md 时先读它，里面的个人偏好优先（称呼、素材盘路径、代理地址、默认配乐、范例片）。没有就按本文件和 skill 的默认值，模板见 `LOCAL.example.md`。

用 open-edit skill（`@veedstudio/openedit-cli` 0.10.0）剪视频的工作区，只支持 macOS。`runs/<key>/` 一片一个文件夹（不进仓库）；私人文件（自己的配乐、范例配置）放 `local/`，也不进仓库。
open-edit 本体的 skill（`.claude/skills/open-edit/`、`.agents/skills/open-edit/`）由 `openedit init` 安装，不进仓库。

## 硬规则：不碰付费服务

- 不登录 VEED（不跑 `openedit login`），不用 `--provider veed`、`generate`（Fabric）、`lipsync`、`veed-project`、`veed-pull`。
- 不配 `FAL_KEY`，不跑 `fal run`、`background-removal`（默认路线也要 VEED 登录）、`reframe --erase`。`sfx` 在本机没有音效库，skill 会建议改用 fal 生成，别照做。
- 0.10.0 新增的两个付费入口也不开：不设 `OPEN_EDIT_SPEAKER_CUTOUT`（render 会在 fal 上自动买抠像），不设 faces 的云端分析变量；`faces` 只用本地 MediaPipe 或 `--speakers` 文件。
- skill 里任何一步要用到上面这些，停下来告诉用户，给出本地替代方案。

## 转写：本地 faster-whisper

`.open-edit-prefs.json`（不进仓库）里把转写登记成 `custom`：`{"transcription": {"provider": "custom"}}`。转写一律用：

```
tools/transcribe-local.sh <video> --lang zh --hint "Claude Code, OpenEdit"
tools/transcribe-local.sh <video> --lang en
tools/transcribe-local.sh <video> --lang zh --model medium   # 更准；首次要 DOWNLOAD=1 下载模型
```

- 带 faster-whisper 的 Python 按这个顺序找：环境变量 `WHISPER_PY` → 仓库里的 `.venv` → `~/OpenMontage/.venv`。都没有就建一个：
  `python3 -m venv .venv && .venv/bin/pip install faster-whisper`。`tools/koubo/candidates.py` 用同样的顺序。
- 默认离线跑。某个模型第一次用要加 `DOWNLOAD=1` 从 Hugging Face 下载一次（国内需要代理时同时设 `HTTPS_PROXY`，地址写在 LOCAL.md）。
- 写出 `runs/<key>/transcript.json`（`<key>` 是文件名去掉扩展名）。
- 中文：自动加简体提示词（否则会出繁体），半角 `,?!:;` 转全角。
- `--hint`：片中出现的英文名、产品名、术语，按应有的拼写写。中文模式下不给 hint，英文会听错（Claude Code → "clotcode"）
  且被拆成碎片；给了 hint 后拼写和空格都对，脚本再把 `' Cla' + 'ude'` 这类碎片合回一个词。
- 已有转写要重跑加 `--force`。

## 中文字幕：必须带 CJK 修复（已验证）

open-edit 的 `captions.js` 在每两个词之间插一个空格，中文会显示成「视 频 剪 辑」。每个中文片子：

1. 把 `tools/cjk-captions.css` 和 `tools/cjk-captions.js` 复制进 `runs/<key>/`（一片一个文件夹，资产放在页面旁边）。用赛博朋克模板时 `build.py` 会自动拷。
2. 页面里 `<link rel="stylesheet" href="cjk-captions.css">`，并在 `captions.js` 之后紧跟 `<script src="cjk-captions.js"></script>`。

效果：中文字之间无空格；英文词之间、中英文交界保留空格（「用 Claude Code 剪」）。参考样例：`examples/demo/`。

还没解决：自动折行可能把一个短语拆到两行（「Claude / Code」「加 / 上字幕」）。需要时用 `data-chars` / `data-lines` 调整，或改短句子。

## 网络（国内）

- 国内 npm 镜像可能还没同步新版本。升级用：
  `npm_config_registry=https://registry.npmjs.org npx @veedstudio/openedit-cli init --update <版本> --workspace "$PWD"`（在仓库根目录跑），并且只在用户同意后升级。
- 渲染用的 Chrome Headless Shell 由 `./node_modules/.bin/openedit install-browser` 装到 `~/Library/Application Support/veed-openedit/browser/`。
  `tools/koubo/webaudio/` 自动取其中版本号最大的一份，也可以用环境变量 `OPENEDIT_CHROME` 指定。下载需要代理时：
  `HTTPS_PROXY=<代理地址> ./node_modules/.bin/openedit install-browser`。渲染本身不要挂代理。

## 口播剪辑流程与赛博朋克模板

剪多段口播、做抖音封面和标题时，先读 `.agents/skills/koubo-edit/SKILL.md`（Claude Code 和 Codex 共用这一份）。脚本在 `tools/koubo/`，模板在 `templates/cyberpunk/`，范例是 `examples/demo/`（合成样片）。

- 仓库里只有 `.agents/` 这一份 koubo-edit skill，改 skill 只改它。想让 Claude Code 把它列进 skill 列表，在仓库根目录建一个软链（`.gitignore` 已忽略这个位置）：
  `mkdir -p .claude/skills && ln -s ../../.agents/skills/koubo-edit .claude/skills/koubo-edit`
- 双击启动 Claude Code 的桌面小程序：`extras/剪视频.applescript`（文件开头写了怎么编译）。
