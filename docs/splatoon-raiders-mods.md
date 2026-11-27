# 《斯普拉遁 涂击队》宿主侧金手指

本文记录 Hermit 中《斯普拉遁 涂击队》（Splatoon Raiders）金手指的设计、
构建注入流程、使用方法和后续维护要求。

## 适用范围

| 项目 | 值 |
|---|---|
| 游戏 | Splatoon Raiders / 斯普拉遁 涂击队 |
| Title ID | `0400380020056000` |
| 更新版本 | `v65536` |
| 主程序 Build ID | `663c2e087a083f05307f229dfc4042d5` |
| 当前引擎固定点 | `nxnative@ef8b25d2c5a8a37588ebc1bf1785a56468900688` |
| 参考来源 | [kirakira-dev/OunceNative](https://github.com/kirakira-dev/OunceNative) at `c8785eb835a0` |
| 许可证 | MIT |

当前实现只适用于上述精确主程序版本。它不是可跨版本复用的普通 Atmosphère
金手指文件；如果游戏更新，必须重新核对地址、对象结构、状态校验和原始指令。

只应在离线单人模式使用。该方案不提供无敌，也不能用于联网模式或影响其他玩家。

## 功能

- 无限墨水：两个墨水槽保持满值。
- 快速射击：取消射击间隔。
- 飞行 / 穿墙：按摄像机方向移动，R 上升，L 下降，按下左摇杆加速。
- 任意地点游泳：按住 ZL 时可在干燥地面和空中移动。
- 武器切换：122 个主武器变体。
- 恢复原始武器：恢复到覆盖前持有的装备。

前四项是 `2` 键设置面板中的即时开关。武器切换和恢复也是同一面板中的选项。

## 为什么不是普通 `.txt` 金手指

无限墨水和快速射击本身是较小的状态写入，但仍需要先找到并验证当前玩家和
射击器对象。飞行、游泳和武器切换还需要实时访问：

- 已通过类型校验的本地玩家对象；
- 玩家摄像机方向；
- 当前控制器输入；
- 玩家物理体列表；
- 当前武器管理器和装备槽。

普通 Atmosphère 金手指只能写固定地址，无法可靠实现这些逐帧状态机和对象校验。
因此本方案使用 nxnative 的观察钩子和宿主 C 回调。产品界面仍然把它显示为
“金手指”，但不会生成或依赖 `663C2E087A083F05.txt`。

## 文件

| 文件 | 用途 |
|---|---|
| [`tools/engine/raiders/hle_raiders_mods.c`](../tools/engine/raiders/hle_raiders_mods.c) | 状态钩子、对象校验、飞行/游泳、墨水、快速射击和武器请求 |
| [`tools/engine/raiders/dm_raiders_mods.h`](../tools/engine/raiders/dm_raiders_mods.h) | 前端使用的宿主 API |
| [`tools/engine/raiders/dm_raiders_weapons.inc`](../tools/engine/raiders/dm_raiders_weapons.inc) | 武器行名与可执行文件内部枚举值的对应表 |
| [`tools/engine/raiders/patches.py.in`](../tools/engine/raiders/patches.py.in) | 精确构建对应的四个观察钩子定义 |
| [`tools/engine/raiders/t_raiders_mods.c`](../tools/engine/raiders/t_raiders_mods.c) | 状态写入、输入过滤和武器恢复单元测试 |
| [`tools/engine/patch.py`](../tools/engine/patch.py) | 把文件复制到 nxnative，并修改宿主接口 |
| [`tools/engine/s2m_ui.m`](../tools/engine/s2m_ui.m) | 在 `2` 键设置面板顶部添加“金手指”区域 |
| [`tools/engine/update.py`](../tools/engine/update.py) | 检查新 nxnative 提交时传递目标 Title ID |

这些源码在构建时复制到临时引擎目录，不会手工修改已签名的成品 App。

## 构建时注入

`hermit.py build` 会按 `games/splatoon-raiders/game.json` 拉取指定提交的
nxnative，然后运行 `tools/engine/patch.py`。

当目标 Title ID 为 `0400380020056000` 时，`raiders_mods()` 会依次执行：

1. 把 Raiders 宿主源码、头文件和武器表复制到 `dm/host/`。
2. 在 `dm/host/dm.h` 中增加四个观察钩子编号和连续 guest heap 检查声明。
3. 写入 `dm/games/0400380020056000/patches.py`，其中包含 v65536 的四个精确
   钩子偏移和原始指令。
4. 在宿主控制器代码中加入 `dm_input_current()`，读取玩家 1 当前按键和摇杆，
   但不消费按键边沿。
5. 在正常控制器填充路径调用 Raiders 输入过滤器。飞行时屏蔽走路、肩键和左
   摇杆输入；按住 ZL 使用游泳模式时屏蔽对应动作。

宿主 Makefile 本来就会编译所有 `hle_*.c`，因此复制
`hle_raiders_mods.c` 后无需再手工增加源文件列表。

`tools/engine/update.py` 检查新的 nxnative 提交时会设置 `DM_GAME`。共享的
设置面板会复制到所有引擎，但 Raiders 钩子只允许注入到该游戏。

## 观察钩子

四个钩子绑定到以下 v65536 主程序指令：

| 偏移 | 原始字节 | 宿主用途 |
|---|---|---|
| `main+0x23f2980` | `d1185008` | 墨水消耗；x0 为玩家逻辑对象加 `0x614` |
| `main+0x25099f8` | `f9401e68` | 射击器更新；x19 为 `PlayerInkActionShooter` |
| `main+0x250bfa0` | `d503237f` | 主动射击就绪检查；x0 为射击器 |
| `main+0x22ec3a4` | `a95b4ff4` | 移动完成；x28 为玩家逻辑对象加 `0x5d8` |

`patch_nso.py` 会在改写前逐字校验原始指令。四个钩子中任意一个缺失时，宿主
不会提供这些功能。`hle_raiders_mods.c` 还会检查：

- 编译时的 Program ID 是 `0400380020056000`；
- main 的完整 Build ID 是 `663c2e087a083f05307f229dfc4042d5`；
- 候选玩家和射击器对象的虚表指针正确；
- 玩家对象中的标量 key 与当前游戏 token 匹配；
- 物理体、摄像机、武器管理器和装备槽对象的类型及可读范围正确。

校验采用失败即关闭的策略。版本或对象不匹配时不会向猜测地址写入。

## 使用方式

进入游戏后按 `2` 打开设置。只有精确 Build ID 和四个观察钩子都匹配时，顶部
才会出现“金手指”区域。

- 无限墨水：即时开关。
- 快速射击：即时开关。
- 飞行 / 穿墙：即时开关。按左摇杆方向移动，R 上升，L 下降，按下左摇杆加速。
- 任意地点游泳：即时开关；按住 ZL。
- 武器切换：通过游戏自己的装备请求流程切换。
- 恢复原始武器：武器列表第一项。

开关状态保存在 App 的用户偏好中。通过启动环境设置的开关优先于保存值，并在
该次运行的设置面板中锁定。

## 诊断开关

```text
DM_RAIDERS_MODS=ink,rapid,fly,swim
DM_RAIDERS_WEAPON=<RSDB row name>
DM_RAIDERS_MOD_DIAGNOSTICS=1
```

`DM_RAIDERS_MODS` 使用逗号分隔。`DM_RAIDERS_WEAPON` 接收武器表中的行名，
例如 `Blaster_A`。诊断开关只增加状态和射击频率日志，不改变已选择的功能。

## 验证

本次实现执行了以下检查：

```bash
NX="engines/nxnative-<commit>"

clang -O1 -g -Wall -Werror -Wno-unused-function \
  -fsanitize=address,undefined \
  -I "$NX/dm/host" \
  -I "$NX/dm/host/gen/0400380020056000" \
  tools/engine/raiders/t_raiders_mods.c \
  -o /tmp/t_raiders_mods_san

ASAN_OPTIONS=detect_leaks=0 /tmp/t_raiders_mods_san

python3 -m unittest \
  "$NX/dm/tools/tests/test_patches.py"

make -C "$NX/dm/host" \
  GAME=0400380020056000 dmhost
```

覆盖内容：

- 无钩子或错误 Build ID 会被拒绝；
- 只向通过校验的玩家对象写墨水；
- 快速射击只修改通过校验的射击器状态；
- 飞行会过滤走路、肩键和左摇杆输入；
- 关闭金手指后停止状态写入；
- 武器切换调用游戏自己的装备请求函数；
- 关闭武器覆盖后恢复捕获的原始武器；
- 本机已安装 App 的四条原始指令均与 v65536 预期字节一致；
- 不含 Raiders 头文件和钩子的其他 nxnative 引擎仍可编译共享设置面板。

代码检查期间没有启动游戏。按照项目规则，启动游戏前必须询问用户。

## 游戏更新后的维护

不能把当前偏移直接套用到新版本。游戏出现新的 main Build ID 时，需要：

1. 在新可执行文件中重新定位玩家、射击器、移动、摄像机和武器对象路径。
2. 重新核对四个原始指令和所有对象虚表。
3. 如果可执行文件中的武器枚举发生变化，重新生成武器表。
4. 同时更新 `RAIDERS_BUILD`、`patches.py.in`、武器表和单元测试数据。
5. 重新运行补丁注册表测试、ASan/UBSan 单测和宿主编译。
6. 更新本文和 `games/splatoon-raiders/README.md`。

完成这些步骤前，新版本会因 Build ID、钩子或对象校验不匹配而隐藏“金手指”
区域，不会尝试向新版本地址写入。

## 许可证与来源

Raiders 宿主钩子和武器映射参考
[kirakira-dev/OunceNative](https://github.com/kirakira-dev/OunceNative) 的
`c8785eb835a0`，原项目使用 MIT 许可证。Hermit 保留其核心方法，并适配本项目
的观察钩子、设置面板和构建注入接口。
