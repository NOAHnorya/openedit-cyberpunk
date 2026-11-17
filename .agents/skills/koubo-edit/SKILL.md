---
name: koubo-edit
description: 多段自媒体口播素材 → 竖屏成片 + 抖音封面、标题、简介的全流程，以及固定使用的赛博朋克剪辑模板（建在 open-edit 之上）。用于：剪口播、一组 PMR000xx 连拍素材、去重录和口误、人像抠图贴纸、赛博朋克风格包装、配乐和卡点音效、抖音封面和标题。命令细节看 open-edit；零付费规则看 AGENTS.md。
---

# koubo-edit：口播剪辑流程 + 赛博朋克模板

仓库根目录有 LOCAL.md 时先读它，里面的个人偏好优先（称呼、素材盘路径、代理、默认配乐、方案怎么交给用户拍板）。

范例：`examples/demo/`（合成样片：分段配置 `scenes.json`、封面配置 `cover.json`、字幕修正 `fixes.json`）。
脚本：`tools/koubo/`。模板：`templates/cyberpunk/`。需要用户拍板的方案先列给用户确认再做（交付方式按 LOCAL.md，没写就直接在对话里列）。

## 1. 接素材

- 看整个素材文件夹，不只看用户给的那一个文件。同机位连拍的 PMR000xx 按拍摄顺序就是成片顺序；用户给的可能只是最后一段。
- 用户会中途新增或改名素材（比如补一张截图、重录一段 CTA），每轮开工前先 `ls -lt` 看一眼。
- 每段先本地转写：`tools/transcribe-local.sh <video> --lang zh --hint "英文名词, ..."`。对比各段文字找废条（讲到一半断了，后一段是重录）和重录片段（同一要点讲了两遍，留后录的）。
- 把「段 / 时长 / 讲什么 / 处理」列成表给用户看，再动刀。

## 2. 粗剪

- 写 `runs/<key>/edl.json`，`openedit apply-edl --edl ... --out runs/<key>/<key>.mp4`。
- 切点用 `speech-probe` 实测的静音。句尾一定用 `--window 5` 细测：默认精度测出的语音结束点会偏早约 0.5 秒，句尾的单字（如「看」「等」）会被切掉。
- 口误前后没有静音可切时，用 `python3 tools/koubo/candidates.py <spec.json>`（会自动换到带 faster-whisper 的 Python，查找顺序见 AGENTS.md「转写」）拼出几种候选剪法的音频并重新转写，选没有重复、没有缺字的那一刀；怎么拼都不干净就保留原话。
- 只压短超过 0.7 秒的停顿，免得画面跳太多。
- 粗剪后整条重新转写核对接缝。长音频转写偶尔会漏整句，发现缺句先单独截那段再转写确认，不要直接当成剪掉了。
- 追加片尾或替换某段：只改 EDL 里那一个 range，apply-edl 会复用其余段。素材的画面可能比音轨短，终点不能超过画面。

## 3. 字幕

- 字幕用粗剪后重新转写的结果（`transcribe-local.sh runs/<key>/<key>.mp4 --force`），不用 apply-edl 从源素材搬过来的（时间会漂）。
- `tools/koubo/fix_transcript.py transcript.json fixes.json [--from 秒]`：按每片自己的 `fixes.json` 替换听错的词，并把要标黄的关键词合成一个词（才能写进 `data-key-words`，每行最多 2 个）。范例 `examples/demo/fixes.json`。脚本会打印合并后关键词的时间，直接抄进 `keyWords`。
- 重新拼接之前先备份改好的字幕（`transcript.fixed.json`），新增段用 `--from` 只修新的部分。
- 中文片必加 CJK 修复；字幕两行，放在人脸下面。`openedit captions transcript.json` 生成 `captions.js`。

## 4. 定风格：先给方案再做

- 先给 2–4 个方案让用户选；每个方案用用户真实画面做静帧样图，放 `runs/<key>/drafts/`（LOCAL.md 另有约定时按它）。
- 案例素材里的关键演示不能裁掉（比如录屏里演示手势的小窗），要完整露出并做放大特写。
- 9:16 安全区：要读的字放中间 680 px、y 240–1478，不小于 49 px。装饰小标签用 `--no-text-floor` 保留，review 会报，要跟用户说明。
- 模板里已带字体。要加别的字体用 `openedit fonts ... --out fonts`；国内网络下载不动时设 `HTTPS_PROXY`（代理地址写在 LOCAL.md），不稳就重试到 `fonts.css` 写出来。

## 5. 人像抠图贴纸（本地、免费）

