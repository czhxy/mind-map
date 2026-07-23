# IMU 缺少校准导致 Yaw 不更新面试版排查链路

## 一、问题背景

在一次 IMU 姿态问题排查中，现场现象是：

- `yaw` 角不更新，表现为数值卡住
- `pitch` 和 `roll` 仍然有变化
- 问题与“缺少校准初始化”相关

这类问题表面上像是姿态算法本身有 bug，但实际排查后确认，根因并不是 `yaw` 公式算错，而是整条 `yaw` 输出链路被启动校准条件门控住了。

## 二、我的排查思路

我的排查顺序不是一开始就盯着算法公式，而是先按“数据有没有真的流到最终输出”这个思路，从输出向上游反推。

### 第一步：先确认 `yaw` 最终发布点

我先看 `Mod_Imu.imu_data.yaw` 是在哪里赋值的，确认最终对外输出来自：

```c
Mod_Imu.imu_data.yaw = mod_imu_sensor.yaw;
```

然后继续往上追，发现 `mod_imu_sensor.yaw` 来自：

```c
mod_imu_sensor.yaw = yaw_1 * 1000;
```

到这里可以得到第一个结论：

- 外部看到的 `yaw` 不更新，不一定是传输出问题
- 更大概率是 `yaw_1` 本身就没有被更新

### 第二步：继续往上追 `yaw_1` 的更新条件

继续看 `yaw_1` 是谁更新，发现它在姿态解算主分支里更新，对应的是：

- `UpdateQuaternion(...)`
- `UpdateEuler(...)`

但这两步外面包着一个条件：

```c
if (!zero_calibration_flag) {
    ...
}
```

到这里排查重点就从“算法有没有跑偏”转成了“为什么这个条件没有放开”。

我当时就得到了第二个关键判断：

- 如果 `zero_calibration_flag` 一直是 `1`
- 那么姿态解算根本不会执行
- `yaw_1` 当然不会更新
- 所以最终 `yaw` 看起来就是卡死

### 第三步：确认 `zero_calibration_flag` 是谁更新的

接着我继续查 `zero_calibration_flag` 的写入点，发现它定义时默认值就是：

```c
static uint8_t zero_calibration_flag = 1;
```

而且运行时真正把它清零的地方只有一个：

```c
if (GyroZeroCalibration(...)) {
    zero_calibration_flag = 0;
}
```

这说明姿态解算是否启动，完全依赖 `GyroZeroCalibration()` 是否成功。

到这里链路已经很清楚了：

- 系统上电后 `zero_calibration_flag` 初始为 `1`
- 只有启动零偏校准成功后，它才会变成 `0`
- 只有它变成 `0`，姿态解算才真正开始
- `yaw` 也才有机会更新

### 第四步：解释为什么 `pitch/roll` 还能动

如果只停在上一步，其实还没完全解释现场现象。

因为还有一个明显矛盾：

- 既然姿态解算整体被门控住了
- 为什么 `pitch` 和 `roll` 还在变化

我继续往后看 `pitch/roll` 的发布逻辑，发现它们不是只有姿态解算这一条链路。

代码里除了 `pitch_ / roll_` 这种姿态解算结果，还额外算了：

```c
float pitch__ = 1000 * atan2(acc_x, sqrt(acc_y * acc_y + acc_z * acc_z));
float roll__  = 1000 * -atan2(acc_y, sqrt(acc_x * acc_x + acc_z * acc_z));
```

这实际上是直接用加速度算倾角。

后面发布时会根据状态二选一：

- 未进入工作态，或者 `calibration_status == 0` 时，发布 `pitch__ / roll__`
- 满足条件后，才切到姿态解算结果 `pitch_ / roll_`

所以这里的真实机制是：

- `pitch/roll` 有备用链路
- `yaw` 没有备用链路
- 因此启动校准卡住时，`yaw` 会静止，但 `pitch/roll` 仍可能变化

这一步把现场现象彻底解释通了。

### 第五步：把 `Imu_Calibration_Init()` 放回整条链路里理解

用户最初提到的是“缺少 `Imu_Calibration_Init()` 为什么会导致 yaw 不更新”，所以我又回头看了初始化链路。

