# 求职辅助 Skill 使用说明

> 面向**技术岗求职**整理的一套 Claude Code 求职 Skill，覆盖简历撰写、STAR 法则、岗位技能分析、岗位背景定制、模拟面试问答、求职信、薪资谈判、职位搜索等完整链路。本说明基于 2026-08-03 安装的版本编写。

---

## 一、安装概览

| 项 | 位置 |
|----|------|
| Skill 安装目录 | `C:\Users\cz\.claude\skills\`（已激活） |
| 源码下载目录 | `C:\Users\cz\job-skills\` |
| resumePolice 提示词 | `C:\Users\cz\job-skills\resumePolice\`（非 skill，手动使用） |

**已安装 28 个求职 Skill**，按来源分：

- **ResumeSkills**（22 个，英文）：功能最全，简历优化 / JD 分析 / 辅助材料 / 面试谈判
- **resume-grill**（1 个，中文）：对抗性模拟面试、简历拷打
- **get-job**（1 个，中文）：岗位调研 → 改简历 → 面试准备全流程
- **job-search-skills**（4 个，英文）：职位爬取、申请表填写、内推人脉查找

> 另有 resumePolice（简历警察）为**中文提示词 + Dify 工作流**，不占用 skill 目录，用法见第四节。

---

## ⚠️ 使用前需注意（必读）

1. **job-search-skills 必须配置后才能用**：将 `C:\Users\cz\job-skills\job-search-skills\config.yaml.example` 复制为 `config.yaml`（放入对应 skill 目录，如 `~/.claude/skills/job-analyzer/config.yaml`），填入你的简历路径、求职偏好、LinkedIn 账号等信息。**未配置时** `job-analyzer` / `job-crawler` / `job-form-filler` / `network-finder` 无法正常工作。详见 5.1。
2. **其余 24 个 skill 无需配置**，安装后即可直接触发使用（`resume-grill` 仅需本机有 Python 3 + Node 环境）。
3. **快速上手**：无需记忆技能名，直接对 Claude 用自然语言触发即可——
   - 「帮我按这个 JD 改简历」→ 触发 `get-job` / `resume-tailor` / `tech-resume-optimizer`
   - 「拷打这份简历」/「面试前帮我全面自查」→ 触发 `resume-grill`
   - 「帮我分析这个岗位 JD」→ 触发 `job-description-analyzer` / `job-analyzer`
   - 「为这个岗位写封求职信」→ 触发 `cover-letter-generator`

---

## 二、推荐工作流（按求职阶段）

求职是一条链路：**先搞清岗位要什么 → 才知道简历往哪改 → 简历定了 → 才知道面试拆哪些雷**。

### 阶段 1：找岗位 & 分析 JD
| 目的 | 用哪个 Skill | 触发示例 |
|------|------------|---------|
| 爬取某公司招聘页、找最适合我的岗位 | `job-crawler` | "看看 palantir careers 有什么岗位适合我" |
| 分析单个岗位 JD、评估匹配度 | `job-analyzer` / `job-description-analyzer` | "帮我分析这个 JD，我匹配吗" |
| 深度调研公司/岗位/面经/隐性门槛 | `get-job` | "帮我调研字节后端岗位，我要投递" |

### 阶段 2：改简历（核心）
| 目的 | 用哪个 Skill | 触发示例 |
|------|------------|---------|
| 全流程改简历（定位+STAR/CAR 改写+迁移翻译，产出 docx） | `get-job` | "按这个 JD 帮我改简历" |
| 针对岗位定制、关键词整合 | `resume-tailor` | "把简历定制到匹配这个岗位" |
| 技术岗简历专项（技术栈/项目/GitHub） | `tech-resume-optimizer` | "优化我的技术简历" |
| 弱 bullet 改写为成就化描述 | `resume-bullet-writer` | "帮我改这条工作描述" |
| 补量化指标 | `resume-quantifier` | "这条经历怎么量化" |
| ATS 兼容检查 / 排版 | `resume-ats-optimizer` / `resume-formatter` | "检查简历 ATS 兼容性" |
| 简历深度体检（批判-解析-建议） | resumePolice 提示词 | "用简历警察提示词审我的简历" |

### 阶段 3：投递 & 辅助材料
| 目的 | 用哪个 Skill | 触发示例 |
|------|------------|---------|
| 求职信 | `cover-letter-generator` | "为这个岗位写封求职信" |
| 冷邮件 / 主动联系 | `cold-email-writer` | "给这个 HR 写封冷邮件" |
| 自动填申请表（不自动提交） | `application-form-filler` / `job-form-filler` | "帮我把这个申请表填了" |
| 找内推人脉 | `network-finder` | "帮我找这个公司的内推" |
| LinkedIn 优化 | `linkedin-profile-optimizer` | "优化我的 LinkedIn 主页" |

### 阶段 4：面试准备（核心）
| 目的 | 用哪个 Skill | 触发示例 |
|------|------------|---------|
| 分轮次面试准备（逐 bullet 深挖/自我介绍/模拟面试/面后复盘） | `get-job` | "帮我准备这个岗位的面试" |
| STAR 故事库 + 常见面试题 | `interview-prep-generator` | "把简历经历做成 STAR 故事" |
| 对抗性简历拷打（攻防卡片/评分卡，面试前自查） | `resume-grill` | "拷打这份简历" / "面试前帮我全面自查" |

### 阶段 5：谈薪 & 决策
| 目的 | 用哪个 Skill | 触发示例 |
|------|------------|---------|
| 薪资谈判策略 | `salary-negotiation-prep` | "帮我准备薪资谈判" |
| 多 offer 对比 | `offer-comparison-analyzer` | "对比这两个 offer" |

---

## 三、各 Skill 详细说明

### 3.1 简历撰写与优化（ResumeSkills）

| Skill | 功能 | 备注 |
|-------|------|------|
| `resume-bullet-writer` | 把弱描述改写为成就化陈述 | 动词开头 + 量化结果 |
| `resume-quantifier` | 找机会补量化数字，缺数据时给估算 | 可给估算但标注 |
| `resume-formatter` | ATS 友好排版、可扫读布局 | |
| `resume-section-builder` | 按经验层级/岗位建简历分节 | |
| `resume-ats-optimizer` | ATS 兼容检查、关键词匹配分析 | |
| `resume-version-manager` | 维护母版简历 + 各岗位版本管理 | 命名规范 |
| `tech-resume-optimizer` | **技术岗专项**：技能栈组织、项目呈现、GitHub 优化、SWE/数据/DevOps bullet 公式 | 技术岗首选 |
| `executive-resume-writer` | 高管/VP 简历，强调战略领导力 | 资深可选 |
| `academic-cv-builder` | 学术 CV（论文/基金/教学） | 学术岗可选 |
| `creative-portfolio-resume` | 创意岗简历，视觉与 ATS 平衡 | 非技术岗 |
| `career-changer-translator` | 转行能力翻译、识别可迁移技能 | 转行可选 |

### 3.2 岗位分析（ResumeSkills + job-search-skills）

| Skill | 功能 |
|-------|------|
| `job-description-analyzer` | 拆解 JD（必选/加分项）、算 match score、差距分析、红旗检测、生成投递策略 |
| `job-analyzer` | 对照简历+成就库分析 JD，产出定制建议、intro、公司调研、匹配评估 |
| `job-crawler` | 爬公司 careers 页找开放岗位，按你的简历给 Top 3 匹配岗位 |
| `network-finder` | 基于 LinkedIn 找内推路径 |

### 3.3 岗位背景定制（ResumeSkills + get-job）

| Skill | 功能 |
|-------|------|
| `resume-tailor` | 针对具体岗位定制：摘要改写、技能重排、bullet 调整、关键词整合（不造假） |
| `get-job` | 目标岗位反向定位 + 迁移翻译：把真实背景翻译成岗位语言，产出 `改后简历.docx` |

### 3.4 模拟面试问答

| Skill | 功能 | 特点 |
|-------|------|------|
| `get-job` | 按真实轮次准备面试，逐 bullet 深挖、项目逐字稿、自我介绍、表达训练、模拟面试、反问清单 | 中文，含面后复盘题库 |
| `resume-grill` | **对抗性技术面试**：从简历真实项目起手，L1 项目切入→L2 设计决策→L3 硬核验伪，产出面试指南+可打印评分卡+攻防卡片（答案折叠自测） | 中文/英文自动跟随简历；支持 30/60/90 分钟档位与 ultra 全面审查模式 |
| `interview-prep-generator` | 生成 STAR 故事库、预测面试题、准备 talking points | 英文，含常见行为题 |

### 3.5 求职信 / 谈判 / 辅助（ResumeSkills）

| Skill | 功能 |
|-------|------|
| `cover-letter-generator` | 从简历+JD 生成个性化求职信 |
| `cold-email-writer` | 给招聘经理/创始人的个性化冷邮件 |
| `salary-negotiation-prep` | 调研市场行情、构建谈判策略、反报价话术 |
| `offer-comparison-analyzer` | 多 offer 并排比较、总薪酬分析 |
| `linkedin-profile-optimizer` | 简历与 LinkedIn 同步、可搜索性优化 |
| `portfolio-case-study-writer` | 简历 bullet → 完整案例研究 |
| `reference-list-builder` | 推荐人格式与材料 |
| `application-form-filler` | 用简历+JD 智能填表（不提交） |
| `job-form-filler` | 自动填 Lever/Greenhouse/Ashby/Workday 等表格（不提交） |

---

## 四、resumePolice（简历警察）使用说明

**位置**：`C:\Users\cz\job-skills\resumePolice\`

它是**中文提示词**（非 skill），可直接复制给任意大模型使用；也提供 **Dify 工作流**。

### 提示词文件（`prompt/` 目录）
| 文件 | 用途 |
|------|------|
| `resume_police_Zh.md` | **核心**：简历全面审查与修改（批判-解析-建议模型、技术审判官、影响力量化引导） |
| `question_v1_Zh.md` | 面试官视角 V1：传奇 CTO 人设，四步勘探法 + P.O.S.E.R. 模型，生成带陷阱的深度技术面试题（含参考答案/评分/追问） |
| `question_v2_Zh.md` | 面试官视角 V2：三步勘探法，风格更直接，产出精简面试题清单 |

### Dify 工作流（`workflow/` 目录）
| 文件 | 用途 |
|------|------|
| `简历警察V3.yml` | **推荐**：最新最稳定的文本生成工作流 |
| `简历警察Chat.yml` | 多轮对话式，支持追问修改 |
| `大厂产研简历优化教练-C-Level.yml` | 分 4 步、多模型独立处理 |

**使用方法**：Dify 平台新建应用 → 导入 DSL 文件 → 配置模型（README 以 Gemini 为例）。

> ⚠️ 注意：`resume_police_Zh.md` 内硬编码了"当前时间 2025-07-27"，使用时可让模型按实际日期判断简历时间线。

---

## 五、需要配置的项

### 5.1 job-search-skills（⚠️ 使用前必做）
> **不配置就无法工作。** 以下 4 个 skill 依赖 `config.yaml` 中的简历路径与偏好：`job-analyzer` / `job-crawler` / `job-form-filler` / `network-finder`

操作步骤：
1. 找到模板：`C:\Users\cz\job-skills\job-search-skills\config.yaml.example`
2. 复制为 `config.yaml`，放入对应 skill 目录（如 `~/.claude/skills/job-analyzer/config.yaml`）
3. 填入：用户简历路径、求职偏好、LinkedIn 账号等

### 5.2 get-job（需提供输入）
开工前先做"输入体检"，需至少明确：目标岗位 + 现有简历（JD 可后补，skill 会自动 WebSearch 官方招聘页补全）。

### 5.3 resume-grill（依赖脚本）
拷打流程用到 `python scripts/extract_pdf.py` / `analyze.js` / `render.py`，需要本机有 Python 3 + Node 环境；已在安装时复制到 `~/.claude/skills/resume-grill/`。

---

## 六、使用注意事项

1. **诚实底线**：所有 skill 都遵守"翻译 ≠ 造假"——可把真实经历换角度讲，**不编造**经历、指标、职位名。背调硬信息（学历/在职时间/职位名）不可改动。
2. **自动提交红线**：`application-form-filler` / `job-form-filler` 只填表**不点提交**，最终提交需本人检查后手动操作。
3. **中文优先**：`get-job`、`resume-grill`、resumePolice 为中文；ResumeSkills 与 job-search-skills 为英文，但可直接用中文向 Claude 提问，Claude 会按中文输出。
4. **版本与维护**：ResumeSkills 有 `npx skills add` 官方安装方式；若需更新可重新拉取源码目录 `C:\Users\cz\job-skills\`。
5. **隐私**：简历含个人信息，使用 resume-grill 等上传时建议先脱敏（workspace 已 gitignore）。

---

## 七、快速上手 3 步

1. **改简历**：给 Claude 丢简历 + 目标岗位 JD，说"帮我按这个 JD 改简历"（触发 `get-job`）或"优化我的技术简历"（触发 `tech-resume-optimizer`）。
2. **面试自查**：说"拷打这份简历"（触发 `resume-grill`），产出攻防卡片逐题自测。
3. **投递辅助**：给岗位 URL，说"帮我分析这个岗位"（`job-analyzer`）→ "写封求职信"（`cover-letter-generator`）→ "帮我把申请表填了"（`job-form-filler`）。