- `tools/koubo/cutout.sh runs/<key> [起始帧]`：抽帧（30 fps，`CROP` 默认裁 4K 机位的人像区域）→ macOS Vision 人像分割（JXA，高精度约 63 ms/帧）→ 去背景闪烁 → 红色描边 webp 序列（`seg/sticker/`）。追加片尾时传起始帧，只处理新增部分。
- 不依赖 Xcode 编译 Swift，Vision 一律经 JXA（`osascript -l JavaScript`）调用。
- 固定机位时，身后静止的物体（毛垫、椅背、墙上挂饰）会被间歇算进人，描边跟着闪。先画「每像素切换次数」热力图找位置，再用 `ZONES='[[x0,y0,x1,y1],...]'` 指给 `clean_masks.py`（坐标在 1056×864 的帧里）；不要直接切掉那个角落，手会伸进去。
- 封面用的静态人像：`tools/koubo/segment.js` + `sticker.py`（4K 单帧）；物体用 Vision「主体抠图」`tools/koubo/subject.js`。

## 6. 页面与渲染

- 用模板（第 10 节）：写 `scenes.json` → `python3 templates/cyberpunk/build.py runs/<key>` 生成 `index.html`。
- 正式渲染前先出静帧逐段检查：`openedit render runs/<key>/index.html --stills t1,t2,... --sheet ... --no-text-floor`。看素材框有没有显示、字幕压没压脸、卡片和字幕有没有重叠、字有没有溢出，入场时刻看虚影。
- 正式渲染：`openedit render runs/<key>/index.html --out runs/<key>/out.mp4 --fps 30 --frames <N> --no-text-floor`。4.5 分钟 1080×1920 约 6–7 分钟；改顶部 HUD 这类每帧都有的东西会整片重渲。
- 不要编造信息：用户没说过的编号（比如 EP.01）别写，review 的数字检查会抓出来。
- 交付前 `openedit review`，发现的问题自己判断，保留的要告诉用户。

## 7. 配乐与音效

- 先调研再试听：同一段 20 秒画面只换音乐、音效相同，另加一版只有音效的做对照。
- 曲库：Pixabay 拦截脚本下载；Mixkit 能直接下（`https://assets.mixkit.co/music/<id>/<id>.mp3`），但授权全文在弹窗里抓不到，要提醒用户自己确认。下载的曲子放 `local/`（不进仓库）。
- 合成音效和底乐用 `tools/koubo/webaudio/`（Chrome 离线 Web Audio 渲染）：`node render.mjs <audio-dir> <秒数>` 出 4 个音效和 A/B 两版底乐，秒数 0 只出音效；`node render.mjs --music <out.wav> <秒数> [A|B]` 只出一条底乐。Chrome 用 `openedit install-browser` 装的那份（自动取版本最大的），也可用 `OPENEDIT_CHROME` 指定。必须放在低中频：高频上滑的提示音和高八度琶音会被听成「鸟叫」。
- Agent 听不到声音：用频谱图（`showspectrumpic`）、分频段能量（`node tools/koubo/webaudio/balance.mjs`）和 100 ms 峰值检查；音乐压在人声下约 17–20 dB。
- `mix-audio` 给短于 0.4 秒的音效自动定音量会偏大几十 dB：短音效一律手动写 `gainDb`，峰值定在比人声峰值低约 4 dB。模板的 `mix.py` 已经这样算。
- 录音电平：领夹麦可能录得比机内麦还小，统一响度后整体提升很多，交付时提醒底噪。

## 8. 封面、标题、简介（抖音）

- 不能抽帧当封面，抖音会判不合格。要排版成海报：从 4K 原片重新抠人像（挑眼睛睁开、正视的帧，再挑一帧带手势的），物体用主体抠图，配新背景和大字标题。用模板 `templates/cyberpunk/cover/build_covers.py`。
- 尺寸：3:4 = 1080×1440，4:3 = 1440×1080。出 3–4 版，每版两种比例，再加一张总览图。
- 标题给 5 个不同角度（悬念、对比、痛点 + 数字、场景 + 数字、经验）；简介写要点加话题标签。终稿里删了的内容（比如 CTA 进群）简介里也别写。
- 用户可能在剪映里继续改（比如删掉 CTA、剪掉停顿），封面、标题和简介以剪映终稿为准。
- 用户选定的封面拷到这条视频的素材项目目录（位置看 LOCAL.md，没写就问用户），和原始素材放在一起，文件名写清比例，例如 `封面-3比4-<版式>.jpg`、`封面-4比3-<版式>.jpg`。待选的版本单独放，不和定稿混在一起。

## 9. 默认风格规范

- 布局：竖屏 9:16；讲案例时素材在上、人像贴纸在下；讲要点时是任务清单或要点卡加人像。不要突然切回原画面的大脸。
- 配色：人物描边红 #FF2E4D；界面线条和标签青 #2EF2FF；标题酸性黄 #E4FF1A，标题里的关键词用红；字幕关键词黄 #FCEE0A，每屏最多 2 处。
- 字体：ZCOOL QingKe HuangYou、Rajdhani、Share Tech Mono（模板 `fonts/` 已带）。
- 配乐风格：偏合人声的暗色电子氛围乐，卡点音效低调。默认底乐由 `mix.py` 按成片时长合成（webaudio 变体 A）；换曲子用 `--music` 或 `scenes.json` 的 `music`。

## 10. 赛博朋克剪辑模板（以后固定用）

