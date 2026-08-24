# car_panel boot解析

> 个人学习笔记：Car_Panel 显示域（STM32F429）Bootloader + YMODEM OTA + 真 AB 分区机制解析。
> 参考代码：`Car_Panel-master/project/display_ecu_f429/bootloader/`

---

## 一、Flash 分区（背景）

| 区域 | 地址 | 大小 | 说明 |
|---|---|---|---|
| Bootloader | 0x08000000 | 64KB（Sector 0-3） | 上电从这里执行 |
| OTA 参数区 | 0x08010000 | 64KB（Sector 4） | append-only 日志，记录 active 槽/版本/CRC/boot_count |
| App A（活跃槽） | 0x08020000 | 384KB（Sector 5-7） | 位置相关链接，链接脚本绑定此地址 |
| App B（备用槽） | 0x08080000 | 384KB（Sector 8-10） | 同上，独立链接一份镜像 |
| 预留 | 0x080E0000 | 128KB（Sector 11） | — |

核心思想：**真 AB** —— 两个槽各存一份完整镜像，Bootloader 按 `active_partition` 选槽跳转；升级写【非活跃槽】并翻转标记；回滚只翻标记，零 Flash 搬运。

---

## 二、Boot 主流程

```
上电复位 → Bootloader main()
  ├─ ① UART_Init() + key_init()          ← 串口日志 + 升级按键
  ├─ ② ota_params_load()                  ← 从 Sector 4 读最后一条有效参数
  │     └─ magic 不对 → ota_params_init() 格式化参数区
  ├─ ③ boot_decision()                    ← 启动决策状态机（核心）
  │     返回 1 = 可跳转
  ├─ ④ 可跳转时：先验证活跃槽 SP 合法 → 2 秒按键窗口
  │     ├─ PE2 按下 → 进入 OTA 模式
  │     └─ 超时    → jump_to_app(活跃槽地址)
  └─ ⑤ 未跳转/选择升级 → 死循环 ota_ymodem_start()（失败 3s 重试）
```

2 秒窗口内并行响应上位机的芯片信息查询（`Boot_Query_WaitPress`）。

### 启动决策状态机（boot_decision.c）

按 OTA 参数区的 `ota_state` 走 switch 分多支：

| 状态 | 行为 | 备注 |
|---|---|---|
| `OTA_STATE_IDLE`（正常态） | 活跃槽 SP 合法 → 跳转；否则进 OTA 模式 | 常态 |
| `OTA_STATE_COMPLETE`（升级后待确认） | 见下方”回滚闭环” | 升级后唯一活跃分支 |
| `OTA_STATE_FAILED`（上次升级失败） | `case` 直接进 OTA 模式重收 | **死代码：全项目无任何写入点** |
| 未知脏值 | `default` 分支 → 进 OTA 模式 | 兜底 |

> `OTA_STATE_RECEIVING`/`VERIFY`/`FAILED` 三个枚举值**都没有被任何代码赋值**（接收全程 ota_state 保持 IDLE，成功才置 COMPLETE；回滚/确认都直接落到 IDLE 或 COMPLETE），对应 case 是防御性死代码。

`COMPLETE` 分支逻辑（核心回滚闭环，**超限判断优先于 CRC**）：

1. `boot_count++` 并**先持久化**（掉电也不丢计数）
2. 对活跃槽做 CRC32 校验（`crc32_flash(addr, size)`，先算出来用于调试打印）
3. **先判断 `boot_count >= max_boot_count`**：超限 → 直接 `rollback_to_other()` 切槽回滚，**不看 CRC 结果**（这是堵住”CRC 对但固件启动即崩溃”死循环的关键）
4. **未超限 + CRC 通过** → 返回跳转，但**保持 COMPLETE 不清零** —— 由 App 启动成功后写参数区确认（`App_Ota_Confirm_Active` → COMPLETE→IDLE + boot_count=0）
5. **未超限 + CRC 失败** → `NVIC_SystemReset()` 重启重试（重启后 boot_count 再递增，直到超限回滚）

### 跳转过程（boot_jump.c）

