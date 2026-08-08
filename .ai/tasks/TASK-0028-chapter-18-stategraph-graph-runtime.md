# TASK-0028：Chapter 18《StateGraph 构图与 Graph Runtime 执行模型》（Part 04 前置章）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-08 |
| Updated | 2026-08-08 |
| Related ADR | ADR-0001 / ADR-0002 / ADR-0003 |
| Related Chapter | 第 9-17 章（Part 03 语义，只引用）；TASK-0026（Part 04 Scope Planning，冻结决策） |
| Related Example | examples/basic_langgraph（graph.py / agent.py——真实代码直接证据） |
| Related Test | tests/basic_langgraph（`test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 04 前置章 `docs/04-text2sql/ch18-stategraph-graph-runtime.md`：回答「Part 03 已建立的 Runtime 语义如何被组装成一个可执行 Graph？」。**核心主线固定（用户 2026-08-08 冻结，写作不得偏离）**：StateGraph 负责声明图结构，compile() 将图定义转换为可执行的 Graph Runtime，invoke()/stream() 通过该 Runtime 驱动 State、Node 与控制流运行；这些 API 不重新定义 Part 03 的 Runtime 语义，只负责把既有语义组装并执行。

**章节结构冻结（用户建议）**：按链式组织——**定义图 → 注册组件 → 连接控制流 → compile → invoke/stream → 与 Part 03 对照**；**不按 StateGraph.add_node/add_edge/... 方法列表排目录**（守住 Runtime-first）。

**只集中讲四件事**：① 构图入口 ② 组件注册与连接 ③ compile() 的语义边界 ④ 编译后 Runtime 的执行入口。Node / Edge / Reducer / Command / Send / Checkpoint / Interrupt / Stream 只引用 Part 03，不重新解释。

## 需要新增

- `docs/04-text2sql/ch18-stategraph-graph-runtime.md`（18.1-18.10 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0028-chapter-18-stategraph-graph-runtime.md`（本文件）

## 需要修改

- `mkdocs.yml`（Text-to-SQL 导航加入第 18 章）
- `docs/04-text2sql/index.md`（第 18 章条目）
- `docs/00-introduction/content-map.md`（新增第 18 章行，状态「实现完成 / 待架构审查」；Part 4 行更新）
- `ROADMAP.md`（v0.5.0 Chapter 18 → draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线与章节结构冻结**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：每步先引用 Part 03 语义（ch09-17），再讲组装/执行承载；禁止从 API 方法列表出发
- **只引用不重新解释**：Node（ch10）/ Edge（ch11）/ Reducer（ch12）/ Command-Send（ch13）/ Checkpoint（ch14）/ Interrupt（ch15）/ Stream（ch16）/ Subgraph（ch17）——语义解释一律回指
- **State schema 可见范围**：StateGraph(GraphState) 声明图级 State schema 与 channel 更新规则，**不等于所有 Node 读取全部字段**（更窄输入 / input-output schema / internal-private channels 属第 9 章通用能力边界，不重新展开）
- **add_node / DI 边界**：add_node = 注册 callable 并赋予图内标识（LangGraph 通用语义）；依赖组装在注册前由应用经 Node Factory / closure 完成（当前 Demo 工程选择）；链路 = Application dependency wiring → Node callable → add_node → StateGraph；**StateGraph 不是 DI Container**
- **Node-Routing 两层边界（跨章节一致）**：当前 Demo = Node 返回 Update + Conditional Edge 选路；LangGraph 通用能力 = Node 可经 Command 返回 Update + routing intent；无论哪种方式 Node 不自行执行跳转、Graph Runtime 解释并 Scheduling Execution（不得退回"所有 Node 永远只执行"）
- **compile() 职责三层**：Graph Definition（schema / Nodes / Edges-branches）→ compile（结构校验 + materialize 为 executable compiled graph + 挂载已配置 Runtime 能力）→ Compiled Graph（invoke / stream 入口）；**compile 不创造 Scheduler / Reducer / 业务 Failure Boundary**
- **invoke / stream**：都运行同一 compiled graph——invoke = aggregated execution interface（聚合返回，Interrupt / failure / cancellation 不假设成功终态）；stream = streaming execution interface（持续交付所选 Stream Mode 事件，引用 ch16）；**核心区别是结果交付协议，不是"一个执行一个旁观"**
- **动态路径边界**：静态 topology 与 routing declarations 基本完成 ≠ 运行路径唯一确定（Conditional Edge / Command / Send 的 Runtime 控制结果决定实际路径，引用 ch11/13）
- **证据分层**：代码事实（graph.py / agent.py 用法）与测试事实（`test_direct_equivalence_with_manual` 断言最终 State 关键字段 / 终止行为 / history 动作序列等观察维度等价——第 8 章已收窄口径，不宣称一般性行为等价）分开；未验证清单含 StateGraph 一般性语义 / compile 内部实现 / concurrency / side-effect ordering / stream / Checkpoint-Interrupt 组合 / delivery semantics / API 参数面
- **不提前展开**：T01-T12 业务重构（后续章节）、StateGraph API 完整参数面（API 教程超出范围）、Pregel 内部实现（超出本书范围）
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014 / TASK-0026、Chapter 08-17 正文、examples、tests、principles、ADR、references、architecture-map、Part 编号

