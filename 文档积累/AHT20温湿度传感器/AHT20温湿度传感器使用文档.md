## 1、需求

实现 AHT20 温湿度传感器读取温湿度，并提供接口给外部使用。

## 2、函数说明

| 函数                                                      | 作用               | 说明                                                      |
| --------------------------------------------------------- | ------------------ | --------------------------------------------------------- |
| `bool AHT20_Init(const AHT20_HAL_t *hal)`                 | 初始化驱动与传感器 | 传入 HAL，完成上电等待、就绪检查、必要校准                |
| `bool AHT20_Init_Default(void)`                           | 使用默认端口初始化 | 内部调用 `AHT20_Port_GetDefaultHAL()` 再调用 `AHT20_Init` |
| `const AHT20_HAL_t *AHT20_GetDefaultHAL(void)`            | 获取默认 HAL       | 返回默认平台适配层的 HAL 指针                             |
| `bool AHT20_BeginMeasurementNonBlocking(void)`            | 触发一次非阻塞测量 | 发送 `0xAC 0x33 0x00`，状态转为 WAITING                   |
| `void AHT20_Process(void)`                                | 推进状态机         | 主循环周期调用，用于判断忙位、超时、就绪                  |
| `bool AHT20_IsDataReady(void)`                            | 判断数据是否就绪   | `true` 表示可以执行读取                                   |
| `bool AHT20_TryRead(float *temperature, float *humidity)` | 读取一次测量结果   | 成功后状态回到 IDLE，失败写入错误码                       |
| `AHT20_RunState_t AHT20_GetRunState(void)`                | 获取当前运行状态   | 用于业务层调度                                            |
| `AHT20_Error_t AHT20_GetLastError(void)`                  | 获取最近错误码     | 用于日志和重试策略                                        |

## 3、移植说明

### 3.1 最小移植文件

1. 核心驱动：`AHT20.c`、`AHT20.h`。
2. 默认端口（本工程）：`AHT20_port_n32g430.c`。

若需要移植到别的mcu上，只需要在`AHT20_port_n32g430.c`对**板极初始化**和**I2C相关读写及延时**进行更改就行。

如：

```
static bool DEF_AHT20_I2C_Write(uint8_t addr, const uint8_t* data, uint32_t len)
{
    if (data == NULL || len == 0U || len > 255U)
    {
        return false;
    }

    return (Bsp_I2c_Write_Byte(BSP_I2C1, addr, (uint8_t*)data, (uint8_t)len) == 0);
}
```

只需实现新mcu的bsp层I2C写即可，上层不用动。（这里用的是主板的bsp相关）

### 3.2 HAL 必需接口

`AHT20_HAL_t` 必须实现以下函数：

| 函数指针      | 说明                                            |
| ------------- | ----------------------------------------------- |
| `i2c_write`   | I2C 写操作，参数为 (8-bit 地址, 数据指针, 长度) |
| `i2c_read`    | I2C 读操作，参数为 (8-bit 地址, 数据指针, 长度) |
| `delay_ms`    | 毫秒级阻塞延时                                  |
| `get_tick_ms` | 返回单调递增的毫秒时基，需可高频调用            |

### 3.3 默认端口说明

| 项目     | 配置                                          |
| -------- | --------------------------------------------- |
| 文件     | `AHT20_port_n32g430.c`                        |
| MCU      | N32G430                                       |
| I2C 外设 | I2C1                                          |
| SCL 引脚 | PB8                                           |
| SDA 引脚 | PB9                                           |
| GPIO AF  | AF5                                           |
| I2C 速率 | 100 kHz                                       |
| 时基实现 | DWT 周期计数器（基于 `SystemClockFrequency`） |

`AHT20_GetDefaultHAL()` 与 `AHT20_Init_Default()` 依赖 `AHT20_port_n32g430.c` 被编译进工程。

### 3.4 关键配置宏

可在 `AHT20.h` 中或通过编译参数 `-D` 覆盖：

