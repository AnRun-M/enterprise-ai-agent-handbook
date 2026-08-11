# TASK-0031：Agent & Workflow Patterns Scope Planning（长期规划 Backlog）

## 元信息

| 字段 | 值 |
|---|---|
| Status | proposed |
| Owner | AnRun-M |
| Created | 2026-08-11 |
| Updated | 2026-08-11 |
| Related ADR | ADR-0001 / ADR-0003（LangGraph 是核心实践框架但不是唯一主题） |
| Related Task | TASK-0029（T01-T12 Execution Planning）、TASK-0030（T05 首个 implementation task） |
| Related Chapter | Chapter 08-18（Runtime 已冻结，本规划只引用） |

## 定位

**这是 Scope Planning，不是正文，不是 Chapter。** 在当前 T01-T12 Execution Planning 之外登记的未来版本长期规划 Backlog：

- 属于**未来版本（v0.6.0+）**
- **不属于当前 v0.5.0**，不影响当前 T01-T12
- 不修改 Runtime Handbook / Part 03 / Part 04
- 不启动任何 Pattern 教学；不写任何 Chapter

**固定原则（所有 Pattern 必须遵守）**：

> **Runtime-first，Framework-second。** 每个 Pattern 是"一种 Runtime Workflow Pattern，LangGraph 可以表达，但 Pattern 不属于 LangGraph"——不是"这是 LangGraph Router / 这是 LangGraph Map-Reduce"。

**引用规则**：允许引用 Chapter 08-18；**不得重新定义** State / Node / Edge / Reducer / Command / Send / Checkpoint / Interrupt / Stream / Subgraph / StateGraph（全部引用已有章节）。

---

## 一、Pattern 清单（14 项，统一模板）

模板字段：Pattern Name / Problem Solved / Runtime Concept Reused（引用已有 Chapter）/ Boundary / Not Covered / Potential Demo / Review Focus。

### 1. ReAct Pattern
- **Problem Solved**：Reason + Act 交替——模型在"推理"与"工具动作"之间循环，直到获得足够事实
- **Runtime Concept Reused**：Observe → Decide → Act → Update State 四阶段回路（ch01）；Node 执行单元（ch10）；State 携带中间推理（ch02）；Context 组装（ch03）
- **Boundary**：循环控制属 Runtime（ch01 1.4）；模型在 Decide 中做开放式推理，工具在 Act 中调用
- **Not Covered**：工具安全与权限（Part 05 / 策略层）、推理上下文预算（Part 05）
- **Potential Demo**：Text-to-SQL 的"先检索元数据 → 再生成 SQL"循环的教学变体
- **Review Focus**：是否把 ReAct 写成框架概念（应 Runtime-first）；循环归属是否清晰

### 2. Router Pattern
- **Problem Solved**：把请求路由到不同的能力 / 流程分支（单一入口多出口）
- **Runtime Concept Reused**：Conditional Edge / routing callable（ch11）；模型决策写入 State 后由确定性路由分发（ch11 11.5）；Route Decision 纯函数化（ch06 6.9）
- **Boundary**：路由只分发不决策（ch11：模型决定做什么、路由决定把控制权交给谁）
- **Not Covered**：引擎路由的具体工程实现（T08，Part 04）
- **Potential Demo**：意图识别后路由到"可回答 / 需澄清 / 拒绝"三分支
- **Review Focus**：是否写成"LangGraph Router"（应 Runtime 路由语义）；路由是否替代模型决策

### 3. Sequential Workflow Pattern
- **Problem Solved**：固定顺序的确定性流水线（每步输出进入下一步输入）
- **Runtime Concept Reused**：Edge（确定性连接，ch11 11.2）；State Update → Reducer → Merged State（ch12）；compile / invoke（ch18）
- **Boundary**：无循环、无运行时路由；连接在构图时声明
- **Not Covered**：动态控制流（Command / Send，ch13）
- **Potential Demo**：canonical T01→T02→T04→T05 的固定前置流水线段
- **Review Focus**：是否把"顺序执行"写成框架专属（应通用 Runtime 语义）

### 4. StateGraph Workflow Pattern
- **Problem Solved**：显式声明状态 + 控制流的工作流（图式结构）
- **Runtime Concept Reused**：Graph State（ch09）；Node / Edge / Conditional Edge（ch10-11）；compile / invoke / stream（ch18）
- **Boundary**：Pattern = 用图结构组织确定性 + 模型步骤；不是 StateGraph API 教程
- **Not Covered**：StateGraph API 参数面（ch18 语义边界）
- **Potential Demo**：Text-to-SQL 全流程的图式组织（Part 04 T01-T12 落地后的教学视图）
- **Review Focus**：是否退化为 API 教程（应 Runtime-first 结构组织）

