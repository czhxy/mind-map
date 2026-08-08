# -*- coding: utf-8 -*-
"""
优化"秋招简历v0.2电机方向 - 副本.docx" → "秋招简历v0.3电机方向.docx"
- 实习经历：STAR 法则（角色概括 / 核心工作 1-2 段 / 结果数据化）
- 项目经历：项目背景（去硬件细节）/ 功能实现（1-2 个亮点）/ 成果数据化（精炼不分点）
同时改写 mc:Choice(DrawingML) 与 mc:Fallback(VML) 两套文本框，保留段落与加粗高亮格式。
文本中 **xx** 表示加粗片段。
"""
import copy
import zipfile
import shutil
from lxml import etree

SRC = "秋招简历v0.2电机方向 - 副本.docx"
DST = "秋招简历v0.4电机方向.docx"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# ============ 编辑内容定义 ============
# 段落索引 → 新文本（** 为加粗标记；空串表示清空该段）
INTERN = {
    1: "任职描述：参与智能割草机器人整机项目，独立负责外设板驱动开发、传感器器件验证与电机/底盘类 Bug 根因分析，并承担边缘功能开发与技术文档沉淀。",
    2: "**核心工作 1：驱动开发与器件验证**：基于 RT-Thread 独立完成外设板线程划分与数据流设计，开发 **AHT20、MLX90624** 等传感器驱动及 USB CDC、红外接收模块，代码经团队评审**合入主分支**；结合原理图与数据手册独立解决 I2C 引脚复用、上拉电阻缺失、时序裕量不足、固件兼容等 **4 项硬件问题**，缩短器件验证周期。",
    3: "**核心工作 2：Bug 分析与问题定位**：经 Teambition 处理 **30+ 个问题单**（刀盘堵转、轮子堵转、轮子过温、回充上桩异常等**电机/底盘类问题**），通过日志分析与场景复现定位根因并判定责任归属，嵌入式问题大部分**当天闭环**；对返厂整机无响应问题逐级排查供电与通信链路，协助硬件确认 **MOS 管烧毁根因**。",
    4: "**工作成果**：处理 **30+ 个问题单**并全量闭环、驱动代码合入主分支，支撑整机按期量产；沉淀**新人指引与 3 份器件验证报告**，缩短团队上手与选型周期；独立落地**雨水传感器滤波算法、蜂鸣器勿扰模式**，保障户外场景稳定运行。",
    5: "",
    6: "",
    7: "",
}

CAR_TOP = {
    1: "**项目背景：**基于 STM32 双 MCU + CAN 总线的汽车仪表盘演示系统，实现仪表盘 UI 显示、电机闭环控制与固件 OTA 升级，打通整车“通信-显示-控制”完整链路。",
    2: "",  # 原硬件平台段清空（细节不展开）
    3: "**功能实现：**",
    4: "**双 ECU CAN 通信架构：**设计 29-bit 扩展帧位域协议，显示域 FreeRTOS 双队列异步收发，动力域环形缓冲 + 弱符号回调解耦，实现 500kbps 下稳定通信。",
    5: "**电机位置式 PID 闭环：**20kHz PWM 驱动 + 编码器反馈采样，目标转速经 CAN 下发、转速与故障码回传刷新仪表盘，实现闭环调速与实时告警。",
}

CAR_BOTTOM = {
    1: "**LVGL 仪表盘 UI：**基于 LVGL v8.3 实现车速表、转速表、CAN 状态指示与电机故障告警，双缓冲渲染无撕裂、触摸响应及时。",
    2: "**FreeRTOS 多任务架构：**显示域按实时性分层 8 任务，动力域三级周期调度，双 ECU 状态同步，无死锁、无优先级反转。",
    3: "",
    4: "**项目成果：**",
    5: "CAN 总线 500kbps 下**通信零丢帧**，仪表盘 **5ms/帧**稳定刷新、双缓冲无撕裂，8 任务架构无死锁，全系统稳定运行。",
}

