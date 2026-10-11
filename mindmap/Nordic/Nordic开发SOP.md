# Nordic / nRF Connect SDK 开发 SOP

> 目标板：Seeed XIAO nRF52840（**非 Sense** 版）
> SDK：nRF Connect SDK v3.4.1（workspace 在 `C:\ncs\v3.4.1`）
> 项目根目录：`C:\Users\cz\Desktop\Nordic\my_project\`

---

## 0. 环境前提（每次开新终端都要确认）

所有 `west` 命令**必须在已加载 nRF Connect 工具链环境的终端里**执行。

- 推荐：VS Code 集成终端（nRF Connect 扩展会配好环境）
- 或者：Toolchain Manager 里的 "Open Terminal"
- 实测普通 PowerShell / Git Bash 里没有 `west`，`$env:ZEPHYR_BASE` 也是空的

自检三条命令：

```powershell
west --version
echo $env:ZEPHYR_BASE      # 应指向 C:\ncs\v3.4.1\zephyr
ninja --version
```

如果报 `west: unknown command "build"; do you need to run this inside a workspace?`
→ 就是环境没加载，换终端，见第 3 节。

---

## 1. 日常编译 & 烧录

```powershell
cd C:\Users\cz\Desktop\Nordic\my_project\<项目名>

# 首次 / 换 board target / 大改配置 → 全量重新配置
west build -b xiao_ble/nrf52840 -p always

# 日常只改了 main.c → 增量编译（不用再带 -b，缓存里有）
west build

# 双按 RESET 键进 bootloader（出现 XIAO-SENSE 盘），然后烧录
west flash
```

### 要点

- **board target 固定用 `xiao_ble/nrf52840`**（非 Sense 版），不要用 `xiao_ble/nrf52840/sense`
- **换 board target 必须加 `-p always`**，否则会撞上旧缓存
- 改 `prj.conf` / `CMakeLists.txt` 后 CMake 一般会自动重跑 configure；不确定就加 `-p always`
- `CMakeLists.txt` 里已加 `set(BOARD_FLASH_RUNNER uf2)`，所以 `west flash` 不用再写 `--runner uf2`
- `west flash` 结尾的 `OSError: [WinError 433] 指定不存在的设备` **是正常的**，文件已经写进去了，忽略即可

### 产物路径（sysbuild 会多一层目录）

```
build\<项目名>\zephyr\zephyr.uf2     ← 手动拖拽烧录用这个
build\<项目名>\zephyr\zephyr.elf
```

注意是 `build\hello_world\zephyr\`，**不是** `build\zephyr\`。

### 查看串口输出

XIAO BLE 上 Zephyr 的 console 默认走 **USB CDC ACM**，插上 USB 线后会出现一个「USB 串行设备 (COMx)」，115200 打开即可，不需要 USB-TTL 转接板。

```powershell
# 列出串口
[System.IO.Ports.SerialPort]::GetPortNames()
```

---

## 2. 复制一个工程做二次开发（以蓝牙透传为例）

### 2.1 选样例

| 需求 | 样例路径 |
|---|---|
| 蓝牙透传（最简，推荐起步） | `C:\ncs\v3.4.1\zephyr\samples\bluetooth\peripheral_nus` |
| 完整 UART↔BLE 双向透传（NUS + 异步 UART） | `C:\ncs\v3.4.1\nrf\samples\bluetooth\peripheral_uart` |

新手建议先用 `peripheral_nus`：只有一个 `main.c`，只用 `printk`，不依赖 DK 库和 RTT，移植成本最低。

### 2.2 复制（目标目录不要放在 `C:\ncs` 里面）

```powershell
cd C:\Users\cz\Desktop\Nordic\my_project