### 5. Planner-Executor Pattern
- **Problem Solved**：先规划（分解步骤）再执行（逐步骤执行）
- **Runtime Concept Reused**：模型决策（Decide，ch01）；work item（ch06 6.2）；动态展开（Send，ch13 13.4——仅引用）
- **Boundary**：计划是 State 中的控制信息；执行步骤由 Runtime 调度
- **Not Covered**：计划质量评估 / 计划修正（未来扩展）
- **Potential Demo**：多引擎查询计划（先规划引擎顺序再逐个执行）
- **Review Focus**：是否把 Planner 写成独立 Agent（应同一 Runtime 内的决策 + 执行）

### 6. Reflection Pattern
- **Problem Solved**：产出后自我评估并迭代修正（生成 → 评价 → 改进）
- **Runtime Concept Reused**：Loop 回路（ch01 / ch11 条件边回路）；质量门（canonical T10 语义）；State 携带评估结果（ch02）
- **Boundary**：评估是模型决策（开放式）；迭代终止由确定性守卫保证
- **Not Covered**：评估指标定义（Part 05 Evaluation）
- **Potential Demo**：SQL 生成后质量自评（对 canonical T10 的教学扩展）
- **Review Focus**：是否让模型拥有终止权（应确定性终止）

### 7. Retry Pattern
- **Problem Solved**：瞬时失败重放同一动作
- **Runtime Concept Reused**：Retry ≠ Loop（ch01 1.6：重放同一动作 vs 重新决策）；Error Boundary（ch10 10.7）；节点级错误转换
- **Boundary**：重试是确定性策略层 / 生产语义（Part 05 / v0.6.0），非图原语自动提供
- **Not Covered**：退避 / 幂等 / 补偿（Part 05）
- **Potential Demo**：工具调用瞬时失败重试的教学实现（Part 05 前不做）
- **Review Focus**：是否把 Retry 写成框架内置（应策略层职责）

### 8. Human-in-the-loop Pattern
- **Problem Solved**：关键步骤暂停等待人工确认 / 修改 / 拒绝
- **Runtime Concept Reused**：Human Stop 暂停态（ch01 1.5）；Interrupt 协议（ch15）；Checkpoint 承载（ch14）；Command resume（ch15 15.4 引用）
- **Boundary**：Pattern = 暂停 → 交还 → 恢复；生产 HITL（审批流程 / 超时 / 审计）属 Part 05
- **Not Covered**：审批 UI / 通道、审批策略（Part 05）
- **Potential Demo**：canonical T07 人工审批挂载点（ch15 已立边界）
- **Review Focus**：是否提前实现生产 HITL（应只表达暂停恢复语义）

### 9. Map-Reduce Pattern
- **Problem Solved**：按数据分片并行处理并归并结果
- **Runtime Concept Reused**：Send（动态 fan-out，ch13 13.4）；Reducer / channel 合并（ch12）；Subgraph 组合（ch17 17.5 仅引用）
- **Boundary**：Send 描述 work items；Graph Runtime 实例化调度；归并依赖 channel 语义
- **Not Covered**：并行调度确定性 / fan-in 合并验证（ch13 13.9 未验证清单）
- **Potential Demo**：多表 / 多引擎批处理查询（教学，并行语义不承诺）
- **Review Focus**：是否把 Send 写成框架专属（应 Runtime work-item 语义）；是否宣称未验证的并行保证

### 10. Supervisor Pattern
- **Problem Solved**：一个协调者委托任务给多个执行者并汇总
- **Runtime Concept Reused**：Scheduler 编排语义（ch06 6.5-6.6）；Dispatch（ch06）；模型决策（ch01）
- **Boundary**：协调者是同 Runtime 内的控制结构；"多 Agent"须满足第 0 章五要素判据
- **Not Covered**：跨 Agent 协作（A2A，Part 06）；独立部署边界
- **Potential Demo**：Text-to-SQL 主流程 + 工具子任务的委托教学
- **Review Focus**：是否把函数调用写成多 Agent（AGENTS.md 禁止）；是否提前进入 Part 06

