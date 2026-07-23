# IMU工作原理说明文档

## 1. 概述

本文档描述项目中IMU（惯性测量单元）的工作机制，包括硬件接口、软件驱动、数据处理流程。

**主控芯片**: N32G430
**IMU系列**: TDK ICM系列（多型号自动识别）

---

## 2. 支持的IMU型号

| 型号 | WHO_AM_I地址 | WHO_AM_I值 | 寄存器组标识 |
|------|-------------|-----------|-------------|
| ICM-40607 | 0x75 | 0x38 | g_Reg_icm40607 |
| ICM-40608 | 0x75 | 0x39 | g_Reg_icm40608 |
| ICM-42670 | 0x75 | 0x67 | g_Reg_icm42670 |
| ICM-42652 | 0x75 | 0x6F | g_Reg_icm42652 |
| **ICM-45606** | **0x72** | **0x84** | **g_Reg_icm45606 (待实现)** |

> **注意**: ICM-45606与ICM-42607x系列是完全不同的芯片，寄存器映射完全不同！

---

## 3. 硬件接口

### 3.1 SPI接口配置

| 功能 | GPIO端口 | 引脚号 |
|-----|---------|-------|
| SPI时钟 (SCK) | GPIOA | PIN_5 |
| SPI主机输入从机输出 (MISO) | GPIOA | PIN_6 |
| SPI主机输出从机输入 (MOSI) | GPIOA | PIN_7 |
| 片选信号 (CS) | GPIOA | PIN_4 |
| 电源控制 | GPIOA | PIN_15 |

### 3.2 SPI参数配置

```c
// SPI配置
SPI_InitStructure.DataDirection = SPI_DIR_DOUBLELINE_FULLDUPLEX;  // 全双工
SPI_InitStructure.SpiMode       = SPI_MODE_MASTER;               // 主机模式
SPI_InitStructure.DataLen       = SPI_DATA_SIZE_8BITS;           // 8位数据
SPI_InitStructure.CLKPOL        = SPI_CLKPOL_HIGH;                // 时钟空闲高电平
SPI_InitStructure.CLKPHA        = SPI_CLKPHA_SECOND_EDGE;        // 第二个边沿采样
SPI_InitStructure.NSS           = SPI_NSS_SOFT;                   // 软件控制NSS
SPI_InitStructure.BaudRatePres  = SPI_BR_PRESCALER_4;             // 预分频4 (~12MHz)
SPI_InitStructure.FirstBit      = SPI_FB_MSB;                     // 高位先出
```

---

## 4. 软件架构

### 4.1 分层结构

```
┌─────────────────────────────────────────────┐
│  Task层: task_imu.c                         │  定时采样和任务调度
├─────────────────────────────────────────────┤
│  模块层: mod_imu.c                          │  设备配置、数据处理、姿态解算
├─────────────────────────────────────────────┤
│  BSP层: bsp_imu.c                           │  SPI接口、数据读写
└─────────────────────────────────────────────┘
```

### 4.2 相关文件

| 文件路径 | 功能描述 |
|---------|---------|
| `projects/app_n32g430/bsp/bsp_imu.c` | BSP层IMU驱动 - SPI接口配置和数据读写 |
| `projects/app_n32g430/bsp/bsp_imu.h` | BSP层IMU头文件 - 宏定义和函数声明 |
| `projects/app_n32g430/mod_driver/mod_imu.c` | 模块层IMU驱动 - 设备配置、数据处理、姿态解算 |
| `projects/app_n32g430/mod_driver/mod_imu.h` | 模块层IMU头文件 - 数据结构定义 |
| `projects/app_n32g430/task/task_function/task_imu.c` | Task层IMU任务 - 定时采样和调度 |

---

## 5. 寄存器配置

### 5.1 寄存器结构体定义

