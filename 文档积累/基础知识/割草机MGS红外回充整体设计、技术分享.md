# 割草机MGS红外回充整体设计、技术分享

# 一、前言概述

本文档系统性地阐述割草机MGS红外回充系统的软硬件及结构设计，涵盖红外发射、红外接收、回充逻辑三大核心模块。旨在为相关领域人员提供全面的技术参考，统一对红外回充功能的认知标准。本文档适用于结构工程师、硬件开发人员及软件算法工程师，重点关注设计要点、信号逻辑及实际应用中的优化思路。

# 二、红外发射设计

## 2.1、充电桩发射结构

充电桩发射结构是红外回充系统的信号源，其设计直接影响信号覆盖范围与精度。以下分常规扫地机和MGS割草机两类结构进行对比说明。

### 2.1.1、常规扫地机充电桩的发射结构

常规扫地机充电桩通常采用对称式发射灯布局，通过遮光件控制红外光的定向发射。其结构核心在于避免光路串扰，确保信号区域分明。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/b6bb80a6-bfe3-4d36-848a-93adc59e4590.png)

图2.1-1、常规发射结构

注：结构内部需做磨砂或锯齿处理，减少反光干扰。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/eea19f1f-6c23-4321-b13b-a3ff9dccf8ee.png)

图2.1-2、发射信号覆盖图

实际应用中，需通过测试验证信号覆盖的连续性，避免盲区。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/df011b60-51f5-4ae5-a65b-50e38369357d.png)

图2.1-3、常规发射俯视解剖图

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/fe0acce3-69a7-48a9-8597-6328d948468e.png)

图2.1-4、银星量产产品充电桩发射图

### 2.1.2、MGS割草机充电桩发射结构

MGS割草机充电桩采用四灯布局（左、左中、右中、右），支持远近双模式信号发射。结构上强调光路的对称性与公差容错能力。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/da63514b-170d-41cc-b869-3946a39ac45d.png)

图2.1-5、MGS充电桩发射俯视解剖结构图

关键设计要点：

*   灯位深度：发射灯嵌入深度越深，对结构公差要求越低。
    
*   光路隔离：通过物理隔断防止灯间串光。
    

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/84a0d92d-f7ed-4bbc-85ba-a1247eff449c.png)

图2.1-6、MGS充电桩发射光路俯视图

注：理想光路需通过实测验证，确保各灯信号独立覆盖。

### 2.1.3、发射结构要求

1、**防反光设计**：

*   结构内部表面需为磨砂面或锯齿面。
    
*   材质首选黑色塑胶，可附加黑色棉类吸光材料。
    

2、**防串光漏光**：

*   非光路区需密封处理，杜绝细缝漏光。
    
*   灯间需加隔断，避免信号交叉
    

3、**光路对称性**：

*   出光区边缘遮挡件的公差需控制在±0.1mm以内。
    
*   灯深设计建议＞5mm，以降低对精度依赖
    

4、**光路验证**：

*   常规扫地机理想引导光路：先分开后交叉模式。
    
    ![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/eea19f1f-6c23-4321-b13b-a3ff9dccf8ee.png)
    
*   MGS理想引导光路为：先交叉后分开模式，需通过单接收头扫描实测确认：
    

![image](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/a/pALro9jDPtAqM2A8/f85ecc4c28b1401cbaaeceb6c890faf33734.png)

## 2.2、发射硬件

发射硬件核心为强弱光双模式控制电路，通过MCU调控红外灯的发射强度。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/3983c036-0ecb-4ef1-9a61-8e61a0038010.png)

图2.2-1、强弱两种光发射控制电路

*   **强光控制**：MCU输出高电平至IR\_L引脚，导通Q119，电流经R359驱动LED6。
    

*   **弱光控制**：MCU输出高电平至IR\_L\_NEAR，导通Q120，电流经R368（阻值大于R359）实现弱发射。
    

*   **禁止同时开启**：强弱光同时开启会导致信号混叠，弱信号被淹没
    

## 2.3、发射信号

红外信号设计参考遥控器原理，采用载波调制方式提升抗干扰能力。

### 2.3.1、红外光波段：

发射波长固定为940nm，与接收头（如IRM-H638T-TR2）的峰值响应波段匹配

### 2.3.2、红外发射载波频率

载波频率为38kHz方波，为通用接收头的标准解调频率。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/ec3982e0-5236-4303-911e-2a2e41e1dc5f.png)

图2.3-1

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/3a01e493-19d1-486b-93a6-86c0beaeee10.png)

图2.3-2

当发射管发送38kHz载波时，接收头输出低电平；停止载波时输出高电平。

### 2.3.3、红外发射与接收的信号定义

信号以二进制数据形式编码：

*   **信号0**：发射0.7ms载波 + 2.8ms静默 → 接收端获0.7ms低电平 + 2.8ms高电平。
    
*   **信号1**：发射2.8ms载波 + 0.7ms静默 → 接收端获2.8ms低电平 + 0.7ms高电平。
    

每个信号周期为3.5ms，通过占空比区分0/1