### 11. Multi-Agent Pattern
- **Problem Solved**：多个自主执行主体协作完成目标
- **Runtime Concept Reused**：Agent 定义（ch00 0.3 五要素）；独立 Loop 与决策权（ch01）；A2A 协作（Part 06 引用）
- **Boundary**：多 Agent 需要各自拥有 Loop / 决策权 / 能力；不是多函数
- **Not Covered**：A2A 协议（Part 06）；跨 Agent 状态共享
- **Potential Demo**：需 A2A 支持后（Part 06），本 Backlog 仅登记方向
- **Review Focus**：是否把多个函数简单称为多 Agent（AGENTS.md 明令禁止）

### 12. Hierarchical Agent Pattern
- **Problem Solved**：层级结构——上层 Agent 分解任务，下层 Agent 执行
- **Runtime Concept Reused**：Subgraph 组合（ch17 17.2）；模块化编排（ch06 6.6）；父图调用子图（ch17 17.3）
- **Boundary**：层级是控制流组合（Subgraph）或执行主体层级（多 Agent），须分清
- **Not Covered**：独立 Agent 的部署与治理边界
- **Potential Demo**：校验-修复回路抽成子图复用（basic_langgraph README 第 19 节扩展方向）
- **Review Focus**：是否把 Subgraph 写成独立 Agent（ch17 17.6 边界）；是否混淆组合与协作

### 13. Evaluator-Optimizer Pattern
- **Problem Solved**：模型输出如何自动评估、自动改进、形成评价闭环（Generate → Evaluate → Improve → Repeat）
- **Runtime Concept Reused**：Node（ch10，生成与评估执行单元）；State（ch02，候选与评估结果载体）；Conditional Edge（ch11，评估通过/不通过路由）；Loop 回路（ch01 / ch11）；Checkpoint（ch14，评价循环的可恢复持久化——仅挂载点）
- **Boundary**：属于 **Runtime Pattern**——评估是模型决策（开放式），迭代终止由确定性守卫保证；**不是 LLM-as-a-Judge API**；**不讲 OpenAI Judge / Claude Judge / 任何具体模型**
- **Not Covered**：评估指标定义（Part 05 Evaluation）；供应商 Judge 服务
- **Potential Demo**：Generate → Evaluate → Improve → Repeat（质量门教学闭环，对齐 canonical T10 语义）
- **Review Focus**：是否写成"模型评测 API"（应 Runtime 评价闭环）；是否让模型拥有终止权（应确定性终止）

### 14. Tool Calling Pattern
- **Problem Solved**：Agent 如何选择 Tool、调用 Tool、消费 Tool Result、继续推理（Reason → Select Tool → Invoke Tool → Receive Result → Continue Reasoning）
- **Runtime Concept Reused**：Node（ch10，工具调用执行单元）；State（ch02，Tool Result 控制信息入 State）；Tool（ch05 Tool Registry 语义）；Conditional Edge（ch11，按结果继续 / 重试 / 终止路由）；Command（ch13，携带更新与路由意图——仅引用）
- **Boundary**：讨论 **Tool Selection Runtime Pattern**——工具选择是模型决策、工具调用经注册能力（ch05）；**不讨论 OpenAI Function Calling / Claude Tool Use / Google Function Calling / MCP**（供应商与协议层，MCP 属 Part 06）
- **Not Covered**：工具安全与权限（策略层 / Part 05）；MCP 协议接入（Part 06）
- **Potential Demo**：Text-to-SQL 中 decide → 调用 Validator / Executor → 消费结果继续推理的教学循环
- **Review Focus**：是否写成供应商 API 教程（应 Runtime 语义）；工具调用职责是否落对层（模型选 / Registry 管 / Runtime 调）

---

## 二、Patterns 分类

| 分类 | Patterns |
|---|---|
| **Execution Patterns**（执行形态） | ReAct / Sequential Workflow / StateGraph Workflow / Reflection |
| **Coordination Patterns**（协调形态） | Router / Map-Reduce / Supervisor / Multi-Agent / Hierarchical Agent |
| **Human Interaction Patterns**（人机交互） | Human-in-the-loop |
| **Recovery Patterns**（恢复形态） | Retry |
| **Planning Patterns**（规划形态） | Planner-Executor |
| **Evaluation Patterns**（评价形态） | Evaluator-Optimizer |
| **Tool Interaction Patterns**（工具交互形态） | Tool Calling |

> 分类是登记性的候选组织方式，不是章节规划——具体章节承载在 v0.6.0+ Scope Planning 阶段决定（可跨类合并 / 调整）。

---

## 二·五、Pattern Taxonomy（唯一组织方式）