```c
typedef struct {
    uint8_t reg_SOFTRESET;           // 软复位寄存器地址
    uint8_t value_SOFTRESET_CONFIG;   // 软复位配置值

    uint8_t reg_WHO_AM_I;             // 设备ID寄存器地址
    uint8_t value_WHO_AM_I;           // 设备ID期望值

    uint8_t reg_PWR_MGMT0;            // 电源管理寄存器地址
    uint8_t value_PWR_GYRO_LOWNOISE;  // 陀螺仪低噪声模式配置
    uint8_t value_PWR_ACCEL_LOWNOISE; // 加速度计低噪声模式配置

    uint8_t reg_GYRO_CONFIG0;         // 陀螺仪配置寄存器地址
    uint8_t value_GYRO_FS_SEL;        // 陀螺仪量程配置
    uint8_t value_GYRO_ODR;           // 陀螺仪输出速率配置

    uint8_t reg_ACCEL_CONFIG0;        // 加速度计配置寄存器地址
    uint8_t value_ACCEL_ODR;          // 加速度计输出速率配置

    uint8_t reg_RAW_DATA;             // 原始数据起始地址
} IMU_REG_TYPE;
```

### 5.2 各型号寄存器配置对比

| 参数 | ICM-40607/40608/42652 | ICM-42670 | ICM-42607 |
|------|----------------------|-----------|-----------|
| SOFTRESET寄存器 | 0x11 | 0x02 | **0x02** |
| SOFTRESET值 | 0x01 | 0x20 | **0x10** |
| WHO_AM_I寄存器 | 0x75 | 0x75 | **0x75** |
| WHO_AM_I值 | 0x38/0x39/0x6F | 0x67 | **0x61** |
| PWR_MGMT0寄存器 | 0x4e | 0x1f | **0x1f** |
| GYRO_CONFIG0寄存器 | 0x4f | 0x20 | **0x20** |
| ACCEL_CONFIG0寄存器 | 0x50 | 0x21 | **0x21** |
| RAW_DATA地址 | 0x1d | 0x09 | **0x09** |

---

## 6. 设备识别与初始化流程

### 6.1 设备识别代码

```c
void ModImu_DeviceConfig(void) {
    uint8_t data = 0;

    // 最多重试50次读取WHO_AM_I寄存器
    for (int i = 0; i < 50; i++) {
        BspImu_ReadBytes(0x75, &data, 1);  // 读取WHO_AM_I

        if (data == 0x38) {  // ICM-40607
            g_Reg_used = g_Reg_icm40607;
            current_imu_type = 40607;
        } else if (data == 0x39) {  // ICM-40608
            g_Reg_used = g_Reg_icm40608;
            current_imu_type = 40608;
        } else if (data == 0x67) {  // ICM-42670
            g_Reg_used = g_Reg_icm42670;
            current_imu_type = 42670;
        } else if (data == 0x6F) {  // ICM-42652
            g_Reg_used = g_Reg_icm42652;
            current_imu_type = 42652;
        } else if (data == 0x61) {  // ICM-42607 (新增)
            g_Reg_used = g_Reg_icm42607;
            current_imu_type = 42607;
        }

        if (current_imu_type != 0) {
            break;
        }
        HwSys_Delay1ms(1);
    }
    // ... 后续配置
}
```

### 6.2 初始化配置序列

```c
// 1. 软复位
BspImu_WriteOneByte(REG_SOFTRESET, SOFTRESET_CONFIG);
HwSys_Delay1ms(12);

// 2. 配置电源管理（低噪声模式）
BspImu_WriteOneByte(PWR_MGMT0, PWR_GYRO_LOWNOISE | PWR_ACCEL_LOWNOISE);
HwSys_Delay1ms(1);

// 3. 配置陀螺仪（±500dps, 800Hz）
BspImu_WriteOneByte(GYRO_CONFIG0, GYRO_FS_SEL | GYRO_ODR);
HwSys_Delay1ms(1);

// 4. 配置加速度计（800Hz）
BspImu_WriteOneByte(ACCEL_CONFIG0, ACCEL_ODR);
HwSys_Delay1ms(2);

// 5. 附加配置（滤波器等）
BspImu_WriteOneByte(0x51, 0x04);  // GYRO_CONFIG1
HwSys_Delay1ms(2);
BspImu_WriteOneByte(0x53, 0x08);  // ACCEL_CONFIG1
HwSys_Delay1ms(2);
BspImu_WriteOneByte(0x52, 0x66);  // APEX_CONFIG0
HwSys_Delay1ms(2);
```