| 宏                       | 默认值 | 说明                                            |
| ------------------------ | ------ | ----------------------------------------------- |
| `AHT20_I2C_ADDRESS`      | `0x70` | 8-bit 写地址，对应 7-bit 地址 `0x38`            |
| `AHT20_INIT_TIMEOUT_MS`  | `100`  | 初始化阶段等待就绪超时 (ms)                     |
| `AHT20_MEAS_DELAY_MS`    | `80`   | 发送测量命令后最小等待 (ms)，规格书建议 >= 80ms |
| `AHT20_MEAS_TIMEOUT_MS`  | `200`  | 测量阶段最大等待超时 (ms)                       |
| `AHT20_STARTUP_DELAY_MS` | `10`   | 上电后初始化前延时 (ms)                         |
| `AHT20_USE_CRC`          | `1`    | 是否启用 CRC（0=读 6 字节，1=读 7 字节含 CRC）  |

## 4、接口调用

### 4.1 调用流程

1. 上电后初始化串口日志。
2. 通过 `AHT20_GetDefaultHAL()` 获取 HAL。
3. 调用 `AHT20_Init(hal)` 完成传感器初始化。
4. 主循环内按"触发 -> 处理 -> 读取"顺序调用：
   - `AHT20_BeginMeasurementNonBlocking()`
   - `AHT20_Process()`
   - `AHT20_IsDataReady()` + `AHT20_TryRead()`
5. 成功后按 1000ms 周期采样，失败后按 200ms 退避重试。

### 4.2 典型调用代码（带错误处理）

```
int main(void)
{
    const AHT20_HAL_t* hal;
    float temperature = 0.0f;
    float humidity    = 0.0f;
    uint32_t next_tick;

    uart_init();
    printf("I2C Master + AHT20 demo\r\n");

    hal = AHT20_GetDefaultHAL();
    if (!AHT20_Init(hal))
    {
        printf("AHT20 init failed!\r\n");
        while (1)
        {
        }
    }
    printf("AHT20 init ok\r\n");

    next_tick = hal->get_tick_ms();

    while (1)
    {
        uint32_t now = hal->get_tick_ms();

        if (AHT20_GetRunState() == AHT20_RUN_IDLE && (int32_t)(now - next_tick) >= 0)
        {
            if (!AHT20_BeginMeasurementNonBlocking())
            {
                next_tick = now + 200;
            }
        }

        AHT20_Process();

        if (AHT20_IsDataReady())
        {
            if (AHT20_TryRead(&temperature, &humidity))
            {
                printf("T=%.2fC  H=%.2f%%\r\n", temperature, humidity);
                next_tick = now + 1000;
            }
            else
            {
                next_tick = now + 200;
            }
        }
    }
}
```

## 5、代码现象

隔一定时间打印温湿度信息，格式：

```
T=26.41C  H=56.57%
T=26.42C  H=56.58%
T=26.43C  H=56.66%
T=26.44C  H=56.66%
T=26.44C  H=56.65%
T=26.42C  H=56.63%
T=26.46C  H=56.67%
T=26.42C  H=56.53%
T=26.45C  H=56.68%
```

**注意**：AHT20 温度变化较慢，若上次测量环境中温湿度与现在差距过大，需要等待一段时间才能准确显示当前温湿度状态。

串口打印图片：

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde596ad5c8c4aa3968dc38e5b6541a4433e75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602afc228fb22ff2c4af41f0b37d82aa9bb1cdca418c034ab118d44114cab4a8d13f107c780c41d1e8646c868297b0b30717?tmpCode=2de8fdc8-7031-4bb2-816f-f3cfb6490215)

## 6、常见问题

1. **初始化失败**：检查供电、上拉电阻、I2C 地址是否正确、GPIO AF 映射是否匹配。
2. **频繁超时**：检查 `get_tick_ms` 是否单调递增、I2C 总线是否被占用。
3. **CRC 错误**：确认 `AHT20_USE_CRC` 配置与传感器实际输出一致。



## **7、时序图**

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde596ad5c8c4aa3968dc38e5b6541a4433e75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602aa3ba6b64951bcf7e14e47da32e6b36d8ea8c9ac8d9803b818ab0d99ec0d0ee29d69b8e1c79892206b27aae48d1632957?tmpCode=2de8fdc8-7031-4bb2-816f-f3cfb6490215)



