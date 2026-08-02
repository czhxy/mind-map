# IMU 缺少校准导致 Yaw 不更新面试速记版

## 1. 现象

- `yaw` 不更新，表现为数值卡住
- `pitch/roll` 仍然有变化
- 问题出现在缺少校准初始化的场景下

## 2. 我的排查方法

我的思路是先看最终输出，再反推上游，而不是先怀疑算法公式。

### 第一步：看 `yaw` 最终从哪里出来

先定位到：

```c
Mod_Imu.imu_data.yaw = mod_imu_sensor.yaw;
```

继续往上追到：

```c
mod_imu_sensor.yaw = yaw_1 * 1000;
```

结论：外部看到的 `yaw` 不更新，本质上是 `yaw_1` 没更新。

### 第二步：看 `yaw_1` 为什么没更新

继续追 `yaw_1` 的更新链路，发现它依赖姿态解算主分支：

```c
if (!zero_calibration_flag) {
    UpdateQuaternion(...);
    UpdateEuler(...);
    mod_imu_sensor.yaw = yaw_1 * 1000;
}
```

结论：只要 `zero_calibration_flag` 没清零，姿态解算就不会执行，`yaw` 当然不会更新。

### 第三步：看是谁控制 `zero_calibration_flag`

再查写入点，发现：

```c
static uint8_t zero_calibration_flag = 1;
```

只有这里会把它清零：

```c
if (GyroZeroCalibration(...)) {
    zero_calibration_flag = 0;
}
```

结论：`yaw` 是否更新，直接取决于启动零偏校准是否成功。

## 3. 为什么 `pitch/roll` 还能动

因为 `pitch/roll` 有两条链路：

1. 姿态解算结果 `pitch_/roll_`
2. 加速度直接计算的倾角 `pitch__/roll__`

代码里会根据状态选择最终发布哪一路，所以即使姿态解算主分支没完全进入，`pitch/roll` 仍可能通过加速度链路更新。

而 `yaw` 没有这种备用链路，因为加速度无法观测偏航角。

## 4. `Imu_Calibration_Init()` 在这件事里的位置

`Imu_Calibration_Init()` 不是直接控制 `yaw` 是否更新的标志位来源。

它负责：

- 初始化 `Imu_Calibration` 补偿参数
- 设置 `calibration_done`
- 保证补偿结构体处于可用状态

真正直接控制姿态解算是否放开的，是 `zero_calibration_flag`。

所以更准确的说法是：

- `Imu_Calibration_Init()` 影响的是补偿初始化是否完整
- `GyroZeroCalibration()` 影响的是姿态解算主链路是否解锁
- `yaw` 不更新的直接原因，是 `zero_calibration_flag` 没有被清零

## 5. 面试时可以直接这样说

> 我当时排查 IMU 问题时，先从最终输出反推，而不是先怀疑算法。先定位到 `Mod_Imu.imu_data.yaw`，再追到 `mod_imu_sensor.yaw`，最后确认它来自 `yaw_1`。然后继续追 `yaw_1` 的更新条件，发现姿态解算外面被 `if (!zero_calibration_flag)` 门控住了。再查这个标志位的写入点，确认它默认是 1，只有 `GyroZeroCalibration()` 成功后才会变成 0。所以根因不是 yaw 公式错了，而是姿态解算主链路没有被放开。接着我又解释了为什么 pitch 和 roll 还能动，因为它们有一条基于加速度直接算倾角的备用发布链路，而 yaw 没有。最后再补充，`Imu_Calibration_Init()` 影响的是补偿参数和初始化完整性，不是直接控制 yaw 更新的那个开关。`

## 6. 一句话总结

这个问题的核心不是姿态算法算错，而是 `yaw` 的唯一输出链路被启动零偏校准完成条件卡住了；`pitch/roll` 因为有加速度备用链路，所以表象上还能更新。