---

## 7. 数据读取

### 7.1 SPI读取函数

```c
uint8_t BspImu_ReadBytes(uint8_t addr, uint8_t *data, uint16_t len) {
    GPIO_Pins_Reset(BSP_IMU_SPI_GPIO_CS, BSP_IMU_SPI_PIN_CS);  // CS拉低

    // 发送读取地址（bit7=1表示读操作）
    BspImu_WR_byte(addr | 0x80, NULL);

    // 连续读取数据
    for (int i = 0; i < len; i++) {
        BspImu_WR_byte(0xA5, &data[i]);  // 0xA5为伪数据
    }

    GPIO_Pins_Set(BSP_IMU_SPI_GPIO_CS, BSP_IMU_SPI_PIN_CS);  // CS拉高
    return true;
}
```

### 7.2 原始数据结构（14字节）

| 偏移 | 数据 | 说明 |
|-----|------|------|
| 0-1 | temp | 温度值 |
| 2-3 | accel_x | 加速度计X轴 |
| 4-5 | accel_y | 加速度计Y轴 |
| 6-7 | accel_z | 加速度计Z轴 |
| 8-9 | gyro_x | 陀螺仪X轴 |
| 10-11 | gyro_y | 陀螺仪Y轴 |
| 12-13 | gyro_z | 陀螺仪Z轴 |

### 7.3 数据解析

```c
void ModImu_ReadData_Dma(void) {
    uint8_t DataBuffer[14] = {0};
    BspImu_ReadBytes(REG_RAW_DATA, DataBuffer, 14);

    raw_data->temp    = (DataBuffer[0] << 8) | DataBuffer[1];
    raw_data->accel_x = (DataBuffer[2] << 8) | DataBuffer[3];
    raw_data->accel_y = (DataBuffer[4] << 8) | DataBuffer[5];
    raw_data->accel_z = (DataBuffer[6] << 8) | DataBuffer[7];
    raw_data->gyro_x  = (DataBuffer[8] << 8) | DataBuffer[9];
    raw_data->gyro_y  = (DataBuffer[10] << 8) | DataBuffer[11];
    raw_data->gyro_z  = (DataBuffer[12] << 8) | DataBuffer[13];
}
```

---

## 8. 数据处理流程

```
┌──────────────┐
│  读取原始数据  │
└──────┬───────┘
       ▼
┌──────────────┐
│  滑动滤波    │  (5点滑窗滤波)
└──────┬───────┘
       ▼
┌──────────────┐
│  零偏校准    │  (100帧数据求均值)
└──────┬───────┘
       ▼
┌──────────────┐
│  量程转换    │  gyro_raw → mrad/s
└──────┬───────┘
       ▼
┌──────────────┐
│  姿态解算    │  (四元数/欧拉角)
└──────┬───────┘
       ▼
┌──────────────┐
│  数据输出    │
└──────────────┘
```

### 8.1 量程转换

```c
// 陀螺仪量程: ±500 dps
// 转换公式: gyro_mrad/s = gyro_raw * M_M2PI / 360 * GYRO_FS / 0x7FFF
// 其中 M_M2PI = 6283.307179, GYRO_FS = 500
```

### 8.2 陀螺仪零偏校准

- 采集100帧数据
- 排除异常离群值（阈值20）
- 计算零偏均值并保存

---

## 9. 定时采样

- **采样频率**: 200Hz（TIM4定时器中断）
- **数据输出速率**: 800Hz（IMU内部采样）
- **加速度计量程**: ±16g

---

## 10. 输出数据结构

