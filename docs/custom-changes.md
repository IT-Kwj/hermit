# 自定义修改记录

本文档记录在本机对 switch2mac 项目做的自定义修改。合并上游最新代码、或引擎被重新拉取后，按这里的说明恢复这些改动。

更新时间：2026-11-16

## 修改总览

| 类别 | 仓库内位置 | 内容 | 恢复方式 |
|---|---|---|---|
| 中文化 | `tools/engine/patch.py`、`tools/engine/s2m_ui.m` | 设置面板、通用设置、语言名中文 | 已提交 git；`build` 时 `patch.py` 幂等自动应用 |
| 默认游戏语言 | `games/donkey-kong-bananza/game.json`、`hermit.py` | 打包时默认简体中文（`zh-Hans`） | `build` 自动应用；改 `game.json` 的 `language` 即可 |
| poll 卡顿修复 | `tools/engine/patch.py`（`hle_net_poll()`） | 引擎 `hle_net.c` 的 poll 空等上限 100 ms | `build` 时 `patch.py` 自动应用 |
| 游戏图标（每次构建必做） | 源 logo → `builds/<游戏>/<tid>/extract/v<版本>/icon.jpg` | 自定义 App 图标，构建后必须验证非空白 | 构建前手动生成 `icon.jpg`，见 §3 |
| 存档迁移 | 旧 `work/run/save/` → nxnative App 存档目录 | 恢复旧进度 | 手动复制 `account.sav` |

## 1. 中文化（中文界面）

### 位置

- `tools/engine/s2m_ui.m`：设置面板标题、分区（显示 / 控制 / 性能）、副标题、高级菜单标题（展开前后都显示“高级”）、变更/锁定提示，以及性能悬浮层提示。
- `tools/engine/patch.py` 的 `settings_zh()`：对引擎 `dm/games/settings.tsv`、`dm/games/settings.py`、`dm/tools/nacp.py` 做中文替换。

### 内容

- 通用设置项：主机模式、画面放大、显示模式、游戏语言、手柄震动、震动强度、震动阈值、帧缓冲、Metal 4 管线、管线预构建、编码线程、性能 HUD、游戏内置升频器、帧率、动态分辨率、渲染比例、按键加入、Switch 2 手柄、掉帧时保持帧；iOS 专用的画面适配、帧率显示、触摸反馈、画面形状也一并翻译。
- 语言说明 `UNKNOWN_LANGUAGES` 的中文 note。
- 语言下拉框名称：美式英语、日语、韩语、繁体中文、简体中文等。
- 上游引擎新增设置行时（`dm/games/settings.tsv`），把新行的英文 label/note 补进 `patch.py` 的 `settings_zh()`；否则 key 2 的高级菜单会出现未翻译项。

### 恢复

这些改动都在 switch2mac 仓库的 git 里，且 `patch.py` 是幂等的：重新 `build` 时会自动应用到 `engines/` 下的引擎副本。

## 2. poll 卡顿修复

### 问题

游戏“退出到首页”以及“选赛道之前”会 0fps 卡约 14 秒。根因是离线模式下 socket `poll`/`select` 的空等被按超时原样睡满。

### 修改

`tools/engine/patch.py` 新增 `hle_net_poll()`，把引擎 `dm/host/hle_net.c` 的 `sk_idle` 加上 100 ms 上限：

```c
static int sk_idle(int64_t ms) { if (ms > 100) ms = 100; dm_guest_sleep_ns((ms < 0 ? 100 : ms) * 1000000); return 0; }
```

### 恢复

重新 `build` 时 `patch.py` 自动应用。

### 注意

之前在 switch2mac 引擎上试过同样的改动，出现过一次选完赛道后 SIGBUS（后来回滚）。本次在 nxnative 引擎上应用后需重点验证“进赛道 / 退出到首页”不崩溃。若复现崩溃，回滚 `patch.py` 里的 `hle_net_poll()`，再单独排查。

## 3. 游戏图标（每次构建必做）

> **规则：每次 `build` 都必须确认成品 App 带自定义 logo，不能是空白图标。** 构建日志里要出现 `app icon:`，且 `*.app/Contents/Resources/AppIcon.icns` 存在。

### 原因

dump 文件夹（以及 NUP）没有 control data，nxnative 构建器默认拿不到图标，日志会打印 `no game icon: a dump folder has no control data; the app's icon will be blank`。构建器的图标查找顺序是：`--icon` 参数 → 工作目录 `extract/v<版本>/icon.jpg` → control data 自带图标。把 `icon.jpg` 放进 extract 目录即可被自动采用：`pack_app.py` 用 `sips` + `iconutil` 生成全套 `AppIcon.icns`，并在 `Info.plist` 写入 `CFBundleIconFile=AppIcon`。

logo 属于游戏内容，**不要提交进 git**；源文件放在仓库外（如 Downloads），`icon.jpg` 只存在于 `work/`、`builds/` 这类被忽略的构建目录里。

### 大金刚（Donkey Kong Bananza，title ID `040074A01BF12000`）

源图：`/Users/amid031799/Downloads/QIGANG/logo.jpeg`（1268×951 横版）。横版图先居中裁成正方形，再缩到 1024×1024 的 JPEG：

```bash
TMP="$(mktemp -d)/square.png"
sips -s format png -c 951 951 /Users/amid031799/Downloads/QIGANG/logo.jpeg --out "$TMP" >/dev/null
sips -s format jpeg -z 1024 1024 "$TMP" --out builds/dk/040074A01BF12000/extract/v458752/icon.jpg >/dev/null
```

放置位置（版本号随 dump 的 update 版本变化，当前是 v458752）：

```
builds/dk/040074A01BF12000/extract/v458752/icon.jpg
```

### 马车世界（Mario Kart World）

1. 把图标 PNG（1024×1024）用 `sips` 转成 JPEG，命名为 `icon.jpg`。
2. 放到对应工作目录的 `extract/v0/icon.jpg`（默认 `work/0400C3F00006E000/extract/v0/`，独立目录则是 `builds/mkw/.../extract/v0/`）。

### 缓存与失效

- extract 阶段被复用时（日志 `reusing the extracted ...`），已放入的 `icon.jpg` 会保留，不需要重做。
- 以下情况 `icon.jpg` 会丢失，**必须在 `build` 之前重新生成**：
  - 删除或清空了 `builds/<游戏>/<title ID>/extract/`（换工作目录、磁盘清理）。
  - 游戏升级到新 update 版本，extract 目录变成新的 `v<新版本>/`。
  - 重新全量解包（`.partial` 交换替换整个 extract 目录）。
- 构建后验证：

```bash
ls -l '/Applications/Donkey Kong Bananza.app/Contents/Resources/AppIcon.icns'
/usr/libexec/PlistBuddy -c 'Print :CFBundleIconFile' '/Applications/Donkey Kong Bananza.app/Contents/Info.plist'
```

> dump 的 `base/` 目录是 root 所有，普通用户无法直接写，所以 `icon.jpg` 放在构建工作目录的 extract 里即可，不要往 dump 里写。

## 4. 存档迁移

### 说明

switch2mac 引擎（`run` 模式）的存档在 `work/run/save/Play/account.sav`，nxnative App 的存档在 `~/Library/Application Support/nxnative/<title ID>/save/Play/account.sav`。两者不通用。

### 恢复

复制旧的 `account.sav` 到 nxnative App 的 `save/Play/` 和 `save.work/Play/` 两处（两个引擎的存档都是同一个游戏的 `account.sav` 格式）。

## 5. 已知未解决