## 验收标准

- [ ] 章节结构 18.1-18.10 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持；链式结构（定义图 → 注册 → 连接 → compile → invoke/stream → 对照）非方法列表
- [ ] 5 张 Mermaid 图（语义→组装→执行 / 链式流程 / compile 语义边界 / invoke-stream 执行入口 / 与 Part 03 对照）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0028 Status = in_progress；ROADMAP Chapter 18 = draft / 待架构审查；content-map 第 18 章 = 实现完成 / 待架构审查
- [ ] PR 创建（分支 feature/chapter-18-stategraph-graph-runtime，commit `docs: draft chapter 18 stategraph graph runtime`）
- [ ] PR #51 Architecture Review 七项修正全部应用（State schema 可见范围 / add_node-DI 边界 / Node-Routing 两层 / compile 职责三层 / invoke-stream 执行语义 / 测试证据分层 / 动态路径边界）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-08：任务创建，正文初稿完成；四源更新；PR #51 创建。
- 2026-08-08：**PR #51 Architecture Review 七项修正**（commit：docs: refine stategraph compilation and execution boundaries）全部应用并推送更新 PR #51：
  1. **State schema 可见范围**（18.2 / Q2 / 误区 / 验收标准）：StateGraph(GraphState) = 图级 State 契约，**不等于所有 Node 读取全部字段**；更窄输入 / input-output schema / internal-private channels 属第 9 章边界；"没有 schema 节点无从谈起"改为"schema 提供基础契约，Node / routing callable 读取范围由输入契约决定"
  2. **add_node / DI 边界**（18.3 / Q3 / 18.7 / 误区 / 验收标准）：删除"注册 = 依赖组装"；两层——LangGraph 通用（add_node 注册 callable 并赋予图内标识）vs 当前 Demo 工程选择（应用先经 Node Factory 完成依赖组装再注册）；链路 = Application dependency wiring → Node callable → add_node → StateGraph；**StateGraph 不是 DI Container**
  3. **Node-Routing 两层边界**（18.3 / 18.7 / Q3 / 误区 / 验收标准）：恢复第 10 / 13 章最终边界——Demo（Update + Conditional Edge）与通用能力（Command 携带 routing intent）两层；无论哪种方式 Node 不自行执行跳转、Graph Runtime 解释并 Scheduling Execution
  4. **compile 职责三层**（18.5 / Mermaid / 18.7 / Q5 / 误区 #3/#9 / 验收标准）：Graph Definition → compile（结构校验 + materialize + 挂载已配置 Runtime 能力）→ Compiled Graph；推荐表述"compile 不创造 Scheduler、Reducer 或业务 Failure Boundary"
  5. **invoke / stream 执行语义**（18.6 / Mermaid / 18.7 / Q6 / 误区 #6 / 验收标准）：删除"执行 vs 旁观"二分；invoke = aggregated execution interface（Interrupt / failure / cancellation 不假设成功终态）；stream = streaming execution interface（持续交付 Stream Mode 事件，引用 ch16）；核心区别 = 结果交付协议
  6. **测试证据分层**（18.8 / Q9 / Q10 / 验收标准）：代码事实（graph.py / agent.py 用法）与测试事实（观察维度等价——第 8 章已收窄口径）分开；不宣称测试证明一般性行为等价；未验证清单扩充（一般性语义 / compile 内部 / concurrency / side-effect ordering / stream / Checkpoint-Interrupt / delivery semantics / API 参数面）
  7. **动态路径边界**（18.4 / Q4）："图结构完整成型"改为"静态 topology 与 routing declarations 基本完成；实际运行路径仍可由 Conditional Edge / Command / Send 的 Runtime 控制结果决定"（引用 ch11/13）