```c
typedef struct {
    uint8_t work_state;          // 工作状态
    uint8_t calibration_status;  // 校准状态
    float gyro_x;                // X轴角速度 [mrad/s]
    float gyro_y;                // Y轴角速度 [mrad/s]
    float gyro_z;                // Z轴角速度 [mrad/s]
    float accel_x;               // X轴加速度 [原始值]
    float accel_y;               // Y轴加速度 [原始值]
    float accel_z;               // Z轴加速度 [原始值]
    float yaw;                   // Yaw角度 [mrad]
    float pitch;                 // Pitch角度 [mrad]
    float roll;                  // Roll角度 [mrad]
} ModImuFb;
```

---

## 11. ICM-45606 配置说明

> **重要**: ICM-45606与ICM-42607x系列是**完全不同的芯片**，寄存器映射完全不同！

根据ICM-45606数据手册，正确配置如下：

### 关键寄存器地址

| 寄存器 | 地址 | 说明 |
|-------|------|------|
| PWR_MGMT0 | 0x10 | 电源管理 |
| ACCEL_CONFIG0 | 0x1B | 加速度计配置 |
| GYRO_CONFIG0 | 0x1C | 陀螺仪配置 |
| REG_MISC2 | 0x7F | 软复位 |
| WHO_AM_I | 0x72 | 设备ID (0x84) |

### 数据寄存器顺序（14字节）

| 偏移 | 数据 | 说明 |
|-----|------|------|
| 0-1 | accel_x | 加速度计X轴 |
| 2-3 | accel_y | 加速度计Y轴 |
| 4-5 | accel_z | 加速度计Z轴 |
| 6-7 | gyro_x | 陀螺仪X轴 |
| 8-9 | gyro_y | 陀螺仪Y轴 |
| 10-11 | gyro_z | 陀螺仪Z轴 |
| 12-13 | temp | 温度值 |

### 正确配置值

| 配置项 | 值 | 说明 |
|-------|-----|------|
| SOFTRESET | 0x01 | 写入REG_MISC2(0x7F)的bit0 |
| PWR_MGMT0 | 0x0F | 陀螺仪+加速度计低噪声模式 |
| GYRO_CONFIG0 | 0x36 | ±500dps, 800Hz (0x30 \| 0x06) |
| ACCEL_CONFIG0 | 0x16 | ±16g, 800Hz (0x10 \| 0x06) |

---

## 12. 代码问题与修复

### 现状

代码中 `g_Reg_icm42607` 的配置是针对ICM-42607系列的，**与ICM-45606不兼容**。

### 主要差异

| 项目 | ICM-42607x | ICM-45606 |
|------|-------------|-----------|
| WHO_AM_I地址 | 0x75 | **0x72** |
| WHO_AM_I值 | 0x61 | **0x84** |
| SOFTRESET地址 | 0x02 | **0x7F** |
| 数据起始地址 | 0x09 | **0x00** |
| 数据顺序 | 温度在前 | **加速度计在前** |

### 需要修改的代码

1. **替换结构体定义**: 将 `g_Reg_icm42607` 替换为 `g_Reg_icm45606`
2. **更新设备识别**: WHO_AM_I地址从 0x75 改为 0x72，ID从 0x61 改为 0x84
3. **更新数据解析**: 温度数据在最后，需要调整解析顺序
4. **移除无效配置**: 删除对地址 0x51/0x52/0x53 的写入

---

## 13. 关键宏定义

| 宏定义 | 值 | 描述 |
|-------|-----|-----|
| `GYRO_FS` | 500 | 陀螺仪量程 [dps] |
| `IMU_UPDATE_FREQ` | 200 | 更新频率 [Hz] |
| `M_M2PI` | 6283.307179f | 2π×1000 |
| `DEG_RAD(_a)` | `(_a) * M_M2PI / 360` | 角度转毫弧度 |

---

*文档生成日期: 2026-07-22*
*更新日期: 2026-07-22 (修正ICM-45606配置)*