```c
wdg_start();                 // ① 先启动 IWDG（~16.4s 超时窗口）
__disable_irq();             // ② 关全局中断
SysTick->CTRL/LOAD/VAL = 0;  // ③ 停 SysTick（FreeRTOS tick 源）
NVIC->ICER/ICPR 全清         // ④ 清所有中断使能 + 挂起位
SCB->VTOR = app_addr;        // ⑤ 重定位向量表到槽起始地址
__set_MSP(sp);               // ⑥ 设主栈指针（取自槽首 4 字节）
entry();                     // ⑦ 跳到 reset handler（槽首 +4 字节）
```

`partition_is_valid()`：读槽首字（初始 SP），必须落在 `0x20000000–0x2002FFFF`（F429 连续 192KB SRAM）。擦空的 Flash 读出 0xFFFFFFFF，自然不合法。

### 回滚闭环（启动期存活检测）

```
Bootloader 跳转前启动 IWDG（16.4s 窗口）
        ↓
App 启动：UART → FreeRTOS → LCD/LVGL → 创建 8 个任务（实测 < 2s）
        ↓
    ┌─ 启动成功：App_Ota_Confirm_Active() → 参数区 COMPLETE→IDLE + boot_count=0
    │    → 之后 Heartbeat_Task 每 500ms wdg_feed() 喂狗
    └─ 启动即崩溃：没人喂狗 → IWDG 复位回 Bootloader
         → 仍处 COMPLETE 分支 → boot_count++ → 未超限再跳（重试）
         → 超过 max_boot_count → 切回旧槽（回滚）
```

---

## 三、异常状态兜底措施（详细）

设计主线：**任何异常路径的终点都收敛到“OTA 模式”（可重新刷机），而不是死机或变砖。**

### 阶段 0：参数区加载（boot_main.c / ota_params.c）

| 异常 | 兜底措施 | 位置 |
|---|---|---|
| 全新芯片 / 参数区全空（读出 0xFF） | magic 不匹配 → 擦除并写默认记录（active=A、IDLE、max_boot_count=3） | ota_params_init() |
| 某条记录**写一半掉电** | 该槽 CRC32 不匹配 → load_latest 跳过，取上一条有效记录 | ota_params.c 的 load_latest |
| 日志写满整擦时恰好掉电（1/1024 窗口） | 无有效记录 → 退化为参数初始化、默认 active=A，仍可安全启动 | ota_params.c 设计声明 |
| ota_params_init() 失败（Flash 硬件故障） | `while(1)` 死循环停在 boot —— 最终兜底，等人工介入 | boot_main.c |
| 历史脏数据 max_boot_count==0 | 加载时修正为默认值并持久化（防除零/防无限重试） | ota_params.c 的 ota_params_load |

### 阶段 1：启动决策（boot_decision.c）

| 异常 | 兜底措施 |
|---|---|
| ota_state 为未知脏值 | default 分支 → 进 OTA 模式 |
| OTA_STATE_FAILED（上次升级中途失败） | `case` 直接进 OTA 模式 —— **但该状态当前无任何写入点，为防御性死代码** |
| IDLE + 活跃槽 SP 非法（空片/被擦坏） | 不跳转 → 进 OTA 模式 |
| COMPLETE + 活跃槽**无元数据**（size=0/0xFFFFFFFF） | 无法校验 → 进 OTA 模式 |
| COMPLETE + **boot_count ≥ max（超限，无论 CRC 结果）** | rollback_to_other() 切回另一槽（仅翻标记，零搬运） |
| COMPLETE + **未超限 + CRC32 失败** | NVIC_SystemReset() 重启重试；boot_count 已先持久化，掉电不重置计数 |
| 回滚目标槽 SP 非法 | 回滚失败 → 进 OTA 模式 |
| 回滚目标槽 CRC 不匹配 | 回滚失败 → 进 OTA 模式 |
| 回滚目标槽**无元数据但 SP 合法** | 仅凭 SP 合法性信任（覆盖“手工烧录未记账”的出厂场景） |

### 阶段 2：跳转（boot_jump.c）

| 异常 | 兜底措施 |
|---|---|
| 跳转时 SP 二次校验失败 | jump_to_app 拒绝跳转并 return → 流程自然落入 OTA 模式 |
| App 启动后崩溃/卡死不喂狗 | 跳转前先启动 IWDG → 复位回 boot，与 COMPLETE/boot_count 接力触发回滚 |
| boot 中断状态泄漏毒害 App | 关全局中断 + 停 SysTick + 清全部 NVIC 使能/挂起位 + 重设 VTOR/MSP |