FOC = {
    2: "**项目背景：**基于 ESP32 双核 + FreeRTOS 搭建双路表贴式永磁同步电机（SPMSM）FOC 磁场定向控制验证平台，解决单循环架构下双电机控制的实时性冲突与周期抖动问题，面向智能旋钮、力反馈控制器等触觉反馈场景。",
    4: "ESP32 双核 MCU + 双路 SPMSM 电机 + 双路 12 位磁编码器 + 三相半桥驱动电路。",
    6: "**FOC 核心算法与三闭环控制：**从零实现 Clark/Park 变换、SVPWM 与 **Id=0 最大力矩电流比控制**，搭建力矩/速度/位置三闭环串级 PID 架构，支持控制模式灵活切换。",
    7: "**双核多任务架构与驱动：**FreeRTOS 多任务分层 + 核亲和性绑定，完成 6 路 **10kHz** 高速 PWM 驱动，匹配三相半桥控制时序。",
    8: "**工程化落地：**设计 **8 种可配置触觉反馈模式**（阻尼旋钮、惯性滑行、弹簧回弹、双电机同步跟随等），通过切换闭环架构与参数实现差异化手感。",
    9: "",
    11: "双路磁编码器读取成功率 **100%**，角度采样精度 **12bit**，相电流采样误差 **±50mA** 内，满足闭环控制需求。",
    12: "落地 **8 种可配置触觉反馈模式**，在线调参使**调试效率提升 60%**。",
}

# 类型 → (识别关键词, 编辑映射)
RULE_KEYWORDS = {
    "intern": ("乐动机器人", INTERN),
    "car_top": ("全车智能中控面板", CAR_TOP),
    "car_bottom": ("LVGL", CAR_BOTTOM),
    "foc": ("FOC 磁场定向控制", FOC),
}


def parse_segments(text):
    """把 **加粗** 标记解析为 [(text, is_bold), ...]"""
    segs = []
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        segs.append((part, i % 2 == 1))
    return segs


def is_bold(run):
    rPr = run.find(W + "rPr")
    if rPr is None:
        return False
    b = rPr.find(W + "b")
    if b is None:
        return False
    val = b.get(W + "val")
    return val is None or val in ("1", "true", "on")


def pick_base_rPr(p):
    """取段落内第一个非加粗 run 的 rPr 作基准；若无则取第一个 run。"""
    base = None
    for r in p.findall(W + "r"):
        if not is_bold(r):
            rPr = r.find(W + "rPr")
            if rPr is not None:
                base = rPr
                break
    if base is None:
        for r in p.findall(W + "r"):
            rPr = r.find(W + "rPr")
            if rPr is not None:
                base = rPr
                break
    return base


def set_bold(rPr, bold):
    for tag in ("b", "bCs"):
        e = rPr.find(W + tag)
        if e is not None:
            rPr.remove(e)
    if not bold:
        return
    b = etree.Element(W + "b")
    bcs = etree.Element(W + "bCs")
    rfonts = rPr.find(W + "rFonts")
    if rfonts is not None:
        rfonts.addnext(bcs)
        rfonts.addnext(b)
    else:
        rPr.insert(0, bcs)
        rPr.insert(0, b)


def build_run(base_rPr, text, bold):
    r = etree.Element(W + "r")
    rPr = copy.deepcopy(base_rPr) if base_rPr is not None else etree.Element(W + "rPr")
    set_bold(rPr, bold)
    r.append(rPr)
    t = etree.SubElement(r, W + "t")
    t.text = text
    if text != text.strip():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def rewrite_paragraph(p, newtext):
    base = pick_base_rPr(p)
    for r in p.findall(W + "r"):
        p.remove(r)
    if not newtext.strip():
        return
    for text, bold in parse_segments(newtext):
        p.append(build_run(base, text, bold))


def apply_edits(tb, para_map):
    paras = tb.findall(W + "p")
    for idx, newtext in para_map.items():
        if idx < len(paras):
            rewrite_paragraph(paras[idx], newtext)


def classify(txt):
    for key, (kw, _) in RULE_KEYWORDS.items():
        if kw in txt:
            return key
    return None


def main():
    shutil.copy(SRC, "_backup_" + SRC)
    with zipfile.ZipFile(SRC) as zin:
        with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                data = zin.read(item)
                if item == "word/document.xml":
                    tree = etree.fromstring(data)
                    applied = {}
                    for tb in tree.iter(W + "txbxContent"):
                        txt = "".join(t.text or "" for t in tb.iter(W + "t"))
                        key = classify(txt)
                        if key is None:
                            continue
                        para_map = RULE_KEYWORDS[key][1]
                        apply_edits(tb, para_map)
                        applied[key] = applied.get(key, 0) + 1
                    data = etree.tostring(tree, xml_declaration=True,
                                          encoding="UTF-8", standalone=True)
                    print("已改写文本框数量:", applied)
                zout.writestr(item, data)
    print("已生成:", DST)


if __name__ == "__main__":
    main()
