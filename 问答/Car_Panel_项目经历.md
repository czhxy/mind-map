# 项目经历

---

2026.5 - 至今                   全车智能中控面板（Car_Panel）                   独立开发

项目描述：基于 STM32 双 MCU + CAN 总线的汽车仪表盘演示系统，实现仪表盘 UI 显示、电机闭环控制与固件 YMODEM OTA 升级。

硬件平台：STM32F429IGT6（显示域 ECU，Cortex-M4，180MHz），STM32F103C8T6（动力域 ECU，Cortex-M3，72MHz），MSP2834 2.8 寸 SPI 触摸屏（ILI9341V + FT6336G 电容触摸），MG310 直流减速电机 + DRV8833 H 桥驱动 + 霍尔编码器，CAN 500kbps 总线，29-bit 扩展帧。

功能实现：
1. 双 ECU CAN 总线通信架构设计：设计 29-bit 扩展帧 ID 位域编解码协议，划分优先级、源/目标地址、帧类型、功能字段共 6 层。显示域基于 FreeRTOS 实现 TX/RX 双队列异步通信，RX 中断通过 xQueueSendFromISR 投递帧到队列（深度 64），10ms 周期消费分发；TX 任务 10ms 周期发送，邮箱满时回灌队首防丢帧。动力域裸机侧采用环形缓冲队列 + 弱符号回调机制，实现收/发/解析三层解耦。

2. LVGL 仪表盘 UI 实现：基于 LVGL v8 完成仪表盘界面开发，包含车速表、转速表、CAN 通信状态指示灯、电机故障告警指示。SPI2 驱动 ILI9341V（5.625MHz），配置双缓冲（28.8KB），400kHz I2C 驱动触摸屏，5ms 周期完成渲染刷新。

3. 电机位置式 PID 闭环控制：TIM1 输出 20kHz PWM 驱动 DRV8833 H 桥，TIM2 正交编码器模式 5ms 周期采集实际转速（基于 1320 计数/转换算 rpm×10）。实现位置式 PID 闭环，目标转速由显示域经 CAN 控制帧（10ms 周期）下发，实际转速与故障码经 CAN 状态帧回传并更新仪表盘。

4. Bootloader YMODEM OTA 升级：设计真 AB 分区方案（Bootloader 64KB + 参数区 64KB + App A/B 各 384KB），两槽独立 scatter 链接，YMODEM 传输写入非活跃槽后翻转标志零搬运切换。参数区采用 append-only 日志（1024 槽 × 64B），条带 CRC32 校验，解决 NOR Flash 非原子写入的掉电损坏问题。自研 Python OTA GUI 上位机（tkinter + PyInstaller 打包），支持串口选择、芯片查询、固件发送，3 套 UI 主题。

5. FreeRTOS 多任务架构设计：显示域划分 8 个 FreeRTOS 任务，按实时性分层——高频控制层（CAN_TX 10ms、CAN_RX 10ms，优先级 3），UI 与交互层（DISPLAY 5ms、KEY_SCAN 20ms、UART_QUERY 10ms，优先级 2），后台监控层（HEARTBEAT 500ms，优先级 1）。动力域裸机基于 SysTick 实现三级周期性调度（5ms/10ms/500ms），双 ECU 间通过 CAN 总线完成状态同步。

项目成果：
- CAN 总线通信零丢帧，TX/RX 双队列架构在 500kbps 速率下 10ms/10ms 收发周期稳定运行，邮箱满回灌机制杜绝帧丢失问题
- 电机闭环控制稳态误差控制在 ±2 rpm 以内，编码器采样精度达 1320 计数/转，PWM 输出频率 20kHz 匹配 H 桥驱动要求
- OTA 升级成功率 100%，AB 分区零搬运切换 + append-only 参数区 CRC32 校验保证升级过程掉电可恢复，上位机支持一键 YMODEM 固件下发
- LVGL 仪表盘 UI 5ms/帧稳定刷新，双缓冲无撕裂，触摸响应延迟 < 10ms
- 8 任务 FreeRTOS 架构合理分层，任务间通过队列/信号量 IPC 通信，无死锁、无优先级反转
- 产出 CAN 通信协议、Bootloader OTA 方案、FreeRTOS 任务设计等 5 份技术文档及 OTA GUI 上位机