### 阶段 3：OTA 传输（ymodem.c）

| 异常 | 兜底措施 |
|---|---|
| 文件超过槽容量（384KB） | 文件名包阶段预检拒绝，不擦不写 |
| 包误码 / 超时 / 垃圾字节 | NAK 请求重传；**连续 10 次**失败才放弃（成功一包即清零计数） |
| ACK 丢失导致重复包 | ACK + 丢弃，不推进 Flash 偏移（防数据错位） |
| 序号真正乱序 | 立即终止（宁可重开会话也不烧错位镜像） |
| Flash 写入后数据不对 | flash_if_write_word **写后回读校验**，不一致报错 → abort |
| 擦除/写失败、传输整体失败 | 回到 boot_main.c 的 while(1)，3 秒后无限重试 |

**结构性兜底（最重要）**：YMODEM 始终写**非活跃槽** —— 传输期任何失败发生时，**正在运行的活跃槽镜像一个字节都不会受伤**，失败成本为零。

### 阶段 4：OTA 落账（ota.c）

| 异常 | 兜底措施 |
|---|---|
| **发错 bin**（镜像链接地址与目标槽不符） | reset-handler 范围校验 → 中止且**不翻转 active、不重启**，活跃槽无损回到重试循环 |
| 文件名里解析不到版本号 | 返回 0（记为“未知版本”），不阻塞升级 |
| 翻转 active 的 ota_params_save 中途掉电 | append-only 日志上一条记录仍有效 → 重启后沿用旧 active，等价于“这次升级从未发生” |

### 阶段 5：升级后首启（重启回 boot 的观察窗口）

| 异常 | 兜底措施 |
|---|---|
| 新固件 CRC 坏 | 未超限 → 重启重试；boot_count 递增至超限 → 切槽回滚 |
| **新固件 CRC 全对但启动即崩溃**（CRC 检测不到的缺陷） | CRC 通过时**故意保持 COMPLETE 不清零** → App 崩 → IWDG 复位 → 重新进 COMPLETE → boot_count 递增 → 超限回滚（超限判断在 CRC 之前，故 CRC 永远通过也会回滚） |
| 新固件正常启动 | App_Ota_Confirm_Active() 把 COMPLETE→IDLE、boot_count=0，关闭观察窗口 |

### 分层校验体系（五种手段各司其职）

```
SP 范围检查      → 粗筛：这槽里有东西吗？（1 次内存读）
CRC16 (YMODEM)  → 防传输误码（每包）
reset-handler   → 防错包/错槽（1 次内存读）
CRC32 全量      → 防落盘损坏/位翻转（每次启动）
IWDG + boot_count → 防"CRC 查不出"的启动期/运行期崩溃
```

### 诚实指出两个兜底缺口

1. **IDLE 态的“重启风暴”无保护**：boot_count 只在 COMPLETE 态累计。App 确认（IDLE）后若运行期 bug 死机 → IWDG 复位 → boot 检查 SP/CRC 全好 → 直接跳回 → 再崩 → **无限循环**。行业做法：App 崩溃处理在复位前写标志（RAM/备份寄存器）通知 boot 计数；或 boot 每次跳转都计数、App 正常启动清零。
2. **Bootloader 自身损坏无兜底**：所有兜底执行者都是 bootloader，它自己坏了就全盘失效。行业用双备份 boot（bootloader 也 AB 化）或依赖 SWD 人工救砖。

### 五条设计原则

| 原则 | 体现 |
|---|---|
| **永不砖死** | 所有失败终点 = OTA 模式（死循环等 YMODEM），最差也有 SWD |
| **不动正在运行的** | 升级只写非活跃槽，校验通过才翻转指针 |
| **先持久化，后动作** | boot_count/active 翻转都先落盘再执行下一步，掉电可恢复 |
| **观察窗口收口** | COMPLETE 态 + IWDG + App 确认，覆盖 CRC 无法检测的“启动即崩” |
| **每层只做一件事** | 传输归 CRC16，落盘归 CRC32，槽对位归 reset-handler，存活归 IWDG |

---

## 四、YMODEM 协议详解

### 4.1 作用

Chuck Forsberg 1980 年代在 XMODEM 基础上改进的**串口文件传输协议**。核心使命：在不可靠、无流控的 UART 链路上可靠传输一个完整文件。