**未来任何新增 Pattern，必须先归入七大分类之一**：Execution / Coordination / Planning / Recovery / Human Interaction / Evaluation / Tool Interaction。**不得新增孤立 Pattern**（不在 Taxonomy 中的 Pattern 不得进入 Backlog）。

**Pattern Taxonomy 是未来所有 Agent Pattern 的唯一组织方式**——新增候选必须先回答"归入哪类"；分类调整需显式说明（如跨类合并 / 拆分），不得静默新增类别。

**固定表述（所有 Pattern 必须遵守）：**

> **Pattern 不是 Framework Feature。LangGraph、OpenAI Agents SDK、Google ADK、CrewAI、AutoGen、Claude 都只是 Pattern 的一种实现——Pattern 属于 Runtime，不属于任何框架。**

（Runtime-first / Framework-second 由此推广到全框架：任何 Pattern 的讲解先给 Runtime 语义，再说明各框架如何承载。）

---

## 三、Roadmap 建议（Planning）

- **当前（v0.5.0）**：专注 **Text-to-SQL Runtime Refactor**（T01-T12 按 Recommended Implementation Waves 推进；当前 Wave 1 进行中：T05 已完成，T01 / T03 优先）
- **完成 v0.5.0 之后**：才进入 **Agent Workflow Patterns**（v0.6.0+ 候选）
- **不提前启动**：本 Backlog 只登记方向，不进入 ROADMAP / content-map / mkdocs；不创建 TASK 正式执行文件（本文件为 proposed 登记）

**为什么不属于当前 v0.5.0**：v0.5.0 的唯一目标是 Text-to-SQL 全流程落地（canonical T01-T12 按需使用 StateGraph API）；Agent & Workflow Patterns 是独立的知识主题，与 T01-T12 无依赖关系，提前启动会分散当前重构主线。
**为什么放到 v0.6.0+**：v0.6.0 里程碑定位为生产级能力（Checkpoint / HITL / Retry / Observability 等）——其中 HITL（Human-in-the-loop）、Retry、Map-Reduce（并行治理）等 Pattern 与生产能力强相关，待生产语义建立后再系统讲解更顺；且 v0.5.0 的图式重构（StateGraph Workflow）是多数 Pattern 的演示基础。

---

## 四、约束与禁止

- 不修改任何 Chapter / ROADMAP / content-map / examples / tests / ADR / principles / architecture-map / references / Runtime Handbook
- 不创建 Chapter；不启动正文；不引入 LangGraph 专有表述（Runtime-first）
- 不重新定义冻结语义（ch08-18 只引用）
- 当前执行计划不变（T01-T12 继续按 Waves 推进）

## 验收标准

- [x] 14 个 Pattern 统一模板（7 字段）完整登记
- [x] 分类一节（**七大分类**：Execution / Coordination / Planning / Recovery / Human Interaction / Evaluation / Tool Interaction）
- [x] **Pattern Taxonomy 节**（唯一组织方式；未来新增 Pattern 必须先归入；不得新增孤立 Pattern；"Pattern 不是 Framework Feature——LangGraph / OpenAI Agents SDK / Google ADK / CrewAI / AutoGen / Claude 都只是 Pattern 的一种实现"）
- [x] Roadmap 建议（v0.5.0 完成后才进入 Agent Workflow Patterns，不提前启动）
- [x] Runtime-first / Framework-second（无"这是 LangGraph X"表述；Pattern 13/14 明确不讨论供应商 Judge / Function Calling API）
- [x] 只引用 ch08-18，不重新定义任何冻结语义
- [x] Status = proposed（非 in_progress）；不创建 PR 描述；不启动正文
- [ ] 等待后续确认（是否纳入未来版本规划）

## 完成记录

- 2026-08-11：任务创建（proposed 登记）；12 Patterns 模板 + 分类 + Roadmap 建议完成；仅修改本文件与 current.md。
- 2026-08-11：**Pattern Universe 扩展**：新增 Pattern 13（Evaluator-Optimizer——评价闭环，Boundary 明确非 LLM-as-a-Judge API / 不讲供应商 Judge）与 Pattern 14（Tool Calling——Tool Selection Runtime Pattern，不讨论 OpenAI Function Calling / Claude Tool Use / Google Function Calling / MCP）；新增 **Evaluation Patterns** 与 **Tool Interaction Patterns** 两个分类（共七大分类）；新增 **Pattern Taxonomy 节**（未来所有 Agent Pattern 的唯一组织方式，新增必须归入七类，不得孤立；固定表述"Pattern 不是 Framework Feature——各框架都只是 Pattern 的一种实现"）。
