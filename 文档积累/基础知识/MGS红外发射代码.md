# MGS红外发射代码

```c
/**
 * @file mod_led.c
 * @author 陈权 (cq@ldrobot.com)
 * @brief 
 * @version 0.1
 * @date 2025-12-29
 * @copyright Copyright (c) {2021} 深圳乐动机器人版权所有
 */
#include "mod_include.h"
#include "app_main.h"

#if PRODUCT_TYPE == MGS_ALL
#define IR_FL_FAR_L  TIM_Compare2_Set(TIM4, 0)
#define IR_FL_FAR_H  TIM_Compare2_Set(TIM4, 2)
#define IR_FL_NEAR_L TIM_Compare1_Set(TIM2, 0)
#define IR_FL_NEAR_H TIM_Compare1_Set(TIM2, 2)

#define IR_FR_FAR_L  TIM_Compare2_Set(TIM2, 0)
#define IR_FR_FAR_H  TIM_Compare2_Set(TIM2, 2)
#define IR_FR_NEAR_L TIM_Compare1_Set(TIM3, 0)
#define IR_FR_NEAR_H TIM_Compare1_Set(TIM3, 2)

#define IR_R_FAR_L  TIM_Compare2_Set(TIM5, 0)
#define IR_R_FAR_H  TIM_Compare2_Set(TIM5, 2)
#define IR_R_NEAR_L TIM_Compare3_Set(TIM1, 0)
#define IR_R_NEAR_H TIM_Compare3_Set(TIM1, 2)

#define IR_L_FAR_L  TIM_Compare1_Set(TIM4, 0)
#define IR_L_FAR_H  TIM_Compare1_Set(TIM4, 2)
#define IR_L_NEAR_L TIM_Compare1_Set(TIM1, 0)
#define IR_L_NEAR_H TIM_Compare1_Set(TIM1, 2)

#define IR_L_NEAR_DATA  0x80
#define IR_FL_NEAR_DATA 0x40
#define IR_FR_NEAR_DATA 0x20
#define IR_R_NEAR_DATA  0x10

#define IR_L_FAR_DATA  0x08
#define IR_FL_FAR_DATA 0x04
#define IR_FR_FAR_DATA 0x02
#define IR_R_FAR_DATA  0x01

//factory gpio 控制
#define FACTORY_IR_FL_FAR_H  TIM_Compare2_Set(TIM4, 0)
#define FACTORY_IR_FL_NEAR_H TIM_Compare1_Set(TIM2, 0)
#define FACTORY_IR_FR_FAR_H  TIM_Compare2_Set(TIM2, 0)
#define FACTORY_IR_FR_NEAR_H TIM_Compare1_Set(TIM3, 0)
#define FACTORY_IR_R_FAR_H  TIM_Compare2_Set(TIM5, 0)
#define FACTORY_IR_R_NEAR_H TIM_Compare3_Set(TIM1, 0)
#define FACTORY_IR_L_FAR_H  TIM_Compare1_Set(TIM4, 0)
#define FACTORY_IR_L_NEAR_H TIM_Compare1_Set(TIM1, 0)

#define FACTORY_IR_FL_FAR_L  TIM_Compare2_Set(TIM4, 4)
#define FACTORY_IR_FL_NEAR_L TIM_Compare1_Set(TIM2, 4)
#define FACTORY_IR_FR_FAR_L  TIM_Compare2_Set(TIM2, 4)
#define FACTORY_IR_FR_NEAR_L TIM_Compare1_Set(TIM3, 4)
#define FACTORY_IR_R_FAR_L  TIM_Compare2_Set(TIM5, 4)
#define FACTORY_IR_R_NEAR_L TIM_Compare3_Set(TIM1, 4)
#define FACTORY_IR_L_FAR_L  TIM_Compare1_Set(TIM4, 4)
#define FACTORY_IR_L_NEAR_L TIM_Compare1_Set(TIM1, 4)

#endif

#if PRODUCT_TYPE == MGV01
#define IR_FL_FAR_L  TIM_Compare2_Set(TIM4, 0)
#define IR_FL_FAR_H  TIM_Compare2_Set(TIM4, 2)
#define IR_FL_NEAR_L TIM_Compare1_Set(TIM2, 0)
#define IR_FL_NEAR_H TIM_Compare1_Set(TIM2, 2)

#define IR_FR_FAR_L  TIM_Compare2_Set(TIM2, 0)
#define IR_FR_FAR_H  TIM_Compare2_Set(TIM2, 2)
#define IR_FR_NEAR_L TIM_Compare1_Set(TIM3, 0)
#define IR_FR_NEAR_H TIM_Compare1_Set(TIM3, 2)

#define IR_R_FAR_L  (NULL)
#define IR_R_FAR_H  (NULL)
#define IR_R_NEAR_L (NULL)
#define IR_R_NEAR_H (NULL)

#define IR_L_FAR_L  (NULL)
#define IR_L_FAR_H  (NULL)
#define IR_L_NEAR_L (NULL)
#define IR_L_NEAR_H (NULL)

#define IR_L_NEAR_DATA  0x00
#define IR_FL_NEAR_DATA 0x04
#define IR_FR_NEAR_DATA 0x02
#define IR_R_NEAR_DATA  0x00

#define IR_L_FAR_DATA  0x00
#define IR_FL_FAR_DATA 0x10
#define IR_FR_FAR_DATA 0x08
#define IR_R_FAR_DATA  0x00

#endif


void Signaling_TimeDivisionTransmission(void);
void Signaling_Transmission_AllOff(void);
void Signaling_Transmission_Open(uint8_t data);
void Signaling_Transmission_Off(uint32_t time);
void Signaling_Transmission(uint8_t data,uint32_t time);

void Signaling_FactoryTimeDivisionTransmission(void);
void Signaling_Factory_Transmission_Off(uint32_t time);
void Signaling_FactoryGpioCtl(void);

// extern ModBoardChargeBaseVerInfoFb baseinfodt;
/**
 * @brief 定义红外信号分时发送状态的枚举类型
 * @details 该枚举类型用于表示红外信号分时发送的不同状态，包括发送不同组数据的状态以及最大状态标识。
 */
typedef enum {
    ONE_TRANSMISSION = 0x00,   // 发送第一组数据，即左(L)、左中(FL)、右中(FR)、右(R)的近位信号数据
    TWO_TRANSMISSION,          // 发送第二组数据，即左(L)、左中(FL)、右中(FR)、右(R)的远位信号数据
    THREE_TRANSMISSION,        // 发送第三组数据，此阶段不发送数据，用于等待远强光发射后接收近弱光
    MAX_STATE,                 // 最大状态标识，用于状态异常时的重置判断
} TimeDivision_State;          // Time - division Transmission // 分时发送状态枚举类型

#define BIT_TIME      5                     // 1bit的时间周期:5* 0.7ms,(谨慎修改，只能取4或者5，改了之后，接收代码要改)
#define DATA_TIME     (BIT_TIME * 8 + 40)   // 发送8bit的时间加等待时间
#define NEAR_FAR_TIME (MAX_STATE + 2) * DATA_TIME   // 所有分时发送的全周期时间

static uint32_t count = 0;

static uint8_t powerstart = 1;  // 启动为1

static uint32_t sendcount = 0;  // 上电为0

int infrared_send_byte(uint8_t byte1, uint8_t device, uint8_t time_count);
void TIM6_IRQHandler(void) {
    // static uint8_t flag_t = 0;
    if (TIM_Interrupt_Status_Get(TIM6, TIM_INT_UPDATE) != RESET) {
        TIM_Interrupt_Status_Clear(TIM6, TIM_INT_UPDATE);
        // 红外信号分时发送状态机函数
        if (ModGlobalData_CommSocData().factory_board_Ctl.factory_flag == 0) {
            if (ModGlobalData_CommSocAddr()->baseinfodt.ir_mode > 0 && ModGlobalData_CommSocAddr()->baseinfodt.ir_mode <= 4) {
                Signaling_FactoryTimeDivisionTransmission();
            } else {
                Signaling_TimeDivisionTransmission();
            }
        }

        count++;
        if (count >= NEAR_FAR_TIME) {
            count = 0;
        }
        // }
    }
}

void Signaling_FactoryGpioCtl(void) {
    ModGlobalData_CommSocType *comm_soc = ModGlobalData_CommSocAddr();
    if (comm_soc->factory_board_Ctl.factory_flag) {
        if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_en) {
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_L_NEAR_DATA) {
                FACTORY_IR_L_NEAR_H;
            } else {
                FACTORY_IR_L_NEAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_FL_NEAR_DATA) {
                FACTORY_IR_FL_NEAR_H;
            } else {
                FACTORY_IR_FL_NEAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_FR_NEAR_DATA) {
                FACTORY_IR_FR_NEAR_H;
            } else {
                FACTORY_IR_FR_NEAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_R_NEAR_DATA) {
                FACTORY_IR_R_NEAR_H;
            } else {
                FACTORY_IR_R_NEAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_L_FAR_DATA) {
                FACTORY_IR_L_FAR_H;
            } else {
                FACTORY_IR_L_FAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_FL_FAR_DATA) {
                FACTORY_IR_FL_FAR_H;
            } else {
                FACTORY_IR_FL_FAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_FR_FAR_DATA) {
                FACTORY_IR_FR_FAR_H;
            } else {
                FACTORY_IR_FR_FAR_L;
            }
            if (comm_soc->factory_board_Ctl.ir_gpio_ctl.gpio_state & IR_R_FAR_DATA) {
                FACTORY_IR_R_FAR_H;
            } else {
                FACTORY_IR_R_FAR_L;
            }
        }
    }
}

/**
 * @brief 当前的红外信号分时发送状态
 * @details 静态变量，用于记录当前红外信号分时发送所处的状态，初始化为发送第一组数据的状态。
 */
static TimeDivision_State time_division_state = ONE_TRANSMISSION;

/**
 * @brief 红外信号分时发送状态机
 * @details 根据计数器 `count` 的值，切换不同的红外信号发送状态，实现分时发送功能。
 * @param 无
 * @return 无
 */
void Signaling_TimeDivisionTransmission(void) {
    // 用于存储要发送的红外信号数据
    uint8_t send_data = 0;

    // 根据当前的分时发送状态，执行不同的操作
    switch (time_division_state) {
    case ONE_TRANSMISSION:
		// 组合左(L)、左中(FL)、右中(FR)、右(R)的近位信号数据
        send_data = IR_L_NEAR_DATA | IR_FL_NEAR_DATA | IR_FR_NEAR_DATA | IR_R_NEAR_DATA;
        // 调用发送函数发送组合后的近位信号数据
        Signaling_Transmission(send_data, count);
        // 当计数器值大于等于50（DATA_TIME）时，切换
        if (count >= DATA_TIME) {
            time_division_state = TWO_TRANSMISSION;
        }
        break;
    case TWO_TRANSMISSION:
		// 组合左(L)、左中(FL)、右中(FR)、右(R)的远位信号数据
        send_data = IR_L_FAR_DATA | IR_FL_FAR_DATA | IR_FR_FAR_DATA | IR_R_FAR_DATA;
        // 调用发送函数发送组合后的远位信号数据
        Signaling_Transmission(send_data, count);
        if (count >= 2 * DATA_TIME) {
            time_division_state = THREE_TRANSMISSION;
        }
        break;
    case THREE_TRANSMISSION:
        // 当计数器值大于等于150（3 * DATA_TIME）或者小于50（DATA_TIME）时，切换到发送远位信号的状态
        if (count >= NEAR_FAR_TIME || count <= DATA_TIME) {
            time_division_state = ONE_TRANSMISSION;
        }
        break;
    case MAX_STATE:
        // 若状态为 MAX_STATE，重置为发送远位信号的状态
        time_division_state = ONE_TRANSMISSION;
        break;
    default:
        // 若状态不在枚举范围内，重置为发送远位信号的状态
        time_division_state = ONE_TRANSMISSION;
        break;
    }
}

void Signaling_FactoryTimeDivisionTransmission(void) {
	uint8_t factory_mode = ModGlobalData_CommSocAddr()->baseinfodt.ir_mode;
	uint8_t send_data = 0;
    if (factory_mode == 1) {
        send_data = IR_FL_NEAR_DATA | IR_FR_NEAR_DATA;
    }else if (factory_mode == 2) {
        send_data = IR_L_NEAR_DATA | IR_R_NEAR_DATA;
    }else if (factory_mode == 3){
		send_data = IR_FL_FAR_DATA | IR_FR_FAR_DATA;
	}else if (factory_mode == 4){
		send_data = IR_L_FAR_DATA | IR_R_FAR_DATA;
	}else{
		send_data = 0;
	}
    // 调用发送函数发送组合后的工厂信号数据
    Signaling_Transmission(send_data, count);
}

/**
 * @brief 根据时间控制红外信号的发送与关闭
 * @param data 包含红外信号发送状态信息的字节数据
 * @param time 当前的时间计数
 * @details 根据时间 `time` 的不同取值，调用不同的函数来控制红外信号的发送与关闭。
 *          当 `time % 50` 大于等于 40 时，关闭所有红外信号；
 *          当 `time % 5` 等于 1 时，根据 `data` 打开相应的红外信号；
 *          当 `time % 5` 等于 2 时，根据时间关闭相应的红外信号；
 *          当 `time % 5` 等于 0 时，关闭所有红外信号。
 */
void Signaling_Transmission(uint8_t data, uint32_t time) {
    // 当 time 对 50 取余大于等于 40 时，关闭所有红外信号
    if ((time % DATA_TIME) >= 8 * BIT_TIME) {
        Signaling_Transmission_AllOff();
    } else {
        // 当 time 对 5 取余等于 1 时，根据 data 打开相应的红外信号
        if ((time % BIT_TIME) == 1) {
            Signaling_Transmission_Open(data);
        }
        // 当 time 对 5 取余等于 2 时，根据时间关闭相应的红外信号
        if ((time % BIT_TIME) == 2) {
            // 关掉低电平的发射
            if (ModGlobalData_CommSocAddr()->baseinfodt.ir_mode > 0 && ModGlobalData_CommSocAddr()->baseinfodt.ir_mode <= 4) {
                Signaling_Factory_Transmission_Off(time);
            } else {
                Signaling_Transmission_Off(time);
            }
        }
        // 当 time 对 5 取余等于 0 时，关闭所有红外信号
        if ((time % BIT_TIME) == 0) {
            // 关掉高电平的发射
            Signaling_Transmission_AllOff();
        }
    }
}

/**
 * @brief 关闭所有红外信号
 * @details 调用宏定义将所有红外信号设置为低电平，即关闭状态。
 */
void Signaling_Transmission_AllOff(void) {
    // 关闭左远位红外信号
    IR_L_FAR_L;
    // 关闭左近位红外信号
    IR_L_NEAR_L;
    // 关闭左中远位红外信号
    IR_FL_FAR_L;
    // 关闭左中近位红外信号
    IR_FL_NEAR_L;
    // 关闭右中远位红外信号
    IR_FR_FAR_L;
    // 关闭右中近位红外信号
    IR_FR_NEAR_L;
    // 关闭右远位红外信号
    IR_R_FAR_L;
    // 关闭右近位红外信号
    IR_R_NEAR_L;
}

/**
 * @brief 根据传入的数据打开相应的红外信号
 * @param data 包含红外信号发送状态信息的字节数据
 * @details 通过按位与操作判断 `data` 中各位是否为 1，若为 1 则打开相应的红外信号。
 */
void Signaling_Transmission_Open(uint8_t data) {
    // 若 data 包含左远位信号数据，则打开左远位红外信号
    if (data & IR_L_FAR_DATA) {
        IR_L_FAR_H;
    }
    // 若 data 包含左近位信号数据，则打开左近位红外信号
    if (data & IR_L_NEAR_DATA) {
        IR_L_NEAR_H;
    }
    // 若 data 包含左中远位信号数据，则打开左中远位红外信号
    if (data & IR_FL_FAR_DATA) {
        IR_FL_FAR_H;
    }
    // 若 data 包含左中近位信号数据，则打开左中近位红外信号
    if (data & IR_FL_NEAR_DATA) {
        IR_FL_NEAR_H;
    }
    // 若 data 包含右中远位信号数据，则打开右中远位红外信号
    if (data & IR_FR_FAR_DATA) {
        IR_FR_FAR_H;
    }
    // 若 data 包含右中近位信号数据，则打开右中近位红外信号
    if (data & IR_FR_NEAR_DATA) {
        IR_FR_NEAR_H;
    }
    // 若 data 包含右远位信号数据，则打开右远位红外信号
    if (data & IR_R_FAR_DATA) {
        IR_R_FAR_H;
    }
    // 若 data 包含右近位信号数据，则打开右近位红外信号
    if (data & IR_R_NEAR_DATA) {
        IR_R_NEAR_H;
    }
}

/**
 * @brief 根据时间关闭相应的红外信号
 * @param time 当前的时间计数
 * @details 根据 `time` 计算出 `time_data`，通过比较 `0x01 << time_data` 与各信号数据，
 *          若不相等则关闭相应的红外信号。
 */
void Signaling_Transmission_Off(uint32_t time) {
    uint8_t time_data = 0;
    // 计算时间数据，time 对 50 取余后除以 5
    time_data = (time % DATA_TIME) / BIT_TIME;

    // 让数据码取反发送
    if (time_data <= 7) {
        time_data = 7 - time_data;
    }

    // 若 0x01 << time_data 不等于左远位信号数据，则关闭左远位红外信号
    if ((0x01 << time_data) != IR_L_FAR_DATA) {
        IR_L_FAR_L;
    }
    // 若 0x01 << time_data 不等于左近位信号数据，则关闭左近位红外信号
    if ((0x01 << time_data) != IR_L_NEAR_DATA) {
        IR_L_NEAR_L;
    }
    // 若 0x01 << time_data 不等于左中远位信号数据，则关闭左中远位红外信号
    if ((0x01 << time_data) != IR_FL_FAR_DATA) {
        IR_FL_FAR_L;
    }
    // 若 0x01 << time_data 不等于左中近位信号数据，则关闭左中近位红外信号
    if ((0x01 << time_data) != IR_FL_NEAR_DATA) {
        IR_FL_NEAR_L;
    }
    // 若 0x01 << time_data 不等于右中近位信号数据，则关闭右中近位红外信号
    if ((0x01 << time_data) != IR_FR_NEAR_DATA) {
        IR_FR_NEAR_L;
    }
    // 若 0x01 << time_data 不等于右远位信号数据，则关闭右远位红外信号
    if ((0x01 << time_data) != IR_R_FAR_DATA) {
        IR_R_FAR_L;
    }
    // 若 0x01 << time_data 不等于右近位信号数据，则关闭右近位红外信号
    if ((0x01 << time_data) != IR_R_NEAR_DATA) {
        IR_R_NEAR_L;
    }
    // 若 0x01 << time_data 不等于右中远位信号数据，则关闭右中远位红外信号
    if ((0x01 << time_data) != IR_FR_FAR_DATA) {
        IR_FR_FAR_L;
    }
}

void Signaling_Factory_Transmission_Off(uint32_t time) {
    uint8_t time_data = 0;
    // 计算时间数据，time 对 50 取余后除以 5
    time_data = (time % DATA_TIME) / BIT_TIME;

    // 让数据码取反发送
    if (time_data <= 7) {
        time_data = 7 - time_data;
    }
    if ((0x01 << time_data) != 0x08) {
        IR_FR_FAR_L;
        IR_FR_NEAR_L;
        IR_R_FAR_L;
        IR_R_NEAR_L;
    }
    if ((0x01 << time_data) != 0x10) {
        IR_L_FAR_L;
        IR_L_NEAR_L;
        IR_FL_FAR_L;
        IR_FL_NEAR_L;
    }
}
```

