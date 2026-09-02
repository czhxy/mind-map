# 天气时钟 学习笔记

## 1. 板级初始化为什么使用 LSE？

LSE 是给 RTC 用的（提供精确秒级走时，掉电由备份电池保持）。

## 2. 工作队列传递内容直接为回调函数和参数？为什么这样设计？

> 详见第 3 节，两者是同一个话题。

## 3. app_work 的参数传递

### 问题本质：函数类型不匹配

```c
typedef void (*work_t)(void *param);              // 带一个 void* 参数
void workqueue_run(work_t work, void *param);     // 要传「函数 + 参数」两个东西
```

`void (*)(void)` 和 `void (*)(void *)` 是两种不兼容的函数指针类型，直接写 `workqueue_run(time_sync, NULL)` 在 C 里属于类型不匹配。

### app_work 的适配作用

看 `app.c:209-213`：

```c
static void app_work(void *param)
{
    app_job_t job = (app_job_t)param;   // 把 void* 强转回「函数指针」
    job();                              // 再调用真正的业务函数
}
```

于是 `workqueue_run(app_work, time_sync)` 的含义是：

- `app_work` → 当作 workqueue 的统一入口函数
- `time_sync` → 当作参数（真正的任务）传进去

数据流：

```text
workqueue_run(app_work, time_sync)
        │  打包成 work_message_t { work=app_work, param=time_sync }
        ▼
  xQueueSend → workqueue 线程
        ▼
  msg.work(msg.param)          // = app_work(time_sync)
        ▼
  time_sync()                  // 最终执行
```

这样，workqueue 只用维护一个 `work_t` 接口，所有业务函数都保持无参、干净，适配逻辑集中在 `app_work` 一处，不用给每个任务各写一个包装函数。

## 4. DMA 为什么上限 65535？

- `DMA1_Stream4->NDTR` 是 16 位寄存器，上限 65535 **个数据项**（不是字节）。
- 当前数据项是半字（2 字节），刚好与要传输的数据类型对应上。

一次搬运的具体过程：把数据搬到 DR，SPI 总线就会串行发送；搬完后（NDTR 变为 0）触发 DMA 传输完成中断。

## 5.DMA开启FIFO的作用？
- 减少对AHB总线的访问。

## 6.ui队列异步收发

同下，主要是串行化执行，天然无锁，同时进行异步解耦


## 7.workqueue的作用？

### 1. 串行化执行 = 天然无锁

所有投递的任务都在**同一个 workqueue 线程里一个一个串行跑**，彼此天然不并发，所以后台任务之间**不需要任何互斥量**。这和我们之前聊的「队列串行化 UI」是同一个思想——用「单线程消费队列」从根源消除竞争。

### 2. 异步解耦（fire-and-forget）

投递方只负责「下达任务」，**不等待执行结果、不被拖慢**——`workqueue_run(app_work, time_sync)` 投完就返回，`time_sync` 里的联网 NTP 校时（可能耗时几百 ms~几秒）在后台慢慢做，不影响调用者。

## 8.如何将非实时性任务委托到后台任务调度？

通过软件定时器 `xTimerCreate` 注册定时器，把要执行的业务函数（如 `time_sync`）作为**定时器 ID** 存进去；定时器到期时，FreeRTOS 的 timer task 调用注册的回调，回调里用 `pvTimerGetTimerID` 取出业务函数指针，转回 `app_job_t` 执行。这里其实有**两个回调**，区别在于「在哪里执行」：

- `work_timer_cb`：取出后 `workqueue_run(app_work, job)` **投递到 workqueue 后台线程异步执行**——用于联网等耗时任务（time_sync / wifi / inner / outdoor）。
- `app_timer_cb`：取出后直接 `job()` **在 timer task 里同步执行**——用于轻量任务（time_update）。


好处：**只用 2 个回调（`app_timer_cb` / `work_timer_cb`）就服务了 5 个定时器**——每个定时器把「自己要干的活」作为 ID 随身携带，回调统一解包调用，不必为每个业务各写一个 `TimerCallbackFunction_t`


## 9.创建Timer任务有哪些参数？TimerID是什么类型的？一般在哪里使用？

定时器名称 周期 是否自动重载 TimerID(void *)  回调函数

注意：不能直接设定任意参数的回调函数直接强转类型作为定时器创建的回调函数传入，虽然逻辑上可行，但实际上根据下面的定义`typedef void (*TimerCallbackFunction_t)(TimerHandle_t);  `它是会传入一个定时器句柄的函数，

## 10.为什么fiLL_color不用做小端序的转换而draw_font要做小端序的转换？

fill_color中的color是uint16_t，在mcu中存储时就已经是小端序，而font缓存的pbuf是uint8_t，dma取数据时设置的是16bit，那就要手动把font进行小端序的排序后再存储，若是pbuf设置成uint16_t的话也可以不进行小端序的转换。绘制图像时，虽然图像也是uint8_t类型，但它已经按小端序排好了，所以不需要进行转换。

## 11.st7789_draw_font的作用？

把「字模位图」（1 bit = 1 像素的黑白信息）翻译成「每个像素 16 bit 的 RGB565 颜色」，再刷到屏幕上。

## 12.ASCII和chinese是怎么绘制出来的？

都是寻找对应字模的地址，然后调用st7789_draw_font进行绘制，本质也是将字模位图的bit翻译成16bit的rgb565的数据，然后通过spi传给屏幕。

## 13.为什么每个字库声明类型不同？

通过字模数据和映射表和中文字模数组的排列组合，实现既能显示需要的字符，又不会存储多余不需要的字符从而flash存储空间

| 字段          | 含义                                                         |
| ------------- | ------------------------------------------------------------ |
| `size`        | 字号（字高像素）                                             |
| `ascii_model` | ASCII 字模数组（完整表或精简表）                             |
| `ascii_map`   | ASCII 映射表（有则「只存部分字符」，无则「按标准顺序存全表」） |
| `chinese`     | 中文字模数组（有则能显示中文）                               |

下面是 9 个字库的实际对比：

| 字库                   | size | ascii_model | ascii_map         | chinese | 用途定位       |
| ---------------------- | ---- | ----------- | ----------------- | ------- | -------------- |
| font16_maple           | 16   | ✓           | 无                | ✗       | 小号纯英文     |
| font20_maple_bold      | 20   | ✓           | 无                | ✓       | 中文+英文      |
| font24_maple_bold      | 24   | ✓           | 无                | ✓       | 中文+英文      |
| font24_maple_semibold  | 24   | ✗           | 无                | ✓       | **纯中文**     |
| font32_maple_bold      | 32   | ✓           | 无                | ✓       | 中文+英文      |
| font54_maple_bold      | 54   | ✓           | `"-0123456789. "` | ✗       | 大数字         |
| font54_maple_semibold  | 54   | ✓           | `"-0123456789. "` | ✗       | 大数字         |
| font64_maple_extrabold | 64   | ✓           | `"-0123456789. "` | ✗       | 大数字         |
| font76_maple_extrabold | 76   | ✓           | `"0123456789: -"` | ✗       | 大数字（时钟） |