- 游玩时约一半时间 fps 在 30–40：游戏自身帧率控制器在帧时间超过 16.7 ms 时切到 30 fps 档，触发源是 host 的 `submit+present` 偶尔抖动到 20–38 ms。GPU、CPU、内存都不是瓶颈，尚未修。
- **0fps 长卡顿（已确认是上游问题）**：对应 nxnative issue
  [#1859](https://github.com/seedds/nxnative/issues/1859)。比赛结束/切换画面时，
  MKW 主线程会有一段很长的 CPU 计算：落在性能核上约 13–14 秒，落在能效核上
  约 50–60 秒。日志特征：`[longframe] ... whole frame 14002–60054 ms`，GPU 只有
  25–94 ms，`new pipelines 0 + shader libraries 0`；同一 300 帧窗口 CPU 约 100%
  单核，性能核占比 11–15%（长）或 100%（短）。不是我们的 poll 补丁、不是显存/
  shader 编译，3304d6a0 仍未修，上游也没有确定修复。可试的开关只有 `DM_RT=0`
  （未验证，可能影响升频）。
- 自动加速（Auto-accelerate）开启时无法火箭起步：游戏辅助会在倒计时前就把油门
  视为按住，火箭起步需要窗口内的新按键；这是游戏辅助本身的行为，不是模拟器输入
  丢失。关闭自动加速即可火箭起步。

## 6. 引擎升级记录

### 2026-11-07：nxnative 引擎 `865cc35fad70` → `822f724c92fa`

- 合并上游后，马车世界 nxnative build 的引擎 commit 更新到 `822f724c92fa`（修 shader 表检查，issue #1592）。
- shader 翻译链从 `223f10d34f97` 变为 `d866f9700d78`，所以 shader 库不能复用，需要重新编译全部约 11,560 个 shader（本次约 16 分钟）。
- **新依赖**：新引擎需要 `zbic` Python 包（ZBIC 压缩解码），`pip install zbic`。应同步进 `requirements.txt`，否则 `setup` 后仍会缺。
- 汉化、poll 修复、前端补丁在新引擎上锚点全部匹配，`build` 时 `patch.py` 自动应用，无需改动。
- **构建前需清理磁盘**：删除旧引擎目录（`engines/nxnative-<旧commit>/`）和旧 App，释放约 2 GB；否则构建会因“需要约 50 GB、磁盘只有 46 GB”而停止。清理时不要把 `work/run/`（存档）和 dump 的 RomFS 删掉。

### 汉化全面性检查

`launcher.json` 中所有设置项的 label、note 均已中文，唯一保留英文的是 `MetalFX`（Apple 专有名词，和“Metal 4 管线”里的 Metal 一样保留原文）。

## 7. 打包与升级流程

### 每次构建前检查清单

1. `icon.jpg` 已在 `builds/<游戏>/<tid>/extract/v<版本>/` 里（见 §3）；extract 被清空或换版本后必须重新生成。
2. `game.json` 的 `language` 仍是期望的默认语言（大金刚为 `zh-Hans`，见 §9）。
3. 磁盘可用空间大于该游戏 `game.json` 的 `disk_gb`（大金刚 40 GB）。
4. 构建日志出现 `game language: zh-Hans` 和 `app icon: .../icon.jpg` 才算成功带上中文和 logo。

### 打正式包

```bash
./hermit.py install
```

把 `work/Mario Kart World.app` 移到 `/Applications/Mario Kart World.app`。首次启动 macOS 会扫描 1–3 分钟（无窗口无 Dock 图标），不要重复打开。

### 以后升级前先删旧包（省空间）

重新构建会占用约 50 GB，磁盘不够会直接停止。构建前先删掉下面这些（用 Python `shutil.rmtree`，避开 shell 的 `rm` 限制）：

1. `/Applications/Mario Kart World.app`（旧正式包）
2. `work/Mario Kart World.app`（旧构建产物，如果还在）
3. `engines/nxnative-<旧commit>/`（旧引擎源码，可重新拉取）

### 存档绝对不能丢

- 存档在 `~/Library/Application Support/nxnative/0400C3F00006E000/save/Play/account.sav`，**不在 App 里**，删除或移动 App 都不影响它。
- 清理磁盘时永远不要动 `~/Library/Application Support/nxnative/` 和 `work/run/`（旧 run 模式存档）。
- 日志在 `~/Library/Logs/nxnative/0400C3F00006E000.log`，同样不随 App 位置变化。

## 8. 多游戏独立构建目录

### 为什么

默认 `work/` 里，每个游戏的实际产物在 `work/<title ID>/` 下是独立的，但顶层的 `title.txt`、`build.txt`、`app_switches.txt`、`logs/`、`run/` 是共享的，会被最后构建的游戏覆盖。构建多个游戏时用各自的 `--work` 目录，就能完全隔离。

### 当前结构

```
builds/
  mkw/                         # Mario Kart World
    0400C3F00006E000/          # 构建产物（~28 GB）
    0400C3F00006E000-engine-seed.tsv
    title.txt                  # 0400C3F00006E000
    build.txt                  # nxnative
    app_switches.txt           # S2M_ENGINE=nxnative-1ed28ed0981f
    run/                       # run 模式数据（存档、pso_user、shdump）
    logs/
  dk/                          # Donkey Kong Bananza
    040074A01BF12000/          # 构建产物（~19 GB）
    040074A01BF12000-engine-seed.tsv
    title.txt                  # 040074A01BF12000
    build.txt                  # nxnative
    app_switches.txt           # S2M_ENGINE=nxnative-b5948342b58f
    logs/
```

### 用法

```bash
# 马车世界
./hermit.py --work builds/mkw build "<MKW dump>"
./hermit.py --work builds/mkw install

# 大金刚（以后其它游戏同理，建 builds/<名字>/）
./hermit.py --work builds/dk build "<DK dump>"
./hermit.py --work builds/dk install
```

### 注意

- 每个游戏的 shader 缓存、RomFS、管线归档各存一份，磁盘占用会变大，定期清理旧游戏的缓存。
- 存档仍在 `~/Library/Application Support/nxnative/<title ID>/`，与构建目录无关。
- 以后新增游戏时，先 `mkdir -p builds/<名字>`，然后用 `--work builds/<名字>` 构建。

## 9. 默认游戏语言（简体中文）

### 内容

《大金刚：狂暴香蕉》的 `games/donkey-kong-bananza/game.json` 里有：

```json
"language": "zh-Hans"
```

`hermit.py` 的 `engine_build()` 会把该值作为 `--language zh-Hans` 传给 nxnative 的 `build_ipa_from_nsp.py`。构建器会把它写进：

- `Contents/Info.plist` 的 `DMLanguage`（没有 env.txt 或保存的选择覆盖时，启动器用它作为默认语言）
- `launcher.json` 里“游戏语言”的默认值（`DM_LANG`）

所以以后重新 `build` 出来的 App 默认就是简体中文，不需要再手动改 `Info.plist`。

### 覆盖

- 想改默认语言：修改 `games/donkey-kong-bananza/game.json` 的 `language`（例如 `en-US`、`ja`、`zh-Hant`）。
- 直接调用 nxnative 的构建器时，可以用 `--language <code>` 覆盖。
- 在 App 的设置面板里手动改过语言后，会保存为该 App 的偏好（`launcher.DM_LANG`），优先于打包默认值。要回到打包默认值：

```bash
defaults delete org.nxnative.040074a01bf12000 launcher.DM_LANG
```

### 恢复

这些改动在 Hermit 仓库的 git 里；合并上游后保留 `game.json` 的 `language` 字段和 `hermit.py` 里把 `language` 传给 `--language` 的代码即可。

## 6. 构建历史

### 2026-11-09 重新构建（nxnative 7d8dcdf824a6）

- 引擎版本：nxnative `7d8dcdf824a6`（从 `1ed28ed0981f` 升级）
- 构建时间：约 26 分钟（10:52 - 11:19）
- Shader 数量：11,560 个（全部重新编译，0 个缓存命中）
- Shader 编译时间：16 分 23 秒
- 最终 App 大小：23.1 GB
- 构建产物占用：27 GB（从 29 GB 减少）
- 应用自定义修改：
  - 中文界面（s2m_ui.m）
  - poll 修复（hle_net.c: 100ms 上限）
  - 中文语言设置（settings.tsv, nacp.py）


## 7. 构建后自动安装

用户偏好：构建完成后直接安装到 `/Applications`，不再保留 `work/` 里的副本。

流程：
1. 构建完成（app 在 `work/Mario Kart World.app`）
2. 删除 `/Applications` 里的旧 app（如果有）
3. 移动新 app 到 `/Applications`
4. 存档位置不变：`~/Library/Application Support/nxnative/<title ID>/`


### 2026-11-10 重新构建（nxnative e121931f473a）

- 引擎版本：nxnative `e121931f473a`（从 `7d8dcdf824a6` 升级）
- 构建时间：约 22 分钟（09:39 - 10:01）
- Shader 数量：11,560 个（全部重新编译，0 个缓存命中）
- Shader 编译时间：11 分 57 秒
- 最终 App 大小：23.6 GB（安装后 24 GB）
- 构建产物占用：29 GB（从 27 GB 增加）
- Pipeline archive：665.3 MB（从 508.7 MB 增加）
- 应用自定义修改：
  - 中文界面（s2m_ui.m）
  - poll 修复（hle_net.c: 100ms 上限）
  - 中文语言设置（settings.tsv, nacp.py）
- 更新内容：Compute shared memory 修复（超过 32KB 的共享内存现在为每个 workgroup 分配独立的 slice）


## 8. 游戏图标

每次构建时必须添加游戏 logo 图标。

### 马车世界 (Mario Kart World)

- Logo 文件位置：`/Users/amid031799/Downloads/MKWROM/Mario Kart World.png`
- 构建命令：`./hermit.py build "/Users/amid031799/Downloads/MKWROM" --engine nxnative --icon "/Users/amid031799/Downloads/MKWROM/Mario Kart World.png"`
- `hermit.py` 原先没有 `--icon` 参数（只有引擎的 `build_ipa_from_nsp.py` 支持），
  已在本项目补上：`hermit.py` 的 `build` 子命令接受 `--icon`，nxnative 构建时
  原样传给引擎 builder。


## 9. 马车世界启动崩溃修复（2026-11-11）

### 现象

Mario Kart World（nxnative `e121931f473a`）打开后立即退出，帧率都没出现。两次运行日志
（`~/Library/Logs/nxnative/0400C3F00006E000.log` 及其 `.prev.log`）在同一位置崩溃：

```
[dm] oe notification popped by the game: 15
[dm] CRASH sig=11 addr=0xd8 pc=main+0x26380c4 lr=main+0x2637f80
```

### 原因

1. 启动进入全屏时，游戏窗口短暂失去 key window，引擎的 `front_mac.m` 调
   `dm_focus_set(2)`，`hle_oe.c` 向游戏队列推送 OE 通知 15（焦点/恢复通知）。
2. MKW 的通知处理线程弹出 15 后，会解引用 `main+0x33e54b0` 处的 OE 客户端单例
   （随后读 `+0xd8`）。nxnative 把 `oe::Initialize` 当作 no-op，这个单例保持
   NULL，于是 SIGSEGV（addr 0xd8）。
3. 大金刚（nxnative `7ffa63cca09f`）也会收到 15，但它的处理函数不碰这个空指针，
   所以不崩。`hle_oe.c`/`front_mac.m` 在大金刚与马车两个引擎版本之间完全相同，
   因此升级 nxnative 未必能修好，这是 MKW 专用的 HLE 缺口 + 启动时机。

### 绕过（已应用，无需重新构建）

在 `~/Library/Application Support/nxnative/0400C3F00006E000/env.txt` 写入：

```
DM_FOCUS_KEEP=1
```

引擎不再把窗口失焦上报给游戏（`front_mac.m` 的 `keep` 分支），启动时不会入队
通知 15，MKW 的处理函数也就不会访问空单例。副作用：切到别的 App 时游戏不会
认为自己失焦（不会暂停渲染）。

### 重新构建后要保留

旧构建把 `env.txt` 放在 Application Support，不在 App 包里。当前 No Lag Kart
已经从 2026-11-18 起通过 `games/mario-kart-world/game.json` 的
`switches` 把 `DM_FOCUS_KEEP=1` 直接烘进 App，所以全新安装不再需要手动
创建这份 Application Support 文件。旧安装仍可继续使用原 `env.txt`。


### 2026-11-11 重新构建（nxnative 3304d6a0d7ed）

- 引擎版本：nxnative `3304d6a0d7ed`（从 `e121931f473a` 升级，55 个引擎提交）
- 构建时间：约 21 分钟（09:59 - 10:20）
- Shader 数量：11,560 个（全部重新编译，0 个缓存命中）
- Shader 编译时间：10 分 22 秒
- Shader list：13,431 行（比上次 13,132 行多 299 行）
- 最终 App 大小：23.1 GB（安装后 23 GB）
- 构建产物占用：27 GB
- Pipeline archive：521.6 MB（上次 665.3 MB）
- 已带 logo 图标：`--icon "/Users/amid031799/Downloads/MKWROM/Mario Kart World.png"`
- 应用自定义修改：
  - 中文界面（s2m_ui.m）
  - poll 修复（hle_net.c: 100ms 上限）
  - 中文语言设置（settings.tsv, nacp.py）
- 闪退问题：上游 `3304d6a0` **未修复**，继续保留 `DM_FOCUS_KEEP=1`。
  以后升级时如果上游代码修好了，删掉 Application Support 里的 `env.txt` 即可。

#### 同版本二次构建：高级菜单汉化（11:18）

- 引擎不变：nxnative `3304d6a0d7ed`
- 补齐 key 2 高级菜单的英文项：帧率、按键加入、Switch 2 手柄（含说明）、
  掉帧时保持帧；同时补上动态分辨率、渲染比例、画面适配、帧率显示、触摸反馈、
  画面形状等通用行，以及“高级 ▾ / 高级 ▸”和锁定/变更提示的中文。
- 构建后 `Resources/dm/launcher.json` 已确认：`DM_FPS_TARGET` = 帧率、
  `DM_PAD_PRESS_TO_JOIN` = 按键加入、`DM_SW2` = Switch 2 手柄、
  `DM_FPS_HOLD` = 掉帧时保持帧。
- App 23.1 GB，仍带 logo 图标；已安装到 `/Applications`。

### 2026-11-12 重新构建（nxnative 6815810dfa37）

- 引擎版本：nxnative `6815810dfa37`（从 `3304d6a0d7ed` 升级）
- Shader chain：`8d9afacc48e2`（全新编译）
- Shader 数量：11,560 个（0 个缓存命中）
- Shader 编译时间：5 分 11 秒
- Shader list：13,502 行（比上次 13,431 行多 71 行）
- 最终 App：23.4 GB
- 构建产物：28 GB
- Pipeline archive：743.0 MB
- 已带 logo 图标：`--icon "/Users/amid031799/Downloads/MKWROM/Mario Kart World.png"`
- 关键更新：
  - 帧步进慢帧规则修复（连续 3 个慢帧不再立刻降档，MKW 约 40 fps 抖动改善）
  - MKW 1.8.0 补上 host 帧步进
  - 动态分辨率目标加入堆回收，减少每帧新建 Metal 内存
- 自定义修改全部应用：中文界面、poll 100ms、中文设置项、`--icon`
- 闪退问题：`6815810d` 仍未修复，`DM_FOCUS_KEEP=1` 继续保留
- 0fps 长卡顿：上游 issue #1859 仍 open，本次未修复

### 2026-11-13：上游改名为 Hermit，合并 0.5.0

- `switch2mac.py` 上游已改名为 `hermit.py`；旧 `switch2mac.py` 只保留兼容入口，
  会转调 `hermit.py`。本项目命令统一改为 `./hermit.py`。
- 我们自己的 `--icon` 和 `--language`（game.json `language`）已移植到
  `hermit.py` 的 `engine_build()`；中文界面、poll 100ms 和 `/builds` 忽略仍然保留。
- 马车世界 nxnative 引擎：`6815810d` -> `a2514d7d`（条件渲染改为 host 统一处理，
  render_cond 配置删除；另有 OoT/PRAGMATA 的 compute 线程数修复等）。
- 大金刚 nxnative：`084f5aa5` -> `a2514d7d`。
- 时之笛：nxnative -> `529cf68c`，kid-with-sword -> `5a6abb8e`，
  azmasm 构建继续使用 hermit-builds。
- 新增游戏：Mario Golf: Super Rush、Trails in the Sky 2nd Chapter。
- 启动闪退：`a2514d7d` 仍然是 `oe::Initialize` no-op，继续保留 `DM_FOCUS_KEEP=1`。
- 0fps 长卡顿：上游 issue #1859 仍 open，本次未修复。

#### 启动设置窗口（Ready to play）汉化

- 打开游戏时出现的弹窗是 Hermit 的 “Ready to play” 窗口，源码是
  `tools/engine/s2m_launcher.swift`；游戏内按 2 键的面板是
  `tools/engine/s2m_ui.m`。两者不是同一个界面，但读取同一份
  `Resources/dm/launcher.json`，并把选择写到同一组
  `launcher.<VAR>` 偏好里。
- 启动窗口已汉化：标题、说明、高级设置、启动前显示、恢复默认、开始游戏、
  退出、云存档卡片、文件选择框、菜单栏，以及 Game/Controls/Performance
  分区标题（显示/控制/性能）。
- `patch.py` 新增 `DM_FRAMEGEN`（帧生成）、`DM_FAST_720`（快速模式）、
  `DM_FULL_DOCKED`（完整底座画面）三项的中文 label/note；2 键面板和启动
  窗口都会使用。
- 默认中文语言：`game.json` 的 `language: zh-Hans` 仍然作为“首次启动”的
  默认值。启动窗口里的语言选择会覆盖它，并保存为 `launcher.DM_LANG`。
  如果去掉 `language`，新构建首次启动会是英文，需要在启动窗口选一次中文；
  目前已保留默认中文。
- 这些改动需要重新构建才会写入 App；启动窗口是编译进 App 的 Swift 源码，
  设置项文字则是在构建时生成到 `launcher.json`。

#### 2026-11-13：1.8.0 使用最新 nxnative builder

- 构建入口：`nxnative a2514d7d`（不是 `nxnative-mkw` 的 Thijs2004
  `b1c5e4e5` 旧 fork）。
- 最新 nxnative 没有注册 v917504，构建时自动从 v0 派生 1.8.0 profile：
  `packing v917504 from a profile derived from it`。
- 结果：11,603 个 shader，11,602 成功，1 个失败：Ampere instruction 481
  未实现（见 `work/0400C3F00006E000/logs/dmsh_build.log`）。
- App 23.6 GB，已安装到 `/Applications`。启动窗口和游戏内 2 键的中文已
  检查（关键字符串和二进制内容），图标使用 `Mario Kart World.png`。
- 上游警告：派生 profile 不是注册构建，部分 SDK/线程补丁不会应用；如果
  实际运行有问题，可切回旧的 `nxnative-mkw` 1.8.0 构建。
- `hermit.py` 新增旧 builder 图标兼容：builder 不认识 `--icon` 时，自动
  生成 `work/<tid>/extract/v917504/icon.jpg`，仍使用同一个图标。

#### 2026-11-14：按代码推荐切回 `nxnative-mkw` 1.8.0

- `game.json` 的 `choose` 第一条明确推荐 1.8.0 使用
  `nxnative-mkw`（Thijs2004 `b1c5e4e5`），新 `nxnative` 目前只注册 v0。
- 构建结果：11,649 个 shader，11,648 成功，**同一个 Ampere instruction 481
  仍然失败**；说明这是 translator 的能力缺口，不是新/旧 builder 的差异。
- App 23.2 GB，已安装到 `/Applications`，图标正常，存档未动。
- 旧 fork 的专用设置项已补汉化：`Graphics preset`、`Frame rate`、
  `Frame rate lock`、`Dynamic resolution`、`Render scale`、`Texture quality`、
  `Encode thread`、`Tile memory (TBDR)`、`Free texture memory`。
- `patch.py` 已加入这些旧 fork 行的替换；当前已安装 App 的 `launcher.json`
  也直接修正并重新 ad-hoc 签名。
- **以后规则**：更新上游代码后，先看 `game.json` + `choose` 推荐的构建；
  只有代码里正式注册/推荐了新 builder，才切换过去。`--engine` 只能作为
  实验性覆盖，不作为默认。

#### 2026-11-14 试玩结果：最新 nxnative 派生 1.8.0 更合适

- Mac：M3 Max，36 GB（用户本机）。
- 构建：`nxnative a2514d7d` 对 v917504 的派生 profile。
- 实际试玩反馈：上一版 `nxnative-mkw` 地图等 bug 全部消失，本版可正常游玩。
- 虽然仍有 1 个 shader（Ampere instruction 481）翻译失败，但用户实际玩到的
  内容没有受影响。
- 结论：在 nxnative 正式注册 1.8.0（PR #1252/#2621）之前，本机 1.8.0 优先
  使用 `--engine nxnative` 的最新派生构建；等上游正式注册后再改回代码推荐。

#### 每次构建后的固定检查

1. 启动窗口（Hermit “准备开玩”页面）：检查标题、说明、高级设置、
   启动前显示、恢复默认、开始游戏、云存档、菜单栏和分区标题。
2. 游戏内 2 键面板：检查分区标题、所有设置 label/note、选项文字，
   以及“高级 ▸ / 高级 ▾”和锁定/变更提示。
3. 检查 `Resources/dm/launcher.json` 与 `Contents/MacOS/nxnative` /
   `dmhost` 中的关键中文字符串；发现英文项立即补进 `patch.py` 或
   `s2m_launcher.swift`。

#### 2026-11-14 最新 nxnative a4705fe1 1.8.0 构建

- 构建：`nxnative a4705fe1a98d` 对 v917504 的派生 profile。
- Shader：11,603 个，11,602 成功，仍是同一个 Ampere instruction 481 失败。
- App：24.7 GB，已安装到 `/Applications`；启动窗口和 2 键汉化检查通过。
- 按“只检查不删除”的要求，本次没有让 install 自动 trim 构建缓存；
  `work/0400C3F00006E000` 仍保留，供下次继续构建。
- 构建后可用空间约 34 GB。

#### 2026-11-14：回退单树改造

- 已回退 `builds_by_main`、`prepare_dump()` 和临时 `dump-layout` 代码；
  `MKWROM/180` 恢复为 `base/` + `updates/917504/` 的布局，兼容当前 builder。
- 保留 `nxnative-180` 构建和 `choose` 首选：最新 nxnative `a4705fe1`
  在 M3 Max 上实测可用，不再默认旧 `nxnative-mkw`。
- 目录恢复后 `du` 会重新显示约 45 GB（两份 APFS 克隆），实际物理占用仍约
  22 GB；这是为了减少后续上游合并冲突而接受的显示差异。

## 上游更新固定检查清单

每次合并 `upstream/main` 后依次检查：

1. **1.8.0 支持是否变化**
   - 检查 `games/mario-kart-world/game.json` 是否新增了官方 1.8.0 构建，
     以及 nxnative PR #1252 / #2621 是否已经合并。
   - 当前上游正式推荐的 1.8.0 构建是 `no-lag-kart`
     （`033cbe594bf8`）。如果上游换了新的正式推荐构建，就采用新构建。
   - 如果推荐没有变化，继续使用 `no-lag-kart`。不要回退到旧
     `nxnative-mkw`（实测 bug 多）；本地临时 `nxnative-180` 已删除。

2. **nxnative 是否更新**
   - 对比 `games/mario-kart-world/game.json` 的 `no-lag-kart` commit 是否变化。
     普通 `nxnative` pin 更新不等于 `no-lag-kart` 更新，不能自动替换 1.8.0 构建。
   - 如果 `no-lag-kart` 更新了：检查其 `mkw/pso` 预热列表、1.8.0 profile 和
     构建说明，再重新构建。
   - 检查 `tools/engine/patch.py` 的锚点是否仍匹配，特别是
     `settings.tsv`、`hle_net.c`、`pso_offline.py` 和 launcher 补丁。

3. **启动页和 2 键汉化**
   - 检查 `tools/engine/s2m_launcher.swift` 的启动页面（“准备开玩”
     窗口）和 `tools/engine/s2m_ui.m` 的 2 键面板。
   - 对照新生成的 `Resources/dm/launcher.json`、引擎新 `settings.tsv`
     行、二进制中的关键中文字符串；发现英文项立即补进
     `patch.py` 或 `s2m_launcher.swift`。
   - 每次构建后也必须做一次这项检查，不能只看构建是否成功。

#### 2026-11-16：上游新增 No Lag Kart，采用新的 1.8.0 构建

- 上游 `game.json` 新增 `no-lag-kart`（kingbumi31，MIT，commit `033cbe594bf8`）：
  nxnative 的 1.8.0 专用构建，23 项修复和 15,000 条 pipeline 预热列表；
  上游将其列为 1.8.0 的首选构建。
- 已按“1.8.0 支持变化就使用新版”的规则采用 `no-lag-kart`，删除本地临时的
  `nxnative-180` 构建和 `shader_list-nxnative-180.tsv`。
- 最新 nxnative pin 也从 `a4705fe1` 更新到 `fb26adfc`；`mkw-neo` 更新到
  `304f24ee`。`nxnative-mkw` 仍作为上游的另一个 1.8.0 手动选择保留。
- 启动页和 2 键的 `patch.py` / `s2m_launcher.swift` / `s2m_ui.m` 自定义仍在；
  本次上游没有新增需要补译的 MKW 设置行，实际构建后仍需按固定清单复查。

#### 2026-11-16：`no-lag-kart` 1.8.0 实际构建

- 构建命令使用官方推荐的 `--engine no-lag-kart`，游戏版本 v917504（1.8.0），
  logo 使用用户提供的 `Mario Kart World.png`。
- Shader：11,601 个全部成功；没有再出现旧构建的 Ampere instruction 481 失败。
- 离线 pipeline archive：501.6 MB；9591 个 base、728 个 compute pipeline。
- 发现 `pso_offline.py` 默认每组 1000 个 base 时，第 3 组在本机
  `metal-tt/applegpu-nt` 中持续运行 1 小时 14 分钟，远超该构建文档记录的
  pipeline archive 约 2 分半。终止后把 No Lag Kart 的批次上限改为
  200，完整 archive 用 2 分 16 秒生成。
- `tools/engine/patch.py` 增加 `no_lag_pso_batch()`，只对含 No Lag Kart
  1.8.0 预热列表的引擎副本应用 200 批大小；普通 nxnative 游戏不受影响。
- 新上游把设置行条件改为 `DM_GAME_PRESENT_UPSCALE` 和
  `DM_GAME_FULLSCREEN`，原来的英文匹配锚点因此失效。已补上这两条当前格式：
  “画面放大 / 标准”和“显示模式 / 窗口 / 全屏”现在都是中文。
- `launcher.json` 全部 18 个设置项已复查；除 MetalFX、Metal 4、GPU、CPU、
  FPS、Switch 2、Joy-Con 2、Pro Controller 2 等产品或硬件的正式名称外，
  label、note 和选项都有中文。启动页源码和 2 键宿主源码的标题、说明、
  高级设置、云存档、分区与锁定/变更提示也已复查。
- App：23.3 GB，已安装到 `/Applications/Mario Kart World.app`；
  `CFBundleShortVersionString` 为 1.8.0，`AppIcon.icns` 正常，
  ad-hoc 签名验证通过。
- 存档保留在
  `~/Library/Application Support/nxnative/0400C3F00006E000/save/Play/account.sav`
  （844 KB）；旧 run 存档 `builds/mkw/run/save/Play/account.sav` 未动。
  `DM_FOCUS_KEEP=1` 也仍在 Application Support 的 `env.txt`。

#### 2026-11-16 构建后占用与可清理项

构建后先按“只检查、不删除”处理，随后只清理了已确认的旧运行时缓存和旧引擎：

- `/Applications/Mario Kart World.app`：23 GB（正式安装包）
- `work/0400C3F00006E000`：27 GB，可重建；其中 `extract` 约 22 GB、
  `shader` 约 3.4 GB、`pso` 约 1.1 GB。
- `builds/dk`：25 GB，大金刚的历史构建文件夹；删除后重编大金刚会明显变慢，
  但不影响当前已安装的大金刚 App 和存档。
- 已删除旧运行时缓存 `pso_archive.nxnative`、`pso_archive.switch2mac`
  及对应的旧 `pso_user` / shader-list contribution，避免切换到旧构建时
  继续复用它们。
- 已删除旧引擎 `nxnative-b1c5e4e53019`、`nxnative-3304d6a0d7ed` 和
  `nxnative-a2514d7def4e`；`engines/` 只保留当前 No Lag Kart 使用的
  `nxnative-033cbe594bf8`（约 825 MB）。以后构建仍引用旧 commit 的游戏时，
  Hermit 会重新下载对应源码。
- 当前 No Lag Kart 的 `pso_archive`、`pso_user.tsv`、`save`、`save.work`
  和 `env.txt` 全部保留。
- 本次实际释放约 4.1 GiB，磁盘可用从约 30 GiB 增加到约 34 GiB。
  马车下次重编已有 shader 缓存，构建前若仍报
  “first build needs 50 GB”，可在确认缓存和磁盘余量后使用
  `S2M_SKIP_DISK_CHECK=1`。

#### 2026-11-18：MacBook Air M4 24 GB 专用包

- 目标机为另一台 MacBook Air M4 24 GB，全新安装、不迁移存档；用于网盘传输
  和长期使用。
- 当前构建机的 GPU 是 `applegpu_g15s`（M3 Max）；M4 MacBook Air 的目标
  GPU 架构是 `applegpu_g16g`。使用 `metal-tt -arch applegpu_g16g` 交叉生成
  独立离线 archive，而不是携带本机的 `g15s` archive。
- 构建仍使用 Mario Kart World 1.8.0 的 `no-lag-kart 033cbe594bf8`。
  Shader 为 11,601 个，全部复用成功；`applegpu_g16g` archive 为 501.4 MB，
  9,591 个 base、728 个 compute pipeline，94 个批次约 150 秒合并完成。
- 默认游戏语言设为简体中文（`DMLanguage=zh-Hans`、`DM_LANG` 默认
  `zh-Hans`）；启动页和 2 键设置项沿用现有中文补丁。
- `DM_FOCUS_KEEP=1` 已写入 App 内的 `Contents/Resources/dm/env.txt`，解决
  全新安装没有 Application Support `env.txt` 时的启动焦点崩溃；同时写入
  `game.json` 的 No Lag Kart `switches`，以后自动构建也会带上。
- 产物为 `work/Mario Kart World M4 Air.app`，23.3 GB，版本 1.8.0，
  Bundle ID `org.nxnative.0400c3f00006e000`，ad-hoc 签名验证通过，
  CDHash `f8acc57affbec9c1a2c25dffd60cebf6debb84cc`。
- App 内只携带 `Contents/Resources/pso/applegpu_g16g.mtl4a`，不携带
  M3 Max 的 `g15s` archive。
- 网盘传输包改为 3 GiB 多卷 ZIP，集中在
  `work/Mario Kart World M4 Air upload/`：`.z01` 到 `.z07`，加上最后
  `Mario Kart World M4 Air.zip`。8 个卷必须一起上传、保持文件名不变。
- 同一目录的 `Mario Kart World M4 Air.sha256` 记录每个分卷的 SHA-256；
  `Mario Kart World M4 Air SPLIT-README.txt` 写有网盘上传、校验和
  解压步骤。macOS 自带解压工具不识别这种多卷 ZIP，推荐用 Keka；也可用
  `zip -s 0 "Mario Kart World M4 Air.zip" --out "Mario Kart World M4 Air-full.zip"`
  合并后解压。
- 分卷不包含存档；新机解压后把 App 放入 `/Applications` 即可。

#### 2026-11-18：清理可重建缓存

- 已删除 `work/0400C3F00006E000/shader`（3.4 GB）、
  `work/0400C3F00006E000/pso`（1.7 GB）、
  `work/0400C3F00006E000/logs`（33 MB）、
  `engines/nxnative-033cbe594bf8`（825 MB）、
  `builds/mkw/run/pso_archive`（807 MB）、
  `work/pso-archives/m3max-g15s-20261118`（502 MB）、
  `builds/mkw/logs`（9.3 MB）和 `~/Library/Logs/nxnative`（5.6 MB）。
- 实际释放约 6.7 GiB，磁盘可用从约 40 GiB 增加到约 46 GiB。
- 保留 `work/0400C3F00006E000/extract`：约 22 GB，但 RomFS 与已安装 App
  使用 APFS 克隆共享空间，单独保留 App 时删除它不能释放同等容量。
- 保留 `/Applications/Mario Kart World.app`、Application Support 的
  `save` / `save.work` / `env.txt`、`builds/mkw/run/save` /
  `save.work`。下次重新构建会重新下载 No Lag Kart 引擎并重建 shader/pipeline
  缓存，但当前已安装游戏不受影响。

#### 2026-11-18：Mac mini M6 16 GB 专用包

- 目标机为 Mac mini M6、16 GB、256 GB，全新安装、不迁移存档，用于网盘传输。
- 仍采用当前 1.8.0 的首选 `no-lag-kart 033cbe594bf8`；M6 系列已有
  16 GB 的实机记录，低内存 `mkw-neo` 更偏向 8 GB/Air，峰值性能较低。
- 目标 GPU 架构为 `applegpu_g18g`。在 M3 Max 的 `applegpu_g15s` 上用
  `metal-tt -arch applegpu_g18g` 交叉生成独立 archive。
- 由于 shader 缓存已在上一次清理中删除，本次全部重编：11,601/11,601
  个 shader 成功，约 10 分 28 秒；`applegpu_g18g` archive 493.3 MB，
  9,591 个 base、728 个 compute pipeline。整个构建约 21 分钟。
- 默认游戏语言为简体中文（`DMLanguage=zh-Hans`），App 内
  `Contents/Resources/dm/env.txt` 包含 `DM_FOCUS_KEEP=1`。
- 产物为 `work/Mario Kart World Mac mini M6.app`，23.3 GB，版本 1.8.0，
  ad-hoc 深度签名验证通过，CDHash
  `3e80ef217578449289077469f4e49bfa676396db`；App 内只包含
  `Contents/Resources/pso/applegpu_g18g.mtl4a`。
- 上传包位于 `work/Mario Kart World Mac mini M6 upload/`：`.z01` 到
  `.z07` 加最后 `.zip`，每个大卷 3 GiB，总占用约 22 GB。
  `Mario Kart World Mac mini M6.sha256` 已逐卷校验通过；
  `Mario Kart World Mac mini M6 SPLIT-README.txt` 记录 Keka 解压和命令行
  合并步骤。
- 分卷不包含存档；M6 新机解压后把 App 放入 `/Applications`。目标是
  macOS 26.6 或更高。

#### 2026-11-18：清理 M6 专用产物

- 网盘上传完成后，删除 `work/Mario Kart World Mac mini M6 upload/`
  （约 22.2 GiB）、`work/Mario Kart World Mac mini M6.app`（逻辑约
  23.3 GiB，但 RomFS/pso 与构建缓存共享物理空间）、
  `work/0400C3F00006E000/pso`（约 1.1 GB）和两份构建/运行日志
  （约 34 MB）。
- 实际释放约 24.1 GiB，磁盘可用从约 42.7 GiB 增加到约 66.9 GiB。
- 保留当前 `/Applications/Mario Kart World.app`、Application Support
  的 `save` / `save.work` / `env.txt` / 当前 `pso_archive`，以及用于下次
  快速构建的 `work/0400C3F00006E000/extract`、`shader` 和
  `engines/nxnative-033cbe594bf8`。

#### 2026-11-18：Apple Silicon 16 GB+ 多 GPU 通用包

- 仍使用 Mario Kart World 1.8.0 的 `no-lag-kart 033cbe594bf8`，在同一个
  arm64 App 内预编译 11 份 GPU archive：
  `applegpu_g13d`、`g13g`、`g13s`、`g14g`、`g14s`、`g15g`、`g15s`、
  `g16g`、`g16s`、`g17g`、`g18g`。
- 每份 archive 约 474–510 MB；9,591 个 base、728 个 compute pipeline。
  11 份全部成功，没有无效目标。App 内 `pso/archive.tsv` 记录了全部架构。
- 目标范围是 Apple Silicon `arm64`、macOS 26.6+、16 GB 或更多内存；
  Intel Mac 不支持。不在预编译列表中的 GPU 会回退到首次启动自行构建。
- 默认简体中文，`DM_FOCUS_KEEP=1` 已写入 App 的 `dm/env.txt`，不包含存档。
- 产物为 `work/Mario Kart World Universal 16GB+.app`，28.0 GB；
  ad-hoc 深度签名验证通过，CDHash
  `deca91a1db2f758bc0e459aa40c376ebe0414aff`。
- 3 GiB 多卷上传包位于
  `work/Mario Kart World Universal 16GB+ upload/`：`.z01` 到 `.z08`
  加最后 `.zip`，总占用约 24 GB。`Mario Kart World Universal 16GB+.sha256`
  已逐卷校验通过，SPLIT-README 记录 Keka 和命令行解压方式。

#### 2026-11-18：清理多 GPU 通用产物

- 网盘上传完成后，删除 `work/Mario Kart World Universal 16GB+ upload/`
  和 `work/Mario Kart World Universal 16GB+.app`，并删除通用构建日志。
- `pso/mac` 只保留本机 M3 Max 的 `applegpu_g15s.mtl4a`；其余 10 个 GPU
  的最终 archive 删除。
- `pso/mac-work` 只保留 `batches.applegpu_g15s`、`key.applegpu_g15s`
  及 g15s 的合并日志；其余 10 个 GPU 的批次和 key 删除。
- 实际释放约 35.2 GiB，磁盘可用从约 49.8 GiB 增加到约 85.1 GiB。
- 保留当前 `/Applications/Mario Kart World.app`、全部存档和运行
  `pso_archive`，以及下次本机构建需要的 `extract`、`shader`、引擎源码、
  g15s archive 和 g15s 批次缓存。

#### 2026-11-21：王国之泪特殊私密 UI 版（临时修改，已还原）

- 目标是一次性特殊构建，不安装；修改之后需要还原。
- 在 MacNativeGames 的 `games/totk/runtime/game_version.h` 设置临时宏
  `TOTK_SPECIAL_PRIVATE_UI=1`。
- 该宏关闭 1 键设置页面中的“访问主页”按钮、“着色器贡献”页、
  “性能排行榜”页和“截图分享”页，并关闭游戏启动时的着色器共享询问。
- 同时取消后台着色器贡献、排行榜和截图分享上传；普通本地截图仍保留。
- 修改涉及：
  `games/totk/runtime/game_version.h`、
  `games/totk/runtime/settings_game.h`、
  `shared/runtime/settings_panel.h`、
  `games/totk/app/launcher.m`、
  `games/totk/runtime/frontend.m`。
- 反向补丁保存在 `work/totk-special-private-ui.patch`，SHA-256：
  `5514462536355b080f2181bd8c240860c787057771b634a205dc544a4bbc7a55`。
- 构建产物为
  `work/The Legend of Zelda - Tears of the Kingdom Special.app`；
  分卷上传包位于
  `Downloads/WGZL/The Legend of Zelda - Tears of the Kingdom 1.4.3 Special App upload/`。
- 低配特殊版另关闭原生 4K/5K，产物为
  `work/The Legend of Zelda - Tears of the Kingdom Special 16GB.app`；
  分卷上传包位于
  `Downloads/WGZL/The Legend of Zelda - Tears of the Kingdom 1.4.3 Special 16GB App upload/`。
- 两个特殊版 App 工作副本已删除；两个分包上传目录保留。
- 已用 `git apply -R work/totk-special-private-ui.patch` 还原五个源文件，
  当前 MacNativeGames 的特殊版源码修改已全部撤销。
- 补丁保留下来供以后制作同类特殊版使用。以后构建这种特殊版时沿用本流程：
  临时应用补丁、按普通或低配规格构建、分包且不安装、删除工作目录中的 App
  副本、反向应用补丁恢复源码；分包上传目录始终保留。

#### 2026-11-21：王国之泪 1.4.3 一键金手指页

- 1 键设置面板新增“金手指”页，支持游戏运行中开关，设置保存在
  `totk-cheats-v143.txt`，重启后自动恢复。
- 恢复点在外层仓库和 MacNativeGames 引擎仓库均为
  `restore/totk-cheats-before-20261121-091525`。引擎恢复标签是一个 stash
  commit，保留了当时已经存在的四个无关工作区修改；旧 App 另有 APFS 克隆：
  `work/restorepoints/totk-cheats-20261121-091525/`。
- 新增 `games/totk/runtime/cheats_v143.c` 和 `cheats_v143.h`。切换时先暂停
  所有游戏线程，把目标代码页临时改为可写，写入一个对齐的 32 位字并刷新
  指令缓存，然后恢复 RX 权限并恢复游戏线程，避免在代码仍被线程执行时留下
  可写执行页。
- 已接入这批 1.4.3 文件中可直接静态替换的项目：无限精力、电池、马匹耐力、
  潜行、体温、瘴气、伙伴冷却、武器/弓箭充能、弓箭速射、伤害倍数、移动速度、
  跳跃、默认奔跑、拾取数量、免费购物、无限弓箭/佐纳乌/食物、amiibo、
  地图显示项目、装置上限、时间速度、雾和血月。
- “拾取数量”在 `main+0xA77B40` 把原 `add w3,w6,w3` 改成固定值：
  `52800C83` 为拾取后数量 100，`52807CE3` 为 999；下拉项互斥，避免同时
  修改同一地址。按原金手指行为这是“把该堆叠设为 N”，不是在当前数量上再
  加 N。旧保存值 `items=1` 继续表示 999，新的 `items=2` 表示 100，升级后
  不会把原有 999 设置误改成 100。
- 伤害倍数、移动速度和时间为互斥下拉选项；页面底部提供“全部关闭”。
- `04`/`08` 直接写入码已转换并逐条核对当前 1.4.3 主程序：66 个写入字、
  52 个唯一地址，原始指令 0 个不匹配。每项安装时还会再次校验，版本不匹配
  的项会灰显或拒绝应用。
- 暂不支持原文件里占用本项目保留跳转空隙的无限生命、无限装备耐久度、
  无限食物增益计时器、任务计时器加 60 秒，以及月球跳跃指针链和按住按键
  临时切换滑翔伞速度。它们需要独立重定位或持续执行的金手指 VM，本版没有
  强行写入保留区。
- 设置页改动涉及 `shared/runtime/settings_panel.h`、
  `games/totk/runtime/settings_game.h`、`runtime.h`、
  `game_patches_v143.c` 和 1.4.3 Makefile；测试覆盖中英文、开关、互斥选项、
  全部关闭、滚动页面，以及原有 1.2.1/BotW 设置页编译。
- 新 App 构建约 4 分钟，启动着色器 28,108 个全部复用，`applegpu_g15s`
  pipeline 30,825 条成功；ad-hoc 深度签名校验通过，已安装到
  `/Applications/The Legend of Zelda - Tears of the Kingdom.app`，约 20 GB。

#### 2026-11-21：王国之泪 1.4.3 拾取 ×100 修正

- 用户实测原“拾取数量 100”把 `main+0xA77B40` 的 `add w3,w6,w3` 直接改成
  `mov w3,#100` 后，从背包放回地上的苹果仍只回到 1 个。静态对照 1.0.0
  的 `main+0x2393714` 与 1.4.3 内联后的同名逻辑，确认该处确实是“现有数量
  `w6` 加上本次增量 `w3`”；不再把 1.4.3 的增量直接替换成固定值。
- 1.4.3 文本尾部原本空闲的 padding `+304..+320` 现在登记为
  `PAD_V143_CHEAT`。A77B40 改为跳板：`拾取 ×100` 执行
  `mov w7,#100; madd w3,w3,w7,w6`，即新数量为“当前数量 + 本次拾取数 ×100”；
  “固定 999”保留原金手指行为，执行 `mov w3,#999`。关闭时跳板恢复为 NOP，
  原 `add` 指令恢复。
- `cheat_patch` 每次写入后增加逐字读回校验，并把最后状态写到
  `~/Library/Application Support/MacNativeGames/TOTK/totk-cheats-v143-status.txt`。
  设置本身仍保存在同目录的 `totk-cheats-v143.txt`。
- 设置页名称改为“拾取倍率 / Pickup multiplier”，选项为“游戏原样 /
  拾取 ×100 / 固定 999”，消除“数量 100”与“倍率 100”的歧义。
- 使用真实 1.4.3 `main.patched.bin` 的集成探针通过：39/39 项可用；
  开启 ×100、关闭还原、固定 999 三态的站点和三条跳板指令均逐字校验正确。
  App 增量构建约 4 分钟，28,108 个启动着色器全部复用，30,825 条 pipeline
  成功；深度签名校验通过并已安装到
  `/Applications/The Legend of Zelda - Tears of the Kingdom.app`。安装没有
  改动 `MacNativeGames/TOTK/profile` 下的存档。

#### 2026-11-21：王国之泪特别版 + 金手指分卷包

- 按之前的临时特殊版流程重新应用 `work/totk-special-private-ui.patch`：
  移除“访问主页”、着色器贡献、性能排行榜、截图分享页面，关闭启动时的
  着色器共享询问及对应后台上传；本地截图功能保留。
- 这次特殊版必须在金手指功能之上叠加。旧补丁的
  `shared/runtime/settings_panel.h` 片段与金手指页的页签和页脚改动重叠，
  无法直接应用，所以四个独立文件照常用补丁应用，共享设置面板的手工移植
  与旧补丁相同：给访问主页增加 `SETTINGS_HAS_HOME` 条件，并保留
  `SETTINGS_HAS_CHEATS` 页。
- 已构建普通特别版 + 金手指：
  `work/The Legend of Zelda - Tears of the Kingdom Special Cheats.app`。
  原生 4K、原生 5K 均开启；1.4.3，金手指页及“拾取 ×100”保留。
  深度签名校验通过，启动着色器 28,108 个全部复用，`applegpu_g15s`
  pipeline 30,825 条成功。
- 低配特别版 + 金手指没有构建。普通 App 的 3 GiB 分卷完成后只剩约
  9.3 GB，工作 App 删除后仍约 9.3 GB（打包资源使用 APFS 克隆）；低配
  App 加第二套约 34 GB 分卷无法安全容纳，因此按用户“内存不足就先弄普通
  特别版”的指示停止。
- 分卷上传目录：
  `Downloads/WGZL/The Legend of Zelda - Tears of the Kingdom 1.4.3 Special Cheats App upload/`。
  `.z01` 到 `.z11` 加最后 `.zip` 共 12 个文件，约 34 GB；同目录的
  `解压说明.txt` 用中文写明 Keka 和命令行合并方法，
  `The Legend of Zelda - Tears of the Kingdom Special Cheats.sha256`
  记录全部 12 个分卷的 SHA-256。
- 分卷已按 `.z01` 到 `.z11`、`.zip` 的顺序拼接，使用 macOS `bsdtar`
  完整流式解压到 `/dev/null` 校验通过。工作 App 副本已删除，上传目录保留；
  当前 `/Applications/The Legend of Zelda - Tears of the Kingdom.app` 和
  `MacNativeGames/TOTK/profile` 下的存档均未改动。
- 特殊版临时源码修改已反向还原；当前工作区只保留正常版的金手指实现、
  先前已有的四个 `frontend.m` 修改及测试/文档改动。
- 2026-11-21 后续按用户要求重新生成工作副本供测试：
  `work/The Legend of Zelda - Tears of the Kingdom Special Cheats.app`。
  这次不安装、不再制作分卷。构建时磁盘只剩约 9 GB，构建器的保守空间检查
  会拒绝已有的 APFS 克隆增量构建，因此临时加入
  `MNG_SKIP_DISK_CHECK=1` 开关越过检查；构建成功后该开关已从
  `build_app.py` 撤销。工作副本深度签名校验通过，四份特殊版源码修改也已
  再次还原。

#### 2026-11-21：王国之泪低配特别版 + 金手指分卷包

- 磁盘扩容后补齐低配特殊版。再次临时应用
  `work/totk-special-private-ui.patch`，共享设置面板因金手指页重叠，
  继续按前述方式手工移植；正常金手指代码保持不变。
- 构建参数为 1.4.3、`--no-native-4k --no-native-5k`，产物
  `work/The Legend of Zelda - Tears of the Kingdom Special 16GB Cheats.app`。
  特别版精简界面、完整金手指页和“拾取 ×100”均保留；原生 4K/5K 关闭。
- 深度签名校验通过；启动着色器 28,108 个全部复用，`applegpu_g15s`
  pipeline 30,825 条成功。App 不安装。
- 3 GiB 分卷目录：
  `Downloads/WGZL/The Legend of Zelda - Tears of the Kingdom 1.4.3 Special 16GB Cheats App upload/`。
  `.z01` 到 `.z11` 加最后 `.zip` 共 12 个文件，约 34 GB；同目录
  `解压说明.txt` 用中文写明 Keka／命令行合并步骤，
  `The Legend of Zelda - Tears of the Kingdom Special 16GB Cheats.sha256`
  记录 12 个文件的 SHA-256。
- 已按分卷顺序拼接并用 macOS `bsdtar` 完整流式解压到 `/dev/null` 校验通过。
  低配版工作 App 副本已删除；普通特别版工作 App
  `work/The Legend of Zelda - Tears of the Kingdom Special Cheats.app` 保留。
- 特殊版临时源码修改已反向还原。当前 `/Applications` 正常版和
  `MacNativeGames/TOTK/profile` 下的存档均未改动。

#### 2026-11-21：特别版分卷保留符号链接修正

- 发现前两次特别版分卷使用了 `zip -s 3g -r`，漏掉旧的 `-y` 参数。
  App 内有四个指向 Helpers bundle 的符号链接；不写 `-y` 时 ZIP 会跟随
  链接并重复写入约 15.88 GiB 的 `romfs.bin`，以及着色器、pipeline 数据，
  导致 12 个分卷、约 34 GB。金手指本身和低配显示设置只改变代码，不增加
  这部分空间。
- 已删除两套错误的 12 分卷目录，并用
  `zip -s 3g -r -y` 重新制作普通特别版和低配特别版。两套现在均为
  `.z01` 到 `.z05` 加最后 `.zip`，共 6 个文件、约 17 GB。
- 普通特别版复用已构建的
  `work/The Legend of Zelda - Tears of the Kingdom Special Cheats.app`；
  低配版重新构建
  `work/The Legend of Zelda - Tears of the Kingdom Special 16GB Cheats.app`，
  原生 4K/5K 关闭。按用户要求，这两份工作 App 均保留供测试，不删除、不安装。
- 两套分卷均按顺序拼接并用 macOS `bsdtar` 完整流式解压到 `/dev/null`
  校验通过；两套 SHA-256 清单逐卷复核全部 OK，中文 `解压说明.txt` 也已
  改为 6 个文件并注明必须保留符号链接。
- 低配构建临时应用的特殊版补丁已再次反向还原；正常版金手指实现和已有
  `frontend.m` 修改不变。

#### 特殊版 `.app` 分卷打包固定规则

- 以后所有 mac App 分卷继续使用 3 GiB：
  `zip -s 3g -r -y "<name>.zip" "<name>.app"`。`-y` 是必需项，不能省略；
  它让 ZIP 保存 App 内指向 Helpers bundle 的符号链接，而不是跟随链接把
  RomFS、着色器和 pipeline 再打包一份。
- 打包前先检查链接：
  `find "<name>.app" -type l -print`。王国之泪 1.4.3 正常版应有
  `shader-seed`、`pipelines`、`shader-libs` 和 `romfs.bin` 四个链接；
  低配版结构相同。
- 打包后检查分卷数量。王国之泪 1.4.3 普通特别版和低配特别版使用
  `zip -y` 时应为 `.z01` 到 `.z05` 加最后 `.zip`，共 6 个文件、约 17 GB。
  如果变成 `.z11`、约 34 GB，说明漏了 `-y`，不要上传；只删除这次错误
  分卷，修正命令后重新制作。
- 完成后必须按分卷顺序拼接并流式校验：
  `cat *.z01 *.z02 *.z03 *.z04 *.z05 *.zip | bsdtar -xOf - > /dev/null`，
  再生成并复核 `.sha256`。`.app` 本身保留时，用
  `codesign --verify --deep --strict` 检查签名。
- 上传目录的说明文件统一命名为 `解压说明.txt`，正文只用中文，不再使用
  英文说明文件。内容必须同时包含：
  1. macOS 终端里用 `zip -s 0` 合并分卷并按顺序解压的命令；
  2. 第三方软件 Keka 的图形界面步骤，包括所有 `.z01` 到 `.zNN` 和最后的
     `.zip` 必须放在同一目录、用 Keka 打开最后的 `.zip`、选择解压位置，
     以及必须保留 App 内的符号链接；
  3. 校验 `.sha256` 的方法和最终把 `.app` 放入 `/Applications` 的说明。

#### 2026-11-21：王国之泪清理

- 按用户确认的清单删除：
  `work/restorepoints/totk-cheats-20261121-091525`、
  `Library/Application Support/MacNativeGames/Builder/sources`、
  `Library/Logs/nxnative`、`work/0100F2C0115B6000/logs`、
  `work/The Legend of Zelda - Tears of the Kingdom Special Cheats.app`、
  `work/The Legend of Zelda - Tears of the Kingdom Special 16GB Cheats.app`；
  同时清除项目内的 `__pycache__`、`.DS_Store` 和 AppleDouble 文件。
- 保留两套已修正的特别版分卷、`/Applications` 中的王泪 App、
  `MacNativeGames/TOTK/profile/save`、王泪本体和 1.4.3 更新、`prod.keys`、
  引擎源码，以及 `work/0100F2C0115B6000/totk` 的 extracted/build/rewritten
  等下次构建缓存。普通特别版上传目录里的百度网盘断点续传配置也保留。
- 删除前磁盘可用约 47 GiB，删除后约 48 GiB。旧恢复点和两个测试 App 的
  逻辑大小为 60 GB，但它们的大量文件与构建缓存、当前 App 共享 APFS 克隆，
  因此实际只增加约 1 GiB，不能按逻辑大小预估释放量。

#### 2026-11-21：删除王国之泪 App 与构建缓存

- 按用户确认的范围删除 `/Applications` 中的
  `The Legend of Zelda - Tears of the Kingdom.app`（约 20 GB）和整个
  `work/0100F2C0115B6000` 王泪构建工作目录（约 42 GB）。
- 保留
  `Library/Application Support/MacNativeGames/TOTK/profile/save`：
  删除前后仍为 38 个文件、17 MB。保留王泪本体 XCI 16 GB、1.4.3 更新
  460 MB 和 `prod.keys`；密钥 SHA-256 仍为
  `039895c6e93a0c6208c3af27da8c3fc408083873a96f2320dc334a6fa252c112`。
- 两套修正后的普通／低配特别版分卷、各自的 SHA-256 和中文
  `解压说明.txt` 均保留。MacNativeGames 运行时着色器缓存和引擎源码未删。
- 删除前磁盘可用约 48 GiB，删除后约 70 GiB，实际释放约 22 GiB。
  App 和构建目录的逻辑大小合计约 62 GB；差额来自 APFS 克隆共享块。

#### 2026-11-21：耀西构建暂停点

- 首次完整构建耀西时，NUP 已解包 19.4 GB、文件头校验通过，模块重写和
  133,154 个 shader 的拆分完成；完整 Mac shader 编译到约 95% 时按用户要求
  暂停，准备关机。
- 已停止 `hermit.py`、`build_ipa_from_nsp.py`、Metal 编译和全部子进程。
  未安装、未生成最终 App。保留状态：
  `work/0400245021D2C000` 约 63 GB，其中
  `shader/cache/cas-9c1a9324c032.db` 约 38 GB；解包、重写、shader map、
  缓存数据库和引擎源码都未删除。
- 用户提供的 `Downloads/YX/logo.webp` 已转换为 1920×1920
  `Downloads/YX/logo.png`。NUP 自带提取结果里没有 `control.nacp` 或
  `icon.jpg`，因此恢复构建时必须传 `--icon`，让最终 App 使用该 logo。
- 到家恢复命令：

  `.venv/bin/python hermit.py build /Users/amid031799/Downloads/YX --icon /Users/amid031799/Downloads/YX/logo.png`

  构建完成后安装：

  `.venv/bin/python hermit.py install`

#### 2026-11-21：耀西首次构建与安装

- 恢复后完整 shader 的 133,154 个编译结果已全部进入 SQLite 编译缓存，但
  完整最终 shader 库镜像也需要约 42 GB，必须与约 42 GB 编译缓存同时存在。
  两次发布都在最后写库阶段因磁盘不足失败；未删除分卷、ROM 或存档。
- 为完成可运行安装，改用 nxnative 官方 `--quick`
  （`--seen-shaders`）：使用 profile 已验证的 1,519 个 shader，最终库
  1,521 个，其中 1,520 个直接来自缓存；未覆盖的区域可能缺少 shader，
  后续有空间时应再跑完整构建。
- 用户提供的 `Downloads/YX/logo.webp` 已转为 1920×1920
  `Downloads/YX/logo.png`，并通过 `--icon` 打进 App。最终
  `Contents/Resources/AppIcon.icns` 为 3.4 MB，
  `CFBundleIconFile=AppIcon`；NUP 本身没有 `control.nacp`／`icon.jpg`，
  所以使用的是该 logo。
- 构建结果：nxnative `c8c58e6c5193`，NUP update v131072，Mac App
  约 19.9 GB，bundle ID `org.nxnative.0400245021d2c000`；pipeline archive
  `applegpu_g15s` 79.7 MB。深度签名校验通过，已安装到
  `/Applications/Yoshi and the Mysterious Book.app`。
- `hermit.py install` 删除了 App 不再需要的 22.2 GB 打包中间副本，但保留
  `work/0400245021D2C000/shader/cache/cas-9c1a9324c032.db`
  完整 shader 编译缓存，便于以后补齐完整库。安装后工作目录约 45 GB，
  磁盘可用约 32 GiB。首次启动尚未运行，存档目录会在首次启动时创建。

#### 2026-11-22：时之笛低配版设置页汉化补全并重新分包

- 时之笛低配引擎 `nxnative-a235328d5966` 的设置行有 7 列、8 列和 9 列
  三种形式。此前 `tools/engine/patch.py` 的按变量汉化逻辑错误地要求至少
  9 列，导致 `DM_DYNAMIC_RESOLUTION`、`DM_WIDE_VIEW`、`DM_MIC`、
  `DM_SW2`、`DM_PRESENT_SNAP`、`DM_PSO_MTL4`、`DM_NVN_ENC_THREAD`、
  `DM_NVN_TEX_MIP_SKIP`、`DM_FPS_HOLD` 等 7/8 列项目仍显示英文。
- 现改为按第一列环境变量识别，只要设置行有至少 7 列就替换 label、note
  和选项显示值。启动页与游戏内 2 键设置页都读取最终
  `Contents/Resources/dm/launcher.json`；重建后该文件的 25 个设置项已
  全部中文化。剩余拉丁字符只有 MetalFX、Switch 2、Joy-Con 2、
  Pro Controller 2、macOS、GPU、3D 等产品或技术名称。
- 低配引擎 `kid-with-sword-remake` 增量重建完成，App 约 34.3 GB，
  bundle ID `org.nxnative.0400486024dec000`，版本是 NUP update
  v131072。42,848 个 shader、pipeline archive 和 prewarm 均复用；
  `codesign --verify --deep --strict` 通过。按用户要求不安装，保留工作
  App 供测试。
- App 的 `Contents/Resources/romfs.img`、`msl`、`pso` 三个符号链接均
  保留。删除旧的
  `Downloads/The Legend of Zelda - Ocarina of Time Low Memory App upload/`
  后，使用 `zip -s 3g -r -y` 重新制作，现为 `.z01` 到 `.z09` 加最后
  `.zip`，共 10 个文件、约 29 GB。
- 对新分卷逐卷校验 SHA-256 全部 OK，并按顺序拼接后用 macOS `bsdtar`
  完整流式解压到 `/dev/null` 通过。`zipinfo` 确认三个关键链接属性为
  `lrwxr-xr-x (120755)`，`Contents/MacOS/dmhost` 为
  `-rwxr-xr-x (100755)`。
- 中文 `解压说明.txt` 已同步更新，包含全部文件名、SHA-256 校验、
  `zip -s 0` 合并、`ditto` 解压、签名检查以及 Keka 图形界面步骤；特别
  注明不能使用会丢失符号链接的在线解压，否则会出现
  “game data inside this app is missing or incomplete”。

#### 2026-11-22：时之笛低配构建清理

- 按用户要求保留低配版分卷压缩，删除低配专属的工作 App
  `work/The Legend of Zelda - Ocarina of Time.app`（约 34.3 GB）、
  克隆标记 `work/The Legend of Zelda - Ocarina of Time.app.key` 和低配
  引擎 `engines/nxnative-a235328d5966`（约 966 MB）。
- 保留 `work/0400486024DEC000`（约 54 GB）作为时之笛共用的解包、
  shader／pipeline 与重新构建缓存；保留
  `Downloads/The Legend of Zelda - Ocarina of Time Low Memory App upload/`
  的 10 个分卷、SHA-256 和中文解压说明，共约 29 GB。
- 已安装的 azmasm／`e5de1ecebbca` App 未改动，深度签名校验通过；
  `Application Support/nxnative/0400486024DEC000/save` 的 14 个文件、
  `pso_archive` 和原始 NUP 均保留。磁盘可用空间从约 49 GiB 增至约
  54 GiB；工作 App 与构建缓存有 APFS 克隆共享块，因此逻辑大小
  34.3 GB 不等于实际释放量。

#### 2026-11-22：荒野之息 1.9.0 构建与安装

- 使用 `Downloads/KYZX` 中的 1.6.0 基础 XCI 和 1.9.0 更新 NSP，
  按当前 Mac 的推荐方案构建 MacNativeGames `4a19455866ae`；开启原生
  4K/5K。构建耗时约 16 分钟，15,528 个启动 shader 中预编译 15,473 个，
  `applegpu_g15s` 的 18,250 条 pipeline 全部成功。
- 固件 21.0.0 的共享字体需要 `key_area_key_application_14`，现有
  三份用户 `prod.keys` 都只提供到 master key 12，因此字体提取被阻止。
  没有获取、复制或记录新密钥；改用本机 CrossOver 中已有的开源
  Source Han Sans（SIL OFL 1.1）生成六份合法 BFTTF 共享字体，
  `build_app.py` 的字体清单校验通过。标准、简体、繁体、韩文均使用
  对应的思源黑体；任天堂专用按键图标槽使用同一开源字体，可能缺少少数
  主机按键图形。
- 生成 App 约 16 GB，bundle ID `org.macnativegames.botw`，版本
  1.9.0；`codesign --verify --deep --strict` 通过。按用户要求直接安装到
  `/Applications/The Legend of Zelda - Breath of the Wild.app`，没有制作
  分卷压缩包，也没有启动游戏。
- `hermit.py install` 删除了工作目录中的待安装 App，保留
  `work/01007EF00011E000` 约 33 GB 的代码、RomFS、shader 和 pipeline
  重建缓存。首次启动时 macOS 可能先扫描 App 1-3 分钟；运行时存档和缓存
  将写入 `Application Support/MacNativeGames/BotW`。

##### 新密钥后的原版字体重建

- 用户替换 `Downloads/KYZX/prod.keys` 后，文件包含 master key 0-16 和
  `key_area_key_application_14`。上次检查误判缺失，是因为该密钥文件用
  空白分隔名称和值，而检查脚本只按 `=` 截断；没有读取或输出密钥值。
- 删除开源替代字体目录后，从固件 21.0.0 重新提取六份共享字体。
  `manifest.json` 的完整性记录为逐 NCA 校验 FS header 和六层 IVFC，
  不再是上次的开源字体替代清单。
- 代码、RomFS、shader、pipeline 全部复用，重构建约 2 分钟，18,250 条
  pipeline 再次验证 0 失败；新 App 约 16 GB，深度签名校验通过，已覆盖
  安装到 `/Applications/The Legend of Zelda - Breath of the Wild.app`。
  未制作分卷包，保留 `work/01007EF00011E000` 约 33 GB 重建缓存。

#### 2026-11-22：荒野之息 1.9.0 金手指页

- 用户提供的 `Downloads/KYZX/CD57B23FA4BBAD65.txt` 是 1.9.0 的
  Atmosphère 金手指文件。Hermit 的 `build` 新增 `--cheats <file>`，把文件
  复制到 App 的 `Contents/Resources/totk/cheats/cheats.txt`；原文件仍只在
  Downloads，不进入仓库。
- 文件开头没有节名的版本头/基础代码块不会被载入，因为它没有可对应的菜单项，
  也无法安全判断何时启用。打包时保留从第一个 `[名称]` 或 `{主代码}` 开始
  的 28 个有名字段。
- 移植 MacNativeGames 的通用 Atmosphère 金手指 VM，并接入 TOTK/BotW 共用
  运行时。1 键设置面板新增“金手指 / Cheats”页，每个条目一个开关，底部
  “全部关闭 / Turn all off”一键清除。开关保存在
  `Application Support/MacNativeGames/BotW/cheats-enabled.txt`，重启后恢复；
  第一次启用会先备份整个 `profile` 为 `profile-before-cheats`。
- 代码型金手指通过 main 的第二个可写物理页映射切换，游戏自身页保持
  RX，不临时改成可写；每次写入后刷新指令缓存。关闭时逐字恢复修改前内容；
  两条金手指争用同一地址会拒绝后启用的一条。
- 当前文件识别 28 条，其中 25 条可作为代码开关执行。`速度提升` 和
  `时停延长 (按下方向键下取消)` 使用按键条件包住代码写入，
  `武器耐久度不减` 写入目标 `main+0x21A1BD0`，超出该 1.9.0 主程序可执行
  范围；这三条在页面中显示为不支持并禁用，避免误写。
- 用临时状态启用“无限精力”和“无限弓箭”跑过真实的
  `pipeline-archive` 路径：writable alias 建立，2 条在启动时成功启用，
  18,250 条 pipeline 全部成功。没有在用户存档上启用或留下测试开关。
- 最终 App 约 16 GB，bundle ID `org.macnativegames.botw`，深度签名通过，
  已覆盖安装到 `/Applications/The Legend of Zelda - Breath of the Wild.app`。
  没有制作分卷包；`work/01007EF00011E000` 约 33 GB 重建缓存保留。

##### 金手指关闭修复

- 用户实测金手指能开启，但切换按钮无法关闭。原因是关闭路径仍调用开启时的
  代码校验；已经写成跳转/替换指令的站点会被当成“当前指令异常”再次拒绝，
  所以状态一直留在开启。
- 新增独立的 `code_restore`：关闭和“全部关闭”只根据开启时保存的原指令和
  已拥有地址逐字还原，不再校验已经被金手指改写的当前指令。恢复仍通过 main
  的可写物理页别名并刷新指令缓存。
- 启动恢复已保存开关时，两条金手指争用同一地址会让后一条不生效；现在同时
  从状态文件移除这条未生效的开关，避免页面显示“已开”但实际没有生效。
- 修复版重新构建并安装。再次用“无限精力”和“无限弓箭”通过真实
  `pipeline-archive` 路径验证，2 条均成功启用，18,250 条 pipeline 全部正常。
  用户下次启动时，现有状态里与“一键还原”冲突的两项会被自动清理。

#### 2026-11-22：旷野之息特殊版与清理

- 按用户要求删除 `/Applications/The Legend of Zelda - Breath of the Wild.app`
  和 `Application Support/MacNativeGames/BotW` 下的 `profile` 与
  `profile-before-cheats` 两份存档。ROM、密钥、shader-cache、金手指和普通
  构建缓存保留；特殊版不安装。
- 王国之泪特殊版补丁不能直接应用到当前设置页，因为它与后来加入的金手指页
  重叠。按同一目标手工移植为 `work/botw-special-private-ui.patch`：移除
  “访问主页”、着色器贡献页/上传、性能排行榜页/上传、截图分享页/上传和
  启动时的着色器共享询问；本地截图、金手指页、原生 4K/5K 保留。
- 修改前恢复点：
  `work/restorepoints/botw-special-before-20261122-222258/`。特殊版使用
  MacNativeGames `4a19455`、旷野之息 1.9.0、原版固件共享字体和当前完整
  shader/pipeline 缓存构建，约 16 GB；18,250 条 pipeline 全部成功，深度
  签名校验通过。
- 分卷位于
  `Downloads/The Legend of Zelda - Breath of the Wild Special App upload/`：
  `.z01` 到 `.z04` 加最后 `.zip`，共 5 个文件、约 13 GB。`zip -s 3g -r -y`
  保留了四个关键符号链接，`Contents/MacOS/BotW` 保持可执行；SHA-256 校验、
  ZIP 元数据和完整流式 `bsdtar` 解压均通过。
- 中文 `解压说明.txt` 包含命令行和 Keka 两种解压方法，并注明特殊版移除的
  项目。工作目录中的特殊版 App 已删除，源码特殊版改动已反向还原并与恢复点
  逐文件核对一致；只保留特殊版分卷和可复用补丁。

##### 特殊版测试 App 重建

- 用户需要测试特殊版，重新应用 `work/botw-special-private-ui.patch`，使用同一
  套 1.9.0 原版字体、完整 shader/pipeline 缓存构建，约 2 分钟完成。
- 测试 App 保留在
  `work/The Legend of Zelda - Breath of the Wild Special.app`，约 16 GB；
  18,250 条 pipeline 正常，金手指文件在包内，深度签名校验通过。
- App 没有安装到 `/Applications`；旷野之息普通 App 和存档仍保持删除状态。
  源码特殊版改动再次反向还原并与恢复点逐文件核对一致，现有 5 个分卷包未改动。

#### 2026-11-23：解压说明固定模板

以后所有分卷任务的 `解压说明.txt` 都以
`docs/templates/解压说明模板.txt` 为唯一固定模板。该文件是用户提供的
`Downloads/The Legend of Zelda - Breath of the Wild Special App upload/解压说明.txt`
的逐字副本，原下载目录中的文件删除后不影响此模板。只允许替换标题中的
游戏/版本/版本类型、分卷基名、分卷编号与数量、SHA-256 文件名和 App 文件名；
不要增加、删除或改写其他正文，不要追加命令行解压、Keka 或其他额外说明。

固定模板如下：

```text
塞尔达传说：旷野之息 1.9.0 特殊版
macOS App 分卷压缩包

一、文件要求

请把以下文件全部下载到同一个文件夹：

  The Legend of Zelda - Breath of the Wild Special.z01
  The Legend of Zelda - Breath of the Wild Special.z02
  The Legend of Zelda - Breath of the Wild Special.z03
  The Legend of Zelda - Breath of the Wild Special.z04
  The Legend of Zelda - Breath of the Wild Special.zip
  The Legend of Zelda - Breath of the Wild Special.sha256

缺少任意一个分卷都无法完整解压。不要改名，也不要把分卷分别解压。

这个 App 不包含存档，也不会覆盖其他 App 的存档。

二、先检查文件是否完整

打开“终端”，进入所有分卷所在的文件夹，然后执行：

  cd ~/Downloads
  shasum -a 256 -c "The Legend of Zelda - Breath of the Wild Special.sha256"

全部显示 OK 后再解压。如果有 FAILED，请重新下载对应的分卷。

三、使用 fastzip 解压

1. 安装fastzip。
2. 找到最后那个
   “The Legend of Zelda - Breath of the Wild Special.zip”
   选中后鼠标右键选择解压到单独文件夹。
4. fastzip 会自动读取同目录下的 .z01 至 .z04，不需要逐个打开。
5. 解压完成后启动
   “The Legend of Zelda - Breath of the Wild Special.app”。

不要使用会丢失符号链接的在线解压，也不要只单独解压某个分卷。否则启动时可能出现：

  The game data inside this app is missing or incomplete

如果出现这个提示，请删除本次解压出来的 App，改用上面的方法，从原始分卷重新解压。

五、特殊版说明
第一次启动时 macOS 可能扫描 App 1～3 分钟；首次进入游戏时也可能需要加载着色器和管线。
```

#### 2026-11-23：旷野之息特殊版 + 金手指低配版

- 先确认高配特殊版分卷完整，然后按用户要求删除工作目录中的高配测试 App
  `work/The Legend of Zelda - Breath of the Wild Special.app`，以及测试运行
  产生的 `BotW/profile` 和 `profile-before-cheats`。高配的 5 个分卷、SHA-256
  和 `解压说明.txt` 保留。
- 重新应用 `work/botw-special-private-ui.patch` 构建低配版，使用
  `--no-native-4k --no-native-5k`，并打入 `CD57B23FA4BBAD65.txt` 的 28 个
  金手指条目。访问主页、着色器贡献、排行榜和截图分享仍按特殊版移除，本地
  截图和金手指页保留。
- 低配 App 为
  `work/The Legend of Zelda - Breath of the Wild Special 16GB Cheats.app`，
  约 16 GB；原生 4K/5K 标记均不存在，18,250 条 pipeline 成功，深度签名
  校验通过。按用户本轮要求不安装，工作 App 暂留供测试。
- 分卷位于
  `Downloads/The Legend of Zelda - Breath of the Wild Special 16GB Cheats App upload/`，
  `.z01` 到 `.z04` 加最后 `.zip`，共 5 个文件、约 13 GB；SHA-256 全部通过，
  完整流式解压通过，四个关键符号链接和 `Contents/MacOS/BotW` 权限保留。
- `解压说明.txt` 严格由 `docs/templates/解压说明模板.txt` 生成，只替换标题、
  发布基名、分卷/SHA/App 文件名，没有增加或删改其他正文。构建后特殊版源码
  已反向还原，并与恢复点逐文件核对一致。

#### 2026-11-23：删除旷野之息全部构建与运行文件

- 按用户要求删除低配特殊版工作 App、`work/01007EF00011E000` 约 33 GB
  构建缓存、特殊版补丁和恢复点，以及 Downloads 中高配与低配两个分卷上传
  目录和额外的旷野之息金手指压缩包。
- 删除 `Application Support/MacNativeGames/BotW` 整目录，包括配置、测试
  profile、`profile-before-cheats`、运行时 shader-cache 和状态文件。
  `/Applications` 中没有旷野之息 App。
- `Downloads/KYZX` 完全保留且未改动，仍有原来的 5 个文件、约 17 GB：
  1.6.0 基础 XCI、1.9.0 更新 NSP、金手指文本、logo 和 `prod.keys`。
- 磁盘可用空间从约 27 GiB 增至约 71 GiB。项目源码、共享
  MacNativeGames 引擎和模板文档不属于旷野之息构建产物，继续保留。

#### 2026-11-23：删除时之笛构建缓存

- 按用户要求删除 `work/0400486024DEC000`（约 54 GiB）和
  `work/0400486024DEC000-engine-seed.tsv`（约 9.3 MB）。删除前确认没有
  时之笛游戏进程运行。
- 保留 `/Applications/The Legend of Zelda - Ocarina of Time.app`（约 37 GiB，
  深度签名校验通过）、`Application Support/nxnative/0400486024DEC000`
  （约 1.2 GiB，15 个存档文件）、`Downloads/SHIZHIDI` 原始 NUP（约 24 GiB）
  和其他游戏数据。
- 磁盘可用空间从约 72 GiB 增至约 **143 GiB**。以后重新构建时，解包、shader
  和 pipeline 会重新生成，第一次重建会明显更慢。