下图所示为充电桩发射一组8位信号组成的充电桩发射、割草机接收波形图。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/07ddeae2-0b57-413e-ab1f-9bd3310c27d9.png)

图2.3-3、充电桩发射一组8位数据信号的波形图

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/09fef1b0-5658-415c-8448-d083e673e06f.png)

图2.3-4、接收器对应接收到信号的波形图

### 2.3.4、红外发射与接收的数据定义

每个发射灯独立发送8位数据，高位先发。数据定义如下表：

| 发射灯序号 | 信号远近 | 对应数据 |
| --- | --- | --- |
| 左灯 | 近 | 0x80 |
|  | 远 | 0x08 |
| 左中灯 | 近 | 0x40 |
|  | 远 | 0x04 |
| 右中灯 | 近 | 0x20 |
|  | 远 | 0x02 |
| 右灯 | 近 | 0x10 |
|  | 远 | 0x01 |

示例：图2.3-3和图2.3-4展示数据0x20（右中灯近信号）的波形。

![image](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/adfd5f64-9fa1-4f1d-994f-74a41602e2c2.png)

### 2.3.5、红外发射时序与频率

时序设计避免远近信号重叠：

1.  近信号阶段：4灯同时发射弱光，耗时4×3.5ms×2=28ms（每灯发2位数据）。
    
2.  间隔28ms。
    
3.  远信号阶段：4灯发射强光，耗时28ms。
    
4.  长间隔196ms（确保弱信号可被识别）。
    

完整周期=28ms+28ms+28ms+196ms=280ms，频率≈3.57Hz

注：若需提速，可牺牲弱信号模式，频率最高可达20Hz。

发射时序如下图所示：

![41e90ab89c1df2b177e271e0cfe81b00.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/f4d417e9-4ca3-4b4f-a941-bf5758f85e4d.png)

图2.3-5、MGS充电桩红外发射时序波形图

### 2.3.6、mgs充电桩红外发射代码

代码逻辑需实现：

*   循环控制4灯按时序发射远近信号。
    
*   载波由38kHz PWM生成，数据通过GPIO切换。
    

（代码细节参考附件：[《MGS红外发射代码》](https://alidocs.dingtalk.com/i/nodes/YQBnd5ExVEwMGnwgfAdaypr18yeZqMmz?doc_type=wiki_doc&iframeQuery=utm_source=portal&utm_medium=portal_space_create)）

# 三、红外接收设计

## 3.1、机器接收结构

### 3.1.1、常规扫地机接收结构

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/1803c2e2-e538-49e5-8690-1d0d80c8cb55.png)

图3.1-1、常规接收结构俯视解剖图

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/9969089e-b42b-4760-ac86-90ced6a25c7b.png)

图3.1-2、银星接收结构俯视解剖图

### 3.1.2、MGS割草机接收结构

接收结构决定信号捕获范围与对准精度，MGS采用双接收头设计以扩大视角。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/088c2beb-4fa6-472c-8720-bf180e4bd9f7.png)

图3.1-3、MGS接收结构俯视解剖图

### 3.1.3、接收结构设计要求

1、理想接收角度范围与范围含义。（带着问题往前走：为什么需要2个接收头？）

![image](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/a/pALro9jDPtAqM2A8/9698c5db1e7b43f197a660a659ca3bc73734.png)

图3.1-4、理想接收信号角度图

（1）描述：

第1个角度：蓝色虚线与中线形成的角度；

第2个角度：++**黄色带箭头实线**++与中线形成的角度；

第3个角度：++**蓝色带箭头实线**++与中线形成的角度；

第4个角度：黄色虚线与中线形成的角度；

第5个角度（左接收头角度）：上图蓝色虚线（1号线） 和 蓝色带箭头实线（3号线）组成的角度为左接收头收到信号的角度。

第6个角度（右接收头角度）：上图黄色箭头实线（2号线） 和 黄色虚线（4号线）组成的角度为右接收头收到信号的角度。

++**第7个角度（对准角度）：上图黄色箭头实线（2号线） 和 蓝色带箭头实线（3号线）组成的角度为左右接收头同时收到的角度。**++

（2）为什么要用2个接收头？

结论：为了确保机器对准充电桩的同时，在较大角度上能够搜索到充电桩。

为什么不用一个接收头？    回复：只用一个接收头时，接收范围限制较小时，容易丢失信号；接收范围限制较宽时，容易对不准。

（3）理想角度要求：

| 角度描述 | 大小要求 | 居中对称要求 |
| --- | --- | --- |
| 第2个角度 | 5°~15°之间 | 与第3角度差值小于3° |
| 第3个角度 | 5°~15°之间 | 与第2角度差值小于3° |
| 第1角度 | 45°~90°之间 | 与第4角度差值小于15° |
| 第4角度 | 45°~90°之间 | 与第1角度差值小于15° |
| 第7角度（对准角度） | 10°~30°之间 |  |

2、MGS02的B2机器实际接收范围

