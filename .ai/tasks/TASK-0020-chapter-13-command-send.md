# TASK-0020：Chapter 13《Command 与 Send——动态控制流》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 |
| Related Chapter | 第 6 章（Scheduler / work item）、第 10 章（Node）、第 11 章（Conditional Edge）、第 12 章（Reducer）；TASK-0014（Part 03 规划，ch13 定位） |
| Related Example | examples/basic_langgraph（README 第 9 节：未使用的 LangGraph 能力） |
| Related Test | 无（Demo 未使用 Command / Send，如实标注） |

## 目标

编写 Part 03 第五个原语章 `docs/03-langgraph-core/ch13-command-send.md`：回答「Conditional Edge 之外的动态控制流需求如何表达？」。**核心主线固定（用户 2026-08-05 指定，2026-08-05 复审统一为最新表述，写作不得偏离）**：Conditional Edge 根据图外定义的 routing callable，返回 Graph Runtime 可解释的一个或多个路径目标；在本章讨论的场景中，Command 允许 Node 返回结果同时携带 State Update 与 goto 路由意图；Send 由 routing callable 根据运行时数据返回，用于描述多个带独立输入的 work items，并由 Graph Runtime 解释、实例化和调度。Command 与 Send 都属于动态控制流原语：Command 解决更新与导航绑定；Send 解决按运行时数据描述动态 fan-out work items。

**两条硬边界（用户强调）**：不要把 Command 与 Send 混成同一个原语；不要把 Send 简化成普通 Conditional Edge。

## 需要新增