| 问题 | YMODEM 的手段 |
|---|---|
| 链路误码 | 每包 CRC16-CCITT 校验，错包重传 |
| 丢包/乱序 | 停等协议：每包确认后才发下一包 |
| 收发时钟不同步 | 接收方主动权：发 `'C'` 表示“我准备好了” |
| 传输什么文件 | seq=0 文件名包头携带文件名 + 文件大小元数据 |

为什么嵌入式 bootloader 钟情它：MCU 端实现极小（本项目接收端 ~300 行 C，无堆、无 RTOS、无动态内存）、上位机生态成熟（Tera Term/SecureCRT/Xshell 内置）、停等天然流控。

### 4.2 控制字符与包结构

| 字符 | 值 | 方向 | 含义 |
|---|---|---|---|
| SOH | 0x01 | PC→MCU | 本包数据区 **128 字节** |
| STX | 0x02 | PC→MCU | 本包数据区 **1024 字节**（YMODEM-1K 特有） |
| EOT | 0x04 | PC→MCU | 文件数据发完了 |
| ACK | 0x06 | MCU→PC | 确认，请继续 |
| NAK | 0x15 | MCU→PC | 校验失败，请重发本包 |
| CAN | 0x18 | 双向 | 取消整个传输 |
| `'C'` | 0x43 | MCU→PC | 我就绪，请求开始/下一批（指定 CRC16 模式） |

**包头第一字节双重语义**：SOH/STX 同时声明“新包开始”和“本包数据区长度”。YMODEM-1K 允许 128/1024 混用 —— 文件名包用 SOH（元数据短），数据包用 STX（1024B 减少协议开销和 ACK 往返）。

```
┌──────┬──────┬─────────┬────────────────┬───────────┐
│ SOH/ │ seq  │ ~seq    │  数据区          │  CRC16    │
│ STX  │ (1B) │ (1B)    │  128 / 1024 B   │ (2B,大端) │
└──────┴──────┴─────────┴────────────────┴───────────┘
```

- seq：包序号，0=文件名头包，1..N=数据包，mod 256 回绕
- ~seq：序号取反，`seq + ~seq == 0xFF` 校验（防序号被误码破坏）
- CRC16：多项式 0x1021（CRC-16/CCITT），初值 0，MSB 先行，高字节在前

**seq=0 文件名包数据区**：`"app_v1_2.bin" \0 "394256" \0 0x00...`（文件名 + NUL + ASCII 大小 + NUL + 填充）。

### 4.3 完整会话时序

```
MCU (ymodem.c)                          PC (ymodem_send.py)
────────────────────────────────────────────────────────────
① 发 'C' 每100ms × 300次 ──────────────> 等到 'C'，开始会话
              (声明: 我用 CRC16 模式)
②      <──── SOH 00 FF "xxx.bin"\0"394256"\0..CRC ────  文件名包
   CRC 校验 + 解析 + 大小预检
   发 ACK ──────────────────────────────> 收到 ACK
③ [擦除目标槽 Flash, 数秒]
   发 'C' ──────────────────────────────> 收到 'C'，开始发数据
④      <──── STX 01 FE data[1024] CRC16 ────  数据包
   CRC 校验 → 逐字节写 Flash
   发 ACK ──────────────────────────────> 收到 ACK，发下一包
        ... 重复 N 次（seq 递增，255 回绕 0）...
⑤      <──── EOT ───────────────────────  "文件发完了"
   发 NAK ──────────────────────────────> 收到 NAK，重发 EOT
⑥      <──── EOT（第二次）───────────────
   发 ACK ──────────────────────────────> 收到 ACK
⑦      <──── SOH 00 FF 全 0x00..CRC ────  空文件名包=批处理结束
   发 ACK ──────────────────────────────> 完成
```

时序细节设计意图：
- **③ 擦除放在 ACK 后、'C' 前**：F429 擦 384KB 要数秒，让发送方在等 `'C'` 的空档干等，避免发送方超时
- **⑤⑥ 两次 EOT**：防数据字节被误码恰好变成 0x04(EOT) 导致提前截尾
- **⑦ 空文件名包**：YMODEM 是批处理协议，全零头包表示“没有更多文件了”

### 4.4 接收数据如何逐层解析使用

