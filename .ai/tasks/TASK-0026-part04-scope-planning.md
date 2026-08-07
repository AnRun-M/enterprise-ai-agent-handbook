# TASK-0026：Part 04 Scope Planning（StateGraph API 承载方式决策）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-07 |
| Updated | 2026-08-07 |
| Related ADR | ADR-0001 / ADR-0002 / ADR-0003 / ADR-0004 / ADR-0005 |
| Related Chapter | Part 03 全部（Chapter 08-17）、ROADMAP v0.5.0（Text-to-SQL 重构）、canonical-pipeline（T01-T12） |
| Related Example | examples/basic_langgraph（StateGraph 最小 API 使用）、examples/text2sql_state、examples/sql_validation |

## 定位

Part 03 收官后、Part 04 正文启动前的范围决策任务。**不写正文**，只回答一个问题：

> **StateGraph API 应该作为独立桥接章节、Part 04 前置章节，还是直接融入 Text-to-SQL 重构中的实现切面？**

范围决策定下来之后，才进入 Part 04 正文（ROADMAP / content-map / current.md 的更新在决策确认后执行）。

## 一、现状盘点

### StateGraph API 在 Part 03 的位置（最小角色引用，非系统讲解）

`examples/basic_langgraph/graph.py` 实际使用的 StateGraph 最小 API：
- `StateGraph(GraphState)`（schema 绑定图，ch09 9.2）
- `add_node` / `add_edge` / `add_conditional_edges`（节点注册 / 静态边 / 条件边，ch10-11）
- `START` / `END`（图结构哨兵，ch09 9.6 / ch11 11.8）
- `compile()` 产出可执行图、`.invoke(state)` 执行入口（**ch09/ch10/ch11 反复声明"执行机制属 Graph Runtime 执行路径，本章不展开"**）

### Part 03 留下的教学承诺（未兑现的挂载点）

- ch09 9.5 / ch10 8.8 / ch11：`compile()` / `.invoke()` 的图执行机制——"Graph Runtime 执行路径（第 11 章执行路径引出，本章不展开）"
- Part 03 Ending（ch17）：“下一部分将进入 StateGraph API 与框架实现层，而不是重新定义这些运行时概念”（**待维护表述**，Release Audit 已记录，见 TASK-0025）

### ROADMAP v0.5.0（Part 04 现状规划）

Text-to-SQL 重构：Text2SQLState / 意图识别 / 元数据检索 / 业务规则检索 / SQL 生成 / SQL 校验 / 权限检查 / 引擎路由 / SQL 修复循环 / Python 分析 / 结构化输出——对应 canonical T01-T12。

### 约束原则

- **ADR-0001**：先讲设计动机和架构边界，再讲 API——**禁止退化为 API 教程**
- **ADR-0002**：Text-to-SQL 是唯一贯穿主案例——每个抽象回到真实业务
- **ADR-0003**：LangGraph 是核心实践框架但不是唯一主题——框架能力按需引入，不按 API 罗列
- **写作节奏决策（用户 2026-08-01）**：让读者把 LangGraph 视为 Runtime 思想的一种实现
- **AGENTS.md 写作规范**：每章优先"从现有 Text-to-SQL 系统出发 → 不使用框架时如何实现 → LangGraph 如何抽象"

## 二、三个选项分析

### 选项 1：独立桥接章节（StateGraph API 桥接章，位于 Part 03 与 Part 04 之间）

- **优点**：最贴近 Part 03 Ending 字面（"下一部分将进入 StateGraph API 与框架实现层"）；集中兑现 compile/invoke 执行模型的边界承诺；读者有"完整 API 概览"的落点
- **缺点**：最易退化为 API 教程（违反 ADR-0001）；与 Part 03 语义章有重叠风险；新增独立章节与 v1.0.0"12-16 核心章节"目标（现有 18 章）冲突；与"框架不是主线"的立场张力最大
- **判定**：作为独立"Part"或独立章节组的成本高、收益主要是"API 概览"——与本书"按需引入"原则冲突