`Imu_Calibration_Init()` 本身做的是补偿参数初始化：

- 装载 Flash 中的零偏参数
- 装载比例系数、交叉轴系数
- 如果 Flash 无效，就写入兜底值

它直接影响的是：

- `Imu_Calibration`
- `calibration_done`

而不是 `zero_calibration_flag`。

也就是说，从代码关系上讲：

- `Imu_Calibration_Init()` 不是直接控制 `yaw` 是否更新的那个开关
- 真正的硬门槛仍然是 `zero_calibration_flag`

但是如果缺少 `Imu_Calibration_Init()`：

- 整个 IMU 补偿结构就处于未正确准备状态
- 排查时很容易把问题表象和补偿问题混在一起
- 最终在系统行为上，会体现为姿态链路没有完整进入稳定工作态
- 而 `yaw` 恰恰又是最依赖“主姿态解算已启动”的那个量

所以更准确的表述不是：

“缺少 `Imu_Calibration_Init()` 直接把 `yaw` 卡死了”

而是：

“缺少初始化暴露了姿态链路对启动零偏校准的强依赖，而 `yaw` 又没有备用发布路径，因此最终表现成 `yaw` 不更新。”

## 三、最终定位结论

我最后给出的根因结论是：

### 1. 直接根因

`yaw` 的最终发布完全依赖姿态解算主分支，而这个主分支被 `zero_calibration_flag` 门控：

```c
if (!zero_calibration_flag) {
    UpdateQuaternion(...);
    UpdateEuler(...);
    mod_imu_sensor.yaw = yaw_1 * 1000;
}
```

只要启动零偏校准没有完成，`yaw` 就不会更新。

### 2. 现象差异的原因

- `yaw` 没有备用链路，只能依赖姿态解算结果
- `pitch/roll` 有加速度倾角备用链路，所以看起来还能变化

### 3. `Imu_Calibration_Init()` 在问题中的位置

它不是直接控制 `yaw` 更新的标志位来源。

它影响的是补偿参数初始化和 `calibration_done` 状态；而真正决定姿态解算是否放开的，是 `GyroZeroCalibration()` 成功后清零的 `zero_calibration_flag`。

## 四、面试时可以怎么讲

可以用下面这段简化表达：

> 当时我排查 IMU 的问题，现场现象是 yaw 不更新，但 pitch 和 roll 还能变化。我的方法不是先怀疑算法公式，而是先沿着最终输出变量反推。先定位到 `Mod_Imu.imu_data.yaw`，再追到 `mod_imu_sensor.yaw`，最后发现它来自 `yaw_1`。接着我看 `yaw_1` 的更新条件，发现 `UpdateQuaternion` 和 `UpdateEuler` 外面被 `if (!zero_calibration_flag)` 包住了。继续查写入点后确认，`zero_calibration_flag` 默认是 1，只有 `GyroZeroCalibration()` 成功后才会变成 0。所以问题本质不是 yaw 算法本身错了，而是姿态解算主链路没有被放开。然后我又解释了为什么 pitch 和 roll 还能动，因为它们有一条基于加速度直接算倾角的备用发布链路，而 yaw 没有。最后再回到初始化，说明 `Imu_Calibration_Init()` 影响的是补偿参数和 `calibration_done`，不是直接控制 yaw 是否更新的开关。真正的硬门槛还是启动零偏校准成功与否。这样整条链路就闭环了。`

## 五、适合面试的关键词

- 先看最终输出，再反推上游链路
- 区分“直接控制标志位”和“间接影响初始化状态”
- 区分“姿态解算主链路”和“备用发布链路”
- 解释现象差异时，不只看算法，还要看最终发布逻辑
- 把“代码关系”和“系统表现”分开讲清楚

## 六、一句话面试总结

这次问题的核心价值不在于我发现了某个变量，而在于我把“初始化、启动零偏校准、姿态解算、最终发布”这几段链路串成了一个闭环，并解释了为什么同样是姿态角，`yaw` 会卡死而 `pitch/roll` 不会同步卡死。