以后的口播默认套这套模板。新片：复制范例配置到 `runs/<key>/scenes.json` 改内容，其余照搬。

| 部分 | 文件 | 作用 |
| --- | --- | --- |
| 分段配置 | `runs/<key>/scenes.json`（范例 `examples/demo/scenes.json`） | 每段的时间、画面模式、标题、要点卡、任务清单、案例素材和弹出时间。新片只改这里 |
| 页面生成 | `templates/cyberpunk/build.py <run>` | 读配置生成 `index.html`，首次运行会把样式、时间轴、字体、CJK 修复拷进 run（`--refresh` 覆盖） |
| 样式和字体 | `style.css`、`fonts/` | 配色、切角面板、任务卡、警告卡、扫描线、虚影层 |
| 时间轴引擎 | `timeline.js` | 按时间显隐元素、入场动效、切段故障闪烁、点亮当前任务、案例视频对时、图片推拉（`kf`）、抠像序列换帧、虚影 |
| 抠像 | `tools/koubo/cutout.sh` | 红色描边贴纸序列、去背景闪烁 |
| 音频 | `templates/cyberpunk/mix.py <run> [--music <曲子>] [--build]`、`audio/` | 故障音、提示音、渐强、重音按配置自动排；底乐按 `--music` → `scenes.json` 的 `music` → 自动合成（`audio/music-synth.wav`）的顺序取；`--build` 直接出 `audio/mix.m4a` |
| 封面 | `templates/cyberpunk/cover/build_covers.py <cover.json> <out> --render [--only v1,v3]` | 4 种海报版式（大头像 / 对比 / 物体 + 手势 / 清单），每种出 3:4 和 4:3；范例 `examples/demo/cover.json` |

`scenes.json` 要点：
- `frames`（总帧数 = 时长 × 30）、`hud`、`keyWords`、`hits`（渐强加重音的时间）、`sticker`（贴纸位置，一般不改）、`music`（可选，底乐文件，相对 run 目录；不写就自动合成）。
- `scenes`：每段 `t0`、`t1`、`mode`（`case` 讲案例 / `kp` 讲要点）、`hud`（右上角标签，`{n}` 显示当前任务号，`hudRanges` 让一个标签跨多段）。`case` 里写 `frame`（`top`、`height`、`bg`）、`items`（`video` + `at` + `rate`，或 `image` + `style` + `kf` 推拉关键帧 `"t,缩放,x,y;..."`）、`boxes`（页面坐标红框）、`inner_boxes`（素材框内坐标红框）、`insets`（手势等放大特写，带 `tag`）、`tags`（`color` r/c，`pop`，`big` 用于要读的标签）。
- `titles`：`ranges` + `html`，`fx` 默认 `ghost`（红青残影入场），揭晓用 `glitch`。
- `cards`：`ranges`、`top`、`lbl`、`html`、`red`、`size`、`cls`、`style`、`fx`。
- `tasks`：`ranges`、`appear`（第一条出现时间，后面每条间隔 0.2 秒）、`items`（`text`、`on` 点亮区间、`subs` 副标题 `[区间, 文案]`）。
- 文案标记：`\n` 换行；`{kw:X}` 标题里的红色关键词；`{kwen:X}` 红色英文；`{ec:X}` 青色英文名；`{en:X}` 英文字体；`{y:X}` 卡片里的黄色关键词；`{hl:X}` 任务点亮时变黄；`{c:X}` 青；`{r:X}` 红；也接受封面那种 `[kw]X[/kw]` 写法；原始 HTML 直接透传。

视觉规范：
- 两种画面：讲案例时素材框在 y 430（宽 1000），人像贴纸在左下；讲要点时标题加任务清单或要点卡，人像贴纸居中。不切回原画面。
- 文字位置：标题两行 74 px，从 y 240 开始；清单和卡片从 y 440 开始（配置里 `top` 是相对安全区，200 ≈ y 440）；字幕两行 52 px，在 y 1120。
- 颜色见第 9 节。
- 动效：元素 0.35 秒上浮入场；切段时 0.17 秒红青故障条加画面抖动；揭晓式标题闪烁入场；当前任务红框发光；案例里的关键演示做红框放大特写。虚影：标题入场带红青残影（向两侧错开、逐层变淡），切段时人像贴纸留 2 帧残影，卡片入场带一层拖影；只出现在入场和切段的 0.3–0.5 秒，不常驻。

新片怎么套：
1. 按第 1–3 节转写、粗剪、修字幕。
2. 按内容分段，填 `scenes.json`（时间从 `openedit words` 的逐词时间里取）。哪些算案例、哪些算要点、卡片文案怎么提炼、素材放大哪一块，由 Agent 先拟，用户确认。
3. `tools/koubo/cutout.sh runs/<key>` → `build.py` → 出静帧检查 → 正式渲染。
4. `mix.py runs/<key> --build` 排好卡点，确认底乐，`openedit mux-audio --video out.mp4 --audio audio/mix.m4a --out <成片>`。
5. 封面从 4 种版式里套，换标题和人像；选定的拷进素材项目文件夹。