### 选项 2：Part 04 前置章节（作为 Text-to-SQL 重构的第一章）

- **优点**：**兑现 Part 03 的 compile/invoke 边界承诺**（教学完整性——Part 03 各章反复声明"执行路径留待引出"，需要一个集中落点）；为 T01-T12 重构提供"图构建基础"（StateGraph 构图 + Graph Runtime 执行模型），后续重构章节**按需使用 API**（融合选项 3 的执行方式，不重复罗列）；不新增 Part、不造成章节数膨胀（相对选项 1）；与 Part 03 Ending 方向一致（"StateGraph API 与框架实现层"具体化为"StateGraph 构图与 Graph Runtime 执行模型"）
- **缺点**：仍需严防 API 教程化——前置章的讲解必须挂在"手写 Runtime 如何组织图"与"重构需要什么"的动机上（ADR-0001）；前置章内容需与 ch10/ch11 的边界声明划清（不重讲 Node/Edge 语义，只讲"如何组装 + 如何执行"）
- **判定**：**推荐**——它是唯一同时满足"兑现教学承诺"与"不新增 Part/不 API 罗列"的选项

### 选项 3：完全融入 Text-to-SQL 重构的实现切面（不设独立章）

- **优点**：最彻底符合 ADR-0001/0002/0003（按需引入、回到业务）；T01-T12 重构时在"引擎路由""SQL 修复循环"等处自然出现 add_conditional_edges 等 API 的工程用法；写作规范第 3/4 条（手写→框架）天然承载
- **缺点**：**compile/invoke 执行模型没有集中落点**——Part 03 各章的"执行路径留待引出"承诺无法兑现处；读者缺少"图如何被组装和执行"的整体视图；API 散落在各章，无系统性
- **判定**：作为**执行方式**（后续重构章节按需引入 API）完全正确，但作为**唯一承载方式**无法兑现 Part 03 的教学承诺

## 三、推荐决策

> **选项 2 为主：Part 04 前置章节——「StateGraph 构图与 Graph Runtime 执行模型」。**
>
> 作为 Part 04（Text-to-SQL 重构）的第一章：集中兑现 Part 03 的 compile/invoke 边界承诺，讲解图如何被组装（StateGraph 构图入口）与如何被执行（Graph Runtime 执行路径）；**不重讲** Node / Edge / Reducer 语义（只引用 ch09-13）；**不罗列 API**（挂在"重构 Text-to-SQL 需要什么"的动机上，ADR-0001）。
>
> 其后的 T01-T12 重构章节采用**选项 3 的执行方式**：API 按需出现（如引擎路由处讲解条件边的工程用法），不重复前置章内容。
>
> 选项 1（独立桥接章节）不采用：新增 Part / 章节膨胀，且最易 API 教程化。

## 四、决策落地（待用户确认后执行）

- 用户确认推荐后：
  - ROADMAP：v0.5.0 增加前置章条目（draft）；Part 04 定位描述更新
  - content-map：Part 4 行更新（加前置章）
  - current.md：下一步 = Part 04 正文（前置章）
  - Chapter 17 Ending 的 maintenance task：将"下一部分将进入 StateGraph API 与框架实现层"修正为与决策一致的表述（如"下一部分将进入 StateGraph 构图与 Graph Runtime 执行模型"）
- 用户选择其他选项：按选择调整上述落地

## 验收标准

- [ ] 回答唯一问题：StateGraph API 的承载方式（三个选项 + 推荐 + 理由）
- [ ] 分析锚定仓库事实（basic_langgraph 最小 API / Part 03 边界承诺 / ROADMAP v0.5.0 / 约束原则）
- [ ] 未写正文；未改 ROADMAP / content-map / current.md（决策确认前）
- [ ] 等待用户范围决策

## 完成记录

- 2026-08-07：任务创建；三选项分析完成；推荐选项 2（Part 04 前置章节 + 选项 3 执行方式）；等待用户决策。
