# MGS红外接收代码

一、前言描述

红外接收主要是检测接收管脚的高低电平时长，根据时长解码。

本文件主要以充电桩检测治具代码讲解，

代码处理方案：普通接收IO，在20us的定时器中断内做轮询检测电平时长为例子。

接收数量：目前MGS充电桩检测治具能够支持100个接收头同时检测（单片机管脚限制），实际使用有48个接收头检测。

二、充电桩检测治具相关代码

1、核心代码文件

[请至钉钉文档查看附件《mod\_ir.h》。](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK32EY3pIQENL6jqJkb4Mw9r?doc_type=wiki_doc&iframeQuery=anchorId%3DX02mjqy9gg2aprmlejoiy)

[请至钉钉文档查看附件《mod\_ir.c》。](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK32EY3pIQENL6jqJkb4Mw9r?doc_type=wiki_doc&iframeQuery=anchorId%3DX02mjqy9ghujb895n0zci8)

2、治具代码git仓库

仓库地址：git@ls.ldrobot.com:mgs\_base/charge\_jig.git

链接：[http://ls.ldrobot.com/mgs\_base/charge\_jig](http://ls.ldrobot.com/mgs_base/charge_jig)

3、代码块

```c
/**
 * @file mod_ir.c
 * @author 陈权 (cq@ldrobot.com)
 * @brief  ModBus红外模块相关功能实现
 * @version 0.1
 * @date 2025-11-03
 * @copyright Copyright (c) {2021} 深圳乐动机器人版权所有
 */

#include "mod_ir.h"

#include <stdlib.h>

void ModIr_GpioData_Update(ModIr_DataType *ir_data, uint16_t gpio_num, uint64_t now_time_10us);
void ModIr_Decode(ModIr_DataType *ir_data, uint16_t gpio_num, uint32_t now_time_ms);
void ModIr_RecvDataUpdate(ModIr_DataType *ir_data, uint16_t gpio_num, uint32_t now_time_ms);

#define DATA_AMOUNT        8     /*编码的波形周期总个数*/
#define OVER_CLEAR_TIME_MS 600   // 红外超时时间
/**
 * @brief  时间更新错误标志
 * @note   当传入的时间戳与系统时间偏差过大时置1，表示时间同步异常
 */
uint8_t time_update_err_flag = 1;

/**
 * @brief  红外GPIO状态数组
 * @note   包含N个红外输入通道的状态信息，每个通道对应一个读取函数
 */
ModIr_DataType ModIr_GpioData[] = {{Read_X1},  {Read_X2},  {Read_X3},  {Read_X4},  {Read_X5},    //
                                   {Read_X6},  {Read_X7},  {Read_X8},  {Read_X9},  {Read_X10},   //
                                   {Read_X11}, {Read_X12}, {Read_X13}, {Read_X14}, {Read_X15},   //
                                   {Read_X16}, {Read_X17}, {Read_X18}, {Read_X19}, {Read_X20},   //
                                   {Read_X21}, {Read_X22}, {Read_X23}, {Read_X24}, {Read_X25},   //
                                   {Read_X26}, {Read_X27}, {Read_X28}, {Read_X29}, {Read_X30},   //
                                   {Read_X31}, {Read_X32}, {Read_X33}, {Read_X34}, {Read_X35},   //
                                   {Read_X36}, {Read_X37}, {Read_X38}, {Read_X39}, {Read_X40},   //
                                   {Read_X41}, {Read_X42}, {Read_X43}, {Read_X44}, {Read_X45},   //
                                   {Read_X46}, {Read_X47}, {Read_X48}, {Read_X49}, {Read_X50},   //
                                   {Read_X51}, {Read_X52}, {Read_X53}, {Read_X54}, {Read_X55},   //
                                   {Read_X56}, {Read_X57}, {Read_X58}, {Read_X59}, {Read_X60}, {NULL}};

/**
 * @brief  红外数据处理主更新函数
 * @param  now_time_10us - 当前时间，单位为10微秒
 * @retval 无
 * @note   此函数是红外数据处理的核心入口，负责协调整个数据处理流程
 *         函数依次执行时间验证、GPIO状态更新、数据解码和接收数据更新
 */
void ModIr_DataUpdate(uint64_t now_time_10us) {
    uint16_t gpio_num = 0;
    // 验证时间戳的有效性：检查传入时间与系统时间的偏差是否超过5000ms
    // HAL_GetTick()返回的是毫秒级时间戳，now_time_10us/100将10微秒转换为毫秒
    if (abs(HAL_GetTick() - ((now_time_10us / 100) % 0xffffffff)) > 5000) {
        time_update_err_flag = 1;   // 时间偏差过大，设置错误标志
    } else {
        time_update_err_flag = 0;   // 时间正常，清除错误标志
    }
    // 计算GPIO通道数量：通过数组总大小除以单个元素大小
    gpio_num = sizeof(ModIr_GpioData) / sizeof(ModIr_DataType);
    // 1. 更新所有GPIO通道的状态数据
    ModIr_GpioData_Update(ModIr_GpioData, gpio_num, now_time_10us);
    // 2. 对更新后的GPIO数据进行红外信号解码
    ModIr_Decode(ModIr_GpioData, gpio_num, HAL_GetTick());
    // 3. 更新接收数据，处理超时情况
    ModIr_RecvDataUpdate(ModIr_GpioData, gpio_num, HAL_GetTick());
}

/**
 * @brief  获取指定GPIO索引的红外接收数据
 * @param  gpio_idx - GPIO索引，用于指定要获取数据的红外通道
 * @retval unsigned char - 红外接收数据输出值
 * @note   此函数提供了一个安全的接口，用于读取解码后的红外数据
 *         函数首先检查索引的有效性，避免数组越界访问
 */
unsigned char GetModIr_RecvData(uint16_t gpio_idx) {
    // 索引有效性检查：确保索引不超过ModIr_GpioData数组的最大有效范围
    if (gpio_idx >= sizeof(ModIr_GpioData) / sizeof(ModIr_DataType) - 1) {
        return 0;   // 索引无效，返回默认值0
    }

    // 返回指定索引的解码后红外接收数据
    return ModIr_GpioData[gpio_idx].sensor.recv_data_out;
}

/**
 * @brief  更新红外GPIO状态数据
 * @param  now_time_10us - 当前时间，单位为10微秒
 * @retval 无
 * @note   此函数用于定期更新所有红外输入通道的状态，并记录状态变化的时间信息
 *         函数首先验证时间戳的有效性，然后遍历所有红外通道，检测状态变化并更新相关参数
 */
void ModIr_GpioData_Update(ModIr_DataType *ir_data, uint16_t gpio_num, uint64_t now_time_10us) {
    if (gpio_num == 0) {
        return;
    }

    // 遍历所有红外通道
    for (size_t i = 0; i < gpio_num; i++) {
        // 检查是否有读取函数
        if (ir_data[i].read_func == NULL) {
            continue;   // 没有读取函数，跳过当前通道
        }
        // 读取当前GPIO状态
        ir_data[i].now_gpio_state = ir_data[i].read_func();

        // 检查状态是否发生变化
        if (ir_data[i].now_gpio_state != ir_data[i].last_gpio_state) {
            if (now_time_10us < ir_data[i].last_gpio_change_time_10us) {
                ir_data[i].last_gpio_change_time_10us = now_time_10us;
            }
            // 更新状态记录
            ir_data[i].last_gpio_state = ir_data[i].now_gpio_state;
            // 计算状态持续时间（微秒）
            ir_data[i].last_gpio_state_time_us = (now_time_10us - ir_data[i].last_gpio_change_time_10us) * 10;
            // 记录状态变化的时间戳
            ir_data[i].last_gpio_change_time_10us = now_time_10us;
            // 设置状态变化标志
            ir_data[i].gpio_change_flag = 1;
        }
    }
}

/**
 * @brief  单比特解码函数
 * @param  ir_data - 红外数据指针，包含需要解码的波形信息
 * @retval CodingTypeDef - 解码结果类型枚举值
 * @note   此函数用于根据高低电平时间判断单个数据位的编码类型
 *         函数通过分析高低电平脉宽的比例和总时间来确定是数据位0、数据位1还是结束位
 */
CodingTypeDef OneBitDecode(ModIr_DataType *ir_data) {
    // 参数检查：如果指针为空，返回错误
    if (ir_data == NULL) {
        return CODE_ERROR;
    }

    // 定义解码结果变量
    CodingTypeDef type;

    // 检查是否是最后一个数据位
    if (ir_data[0].sensor.bit_counter == DATA_AMOUNT - 1) {   // 接收最后一个bit
        // 根据低电平时间判断是结束位1还是结束位0
        type = (ir_data[0].sensor.low_level_time > INTERVAL_LONG_NIM) ? CODE_END1 : CODE_END0;
    } else {
        // 检查总时间是否超过正常范围（判断为错误）
        if ((ir_data[0].sensor.low_level_time + ir_data[0].sensor.high_level_time) >
            (INTERVAL_SHORT_MAX + INTERVAL_LONG_MAX)) {
            // bit总时间记录大于正常范围判定错误  700 + 2800(max:800+3000)
            type = CODE_ERROR;
        }
        // 检查总时间是否小于正常范围（判断为未接收完成）
        else if (ir_data[0].sensor.low_level_time + ir_data[0].sensor.high_level_time <
                 INTERVAL_SHORT_MIN + INTERVAL_LONG_NIM) {
            // bit总时间记录小于正常范围判定未接收完成  700 + 2800(min:600+2600)
            type = CODE_NULL;
        }
        // 根据高低电平时间比例判断是数据位1还是数据位0
        else {
            // 低电平时间长于高电平时间为数据位1，否则为数据位0
            type = (ir_data[0].sensor.low_level_time > ir_data[0].sensor.high_level_time) ? CODE_DATA1 : CODE_DATA0;
        }
    }

    // 返回解码结果
    return type;
}

/**
 * @brief  红外数据解码函数
 * @param  ir_data - 红外数据数组指针，包含所有通道的红外数据
 * @param  gpio_num - 红外通道数量
 * @param  now_time_ms - 当前时间，单位为毫秒
 * @retval 无
 * @note   此函数用于解码红外信号波形，识别数据位和结束位
 *         函数通过分析高低电平脉冲宽度来判断编码类型，并更新相应的数据位
 */
void ModIr_Decode(ModIr_DataType *ir_data, uint16_t gpio_num, uint32_t now_time_ms) {
    // 参数检查：如果通道数为0，直接返回
    if (gpio_num == 0) {
        return;
    }

    // 遍历所有红外通道
    for (size_t i = 0; i < gpio_num; i++) {
        // 检查是否有状态变化
        if (ir_data[i].gpio_change_flag == 0) {
            continue;   // 没有状态变化，跳过当前通道
        }

        // 清除状态变化标志
        ir_data[i].gpio_change_flag = 0;

        // 检测起始信号：如果不在解码状态，且当前为低电平，且上一个状态持续时间超过阈值
        if (!ir_data[i].sensor.is_in_decoding && ir_data[i].now_gpio_state == 0 &&
            ir_data[i].last_gpio_state_time_us > (INTERVAL_LONG_MAX + INTERVAL_SHORT_MAX)) {
            // 进入解码状态，初始化解码参数
            ir_data[i].sensor.is_in_decoding  = 1;
            ir_data[i].sensor.direction_byte  = 0;
            ir_data[i].sensor.bit_counter     = 0;
            ir_data[i].sensor.low_level_time  = 0;
            ir_data[i].sensor.high_level_time = 0;
            continue;
        }

        // 判断是否在解码状态中
        if (ir_data[i].sensor.is_in_decoding) {
            // 根据当前GPIO状态，累加相应的电平时间
            if (ir_data[i].now_gpio_state == 1) {
                // 上升沿，累加低电平脉宽时间
                ir_data[i].sensor.low_level_time += ir_data[i].last_gpio_state_time_us;
            } else {
                // 下降沿，累加高电平脉宽时间
                ir_data[i].sensor.high_level_time += ir_data[i].last_gpio_state_time_us;
            }

            // 根据解码结果进行相应处理
            switch (OneBitDecode(&ir_data[i])) {
            case CODE_ERROR:   // 解码错误
                // 特殊情况处理：如果低电平时间很短而高电平时间很长，可能是新的起始信号
                if ((ir_data[i].sensor.low_level_time < INTERVAL_SHORT_MIN) &&
                            (ir_data[i].sensor.high_level_time > INTERVAL_LONG_MAX)) {
                    // 重新进入解码状态，初始化参数
                    ir_data[i].sensor.is_in_decoding  = 1;
                    ir_data[i].sensor.direction_byte  = 0;
                    ir_data[i].sensor.bit_counter     = 0;
                    ir_data[i].sensor.low_level_time  = 0;
                    ir_data[i].sensor.high_level_time = 0;
                } else {
                    // 其他错误情况，退出解码状态
                    ir_data[i].sensor.is_in_decoding = 0;
                }
                break;
            case CODE_DATA0:   // 解码为数据位0
                // 增加位计数，重置电平时间计数器
                ir_data[i].sensor.bit_counter++;
                ir_data[i].sensor.low_level_time  = 0;
                ir_data[i].sensor.high_level_time = 0;
                break;
            case CODE_DATA1:   // 解码为数据位1
                // 增加位计数，设置对应的数据位，重置电平时间计数器
                ir_data[i].sensor.bit_counter++;
                ir_data[i].sensor.direction_byte |= 1 << (DATA_AMOUNT - ir_data[i].sensor.bit_counter);
                ir_data[i].sensor.low_level_time  = 0;
                ir_data[i].sensor.high_level_time = 0;
                // 记录该字节的时间戳
                ir_data[i].sensor.last_byte_time_ms[DATA_AMOUNT - ir_data[i].sensor.bit_counter] = now_time_ms;
                break;
            case CODE_END0:   // 解码为结束位0
                // 更新方向数据，退出解码状态，记录成功时间和数据计数
                ir_data[i].sensor.direction_data |= ir_data[i].sensor.direction_byte;
                ir_data[i].sensor.is_in_decoding       = 0;
                ir_data[i].sensor.last_succeed_time_ms = now_time_ms;
                ir_data[i].sensor.data_count++;
                break;
            case CODE_END1:   // 解码为结束位1
                // 增加位计数，设置对应的数据位，更新方向数据，退出解码状态，记录时间和计数
                ir_data[i].sensor.bit_counter++;
                ir_data[i].sensor.direction_byte |= 1 << (DATA_AMOUNT - ir_data[i].sensor.bit_counter);
                ir_data[i].sensor.direction_data |= ir_data[i].sensor.direction_byte;
                ir_data[i].sensor.is_in_decoding       = 0;
                ir_data[i].sensor.last_succeed_time_ms = now_time_ms;
                ir_data[i].sensor.data_count++;
                ir_data[i].sensor.last_byte_time_ms[DATA_AMOUNT - ir_data[i].sensor.bit_counter] = now_time_ms;
                break;
            case CODE_NULL:   // 未完成解码
                // 无需处理，继续等待
                break;
            default:   // 其他情况
                // 无需处理
                break;
            }
        }
    }
}

/**
 * @brief  更新红外接收数据
 * @param  ir_data - 红外数据数组指针，包含所有通道的红外数据
 * @param  gpio_num - 红外通道数量
 * @param  now_time_ms - 当前时间，单位为毫秒
 * @retval 无
 * @note   此函数用于处理红外解码数据的超时清除逻辑，并更新输出数据
 *         函数会检查每个通道的数据是否超时，如果超时则清除相应的数据位
 */
void ModIr_RecvDataUpdate(ModIr_DataType *ir_data, uint16_t gpio_num, uint32_t now_time_ms) {
    // 解码超时，清空上报数据
    for (size_t idx = 0; idx < gpio_num; idx++) {
        // 检查整体解码是否超时
        if ((now_time_ms - ir_data[idx].sensor.last_succeed_time_ms) > OVER_CLEAR_TIME_MS) {
            // 整体超时，清空所有方向数据
            ir_data[idx].sensor.direction_data = 0;
        } else {
            // 整体未超时，检查每个字节是否超时
            for (size_t i = 0; i < DATA_AMOUNT; i++) {
                // 检查第i个数据位是否超时
                if ((now_time_ms - ir_data[idx].sensor.last_byte_time_ms[i]) > OVER_CLEAR_TIME_MS) {
                    // 清除对应的位（将该位设为0）
                    ir_data[idx].sensor.direction_data &= ~(1 << i);
                }
            }
        }
        // 更新输出数据为当前处理后的方向数据
        ir_data[idx].sensor.recv_data_out = ir_data[idx].sensor.direction_data;
    }
}
```

核心代码块：

```c
/**
 * @brief  红外数据解码函数
 * @param  ir_data - 红外数据数组指针，包含所有通道的红外数据
 * @param  gpio_num - 红外通道数量
 * @param  now_time_ms - 当前时间，单位为毫秒
 * @retval 无
 * @note   此函数用于解码红外信号波形，识别数据位和结束位
 *         函数通过分析高低电平脉冲宽度来判断编码类型，并更新相应的数据位
 */
void ModIr_Decode(ModIr_DataType *ir_data, uint16_t gpio_num, uint32_t now_time_ms) {
    // 参数检查：如果通道数为0，直接返回
    if (gpio_num == 0) {
        return;
    }

    // 遍历所有红外通道
    for (size_t i = 0; i < gpio_num; i++) {
        // 检查是否有状态变化
        if (ir_data[i].gpio_change_flag == 0) {
            continue;   // 没有状态变化，跳过当前通道
        }

        // 清除状态变化标志
        ir_data[i].gpio_change_flag = 0;

        // 检测起始信号：如果不在解码状态，且当前为低电平，且上一个状态持续时间超过阈值
        if (!ir_data[i].sensor.is_in_decoding && ir_data[i].now_gpio_state == 0 &&
            ir_data[i].last_gpio_state_time_us > (INTERVAL_LONG_MAX + INTERVAL_SHORT_MAX)) {
            // 进入解码状态，初始化解码参数
            ir_data[i].sensor.is_in_decoding  = 1;
            ir_data[i].sensor.direction_byte  = 0;
            ir_data[i].sensor.bit_counter     = 0;
            ir_data[i].sensor.low_level_time  = 0;
            ir_data[i].sensor.high_level_time = 0;
            continue;
        }

        // 判断是否在解码状态中
        if (ir_data[i].sensor.is_in_decoding) {
            // 根据当前GPIO状态，累加相应的电平时间
            if (ir_data[i].now_gpio_state == 1) {
                // 上升沿，累加低电平脉宽时间
                ir_data[i].sensor.low_level_time += ir_data[i].last_gpio_state_time_us;
            } else {
                // 下降沿，累加高电平脉宽时间
                ir_data[i].sensor.high_level_time += ir_data[i].last_gpio_state_time_us;
            }

            // 根据解码结果进行相应处理
            switch (OneBitDecode(&ir_data[i])) {
            case CODE_ERROR:   // 解码错误
                // 特殊情况处理：如果低电平时间很短而高电平时间很长，可能是新的起始信号
                if ((ir_data[i].sensor.low_level_time < INTERVAL_SHORT_MIN) &&
                            (ir_data[i].sensor.high_level_time > INTERVAL_LONG_MAX)) {
                    // 重新进入解码状态，初始化参数
                    ir_data[i].sensor.is_in_decoding  = 1;
                    ir_data[i].sensor.direction_byte  = 0;
                    ir_data[i].sensor.bit_counter     = 0;
                    ir_data[i].sensor.low_level_time  = 0;
                    ir_data[i].sensor.high_level_time = 0;
                } else {
                    // 其他错误情况，退出解码状态
                    ir_data[i].sensor.is_in_decoding = 0;
                }
                break;
            case CODE_DATA0:   // 解码为数据位0
                // 增加位计数，重置电平时间计数器
                ir_data[i].sensor.bit_counter++;
                ir_data[i].sensor.low_level_time  = 0;
                ir_data[i].sensor.high_level_time = 0;
                break;
            case CODE_DATA1:   // 解码为数据位1
                // 增加位计数，设置对应的数据位，重置电平时间计数器
                ir_data[i].sensor.bit_counter++;
                ir_data[i].sensor.direction_byte |= 1 << (DATA_AMOUNT - ir_data[i].sensor.bit_counter);
                ir_data[i].sensor.low_level_time  = 0;
                ir_data[i].sensor.high_level_time = 0;
                // 记录该字节的时间戳
                ir_data[i].sensor.last_byte_time_ms[DATA_AMOUNT - ir_data[i].sensor.bit_counter] = now_time_ms;
                break;
            case CODE_END0:   // 解码为结束位0
                // 更新方向数据，退出解码状态，记录成功时间和数据计数
                ir_data[i].sensor.direction_data |= ir_data[i].sensor.direction_byte;
                ir_data[i].sensor.is_in_decoding       = 0;
                ir_data[i].sensor.last_succeed_time_ms = now_time_ms;
                ir_data[i].sensor.data_count++;
                break;
            case CODE_END1:   // 解码为结束位1
                // 增加位计数，设置对应的数据位，更新方向数据，退出解码状态，记录时间和计数
                ir_data[i].sensor.bit_counter++;
                ir_data[i].sensor.direction_byte |= 1 << (DATA_AMOUNT - ir_data[i].sensor.bit_counter);
                ir_data[i].sensor.direction_data |= ir_data[i].sensor.direction_byte;
                ir_data[i].sensor.is_in_decoding       = 0;
                ir_data[i].sensor.last_succeed_time_ms = now_time_ms;
                ir_data[i].sensor.data_count++;
                ir_data[i].sensor.last_byte_time_ms[DATA_AMOUNT - ir_data[i].sensor.bit_counter] = now_time_ms;
                break;
            case CODE_NULL:   // 未完成解码
                // 无需处理，继续等待
                break;
            default:   // 其他情况
                // 无需处理
                break;
            }
        }
    }
}
```