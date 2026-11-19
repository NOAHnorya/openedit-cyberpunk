#!/bin/zsh
# 一键安装：依赖、open-edit skill、渲染用的 Chrome、本地转写，最后渲染合成样片 runs/demo/demo-final.mp4。
# 只支持 macOS。可重复运行，装过的步骤会跳过。全程不登录 VEED、不用 FAL_KEY、不花钱。
#
# usage: ./setup.sh             安装 + 渲染样片（第一次 2–5 分钟，看下载走不走代理，下载约 650 MB；装好之后重跑约 45 秒）
#        ./setup.sh --no-demo   只安装，不渲染样片
#
# 环境变量（都可以不设）：
#   WHISPER_PY=<python>                 用已有的、带 faster-whisper 的 Python，不建 .venv
#   SETUP_VENV=1                        有 ~/OpenMontage/.venv 也照样在仓库里建自己的 .venv
#   HTTPS_PROXY=<代理地址>              下载要走代理时自己设（脚本不写死代理；渲染样片时会去掉代理变量）。
#                                       国内直连 huggingface.co 会被重置，模型要靠它；开着 macOS 系统代理时 pip 和模型会自动走
#   PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple   国内直连 PyPI 很慢时换清华镜像
#   HF_ENDPOINT=https://hf-mirror.com   从镜像下载 whisper 模型（2026-11 实测时好时坏，大文件还会转回 HF 的 CDN）
set -euo pipefail
ROOT=${0:A:h}
cd $ROOT
CLI=@veedstudio/openedit-cli
CLI_VERSION=0.10.0                       # 和 package.json 锁定的版本一致
PY_TOO_NEW=3.15                          # faster-whisper 依赖的 onnxruntime 还没有 3.15 的 wheel（2026-11 查过），出了再调高
OE=$ROOT/node_modules/.bin/openedit
VENV_PY=$ROOT/.venv/bin/python
OM_PY=$HOME/OpenMontage/.venv/bin/python

step() { print -P "%F{cyan}== $*%f" }
ok()   { print -P "   %F{green}✓%f $*" }
note() { print -P "   %F{yellow}!%f $*" }
die()  { print -P "%F{red}✗ $*%f" >&2; exit 1 }
ver_ge() {  # ver_ge <有的版本> <要求的版本>
  local -a h n; h=(${(s:.:)1}); n=(${(s:.:)2}); local i
  for i in 1 2 3; do
    (( ${h[i]:-0} > ${n[i]:-0} )) && return 0
    (( ${h[i]:-0} < ${n[i]:-0} )) && return 1
  done
  return 0
}
has() {  # has <python> "<模块, 模块>"：这个 Python 能不能 import 这些模块
  [[ -n $1 ]] && command -v $1 >/dev/null && $1 -c "import $2" >/dev/null 2>&1
}
pyver() { $1 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null }
py_ok() { [[ -n $1 ]] && ver_ge $1 3.9 && ! ver_ge $1 $PY_TOO_NEW }   # py_ok <版本>：能不能拿来建 .venv

demo=1
for a in "$@"; do
  case $a in
    --no-demo) demo=0 ;;
    -h|--help) sed -n '2,/^[^#]/s/^# \{0,1\}//p' ${0:A}; exit 0 ;;
    *) die "不认识的参数 $a（可用：--no-demo、--help）" ;;
  esac
done

