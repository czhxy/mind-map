## **目录：**

**1、时序说明**

**2、温湿度性能指标**

**3、典型通信时序**

**4、命令字说明**

**5、加热器相关**

**6、代码细节**

**7、打印示例**



## **1、时序说明**

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a27905087190dd0b91bdaf8223b9d3d7a8bd863d90a8aab9aa2cdbff74d85c5a14150f30c66f5c7e9ff102a9c80e50a19?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)



## **2、温湿度性能指标**

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a822951806323f8963fbeb7e37fa3c0c166bd05d661f369c38879f1696f14ad97158b3a551b5c50376f298dce36091f35?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a8169d9d9ddf3b83f7871e67ee32af734534b56f253773bf9ba9ac7fe8fdb3ba71c013f904c5dc04c572cd44458b3dbbc?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)





## **3、典型通信时序**



![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a0d50ecb3f30f832e74a251df72f7bd499081e37106630af3ec374444639445fdf23c6716aa3f8eb5d2c4366742596c59?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)

I²C 操作的数据包长度为 8bit，从传感器返回主机的数据中，每 2 个数据包跟随一个 8bit 的 CRC 校验数据。湿度和温度数据总是以如下的方式进行传输： 2 字节的温度数据+1 字节 CRC+2 字节的湿度数据+1 字节的 CRC校验数据



## **4、命令说明（当前代码采用低重复率测量，最大测量时间1.6ms。精度：0.25%RH,0.1℃）**



![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602aaac77b6f1abe50dfff697bd8fc5b0564d9f07b21a49a8fc3537f554a58541c5a8e7727c87c3708bcab0e4d485c33f4d4?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a7a5c135778ee098cea41da01ef76d107667d281fac2a9eb8e5cc7fa4ca022dcce9b9ece9d24815c17cae8fe2c6a67103?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)

## **5、特殊（带加热器**）

适用场景：

1. 除去传感器表面的溅射或者结露的水滴。虽然结露的水滴对于传感器来说不会导致传感器损坏，但是如 果液态的水滴一直存在于传感器的表面，会影响传感器对环境湿度的响应。
2. 长期高湿环境，通过周期性的加热能够保证传感器的长期可靠性。

![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a0524375348f90ffd1ceeefa3600d2bf785fae060c5765c6159aa4318f2e17ea1a4d6a814fd7805cfd7740755f7e82d3b?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)

加热器注意事项：

1. 加热器的开启/关闭占空比不能超过 10%，也就是说加热时间占整个传感器使用寿命时间的比例不能超过 10%。
2. 在开启加热器期间，传感器的性能指标不再适用。
3. 温度传感器可能会受到热应力的影响从而出现温度测量偏移的问题。
4. 传感器的温度(环境或者加热器导致)不能长期超过 125℃，以保证芯片的正常功能。
5. 在加热器开启的时候，芯片电流最高可能会达到 70mA，供电电源的驱动能力必须足够大以避免大电流 引起的电压降，电压降太大时可能会引起芯片复位。
6. 为了达到更高的加热温度，需要连续发送加热命令。加热器开启的时候环境温度不能超过 65℃，否则会 导致芯片的内部温度超过最高允许温度（125℃）。



## **6、代码细节**

1、初始化后延时100ms，启动软复位，软复位后延时1ms(参考手册最大软复位时间)

2、循环测量，周期为1s。带互斥锁（但实际两个设备i2c总线是分开，不使用也行）

3、测量默认cmd为GXHT4X_CMD_MEASURE_LPM（低重复率测量），等待测量时间为10ms（低重复率下手册最大测量时间为1.6ms,典型时间为1.3ms。高重复率下最大测量时间为8.3ms，典型时间为6.9ms）



## **7、打印示例**

人手放上去的变化

## ![img](https://alidocs.dingtalk.com/core/api/resources/img/5eecdaf48460cde5c9af226ab49d2f278aa7c7377ac0bcad75b8339e1c4c24834be8b1c98e9fc5628d68742cd653602a60709c486a81f6b4b63f74829b5213db67e5cb7ee7228e741ee7100d524fc48818a501af3c595b044c6e6742474c7ec6?tmpCode=78ced144-8330-4603-8957-0fb09fc181ac)