Copy-Item -Recurse C:\ncs\v3.4.1\zephyr\samples\bluetooth\peripheral_nus .\ble_uart
cd .\ble_uart
```

清理这些不需要的东西：

- `build\` —— 旧构建缓存
- `.git\` —— 样例的 git 信息
- `sample.yaml` —— 给 CI（twister）用的，留着会误导

### 2.3 改工程标识

- `CMakeLists.txt` 里的 `project(NONE)` / `project(hello_world)` → `project(ble_uart)`
- `README.rst` 按需改写或删除

### 2.4 加 uf2 runner（**必须**，否则 `west flash` 默认走 nrfutil）

在 `CMakeLists.txt` 里，`find_package(Zephyr ...)` **之前**插入一行：

```cmake
set(BOARD_FLASH_RUNNER uf2)
```

为什么必须：XIAO 板上没有调试探针，默认 runner 是 `nrfutil`（要接探针），会直接失败。

### 2.5 移植到 XIAO 要留意的地方

- **删掉 DK 专有依赖**
  `CONFIG_DK_LIBRARY=y` + `dk_buttons_and_leds_*` 在 XIAO 上没有按键（没有 `sw0` 别名），要改成直接操作 GPIO 或删掉。
- **日志输出方式**
  XIAO 上没有调试器，`CONFIG_USE_SEGGER_RTT=y` / `CONFIG_LOG_BACKEND_RTT=y` 是看不到任何输出的 → 改成 CDC ACM 串口控制台，或直接用 `printk`。
- **不要抢 console 的串口**
  XIAO 的 console 默认走 USB CDC ACM，`uart0`（排针 D6/D7）是空出来的，正好拿来做透传串口；但别在 `prj.conf` 里用 `CONFIG_UART_CONSOLE=y` 把 console 抢回 `uart0`，会和透传串口打架。
- **Flash / RAM 预算**
  板级用了 `nrf52840_partition_uf2_sdv7.dtsi`（为 Adafruit bootloader 预留了 SoftDevice 分区），1MB flash / 256KB RAM，加 BLE + 日志后注意看构建输出里剩下的余量。

### 2.6 编译烧录

```powershell
west build -b xiao_ble/nrf52840 -p always
# 双按 RESET
west flash
```

### 2.7 验证

- 串口（USB CDC ACM 虚拟串口，115200）看启动日志
- 手机 **nRF Connect** App → Scanner → 找到广播名 → 连接 → 看 NUS 服务
  NUS 服务 UUID：`6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- 或桌面版 **nRF Connect for Desktop** → Bluetooth Low Energy 应用

---

## 3. 常见报错速查

| 报错 | 原因 | 处理 |
|---|---|---|
| `source directory ... does not exist` | 路径写错（如漏了一层目录） | 用 Tab 补全；或 `cd` 进项目再 build |
| `source and build directory ... cannot be the same` | 人正在 `build\` 目录里跑 `west build` | `cd ..` 回到项目根目录 |
| `west: unknown command "build"` | 终端没加载工具链环境 | 换 VS Code 集成终端；或 `cd C:\ncs\v3.4.1` 再用 `-s` 指源码 |
| `ERROR: source directory "." does not contain a CMakeLists.txt` | 在 workspace 根目录跑，没给源码路径 | 补 `-s <项目路径>` |
| `zephyr.h/kernel.h: No such file or directory` | 头文件路径写错 | 应为 `#include <zephyr/kernel.h>` |
| `west flash` 结尾 `WinError 433` | bootloader 收完文件立刻重启，`shutil` 收尾 chmod 失败 | **忽略**，已经烧录成功 |
| VS Code 里 `zephyr/kernel.h` 画红线 | IntelliSense 没读到 Zephyr 头文件路径 | 误报，忽略 |
| `west flash` 走了 nrfutil 而不是 uf2 | `CMakeLists.txt` 没设 `BOARD_FLASH_RUNNER` | 加 `set(BOARD_FLASH_RUNNER uf2)`，再 `-p always` 重配 |

---

## 4. west 命令参数速查

```
west  build  -b <board_target>  -p always  -s <源码目录>  -d <构建目录>
```

| 参数 | 全称 | 含义 | 默认值 |
|---|---|---|---|
| `west` | — | Zephyr 元工具；必须在 west workspace 内或已设 `ZEPHYR_BASE` | — |
| `build` | — | 子命令：先 CMake 配置，再 Ninja 编译 | — |
| `-b` | `--board` | board target，如 `xiao_ble/nrf52840` | — |
| `-p` | `--pristine` | 清空构建目录重新配置。取值 `auto` / `always` | `auto` |
| `-s` | `--source-dir` | 应用源码目录（含 `CMakeLists.txt`） | 当前目录 |
| `-d` | `--build-dir` | 构建产物目录 | `<source-dir>/build` |
| `-r` | `--runner` | 烧录器，如 `uf2` | 由 `BOARD_FLASH_RUNNER` 决定 |

`west flash` / `west debug` 复用同一套 `-d` / `-r` / `--domain` 参数。

---

## 5. 本机关键路径

| 用途 | 路径 |
|---|---|
| SDK workspace | `C:\ncs\v3.4.1` |
| Zephyr | `C:\ncs\v3.4.1\zephyr` |
| 工具链 | `C:\ncs\toolchains\4f5b6ad6dd\opt` |
| 板级定义 | `C:\ncs\v3.4.1\zephyr\boards\seeed\xiao_ble` |
| 我的项目 | `C:\Users\cz\Desktop\Nordic\my_project\` |

---

## 附：板子型号确认（备用）

XIAO nRF52840 的 Sense 和非 Sense 版**出厂共用同一份 bootloader**，所以 bootloader U 盘的名字和 `INFO_UF2.TXT` 里的 `Board-ID` 都带 Sense，**不能用来判断硬件版本**：

```
Model: Seeed XIAO nRF52840          ← 这行才是型号
Board-ID: Seeed_XIAO_nRF52840_Sense ← 两个版本都一样
```

要确认硬件，只能扫 I2C0 上的 `0x6A`（LSM6DS3TR-C IMU，Sense 独有）或目视板上有没有 IMU / 麦克风元件。