# 1. 系统和工具：缺什么就给出 brew install，然后退出
step "1/7 检查 macOS、Node、Python、FFmpeg"
[[ $(uname -s) == Darwin ]] || die "只支持 macOS（配音用 say，转写和渲染只在 macOS 上验证过）"
missing=(); pkgs=()
nv=""; pv=""
if command -v node >/dev/null && command -v npm >/dev/null; then nv=${$(node -v)#v}; fi
if [[ -z $nv ]] || ! ver_ge $nv 20.18.1; then   # openedit-cli 0.10.0 要求 Node >= 20.18.1
  missing+=("Node ≥ 20.18${nv:+（现在是 $nv）}"); pkgs+=(node)
fi
# 建 .venv 用的 Python：≥ 3.9 且低于 PY_TOO_NEW，新的优先。Homebrew 的 python 已经是 3.15，所以不能只看 python3；
# 都没有时，Xcode Command Line Tools 自带的 /usr/bin/python3（3.9）也能用
BASE_PY=""; pv3=""
command -v python3 >/dev/null && pv3=$(pyver python3) || pv3=""
for c in python3.14 python3.13 python3.12 python3.11 python3.10 python3 /usr/bin/python3; do
  command -v $c >/dev/null || continue
  v=$(pyver $c) || continue
  if py_ok $v; then BASE_PY=$(command -v $c); pv=$v; break; fi
done
if [[ -z $BASE_PY ]]; then
  missing+=("Python ≥ 3.9 且低于 $PY_TOO_NEW${pv3:+（python3 是 $pv3，faster-whisper 依赖的 onnxruntime 还没有它的安装包）}")
  pkgs+=(python@3.13)
fi
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then missing+=("ffmpeg 和 ffprobe"); pkgs+=(ffmpeg); fi
if (( $#missing )); then
  for m in $missing; do print "   缺：$m"; done
  command -v brew >/dev/null || print "   先装 Homebrew：https://brew.sh"
  print "   装上之后重跑：brew install ${(j: :)pkgs} && ./setup.sh"
  exit 1
fi
ok "macOS $(sw_vers -productVersion)、Node $nv、Python $pv（${BASE_PY:t}）、$(ffmpeg -version | head -1 | cut -d' ' -f1-3)"

# 2. npm 依赖：当前 registry（例如国内镜像）还没同步这个版本时，改用官方 registry 重试
step "2/7 npm install（$CLI $CLI_VERSION）"
cli_ok() { [[ $(node -p "require('$ROOT/node_modules/$CLI/package.json').version" 2>/dev/null) == $CLI_VERSION ]] }
if cli_ok; then
  ok "已装，跳过"
else
  if ! npm install --no-audit --no-fund; then
    note "当前 registry（$(npm config get registry)）拿不到 $CLI_VERSION，改用 https://registry.npmjs.org 重试"
    npm_config_registry=https://registry.npmjs.org npm install --no-audit --no-fund
  fi
  cli_ok || die "npm install 之后还是没有 $CLI $CLI_VERSION"
  ok "装好了"
fi

# 3. 转写登记成本地（custom）。放在 init 之前：init 只在这个文件不存在时，才从 app-data 目录搬旧的偏好过来
step "3/7 .open-edit-prefs.json"
if [[ -e .open-edit-prefs.json ]]; then
  ok "已有，不动"
else
  print '{"transcription":{"provider":"custom"}}' > .open-edit-prefs.json
  ok "写好了：转写用本地 faster-whisper（provider custom）"
fi

# 4. open-edit 官方 skill + Chrome。0.10.0 的 init 只整目录替换 .claude/skills/open-edit 和 .agents/skills/open-edit，
#    不碰 AGENTS.md / CLAUDE.md（看过源码 cli/dist/commands/init.js）；保险起见仍先备份，装完被改了就还原
step "4/7 open-edit skill + 渲染用的 Chrome"
bak=$(mktemp -d)
cp AGENTS.md CLAUDE.md $bak/
rc=0; $OE init --workspace $ROOT || rc=$?
for f in AGENTS.md CLAUDE.md; do
  cmp -s $bak/$f $f || { cp $bak/$f $f; note "init 改了 $f，已还原"; }
done
rm -rf $bak
(( rc == 0 )) || die "openedit init 失败（退出码 $rc），看上面的输出"
ok "skill 装在 .claude/skills/open-edit 和 .agents/skills/open-edit"
if $OE install-browser --check >/dev/null 2>&1; then
  ok "Chrome Headless Shell 已装，跳过"
else
  $OE install-browser || die "Chrome 下载失败；需要代理时：HTTPS_PROXY=<代理地址> ./setup.sh"
  ok "Chrome Headless Shell 装好了"
fi

# 5. 转写用的 Python。tools/transcribe-local.sh 的查找顺序：WHISPER_PY → 仓库 .venv → ~/OpenMontage/.venv
step "5/7 转写用的 Python（faster-whisper）"
if [[ -n ${WHISPER_PY:-} ]]; then
  [[ -x $WHISPER_PY ]] && has $WHISPER_PY faster_whisper || die "WHISPER_PY=$WHISPER_PY 不能 import faster_whisper"
  WPY=$WHISPER_PY
  ok "用 WHISPER_PY：$WPY"
  note "以后转写也要设同样的 WHISPER_PY（可以记进 LOCAL.md），不设就按 .venv → ~/OpenMontage/.venv 的顺序找"
elif [[ ! -e $ROOT/.venv && ${SETUP_VENV:-0} != 1 ]] && has $OM_PY faster_whisper; then
  WPY=$OM_PY
  ok "发现 ~/OpenMontage/.venv 带 faster-whisper，直接复用（transcribe-local.sh 会自动找到它）"
  note "想在仓库里另建 .venv：SETUP_VENV=1 ./setup.sh"
else
  WPY=$VENV_PY
  if has $VENV_PY "faster_whisper, numpy, PIL"; then
    ok "仓库 .venv 已装好，跳过"
  else
    if [[ -x $VENV_PY ]] && ! py_ok "$(pyver $VENV_PY)"; then   # 例如以前用 Homebrew 的 3.15 建的，装不上 faster-whisper
      note ".venv 是 Python $(pyver $VENV_PY)，装不上 faster-whisper，用 Python $pv 重建"
      $BASE_PY -m venv --clear $ROOT/.venv
    fi
    [[ -x $VENV_PY ]] || $BASE_PY -m venv $ROOT/.venv
    print "   建 .venv（Python $pv），pip install faster-whisper numpy pillow（第一次约 1 分钟）"
    [[ -n ${PIP_INDEX_URL:-} ]] || print "   卡在十几 kB/s 时（国内直连 PyPI 常见）：Ctrl-C，换镜像重跑 PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple ./setup.sh"
    $VENV_PY -m pip install -q --upgrade pip
    $VENV_PY -m pip install faster-whisper numpy pillow \
      || die "pip 安装失败。需要代理：HTTPS_PROXY=<代理地址> ./setup.sh；或换 PyPI 镜像：PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple ./setup.sh"
    has $VENV_PY "faster_whisper, numpy, PIL" || die ".venv 装完还是 import 不了 faster_whisper / numpy / PIL"
    ok "建好了：$VENV_PY"
  fi
fi
# 样片和 tools/koubo/ 的脚本还要 Pillow + numpy
DPY=""
for c in ${DEMO_PY:-} $WPY python3; do has $c "PIL, numpy" && { DPY=$c; break; }; done
if [[ -n $DPY ]]; then
  export DEMO_PY=$DPY
  ok "Pillow + numpy：$DPY"
elif (( demo )); then
  die "样片要用带 Pillow 和 numpy 的 Python：pip3 install pillow numpy，或 SETUP_VENV=1 ./setup.sh 建仓库自己的 .venv"
else
  note "没找到带 Pillow + numpy 的 Python，样片和 tools/koubo/ 的脚本要用：pip3 install pillow numpy"
fi

# 6. whisper small 模型（约 480 MB），下载一次之后转写全程离线
step "6/7 whisper small 模型"
dl='import sys; from faster_whisper.utils import download_model; download_model("small", local_files_only=sys.argv[1] == "1")'
if HF_HUB_OFFLINE=1 $WPY -c $dl 1 >/dev/null 2>&1; then
  ok "已缓存，跳过"
elif env -u HF_HUB_OFFLINE $WPY -c $dl 0; then
  ok "下载好了"
else
  die "模型下载失败。国内直连 Hugging Face 会被重置，要走代理：HTTPS_PROXY=<代理地址> ./setup.sh（也可以试镜像 HF_ENDPOINT=https://hf-mirror.com，时好时坏）"
fi

# 7. 合成样片：全程离线，渲染不挂代理
if (( demo )); then
  step "7/7 渲染合成样片（约 1 分钟）"
  env -u HTTPS_PROXY -u HTTP_PROXY -u ALL_PROXY -u https_proxy -u http_proxy -u all_proxy \
    zsh $ROOT/examples/demo/make.sh
  [[ -s $ROOT/runs/demo/demo-final.mp4 ]] || die "样片没有生成，看上面的输出"
  print
  print -P "%F{green}装好了。%f样片：$ROOT/runs/demo/demo-final.mp4"
else
  step "7/7 跳过样片（--no-demo）"
  print -P "%F{green}装好了。%f渲染样片：zsh examples/demo/make.sh"
fi
print "个人偏好（称呼、素材盘、代理、配乐）：cp LOCAL.example.md LOCAL.md 后照着填"
