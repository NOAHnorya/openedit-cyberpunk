# 第三方组件和授权

本仓库自己的代码、文档、合成音效（`templates/cyberpunk/audio/*.wav`，用 `tools/koubo/webaudio/` 合成）和预览图（`docs/preview.jpg`，合成样片的静帧）都用 MIT，见 [`LICENSE`](LICENSE)。下面列出仓库里附带的第三方文件，以及运行时会用到、但不随仓库分发的依赖。

## 随仓库分发

| 组件 | 位置 | 授权 | 版权声明 |
|---|---|---|---|
| ZCOOL QingKe HuangYou（站酷庆科黄油体） | `templates/cyberpunk/fonts/zcool-qingke-huangyou-*.woff2` | SIL OFL 1.1 | Copyright 2018 The ZCOOL QingKe HuangYou Project Authors |
| Rajdhani | `templates/cyberpunk/fonts/rajdhani-*.woff2` | SIL OFL 1.1 | Copyright (c) 2014 Indian Type Foundry |
| Share Tech Mono | `templates/cyberpunk/fonts/share-tech-mono-*.woff2` | SIL OFL 1.1，保留字体名 “Share” | Copyright (c) 2012, Carrois Type Design, Ralph du Carrois |
| Chakra Petch | `templates/cyberpunk/fonts/chakra-petch-*.woff2` | SIL OFL 1.1 | Copyright 2018 The Chakra Petch Project Authors |

这些字体文件是 Google Fonts 提供的 woff2 子集，用 `openedit fonts` 下载，没有改动。完整的版权声明和 OFL 原文见 [`templates/cyberpunk/fonts/OFL.txt`](templates/cyberpunk/fonts/OFL.txt)。

## 不随仓库分发（安装或运行时获取）

| 组件 | 用途 | 授权 | 怎么获取 |
|---|---|---|---|
| [open-edit](https://github.com/veedstudio/open-edit)（`@veedstudio/openedit-cli` 0.10.0） | 剪辑、字幕、渲染、混音的 CLI 和 skill | Apache-2.0 | `npm install`（`package.json` 锁定版本）；skill 由 `openedit init` 装进 `.claude/skills/open-edit/` 和 `.agents/skills/open-edit/`，这两个目录不进仓库 |
| playwright-core 1.63.0 | open-edit 的依赖，驱动渲染用的 Chrome；`tools/koubo/webaudio/` 也用它 | Apache-2.0 | 随 open-edit 一起 `npm install` |
| undici 7.x | open-edit 的依赖 | MIT | 随 open-edit 一起 `npm install` |
| Chrome Headless Shell | 渲染 HTML 页面、离线合成 Web Audio | Chromium 的开源授权（BSD-3-Clause 等）和 Google 的条款 | `openedit install-browser` 下载到用户目录 |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper)，及其依赖（CTranslate2、PyAV、onnxruntime 等） | 本地转写 | faster-whisper 用 MIT，依赖各自的授权见各项目 | `./setup.sh` 用 pip 装进仓库的 `.venv`（不进仓库），或者用你指定的 Python |
| Whisper 模型（`Systran/faster-whisper-small`，从 OpenAI Whisper 转换） | 转写模型 | MIT | 第一次转写前从 Hugging Face 下载到 `~/.cache/huggingface/` |
| Pillow | 样片素材、贴纸描边、封面 | MIT-CMU（HPND） | pip |
| NumPy | 去背景闪烁、混音时算人声电平 | BSD-3-Clause | pip |
| FFmpeg / ffprobe | 剪切、抽帧、编码 | LGPL-2.1+ 或 GPL（看你装的版本） | `brew install ffmpeg` |
| Node.js、Python | 运行环境 | 各自的授权 | `brew install node`；Python 用系统自带的 3.9 或 `brew install python@3.13`（3.15 还不行，见 README「系统要求」） |
| macOS Vision、`say`、`osascript` | 人像分割和主体抠图、样片配音、启动器 | Apple 系统组件 | macOS 自带 |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | 本地转写的思路；你已经装了它的话，复用 `~/OpenMontage/.venv` 里的 faster-whisper | AGPL-3.0 | 本仓库不含它的代码，也不会替你安装 |

## 付费服务

open-edit 能接 VEED 和 fal 的付费服务（VEED 转写、Fabric、lipsync、fal 抠像和生成）。本仓库不用这些服务，`AGENTS.md` 里写了禁用规则。如果你自己开启，使用条款以 VEED 和 fal 的为准，跟本仓库的授权无关。