| 角度描述 | 实际大小 | 实际对称 |
| --- | --- | --- |
| 第2个角度 | 12° | 与第3角度相差1° |
| 第3个角度 | 13° | 与第2角度相差1° |
| 第1角度 | 30° | 与第4角度相差7° |
| 第4角度 | 37° | 与第1角度相差7° |
| 第7角度（对准角度） | 25° |  |

![lQDPKG8xlQ1sc5PNEADNB0CwAwjGC32MXkwJK9Uc3mw0AA_1856_4096.jpeg](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/4b8f64ee-3235-40ee-a561-7f09eb18a879.jpeg?x-oss-process=image/auto-orient,1/ignore-error,1)

图3.1-5、MGS02实际接收角度图

## 3.2、机器接收硬件

1、原理图

接收硬件基于红外接收头（如IRM-H638T-TR2），电路简洁。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/d2bf1f5a-6a9a-405b-be8c-66cb35fff8a3.png)

图3.2-1、MGS红外接收头原理图

2、接收头相关规格信息。

规格书：

[请至钉钉文档查看附件《301060030\_42.013204\_红外接收管\_EVERLIGHT\_IRM-H638T-TR2.pdf》。](https://alidocs.dingtalk.com/i/nodes/NZQYprEoWoeX0Yephrb6oXaPJ1waOeDk?doc_type=wiki_doc&iframeQuery=anchorId%3DX02mjqx6tz9v2kpr2k7rfi&rnd=0.4761943064871068)

主要核心内容：

*   接收头输出直接接MCU GPIO，内置解调器滤除非38kHz干扰。
    

*   规格书关键参数：载波频率38kHz±1kHz，接收角度±45°
    

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/ec3982e0-5236-4303-911e-2a2e41e1dc5f.png)

图2.3-1

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/3a01e493-19d1-486b-93a6-86c0beaeee10.png)

图2.3-2

当红外发射管以标准 38KHz 载波发送信号时，割草机上的红外接收管的状态为低电平，其他情况下为高电平，发送载波的时长决定了扫地机接收低电平的时间。

## 3.3、接收信号与软件解码

### 3.3.1、接收信号

接收头输出波形与发射信号反相（载波期间为低电平）。

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/07ddeae2-0b57-413e-ab1f-9bd3310c27d9.png)

图3.3-3、充电桩发射一组8位数据信号的波形图

![image.png](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/QvjnA3jPPmp3gOXo/img/09fef1b0-5658-415c-8448-d083e673e06f.png)

图3.3-4、接收器对应接收到信号的波形图

### 3.3.2、信号数据保持逻辑

*   数据有效期：560ms（2个发射周期）。
    

*   示例：若左接收头在时刻A收到左中（0x04）和右中（0x02）远信号，数据保持为0x06；若560ms内未刷新左中信号，则更新为0x02
    

### 3.3.3、mgs红外接收相关代码（摘要）

代码需实现：

*   捕获脉冲宽度。
    
*   超时机制清除旧数据。
    

（细节参考附件：[《MGS红外接收代码》](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK32EY3pIQENL6jqJkb4Mw9r?doc_type=wiki_doc&iframeQuery=utm_source=portal&utm_medium=portal_space_create)）

# 四、回充逻辑

描述：这里红外回充主要讲解常规扫地机红外回充逻辑。

## 4.1、回充逻辑基本框架

第一步：发现信号（Get Pos)：机器扫描环境，通过接收头数据定位充电桩方向

第二步：走到充电座近处(far to near)：径直往充电桩走，直到靠近充电桩

第三步：挪到充电座中间(Trans to mid)：根据桩信号,走到桩正前方

第四步：对准走上去(Arc to charge)：在充电桩正前方直线驶入充电桩。

## 4.2、扫地机回充逻辑文件

详细流程参考：

[请至钉钉文档查看附件《回充调试教程v1.1\_20220401.pptx》。](https://alidocs.dingtalk.com/i/nodes/NZQYprEoWoeX0Yephrb6oXaPJ1waOeDk?doc_type=wiki_doc&iframeQuery=anchorId%3DX02mjs6yl8j8fdqamvc247&rnd=0.4761943064871068)

[请至钉钉文档查看附件《乐动无侧边回充灯逻辑.docx》。](https://alidocs.dingtalk.com/i/nodes/NZQYprEoWoeX0Yephrb6oXaPJ1waOeDk?doc_type=wiki_doc&iframeQuery=anchorId%3DX02mjqyxq7gxr208j8ozr&rnd=0.4761943064871068)

# 五、总结

本文档系统梳理了MGS割草机红外回充系统的设计要点，涵盖结构、硬件、信号及逻辑全链路。关键改进包括：

*   结构上通过双接收头扩大检测范围，兼顾对准精度。
    
*   信号编码采用远近分时发射，避免干扰。
    
*   时序设计以280ms周期平衡频率与可靠性。
    

建议在实际部署中结合实测数据优化角度参数与代码容错机制。

## 版本信息

| 版本号 | 修改人 | 修改描述 |
| --- | --- | --- |
| V1.0.0 | 陈权 | 初始版本 |
| V1.0.1 | AI&陈权 | 优化描述 |