```
字节流 → [包层] 组包+校验 → [文件层] 重组 → [Flash层] 落盘 → [元数据层] 记账
```

1. **包层**：`ymodem_recv_packet_body()` 逐字节收完 seq、~seq、数据、CRC，三重校验（序号完整性 `seq+~seq==0xFF`、CRC16、调用方再查顺序性），任一失败整包作废
2. **重复包处理**：`seq == expected_seq - 1` → 补 ACK 但不写 Flash（防 ACK 丢失导致的重发 + 防 Flash 偏移重复推进）
3. **Flash 层**：`flash_if_write(target_addr + total_received, ...)`，偏移 = 槽基址 + 累计字节数；停等协议保证按序到达，无需重排缓冲
4. **元数据层**（ota.c）：传输成功后 → reset-handler 防错包校验 → 全量 CRC32 + 从文件名解析版本号 → 写 OTA 参数区 → 翻转 active → 重启

### 4.5 与行业通用规范的符合性

**✅ 符合**：包结构、CRC16-CCITT、`'C'` 建 CRC 模式、文件名包格式、两次 EOT、序号 mod256、重复包检测、空文件名批结束包、收包期间禁 RXNE 中断 —— 协议主体规范且可互操作（Tera Term/SecureCRT 理论上可通）。

**⚠️ 简化/偏离**：
1. 单个 CAN 即取消（规范建议 CAN CAN + 填充）；噪声恰好 0x18 概率低，可接受
2. padding 字节计入 total_received（标准填充 0x1A），OTA 元数据 size 比真实 bin 略大；功能自洽但更严谨应截断为 `min(total_received, file_size)`，且未交叉校验与 file_size 一致
3. EOT ACK 后未发 `'C'` 直接裸等结束包 —— 与通用终端工具互操作时是潜在兼容点
4. 数据阶段超时用 NAK 重传（标准数据阶段更常用 `'C'`）
5. `uart_getc_timeout` 忙等粗校准（依赖主频假设），换平台会漂移；printf 与 YMODEM 共用 USART1 是危险设计（包体段已禁 printf 规避）

**🔒 安全性视角**：YMODEM 无认证/签名，只保证“收到的字节=发出的字节”（CRC），不保证“发出的字节可信”。本项目防护栈 = YMODEM CRC16（防误码）→ CRC32 全量（防落盘损坏）→ reset-handler 范围校验（防错槽）→ AB 分区 + IWDG + boot_count（防变砖）。行业更高标准：固件签名（ECDSA）、防降级（anti-rollback）、加密传输。

---

## 五、YMODEM 关键代码细节

### 5.1 文件名/文件大小解析（parse_filename_packet）

seq=0 包数据区布局：`文件名 → \0 → ASCII十进制大小 → \0（或空格）→ 全 0x00 填充`。

**文件名解析**（大小字段之前）：
```c
int name_len = 0;
while (name_len < 64 && buf[name_len] != 0x00) name_len++;  // 扫到第一个 NUL
if (name_len >= 64 || name_len == 0) return -1;             // 空名/超长 → 非法包
memcpy(status->file_name, buf, name_len);
status->file_name[name_len] = '\0';
```
`name_len < 64` 是防御：status->file_name 容量 64，防止坏包越界。

**大小解析**（选中段）：
```c
int pos = name_len + 1;      // 跳过 NUL 分隔符，定位大小字段起点
char size_str[16] = {0};
while (pos < 128 && buf[pos] != 0x00 && buf[pos] != 0x20 && s < 15)
    size_str[s++] = buf[pos++];          // 逐字符搬运
size_str[s] = '\0';
status->file_size = 0;
for (int i = 0; i < s; i++)
    if (size_str[i] >= '0' && size_str[i] <= '9')   // 手写 atoi
        status->file_size = status->file_size * 10 + (size_str[i] - '0');
```

四个终止条件各管一事：`pos<128` 不越界；`!=0x00` 遇 NUL 结束（本项目的填充）；`!=0x20` 遇空格结束（兼容带 mtime 的标准格式）；`s<15` 防 size_str 溢出（16 字节容量）。

两个细节：
- 大小缺失时静默降级为 0 → 外层有 "size unknown" 进度分支；但 `file_size > max_size` 预检会失效
- 非数字字符是**跳过而非报错**（`"39a4"` → 394），宽容策略