主要修改代码讲解

```c
/**
 * @brief 红外信号分时发送状态机
 * @details 根据计数器 `count` 的值，切换不同的红外信号发送状态，实现分时发送功能。
 * @param 无
 * @return 无
 */
void Signaling_TimeDivisionTransmission(void) {
    // 用于存储要发送的红外信号数据
    uint8_t send_data = 0;

    // 根据当前的分时发送状态，执行不同的操作
    switch (time_division_state) {
    case ONE_TRANSMISSION:
		// 组合左(L)、左中(FL)、右中(FR)、右(R)的近位信号数据
        send_data = IR_L_NEAR_DATA | IR_FL_NEAR_DATA | IR_FR_NEAR_DATA | IR_R_NEAR_DATA;
        // 调用发送函数发送组合后的近位信号数据
        Signaling_Transmission(send_data, count);
        // 当计数器值大于等于50（DATA_TIME）时，切换
        if (count >= DATA_TIME) {
            time_division_state = TWO_TRANSMISSION;
        }
        break;
    case TWO_TRANSMISSION:
		// 组合左(L)、左中(FL)、右中(FR)、右(R)的远位信号数据
        send_data = IR_L_FAR_DATA | IR_FL_FAR_DATA | IR_FR_FAR_DATA | IR_R_FAR_DATA;
        // 调用发送函数发送组合后的远位信号数据
        Signaling_Transmission(send_data, count);
        if (count >= 2 * DATA_TIME) {
            time_division_state = THREE_TRANSMISSION;
        }
        break;
    case THREE_TRANSMISSION:
        // 当计数器值大于等于150（3 * DATA_TIME）或者小于50（DATA_TIME）时，切换到发送远位信号的状态
        if (count >= NEAR_FAR_TIME || count <= DATA_TIME) {
            time_division_state = ONE_TRANSMISSION;
        }
        break;
    case MAX_STATE:
        // 若状态为 MAX_STATE，重置为发送远位信号的状态
        time_division_state = ONE_TRANSMISSION;
        break;
    default:
        // 若状态不在枚举范围内，重置为发送远位信号的状态
        time_division_state = ONE_TRANSMISSION;
        break;
    }
}
```