- `docs/03-langgraph-core/ch13-command-send.md`（13.1-13.11 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0020-chapter-13-command-send.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 13 章）
- `docs/03-langgraph-core/index.md`（第 13 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 13 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 13 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标）与**两条硬边界**，不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch06 work item 调度 / Scheduler 职责）与 Part 03 已建立语义（ch10 Node / ch11 Conditional Edge / ch12 Reducer），再讲 Command / Send 承载；禁止从 API 出发解释概念
- **Conditional Edge 多目标语义**：返回 Graph Runtime 可解释的一个或多个路径目标——当前 Demo 单路径（单个 route key）；LangGraph 通用能力可返回多个目标形成并行分支；**多目标 ≠ Send 的动态 work-item 语义**；不写"一次选一条 / 有限选一 / 控制流一定单线 / 单选 vs 多选"
- **Command（作用域收窄）**：本章特指 **Node 返回场景下的 State Update + goto 路由组合**（Node 可返回的一种 Runtime 控制结果，不是全部能力）；声明但不展开：Interrupt resume（ch15）/ Tool 返回 Command（Tool / future scope）/ parent graph navigation（ch17）/ invoke-stream 输入 Command（ch15）；与「先更新 State 再路由」= 单图场景可表达相近意图，**不宣称全面等价**（仓库未实现等价性测试）；State Update 走同一 channel 合并（ch12）
- **Send（产生链路修正）**：上游 Node 产生 State / 运行时数据 → Conditional Edge 关联的 routing callable → 返回多个 Send descriptors（每个：目标节点 + work-item-specific input）→ Graph Runtime 解释、实例化并调度；**Send 不自己执行节点、不自己创建线程**——它是 Graph Runtime 可解释的路由 / work-item 描述；典型用法是从 conditional routing function 返回 Send 列表
- **Send 独立输入语义**：每个 Send 至少表达目标节点 + 专属输入 / State；同一目标节点可实例化多次、每实例不同输入（map-reduce / batch / shard）；**核心区别 = Conditional Edge 选择一个或多个路径目标（通常共享图 State）vs Send 按数据动态实例化带独立输入的 work items**——不以"一个选一条，一个选多个"为核心边界
- **动态实例与节点定义边界**：图中 Node 定义通常仍在构建期注册；Send 动态展开的是 work item 数量、执行实例、每实例输入——不是运行时注册任意新 Node 类型；首次出现必须用严格表述"动态实例化已注册目标 Node 的多个 work items"
- **Send 与并行收窄**："Send 实现并行" → "Send 表达 fan-out；Graph Runtime 解释、实例化并调度 work items"；未自动保证：并发度 / 调度顺序 / 稳定结果顺序 / 线程安全 / 重试 / delivery semantics / fan-in 合并确定性
- **不混同 Command 与 Send**：问题不同（更新与导航绑定 vs 按数据实例化带独立输入的 work items）、作用对象不同（Node 可返回的 Runtime 控制结果 vs Graph Runtime 可解释的 work-item 描述）；可组合但先分清各自问题
- **证据诚实**：仓库无 Command / Send 实现证据——基于 `references/official/langgraph.md` 核验记录（刻意未使用）与 README 第 9 节；未验证清单如实标注（行为语义 / fan-out 合并 / 与静态路由等价性（含 Command 等价性未测试）/ 动态生命周期 / fan-out 未自动保证项 / Checkpoint-Interrupt 组合）；不推断实现行为
- **不提前展开**：Command / Send API 签名与写法（框架 API 教程超出范围）、Checkpoint（ch14）/ Interrupt（ch15）/ Stream（ch16）/ Subgraph（ch17，仅引用 map-reduce 组合方向）、生产重试 / 幂等 / 补偿（Part 05）
- **不引入 LangChain API**（一句边界）；不重新定义 Scheduler / Node / Reducer 语义
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-12、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 13.1-13.11 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持；Command / Send 不混同、Send 不简化成 Conditional Edge
- [ ] 5 张 Mermaid 图（静态路由 → 两类动态需求 / Command：State Update + 路由意图 → Graph Runtime / Send：数据 → work items → fan-out → 归并 / Command vs Send 对比 / 当前 Demo 静态图反例）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0020 Status = in_progress；ROADMAP Chapter 13 = draft / 待架构审查；content-map 第 13 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-13-command-send，commit `docs: draft chapter 13 command and send`）
- [ ] PR #37 Architecture Review 七项修正全部应用（Conditional Edge 多目标语义 / Send 产生链路 / Send 独立输入语义 / Command 作用域 / Command 等价性收窄 / 动态实例与节点定义边界 / Send 与并行收窄）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #37 创建。
- 2026-08-05：**PR #37 Architecture Review 七项修正**（commit：docs: refine command send and conditional routing boundaries）全部应用并推送更新 PR #37：
  1. **Conditional Edge 多目标语义**：改为"返回一个或多个路径目标"两层表述（当前 Demo 单路径 vs 通用能力多目标）；多目标 ≠ Send work-item 语义；删除"一次选一条 / 单线 / 单选 vs 多选"——13.1 / Mermaid / 13.4 对照 / 13.7 / Q1 / Q4 / Q5 / 误区 / 总结 / 验收标准
  2. **Send 产生链路修正**：Node 产数据 → conditional routing callable → Send descriptors（target node + 专属输入）→ Graph Runtime 解释、实例化、调度；Send 不执行节点、不创建线程——13.4 正文 / Send Mermaid / 13.5 / Q4 / Q7
  3. **Send 独立输入语义**：每 Send 表达目标节点 + 专属输入 / State；同一目标可实例化多次；核心区别 = "目标选择 vs 带独立输入的实例化"（非单选 vs 多选）——13.4 / 对照 / Q5
  4. **Command 作用域收窄**："本章中的 Command 特指 Node 返回场景下的 State Update + goto 路由组合"；声明不展开：Interrupt resume / Tool return / parent graph navigation / invoke-stream 输入——13.2 / 13.3 / 13.7 / Q2 / Q3 / 本章边界
  5. **Command 等价性收窄**："同一意图" → "单图 Node update + goto 场景可表达相近意图；表达位置 / 耦合方式 / 扩展能力不同；不宣称全面等价；仓库未实现等价性测试"——13.3 / Q3 / 13.9
  6. **动态实例与节点定义边界**："动态创建执行单元" → "动态实例化已注册目标 Node 的多个 work items"（首次严格表述）；Send 不注册新 Node 类型——13.4 / 13.5 / 13.7
  7. **Send 与并行收窄**："Send 表达 fan-out；Graph Runtime 解释、实例化并调度"；未自动保证并发度 / 调度顺序 / 稳定结果顺序 / 线程安全 / 重试 / delivery semantics / fan-in 确定性（加入未验证清单）——13.4 / 13.5 / 13.9 / 误区 #4