**去向**：file_name → `parse_version_from_name("xxx_v1_2.bin")` → 0x00010002 存入 OTA 参数区；file_size → 预检 + 进度显示。

### 5.2 两个异常分支（数据阶段）

```c
if (len < 0) {                    // 分支一：包收不完整/校验不过（链路层）
    if (retries++ < YMODEM_MAX_RETRIES) { uart_putc(NAK); continue; }
    else { flash_if_lock(); return len; }
}
if (seq != expected_seq) {        // 分支二：包完好但序号错（协议层）
    if (seq == (expected_seq - 1)) { uart_putc(ACK); continue; }  // 重复包
    flash_if_lock(); return YMODEM_ERR_SEQ;                        // 真乱序
}
```

| | 分支一 `len < 0` | 分支二 `seq != expected_seq` |
|---|---|---|
| 错误性质 | 包收不完整/校验不过（链路层） | 包完好但序号错（协议层） |
| 典型诱因 | 误码、卡顿、噪声字节 | ACK 丢失（重复包）／状态机失步（乱序） |
| 应对 | NAK 请求重发，最多连续 10 次 | 重复包：ACK+丢弃；真乱序：立即终止 |
| 可恢复性 | 瞬时故障可自愈 | 仅 ACK 丢失可自愈；失步必须重启会话 |

- **重复包**（`seq == expected_seq - 1`）唯一触发场景 = MCU 的 ACK 丢了。补 ACK 但不写 Flash、不推进偏移；否则 total_received 多加 1024B，后面所有数据整体错位 1KB
- **真乱序不 NAK 挽救**：停等协议前提是“每包确认后发下一包”，真乱序说明前提已崩塌，无法确定从哪包重发对齐，硬写只会烧出错位固件，宁可立即失败重来

**小瑕疵**：`YMODEM_ERR_CANCEL`（收到 CAN，用户取消）也走了 NAK 重试分支，会白等 10 次 × 3s。规范做法是收到 CAN 立即终止。

---

## 六、OTA 参数区与 seq

### 6.1 append-only 磨损均衡日志

Sector 4（64KB）= 1024 槽 × 64B，每条记录 = `magic(4) + seq(4) + ota_param_t(52) + crc32(4)`。

- 常规 save **只追加**写下一个已擦除槽（无需擦除）；写满 1024 槽才整扇区擦除重写（每槽擦除频率 ≈ 1/1024）
- 掉电安全：写一半掉电 → 该槽 CRC 不匹配 → load 跳过它取上一条有效记录
- 全擦重写那 1/1024 窗口掉电 → 退化为参数初始化、默认 active=A，仍可安全启动

### 6.2 new_seq 代表什么

```c
load_latest(&cur, &cur_seq);      // 读出当前最新有效记录序号
uint32_t new_seq = cur_seq + 1;   // 新记录 = 最新序号 + 1
```

- **单调递增的日志“代次计数器”**，每次 save 都 +1
- **跨“整擦重写”也持续增长**（1023 → 1024，不会回到 0）—— 因为擦除只清了存储位置，清不掉计数器；写回槽 0 时用的仍是 `new_seq = cur_seq + 1`
- 唯一归零入口：`ota_params_init()`（工厂级全盘重建，写 seq=0），只在**首次上电**或**日志完全损坏无有效记录**时触发
- uint32_t 上限 4GB，每次 save +1，实际不可能溢出

**为什么必须有它**：日志有“回绕”（满日志 → 整擦 → 重写回槽 0），物理位置不再能反映新旧。有了 seq，“谁最新”变成记录自带的内容属性，与存放位置无关。`load_latest` 靠 `rec->seq >= best_seq` 选出最大值那条。

**诚实评估**：以当前实现的严格约束（纯追加无空洞 + F429 扇区擦除硬件原子）看，多数路径用“最后一个有效槽位”选最新结果相同 —— seq 在功能上冗余，但它是 append-only 日志的教科书标准设计，让顺序成为记录内容、天然防御回绕。

### 6.3 Keil 烧录会让 seq 归 0 吗 —— 不一定

| 场景 | 擦除范围 | Sector 4 | seq |
|---|---|---|---|
| Keil 烧 App（默认 Erase Sectors） | 只擦镜像覆盖的扇区（A槽=5-7，B槽=8-10） | 不擦 | 不归 0 |
| Keil 烧 Bootloader（Erase Sectors） | 只擦 Sector 0-3 | 不擦 | 不归 0 |
| Keil 勾选 Erase Full Chip | 整个 Flash | 擦 | 归 0 |
| ST-Link / J-Flash / CubeProgrammer 全片擦 | 整个 Flash | 擦 | 归 0 |

Keil 按**下载镜像地址范围**擦扇区：App 链接在 0x08020000，只擦 Sector 5-7（或 B 槽 8-10）；Sector 4 在 0x08010000 不在范围内，一个字节都不碰。

**seq 归 0 只是“参数区重建”的连带结果**，真正被重置的是一整包状态：`active_partition→A`、`ota_state→IDLE`、`boot_count→0`、两槽 size/crc/version→0。

**两个实践坑**：
1. **全片擦后只烧 B 槽 app 会跑不起来**：active 默认 A，A 是空的 → IDLE 态查 SP 失败 → 直接进 OTA 模式。要么烧到 A 槽，要么先切 active
2. **Keil 烧 app 不更新元数据，可能与 COMPLETE 状态打架**：若 ota_state 恰好是 COMPLETE，boot 会用旧 size/旧 CRC 校验新烧镜像 → CRC 必不匹配 → boot_count 递增 → 超限回滚到另一槽，**你烧的固件会被自动回滚掉**。常规 IDLE 态则只查 SP 不查 CRC，无此问题

> 排查建议：boot 串口每次打印 `Active partition` / `OTA state` / 两槽 size。烧完不按预期跑先看这三行。

---

## 七、工具链与传输

- **MobaXterm 不能直接传**：串口会话无内置 YMODEM 功能（与 MCU 端实现无关）。Tera Term / Xshell / SecureCRT / ExtraPuTTY 有原生支持
- **推荐**：项目自带 `tools/ymodem_send.py`（配套联调过）或 `tools/ota_gui` 图形界面
- **用标准终端传输的注意点**：MCU 确认第二个 EOT 后**不发 'C'** 直接裸等结束包，而标准发送方会等 `'C'` → 两边互等各自超时 → 终端可能弹“传输失败”**但固件已写完**。判断成败的唯一依据是 MCU 串口日志：
  ```
  [YMODEM] Transfer complete.
  [BOOT] OTA params updated, active=App B. Rebooting...
  ```
- **发对槽的 bin**：A 槽活跃时须发链接到 0x08080000 的 `app_b.bin`（Keil Target `stm32f429_b` 编译产物）。发错镜像会被 reset-handler 校验拒绝，不会变砖，但浪费一次传输

---

## 八、协议家族背景

| 协议 | 特点 |
|---|---|
| XMODEM（1977） | 128B 定长包 + 8-bit 校验和，无文件名，一次传“一堆字节” |
| **YMODEM** | CRC16、1024B 包（-1K 变体）、文件名/大小元数据、批处理多文件 |
| YMODEM-g | 去掉每包 ACK 的流模式，速度翻倍但 MCU Flash 写入期间无法反压，**不适合 bootloader** |
| ZMODEM | 滑动窗口 + 自适应包长 + crash recovery，效率最高但实现复杂，嵌入式 bootloader 几乎不用 |

---

## 九、已修复缺陷：COMPLETE 分支回滚触发条件（复盘）

### 原始缺陷

`boot_decision.c` 的 COMPLETE 分支里，`boot_count >= max_boot_count` 的超限检查曾被**嵌套在 `calc_crc != crc`（CRC 失败）分支内部**。而注释声称”App 崩 → IWDG 复位 → 再次进入本分支 → boot_count 递增 → 超限则切槽回滚”——**意图是”无论原因超限就回滚”，实现却是”只有 CRC 失败且超限才回滚”**。

### 崩溃死循环场景（修复前）

固件完整（CRC 永远通过）但 App 运行期崩溃时：

```
Boot1: ++→1  CRC✓ → 跳App → 崩 → IWDG复位
Boot2: ++→2  CRC✓ → 跳App → 崩 → IWDG复位
Boot3: ++→3  CRC✓ → 跳App → 崩 → IWDG复位
... boot_count 无限增长，永远进不了回滚分支 → 死循环
```

对比：CRC 失败场景反而正常——坏镜像下 Boot3（count=3）即触发回滚，因为每次 CRC 都失败会落入超限检查。

### 修复（已落地）

把超限检查提到 CRC 判断之前（先评估尝试预算，再谈校验结果）。当前实际实现（boot_decision.c）：

```c
case OTA_STATE_COMPLETE:
{
    g_ota_param.boot_count++;
    ota_params_save(&g_ota_param);
    printf(“[BOOT] Boot attempt %u/%u\r\n”, boot_count, max_boot_count);

    uint32_t addr = get_active_addr();
    uint32_t size = active_size();
    uint32_t crc  = active_crc();

    if (size == 0 || size == 0xFFFFFFFF) {          // 无元数据 → OTA
        printf(“[BOOT] Active slot has no metadata, entering OTA.\r\n”);
        return 0;
    }

    uint32_t calc_crc = crc32_flash(addr, size);    // 先算出来用于调试打印
    printf(“[BOOT] CRC32: saved=0x%08X calc=0x%08X\r\n”, crc, calc_crc);

    // ★ 超限检查提前：耗尽尝试次数就回滚，不看 CRC 结果
    if (g_ota_param.boot_count >= g_ota_param.max_boot_count) {
        printf(“[BOOT] Max boot attempts, rolling back to other slot...\r\n”);
        if (rollback_to_other() == 0) {
            g_ota_param.ota_state  = OTA_STATE_IDLE;
            g_ota_param.boot_count = 0;
            ota_params_save(&g_ota_param);
            return 1;
        }
        printf(“[BOOT] Rollback failed, entering OTA mode.\r\n”);
        return 0;                                   // 回滚失败 → OTA
    }

    if (calc_crc == crc) {                          // 未超限 + CRC 通过 → 跳转（保持 COMPLETE）
        printf(“[BOOT] Firmware verified OK.\r\n”);
        return 1;
    }
    // 未超限 + CRC 失败 → 重启重试
    printf(“[BOOT] CRC mismatch (attempt %u/%u), reboot to retry...\r\n”,
           g_ota_param.boot_count, g_ota_param.max_boot_count);
    NVIC_SystemReset();
    return 0;   // 不可达，保险
}
```

修复后语义：
- **超限（无论 CRC 结果）** → 回滚
- **未超限 + CRC 通过** → 跳转（正常升级路径）
- **未超限 + CRC 失败** → 重启重试（坏镜像场景）

边界语义：`boot_count >= max`（=3）时新固件实际获得 **2 次跳转机会**（Boot1、Boot2 跳转，Boot3 直接回滚），与 boot_flow.md 文档时序（`2/3 → 3/3 → rollback`）一致；若想给足 3 次，改成 `> max`（count=4 才回滚）。

### 修复带来的附加观察：重试期参数区写入

启动失败重试全程会多次 `ota_params_save`（append-only 追加记录），但中间记录**只有 boot_count 一个字段变化**：ota_state 恒为 COMPLETE、active_partition 恒为新槽、CRC/size/version 恒为 OTA 完成时写入的值。直到最后一次回滚成功才集中改变三个字段——`rollback_to_other()` 翻转 active_partition、置 IDLE、boot_count 清零，且这三次变化在同一次 save 里完成。中间那些”仅 boot_count 差 1”的记录是**跨重启持久化计数**的必要载体，非无用垃圾；1024 槽容量下开销可忽略（约 1/1024 触发整擦回收）。

### 相关独立缺口（仍未修复）

修复后 COMPLETE 死循环被堵住，但**回滚到旧槽后是 IDLE 态**——IDLE 只查 SP 不查 boot_count。若旧槽也恰好运行期崩溃（SP 合法但代码坏）→ IDLE 态”重启风暴”：boot 验 SP 通过 → 跳 → 崩 → IWDG → 循环，无上限。修法与 COMPLETE 的观察窗口机制同构：每次跳转都计数、App 正常启动才清零。

---

## 一句话总结

Bootloader 上电 → 读 append-only 参数区拿 active_partition 和 ota_state → 先按 boot_count 超限决策回滚、再 CRC32 校验活跃槽（超限优先于 CRC）→ 2 秒按键窗口决定跳 App 还是进 YMODEM OTA → 跳转前启动 IWDG，App 启动成功写参数确认、失败则 IWDG 复位累计计数自动切回旧槽；任何异常路径最终都收敛到 OTA 模式，永不砖死。
