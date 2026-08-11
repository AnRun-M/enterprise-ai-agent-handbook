# Current Session

日期：2026-08-05

阶段：**Part 03（LangGraph Core Runtime Execution Model）完成**（Chapter 08-17 全部最终完成，2026-08-07，Part 03 Release Audit 通过，TASK-0025）；**v0.4.0 完成**；**Part 04 进行中**（v0.5.0：Text-to-SQL 重构）——前置章 Chapter 18 最终完成（PR #51）；**T01-T12 Execution Planning 完成**（TASK-0029，PR #53）；**T05 implementation task 完成**（TASK-0030，PR #56，首个 implementation task）；**下一步按 Recommended Implementation Waves 优先进入 T01 / T03**（**当前：T01 Gate A（TASK-0032）+ T03 Gate A（TASK-0033）同分支规划中，planning/wave1-t01-t03-contracts——Gate A 已按 Architecture Review 修正：T01 定 normalized_question / 职责收窄 / Failure 复用 lifecycle contract；T03 定 Reference-Materialized 双层 / Outcome 五态 / Provenance source+freshness；等待复审后进入 Implementation**）；v0.5.0 尚未宣布完成；`v0.3.0` 全部完成（Chapter 01-07 最终完成，Part 02 收官）

## 已完成

- 双 GitHub 账号 SSH 隔离
- 个人仓库创建
- AI-Native 项目骨架设计
- `.ai/` 项目记忆目录
- ADR 目录
- MkDocs 配置
- 示例和测试目录
- 章节骨架
- 骨架收敛重构（2026-08-01）：
  - ADR 单一事实源收敛至 `docs/adr/`（ADR-0001 ~ ADR-0006），`decisions.md` 降级为索引
  - Text-to-SQL canonical 流程（`docs/04-text2sql/canonical-pipeline.md`，T01-T12，含风险分支）
  - AI 协作规则收敛至 `AGENTS.md`，改为按影响范围更新
  - 示例目录改为可标准导入的 Python 包命名（去数字前缀、下划线，含 `__init__.py`），顺序由文档与映射表维护
  - 章节改为 `chXX-` 命名，Part 01 补充 index
  - 章节—示例—测试映射（`docs/00-introduction/content-map.md`）
  - TERMINOLOGY 补充 7 个术语与术语书写规则
  - 删除 `diagrams/`，Mermaid 图随章节内联；明确 docs / references / .ai 边界
  - 任务模板增加生命周期元信息，TASK-0001 标记 completed
  - 版本语义规则（ROADMAP），CHANGELOG 0.2.0 移入 Unreleased
  - `mkdocs build --strict` 通过；`import examples.manual_agent_loop` 等标准导入验证通过
- 第 0 章正文初稿（2026-08-01）：
  - 完成 LLM vs Agent、最小定义、Loop 定位、手写 Runtime vs 框架、框架不消灭 Loop、业务自建能力、该不该用 LangGraph、MCP/A2A/RAG/Memory 边界共 10 问
  - 4 张 Mermaid 图 + 手写 Agent Loop 伪代码（T04/T05/T07 循环）
  - 常见误区 8 条、架构决策清单、本章验收标准
  - 官方来源核验：LangGraph（docs.langchain.com）、MCP（v2025-11-25）、A2A（v1.0.0）、Anthropic Building effective agents（URL 待复核）；OpenAI practical guide 未核验（TODO）
  - 流程严格引用 canonical-pipeline.md，未另立流程
  - content-map 第 0 章状态更新为正文初稿；ROADMAP v0.2.0 第 0 章勾选
- 第 0 章 Architecture Review 修订（2026-08-01，PR #1）：
  - 「LLM = 无状态函数」改为「基础模型推理通常不会自动管理应用级状态，状态由 Runtime 或应用层维护」
  - 「Agent 判断必须存在循环」改为循环是复杂 Agent 典型能力而非必要条件，保留控制流归属/自主决策/工具使用
  - 五要素标注为本书工程分析模型，非行业唯一标准
  - 移除 StateGraph/Node/Edge/Pregel 细节，LangGraph 机制统一指向 Part 3
  - MCP/A2A/RAG/Memory 小节改为「外围能力」框架：Agent 是控制系统，外围能力提供输入/连接/协作
- PR #1（第 0 章）经 Architecture Review 通过，merge 到 main（2026-08-01）
- 手写 Agent Loop Demo（2026-08-01，TASK-0002，分支 feature/manual-agent-loop）：
  - examples/manual_agent_loop/：types / config / state / models / tools / runtime / agent / main
  - 全部 Fake 确定性组件（FakeLLM 首轮缺 LIMIT → 二轮修复；FakeSQLValidator 语法级；FakeSQLExecutor 固定 GMV）
  - 状态显式传递（AgentState + validation_rule），history 记录每轮事件
  - 三种终止：success / failed / max_iterations_reached
  - tests/manual_agent_loop/ 19 个测试通过；CI 新增 tests.yml（pytest + ruff）
  - ROADMAP v0.2.0 勾选「手写 Agent Loop Demo」；content-map 状态更新
  - 修复过程记录：validation_error（消息）与 validation_rule（规则名）分离；Windows 控制台 UTF-8 输出
- PR #2（手写 Agent Loop Demo）已通过 Architecture Review，squash merge 到 main（2026-08-01，commit 2d94239），远程 feature/manual-agent-loop 已删除
  - Review Blocker 全部修复并复审通过：AgentState.failure_reason（Executor 失败 / 运行时异常 / 未知 Action 均记录原因）、FakeSQLExecutor 最小安全检查加固（空 SQL / 非 SELECT / 多语句）、SELECT 首 token 严格匹配（拒绝 SELECTED / SELECTevil / CTE）
- Agent Runtime Design Principles（2026-08-01，TASK-0004，分支 feature/design-principles，PR #5）：
  - .ai/principles/ 六份文档：index（项目宪法定位）/ runtime-design / state-design / llm-vs-runtime / testing-agent / review-checklist
  - 全部原则可溯源：第 0 章、两个 Runtime 代码、PR #2 / PR #4 Review、ADR-0003~0006
  - PR #5 Review 修正：目录从 docs/99-design-principles 移至 .ai/principles（内部规范，不进 MkDocs）；三层职责边界（模型=开放式语义决策 / 确定性策略层=安全与治理 / Runtime=控制机制）；State 范围收窄为"执行控制状态"；Temporal 等降级为待验证方向；Checklist 按影响范围应用
  - ROADMAP v0.3.0 里程碑项保留（描述为内部规范，非读者章节）
- PR #5（Agent Runtime Design Principles）已通过 Architecture Review，squash merge 到 main（2026-08-01，commit 6b93d19），远程 feature/design-principles 已删除；TASK-0004 标记 completed
- LangGraph 等价 Demo（2026-08-01，TASK-0003，分支 feature/basic-langgraph，PR #4）：
  - 固定 langgraph==1.2.9（pyproject 精确固定；references/official/langgraph.md 核验记录）
  - 复用 manual_agent_loop 的 FakeLLM / Validator / Executor，不复制实现
  - GraphState（TypedDict + operator.add reducer）与 manual 字段语义对齐
  - 迭代语义等价：decide 节点递增 iteration，route_decide_or_max 先查上限（max_iterations=2 时 finalize 不执行），有 off-by-one 专项测试
  - PR #4 Review 修复：decide 节点恢复模型决策语义（路由只按 next_action 分发）；节点级异常转换 _failure_boundary 保留异常前 State；终止状态守卫
  - tests/basic_langgraph 26 用例（含 test_direct_equivalence_with_manual 等价对照、异常保状态、决策路由）
  - CI 改为 pip install -e ".[dev]"（单一依赖事实源）；pyproject 增加 [tool.setuptools] packages = []
  - 对照文档 docs/03-langgraph-core/manual-vs-langgraph.md 已入 mkdocs nav
  - ROADMAP/content-map 标记「实现完成 / 待架构审查」
- PR #4（LangGraph 等价 Demo）已通过 Architecture Review，squash merge 到 main（2026-08-01，commit 5c1d627），远程 feature/basic-langgraph 已删除；TASK-0003 标记 completed；LangGraph 等价 Demo 最终完成
- PR #8（Chapter 01：Agent Loop）已通过 Architecture Review（三项概念修正：状态转换过程严格表述 / Workflow vs Agent 判据重写为决策权归属 / Human Stop 改为暂停态），squash merge 到 main（2026-08-01，commit e63e7df）；TASK-0005 标记 completed；Chapter 01 最终完成

## 正在进行

- PR #10（Runtime Architecture Map）已通过 Architecture Review（四个 Blocker：Memory 边界 / 总图控制流 / Checkpoint-Audit / State 引用策略——全部修复并复审通过），squash merge 到 main（2026-08-01，commit 48bca0e）；TASK-0006 标记 completed；Map 最终完成
  - .ai/principles/architecture-map.md：八层总览（Goal / Execution State / Model Context / Memory / Checkpoint / Runtime Control Plane / Tool / Observability）+ 总 Mermaid 图 + 8 概念边界表 + 7 判定问题 + Part 01-03 章节归属 + T01-T12 挂载映射 + 单一事实源规则
  - principles index 增加阅读规则：涉及 Runtime/State/Context/Memory/Checkpoint 的任务必须继续阅读 architecture-map.md
  - 明确未决项：Memory 不选型、Checkpointer 未启用、Human Stop 暂停语义待 v0.6.0、Part 02 清单与 ROADMAP 差异待对齐
  - 顺手修复：content-map 第 0 章状态漂移（实现完成/待架构审查 → 最终完成）
  - 非出版内容，不进 MkDocs
- PR #12（Chapter 02：Execution State）已通过 Architecture Review（五项修正：State 更新机制 / Prompt 与执行语义 / 单一事实源职责划分 / 默认排除规则与例外 / 测试表述——全部修复并复审通过），squash merge 到 main（2026-08-01，commit d535de0）；TASK-0007 标记 completed；Chapter 02 最终完成
  - 2.1-2.9 结构，回答 Q1-Q10（State 是 Loop 的记忆载体 / 唯一事实源 / 生命周期 / 每轮演化 / 进入与不进入 / 可测试 / Schema 契约）
  - 4 张 Mermaid 图（生命周期 / State0→Final 演化 / State 与 Prompt-Memory-Checkpoint-Database 边界 / 进入 vs 默认不进入）
  - 职责划分：本章=面向读者讲解；state-design=内部约束；architecture-map=跨概念关系
  - content-map 状态规范化（本次 PR）：第 2 章=最终完成；Part 2=进行中（Execution State 已完成）；Part 3=进行中（示例与等价 Demo 已完成，正文待写）；统一四种状态
- PR #14（Chapter 03：Model Context）已通过 Architecture Review（六项修正：Context 变化来源 / 控制字段派生进入 / Prompt 术语表 / 生命周期逻辑周期 / 模型-Builder 边界 / Context Contract 测试条件——全部修复并复审通过），squash merge 到 main（2026-08-01，commit 21af67f）；TASK-0008 标记 completed；Chapter 03 最终完成
  - 3.1-3.9 结构，回答 Q1-Q10（模型看不到整个 Runtime / Context 是输入快照 / 最小充分上下文原则 / System Instruction-Prompt-Context 三层术语 / 生命周期 / Builder 归属 Runtime / Context Contract 是推论）
  - 4 张 Mermaid 图（State→Context / Builder 流程 / Prompt-Context-State 关系 / 生命周期）
  - 整章主线：模型只能看到 Runtime 构造给它的那一次调用输入
- PR #16（Chapter 04：Prompt Builder）已通过 Architecture Review（六项修正：Builder 输出表述 / Policy-Builder 边界 / 行为契约与数据契约区分 / 两类测试分离 / 审计最小集合 / RAG 挂载点收窄——全部修复并复审通过），squash merge 到 main（2026-08-01，commit 4be82e2）；TASK-0009 标记 completed；Chapter 04 最终完成
  - 4.1-4.9 结构，回答 Q1-Q10（组装是每轮高频多源动作 / Policy 决定 Builder 执行 / 输出是可发送输入结构语义上构成 Context / Template→Instance→Context / Prompt 是行为配置 / Builder 属于 Control Plane / Memory-RAG-MCP 挂载点）
  - 4 张 Mermaid 图（Builder 位置 / 输入来源 / 输出到 Context / Version 生命周期）
  - 诚实标注：Demo 无显式 Builder，属"Runtime 的逻辑抽象，目前 Demo 为隐式实现"
- **写作节奏决策（用户 2026-08-01）**：暂不进入 Part 3（LangGraph），先把 Part 02 的 Runtime 语义全部讲透（Tool Registry、Scheduler、Context Management 等）——让读者把 LangGraph 视为 Runtime 思想的一种实现，而非全书围绕框架展开（与 ADR-003 一致）
- PR #18（Chapter 05：Tool Registry）已通过 Architecture Review（六项修正：Registry 与 Tool View 分离 / Dispatcher 完整路径 / 术语固定 Handler-Dispatcher-Infrastructure-Engine / canonical definition + Provider Adapter / 判别式 Result Contract / 纵深防御最终边界——全部修复并复审通过），squash merge 到 main（2026-08-01，commit 483b636）；TASK-0010 标记 completed；Chapter 05 最终完成
  - 5.1-5.10 结构，回答 Q1-Q10；5 张 Mermaid 图
  - 主线：Registry = 能力描述与执行映射的注册表，不是工具集合、不是模型决策器
  - 诚实标注：Demo 无 Registry（架构抽象）
- PR #20（Chapter 06：Runtime Scheduler & Orchestration）已通过 Architecture Review（八项修正全部复审通过），squash merge 到 main（2026-08-01，commit c50247a）；TASK-0011 标记 completed；Chapter 06 最终完成
  - 6.1-6.10 结构，回答 Q1-Q10；4 张 Mermaid 图
  - **Part 02 阶段性编排总览**（不提前宣布 Part 02 收官）
  - 诚实标注：Demo 无独立 Scheduler；TASK-0003 仅验证教学 Demo 范围
- PR #22（Part 02 范围对齐）已通过 Architecture Review（五项修正全部复审通过），squash merge 到 main（2026-08-01，commit 51dcaa9）；TASK-0012 标记 completed
  - 结论：Chapter 01-06 保持最终完成；Part 02 还需 Chapter 07；Retry/Timeout/Trace 移 Part 05；Checkpoint/Interrupt/Streaming 拆两处；手写 Runtime 已满足；Part 02 暂不收官
  - 修改：ROADMAP / Part 02 index / content-map 三源对齐
- Chapter 07：Memory、Context 与 Context Management（2026-08-01，TASK-0013）已通过 Architecture Review 并 squash merge 到 main（commit b0195f0，CI build/test 双绿），TASK-0013 标记 completed：
  - 7.1-7.11 结构，回答 Q1-Q10（四概念边界 / 跨轮次≠Memory / History vs Memory / Window vs Budget / Pipeline / Injection 治理 / Memory 写入与读取双流程 / 五类测试与审计）
  - 7 张 Mermaid 图（四概念关系 / 跨执行判定（含充分条件）/ Pipeline / Builder-Manager 职责拆分 / Injection 来源 / Memory 写入生命周期 / Memory 读取生命周期）
  - 主线：State 服务执行、Context 服务调用、Memory 跨执行、Checkpoint 是快照；Context Management 是受预算/权限/事实边界约束的输入治理
  - Architecture Review 七项修正（commit 340835c）：Memory 不天然是权威事实源（可信度取决于来源/类型/验证状态/版本/时效/权威级别/作用域）；跨执行是首要判据但不是充分条件（主动选择/scope/生命周期/provenance/不属于外部事实源）；Memory Candidate 与 Record 分离（Candidate 不得直接注入）；写入与读取双生命周期（Memory Reader ≠ Context Manager）；Context Management 是职责集合不是单一巨型组件（无业务事实裁决权）；Compression 可能丢失信息（lossless structural / lossy semantic）；Configuration 采用引用而非复制（configuration id / version reference / user-level override）
  - 诚实标注：Demo 无跨执行 Memory / 无独立 Context Manager / 无 Compression-Summarization-Injection；双 Runtime 等价测试不验证 Memory 与 Context Management
  - 零向量库/检索算法/LangGraph Memory API；零新增代码
- **Part 02 收官检查（2026-08-01，四项全部满足）→ Part 02 最终完成**：
  - ✅ Chapter 02-07 全部最终完成（content-map 第 2-7 章统一"最终完成"）
  - ✅ ROADMAP v0.3.0 全部完成（Chapter 07 项最终完成，里程碑注记）
  - ✅ Part 02 index 与 content-map 一致（主题表 6 主题 = Part 2 行 6 主题；Chapter 07 状态两处同步）
  - ✅ 没有未归属的 Runtime 基础主题（归属表 12 主题全部有归属：Part 01/02/03/05）
- **Part 03 章节规划（2026-08-03，TASK-0014，本任务）**：
  - 前提确认：Part 02 最终完成 / v0.3.0 已完成 / Runtime 语义全部建立
  - 规划唯一事实源：`.ai/tasks/TASK-0014-part-03-architecture-planning.md`
  - 为什么在 Runtime 之后（ADR-0003 + 写作节奏决策 + architecture-map 归属 + 避免重复 + 证据先行）
  - Runtime → LangGraph 全映射 20 项 = **Part 03 全局参考**（独立文档或 index 前言，不属于单章正文；Review 修正 1）
  - Part 03 = 10 章（ch08-ch17）：ch08 为什么是图（为什么 Runtime 可以用 Graph 表达）/ ch09 Graph State（TypedDict/Schema/START/END/Initial State，compile/invoke 属 Graph Runtime 非本章核心）/ ch10 Execution Nodes（Node 执行模型）/ ch11 Edge+条件边 / ch12 Reducer（State Update→Channel Merge 核心映射）/ ch13 Command+Send / ch14 Checkpoint / ch15 Interrupt / ch16 Stream / ch17 Subgraph
  - Concept Dependency Graph 严格 DAG（根 C08，无环证明）；自审六项全过
  - **Architecture Review：APPROVED WITH MINOR CHANGES**——四项修正已应用（映射表移出 ch08 为全局参考 / ch09 聚焦 Graph State / ch10 改 Execution Nodes / ch12 加定位句）；章节结构、DAG、依赖、Part 03 定位不变，不新增章节不改顺序
  - **PR #26 Review 二轮修正**：DAG 方向语义统一（A→B=先决章节，无环证明修正）、10 章范围冻结（删除 12 章开放项，仅可经独立 Architecture Decision / Scope Alignment 任务调整）、Ch10 Node 表述收窄（实现可为 callable/Runnable，语义上是 Graph Runtime 管理的执行单元）、Ch13 Command/Send 定位收窄（Conditional Edge 已表达运行时路由；Command=State Update+路由意图；Send=运行时动态 fan-out）——已应用并推送更新 PR #26
  - 未决项：v1.0.0 章节数目标过时待对账、RetryPolicy 机制归属、官方 URL 发布前复核、index/content-map/ROADMAP/mkdocs 落地更新待确认后执行（章节范围已冻结：10 章）
  - 未开始任何 Chapter 正文（等用户确认规划）
- **Chapter 08 正文初稿（2026-08-03，TASK-0015，本任务）**：
  - `docs/03-langgraph-core/ch08-why-graph.md`：8.1-8.9，Q1-Q10，4 张 Mermaid 图
  - 主线：执行控制结构可图化（循环显式 / 连接可声明 / 执行结构可审查）；LangGraph Runtime 提供 Checkpoint / Interrupt / Streaming 集成机制（集成点 ≠ 能力自动生效）；图不引入新 Runtime 理论
  - 写作约束已执行：Runtime 第一视角、Framework 第二视角；只引用不重新定义 State/Context/Memory/Scheduler/Tool Registry；映射表为全局参考不复制；Demo 未用能力（Checkpoint/Interrupt/Stream）如实标注
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 8 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 08 draft）
  - **PR #27 Review 二轮修正（2026-08-05）**：8.6 执行控制关切范围（两类关切） / Graph Representation vs LangGraph Runtime 边界 / Routing 纯函数为工程选择（非框架强制） / TASK-0003 观察等价收窄 / Agent Loop 映射修正 / LangChain 边界提示（Future Scope Planning 已记录，不展开）——已应用并推送更新 PR #27
  - **PR #27 已通过 Architecture Review 并 squash merge 到 main（2026-08-05，commit 2a19809，CI build/test 双绿）→ Chapter 08 最终完成**；本 Memory PR（docs/post-pr27-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 09 正文初稿（2026-08-05，TASK-0016，本任务）**：
  - `docs/03-langgraph-core/ch09-graph-state.md`：9.1-9.11，Q1-Q10，5 张 Mermaid 图
  - 主线：Execution State 是 Runtime 语义；Graph State 是 LangGraph 承载；State schema 是数据契约不是业务规则引擎
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；TypedDict 标注为当前 Demo 选择非唯一方案；START/END 为图结构哨兵（END ≠ 成功，暂停 ≠ END）；Node 返回部分更新（Reducer 留 ch12）；不展开 Checkpoint/Interrupt/Stream；证据诚实（未验证清单如实标注，不夸大 TASK-0003）
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 9 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 09 draft / 待架构审查）
  - **PR #29 Review 七项修正（2026-08-05）**：Initial State 完整字段为 Demo 契约非框架要求（input/output schema、internal/private state 属 LangGraph 通用能力）/ StateProxy 只读表述收窄（属性访问适配器，按逻辑只读，非强制不可变、非安全边界、不等于 Model Context）/ Graph State 可见范围两层（具体节点可读字段取决于 schema 划分与节点输入契约）/ Checkpoint 定义修正（状态与执行上下文快照，非简单字典副本）/ 生命周期归属三层（应用设计定契约 / 执行路径实现演化 / schema 只声明形态）/ 测试证据归属拆分（路由纯函数测试不覆盖所有 Node 输入不可变性）/ TypedDict 静态检查为条件非门禁（CI 未启用 mypy --strict）——已应用并推送更新 PR #29
  - **PR #29 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-05，commit 06ea299，CI build/test 双绿）→ Chapter 09 最终完成**；本 Memory PR（docs/post-pr29-merge-memory）收敛状态（ROADMAP / content-map / current.md）
  - **Future maintenance（不立即执行）**：修正 `examples/basic_langgraph/state.py` 中 `build_initial_state` docstring「LangGraph 要求初始 invoke 提供全部字段」→「构造本 Demo 约定的完整初始状态」——属于 examples 文档修正（对齐 Chapter 09 概念边界），不属于 Chapter 09，随 examples 维护任务处理
- **Chapter 10 正文初稿（2026-08-05，TASK-0017，本任务）**：
  - `docs/03-langgraph-core/ch10-execution-nodes.md`：10.1-10.12，Q1-Q10，5 张 Mermaid 图
  - 主线：Node 在实现上可以是普通 Python callable，但在架构语义上是 Graph Runtime 管理的执行单元（读 State → 执行能力 → 返回部分更新 → Runtime 合并 → 下一执行步骤）；Node 不是孤立函数、不是 Tool、不是调度器
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；节点不调用下一节点、不写 while（调度权在路由 / Graph Runtime）；compile/invoke 归 Graph Runtime 执行路径不展开；三类节点（LLM / Tool / Pure Compute）；节点级 `_failure_boundary` 两层错误边界；Node≠Tool / ≠Python function / ≠Runnable（Runnable 仅一句边界）；不提前讲 Reducer/Checkpoint/Interrupt/Streaming/Subgraph；证据诚实（Node 输入不可变性无统一测试如实标注）
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 10 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 10 draft / 待架构审查）
  - **Future LangChain Scope Planning 补全**（并入既有条目，不新增第二份）：目标路线加 Agent Foundations → Production Engineering 全链；预计包含 Runnable 系列 / LCEL / ChatModel / Messages / Tool Calling / Middleware / create_agent / Structured Output / LangSmith 等；原则：LangGraph 可独立使用、LangChain 是更高层 Framework、Part 03 不出现 LangChain API
  - **PR #31 Review 九项修正（2026-08-05）**：Node/Routing 通用边界两层（严格拆分为 Demo 设计非框架强制，Command 留 ch13）/ Graph Runtime 与应用职责拆分（`_failure_boundary` 是应用实现非框架自动机制）/ Failure Boundary 控制流分叉（非同一异常执行两次）/ Node 输出契约收窄（当前 Demo 形态 + 工程建议非绝对禁令）/ 节点分类改四类形态（Semantic Decision / Mixed Capability / External Execution / Deterministic Compute）/ Tool Registry 证据边界（Demo 未实现 lookup，依赖注入，ch05 为未来组织方式）/ Node 输入来源（显式注入，禁止隐式跨轮记忆，dependency 非 State 字段）/ State Update 范围（仅图执行阶段，不覆盖 Initial State / Reducer / Command / Checkpoint）/ 异常前状态保留条件化（非事务回滚）/ LangChain API 清理（删除 create_agent 句，仅保留可包装 callable / Runnable 一句）——已应用并推送更新 PR #31
  - **PR #31 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-05，commit 06a9142，CI build/test 双绿）→ Chapter 10 最终完成**；本 Memory PR（docs/post-pr31-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 11 正文初稿（2026-08-05，TASK-0018，本任务）**：
  - `docs/03-langgraph-core/ch11-edge-conditional-edge.md`：11.1-11.11，Q1-Q10，6 张 Mermaid 图
  - **固定主线已逐字保持**：Edge 描述确定性连接；Conditional Edge 根据运行时结果选择后续路径；路由函数产生 Route Decision；Graph Runtime 解释该结果并调度下一执行步骤。当前 Demo 将模型语义决策写入 State，再由确定性路由函数分发，避免路由层替代模型决策
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；Edge 是连接描述不是执行者；Conditional Edge 不等于模型决策；Route Decision（纯函数化是工程选择）≠ Scheduling Execution；模型语义决策在 decide 节点、route_by_next_action 只分发（未知值 RuntimeError → invoke 兜底）；route_decide_or_max 按真实代码三条顺序（终止守卫最先 → 上限检查 → decide），定位 Lifecycle Guard + 确定性路由，上限检查先于模型动作，off-by-one 语义；END ≠ 业务成功、暂停 ≠ END；不提前讲 Reducer/Command/Send/Checkpoint/Interrupt/Stream/Subgraph；零 LangChain API
  - **代码差异如实报告**：任务书建议结构中的「START → decide 确定性入口」与实际代码不符——START 出口实为条件边（`add_conditional_edges(START, route_decide_or_max, ...)`），本 Demo 静态边仅 finalize→END / max_iterations→END 两条；正文按代码为准并在 11.2 显式注明
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 11 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 11 draft / 待架构审查）
  - **PR #33 Review 六项修正（2026-08-05）**：Routing error 归属（非法 next_action = 应用路由契约错误，应用 callable 产生 / Graph Runtime 传播 / 应用级 invoke 兜底，非框架自动转换）/ Conditional Edge 两层定义（概念层 vs 当前 Demo path map，path map 非必经结构）/ next_action 写入 State 收窄为当前 Demo 显式契约（非框架强制，Command 留 ch13）/ Route Decision 纯函数三层（定义 / 工程推荐 / Demo 事实，"纯函数化"非定义组成部分）/ Edge-Conditional Edge 边界（静态 Edge 不读 State，读 State 的是 routing callable，declaration 与 callable 都不执行 Node）/ Edge-Scheduler 关系（"Edge 是 Runtime 控制流的声明载体，不是 Scheduler 本身"）——已应用并推送更新 PR #33
  - **PR #33 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-05，commit 6f7c33f，CI build/test 双绿）→ Chapter 11 最终完成**；本 Memory PR（docs/post-pr33-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 12 正文初稿（2026-08-05，TASK-0019，本任务）**：
  - `docs/03-langgraph-core/ch12-reducer.md`：12.1-12.12，Q1-Q10，6 张 Mermaid 图
  - **固定主线已逐字保持**：Node 返回 State Update；Reducer 定义同一 State channel 收到更新时如何合并；Graph Runtime 应用该合并规则，形成新的 State。Reducer 是数据合并规则，不是业务决策器、不是路由器、不是 Scheduler、不是权限系统、不是生命周期守卫、也不是并发控制器。当前 Demo：history 使用追加语义；其他字段使用默认覆盖语义
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；三方职责（Node 产更新 / Reducer 定规则 / Runtime 应用规则，三个"不得写"）；overwrite 与 append 无高低之分（取决于 channel 数据契约）；Reducer ≠ 业务逻辑（含 Conflict Resolution Policy 边界：机械合并 vs 权威性裁决）；并发边界严格收窄（不宣称线程安全/事务隔离/确定性并发，当前 Demo 无并发写测试 → 明确"未验证"）；Annotated 是声明挂载关系的一种 Python 表达方式而非 Reducer 本身、operator.add 非唯一追加实现；不提前讲 Annotated API/自定义 Reducer/Pregel/Channel 内部实现/Command/Send/Checkpoint/Interrupt/Stream/Subgraph；零 LangChain API
  - 真实实现已核实（与任务书一致，无差异）：history = `Annotated[list[StepEvent], operator.add]`（state.py:36）、其余字段默认覆盖、Node 返回 history 增量、无并发写同 channel 测试（未验证）、Reducer 专项测试存在（`test_history_reducer_appends_without_duplicates` / `test_reducer_semantics_operator_add`）、无自定义 Reducer、无 Pregel 使用
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 12 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 12 draft / 待架构审查）
  - **PR #35 Review 七项修正（2026-08-05）**：默认覆盖与同一步多更新冲突分离（默认覆盖 = 单个新值替换，不是并行冲突解决机制，新增误区 #11）/ Reducer 业务边界（不是业务决策器，可承载应用定义的数据合并语义，职责限制在值的组合与归并）/ 纯函数工程约束三层（定义 / 工程推荐 / 框架事实——LangGraph 不自动保证无副作用）/ 默认更新证据归属三层（代码 / 执行 / 非并发专项范围）/ Graph Runtime 表述（按已编译 schema 查找并应用规则，非每轮动态制定）/ Append 只是一个示例（不把 Reducer 等同 operator.add）/ history 顺序证据收窄（仅顺序执行路径，并行顺序未验证）——已应用并推送更新 PR #35
  - **PR #35 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-05，commit 8dfc260，CI build/test 双绿）→ Chapter 12 最终完成**；本 Memory PR（docs/post-pr35-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 13 正文初稿（2026-08-05，TASK-0020，本任务）**：
  - `docs/03-langgraph-core/ch13-command-send.md`：13.1-13.11，Q1-Q10，5 张 Mermaid 图
  - **固定主线已逐字保持（2026-08-05 复审统一为最新表述）**：Conditional Edge 根据图外定义的 routing callable，返回 Graph Runtime 可解释的一个或多个路径目标；在本章讨论的场景中，Command 允许 Node 返回结果同时携带 State Update 与 goto 路由意图；Send 由 routing callable 根据运行时数据返回，用于描述多个带独立输入的 work items，并由 Graph Runtime 解释、实例化和调度。Command 与 Send 都属于动态控制流原语：Command 解决更新与导航绑定；Send 解决按运行时数据描述动态 fan-out work items
  - **两条硬边界已守**：Command 与 Send 不混成同一个原语（问题不同 / 作用对象不同 / 可组合但先分清）；Send 不简化成普通 Conditional Edge（选一条路 vs 按数据展开多个执行单元）
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；Command 与「先更新 State 再路由」= 表达位置变化、解释权不变（Graph Runtime）；Send 是 work item 产生者、调度在 Scheduler / Graph Runtime（ch06 对应）；Command 的 State Update 走同一 channel 合并（ch12）；静态图足够时不需要动态原语（反例教学）；不提前讲 Command/Send API 签名 / Checkpoint / Interrupt / Stream / Subgraph（仅引用 map-reduce 组合方向）/ Part 05 生产语义；零 LangChain API
  - **证据诚实**：仓库无 Command / Send 实现证据——基于 `references/official/langgraph.md` 核验记录（刻意未使用）与 README 第 9 节；未验证清单 6 项如实标注，不推断实现行为
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 13 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 13 draft / 待架构审查）
  - **PR #37 Review 七项修正（2026-08-05）**：Conditional Edge 多目标语义（返回一个或多个路径目标；当前 Demo 单路径；多目标 ≠ Send work-item 语义）/ Send 产生链路（Node 产数据 → conditional routing callable → Send descriptors → Graph Runtime 解释实例化调度；Send 不执行节点不创建线程）/ Send 独立输入语义（目标节点 + 专属输入；同一目标可实例化多次；核心区别 = 目标选择 vs 带独立输入的实例化）/ Command 作用域收窄（本章特指 Node 返回的 State Update + goto；resume / Tool return / parent graph / invoke-stream 输入声明不展开）/ Command 等价性收窄（单图场景相近意图，不宣称全面等价，仓库未测）/ 动态实例边界（实例化已注册目标 Node 的 work items，非注册新 Node 类型）/ Send 与并行收窄（表达 fan-out，不自动保证并发度 / 调度顺序 / 稳定顺序 / 线程安全 / 重试 / delivery / fan-in 确定性）——已应用并推送更新 PR #37
  - **PR #37 Review 复审三项跨章节一致性修正（2026-08-05）**：固定主线统一为最新表述（Conditional Edge 返回一个或多个路径目标 / Command = Node 返回的 State Update + goto / Send 由 routing callable 返回、Graph Runtime 解释实例化调度）；"节点不决定下一步"旧绝对边界改写（Node 不自己执行跳转、不拥有 Scheduling Execution；Node 表达 Runtime 控制结果、Graph Runtime 解释并调度；第 10 章两层边界延续）；Send / work item 职责四层（routing callable 构造返回 descriptors / descriptor 描述 target + 输入 / Graph Runtime 解释实例化 / Scheduler 安排执行顺序并发；"Send 表达 fan-out 但不是 work item 的主动创建者或执行者"）——已应用并推送更新 PR #37
  - **PR #37 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-05，commit 0da1938，CI build/test 双绿）→ Chapter 13 最终完成**；本 Memory PR（docs/post-pr37-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 14 正文初稿（2026-08-05，TASK-0021，本任务）**：
  - `docs/03-langgraph-core/ch14-checkpoint.md`：14.1-14.11，Q1-Q10，5 张 Mermaid 图
  - **固定主线已逐字保持（2026-08-05 合并前术语清理统一 Checkpointer 职责表述）**：Graph State 是执行中的当前状态；Checkpoint 是图在某个执行时刻持久化的状态与执行上下文快照。Checkpointer 负责写入、读取、组织检索、列举 checkpoint，并保存恢复所需的 pending writes，使 Runtime 能够恢复、重放或继续执行；Checkpoint 不是 Memory，也不等于一个简单的 State 字典副本
  - **三条核心边界已守**：① Graph State = 当前执行状态；Checkpoint = 执行时刻快照 ② Checkpointer 写入、读取、组织检索、列举 checkpoint 并保存恢复所需 pending writes，恢复策略 / 重放语义 / 续跑规则由 Runtime 与应用契约共同决定 ③ 不是 Memory、不等于简单字典副本
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；持久化内容 = State channel values、next 执行位置、thread/checkpoint 配置与标识、metadata、父快照关系及 tasks/interrupts 等执行信息（Reducer 归并结果体现在 channel values 中）；恢复 / 重放 / 续跑三场景区分；Checkpoint 与 Interrupt 承载基础关系（仅边界）；当前 Demo 未启用如实标注（graph.py 无 checkpointer / agent.py docstring / examples/checkpoint_hitl 预留 / references 核验记录 / architecture-map 未决项）；不提前讲 Checkpointer API 与存储后端 / 生产恢复语义（Part 05）/ Interrupt API（ch15）；零 LangChain API
  - **证据诚实**：仓库无 Checkpoint 实现证据——基于教学边界声明与官方核验记录；未验证清单 7 项如实标注，不推断实现行为
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 14 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 14 draft / 待架构审查）
  - **PR #39 Review 七项修正（2026-08-05）**：持久化内容改 StateSnapshot 语义（channel values 含 reducer 合并结果 / next / thread 标识 / metadata / parent 关系 / 任务信息；pending writes ≠ 完整 checkpoint，完整 checkpoint 通常对应 superstep 边界）/ Checkpoint-Memory 官方术语桥接（thread-scoped short-term memory / Store = cross-thread long-term，本书仍归入 Checkpoint / thread state persistence，删除三项绝对化）/ Checkpointer 机制职责扩展（写入读取检索列举 pending writes 序列化 vs Runtime-应用契约的恢复点 replay-resume 入口副作用幂等治理审批）/ Recovery-Replay-Resume 精确区分（pending writes 避免重跑 / 跳过之前 LLM-Tool 再次触发 / 可携带新输入留 ch15）/ 无 Checkpointer 边界（应用仍可得最终 State 并自行持久化，但不拥有恢复协议）/ 版本化边界（update_state 创建新 checkpoint 不修改旧，fork-replay 派生）/ superstep-pending writes 边界（不展开 Pregel）——已应用并推送更新 PR #39
  - **PR #39 合并前术语清理（2026-08-05）**：删除 14.1 绝对化句（"执行结束即失效"→"State 的控制语义服务于一次执行；未启用 Checkpointer 时 Graph Runtime 不自动维护可恢复的 thread checkpoint history"）；"reducer 累积 / channel 状态含累积"统一为"包含 Reducer 归并结果的 channel values 与底层 channel versions / pending writes 的持久化行为"；Checkpointer 职责统一为"写入、读取、组织检索、列举 checkpoint，并保存恢复所需的 pending writes"、持久化内容统一为 StateSnapshot 六项——同步至正文顶部 / 14.3 / TASK-0021 / current.md / PR #39 描述
  - **PR #39 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-05，commit 007ae18，CI build/test 双绿）→ Chapter 14 最终完成**；本 Memory PR（docs/post-pr39-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 15 正文初稿（2026-08-05，TASK-0022，本任务）**：
  - `docs/03-langgraph-core/ch15-interrupt.md`：15.1-15.10，Q1-Q10，5 张 Mermaid 图
  - **固定主线已逐字保持（2026-08-06 合并前清理统一为最终表述）**：Interrupt 让 Graph Runtime 在可恢复执行点暂停，并把控制权交还应用或人工参与者；恢复时使用同一 thread 的持久化状态，包含 Interrupt 的 Node 会从头重新执行，直到 `interrupt()` 取得 resume payload 后继续后续逻辑——恢复调用通过 Runtime 控制封装携带 resume payload，payload 可以是人工审批结果、修改内容、澄清信息或其他结构化输入；Interrupt 在业务语义上不是失败，但在 LangGraph 实现中通过特殊控制流异常通知 Graph Runtime 暂停；Checkpoint 提供持久化承载，Interrupt 提供暂停与恢复值注入协议
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；三条硬边界（≠ END / ≠ 异常 / ≠ 完整 HITL）；Checkpoint 承载 + Interrupt 协议分工（恢复 = ch14 续跑场景）；恢复可携带人工输入（T07 批准 / 拒绝 / 修改）或控制结果（Command——ch13 作用域声明，API 不展开）；ch01 Human Stop 暂停态（RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING）状态机对应；T07 人工审批挂载点（审批规则属策略层 ADR-004 / ADR-005）；不提前讲 Interrupt API / 生产 HITL（Part 05）/ 审批 UI / Stream（ch16，正交）/ Subgraph（ch17）；零 LangChain API
  - **证据诚实**：仓库无 Interrupt 实现证据——基于第 1 章暂停态定义、references 核验记录（刻意未使用）、README 第 18 节、examples/checkpoint_hitl 预留；未验证清单 5 项如实标注，不推断实现行为
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 15 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 15 draft / 待架构审查）
  - **PR #41 Review 七项修正（2026-08-06）**：Interrupt 业务语义与实现机制两层（业务语义非失败 ≠ FAILED State；实现上 interrupt() 经特殊控制流异常通知 Runtime 暂停，普通 try/except 不应吞掉信号）/ Resume 时 Node 重执行语义（"从暂停点恢复"是图执行语义非指令级 continuation——Node 从头重新执行直至 interrupt() 取得 resume value；副作用须幂等、不可安全重复写入不得置于 Interrupt 前、多个 Interrupt 顺序须稳定）/ Resume payload 与 Command 区分（payload = 应用或人工产生的内容，Command(resume=payload) = 恢复封装，payload 成为 interrupt() 返回值；Payload Contract：可序列化 / 大小受控 / 无句柄 / 敏感字段受约束 / 大对象用引用）/ WAITING_FOR_HUMAN 生命周期归属（应用生命周期语义非 LangGraph 自动写入的 State 字段，业务状态由应用契约维护）/ 五层职责（Application Node-Policy / Interrupt protocol / Checkpointer / Node-Command-Edge / Graph Runtime，删除"Interrupt 负责恢复后去哪"）/ Checkpointer 持久性限定（Checkpointer + 稳定 thread_id；跨进程恢复需 durable persistence backend，内存型 saver 不等于生产持久化）——已应用并推送更新 PR #41
  - **PR #41 合并前一致性清理（2026-08-06）**：删除 15.1 残留错误句（"从暂停点继续，而不是从头或从异常路径重来"）；PR #41 描述顶部摘要直接同步最终结论（章节定位 / Q2-Q7 / 关键边界 / Mermaid）；固定主线中"可携带人工输入或控制结果"收窄为"恢复调用通过 Runtime 控制封装携带 resume payload；payload 可以是人工审批结果、修改内容、澄清信息或其他结构化输入"，最终主线同步至正文顶部 / 15.2 / 15.4 / TASK-0022 / current.md 两处
  - **PR #41 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-06，commit b9ef9fe，CI build/test 双绿）→ Chapter 15 最终完成**；本 Memory PR（docs/post-pr41-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 16 正文初稿（2026-08-06，TASK-0023，本任务）**：
  - `docs/03-langgraph-core/ch16-stream.md`：16.1-16.9，Q1-Q10，5 张 Mermaid 图
  - **固定主线已逐字保持（2026-08-07 合并前清理统一为最终表述）**：Stream 让调用方在图仍在执行时持续接收运行进展与增量输出；它是多类执行事件的统一观察和交付协议，不决定路由、不修改业务状态，也不等于完整的日志系统。Graph Runtime 汇聚执行过程中由 Node、Tool、模型调用及 Runtime 子系统产生的数据，并依据 Stream Mode 封装和交付流事件；应用选择消费模式和展示方式，背压是应用、Graph Runtime 与传输层共同形成的交付契约；Stream 与 Interrupt 正交，一个解决"边跑边看"，一个解决"暂停后再继续"
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；三条硬边界（不决定路由 / 不修改业务状态 / ≠ 完整日志系统）；四类流事件（State projection / Model output / Application event / Runtime event）；最终 State 两类关系（State 类模式成功终止时演进投影；non-state 不要求写入；暂停失败取消提前终止不能假设完整最终 State）；token / message chunk 由模型调用产生、经 messages 流模式由图执行层交付并附元数据；背压分层（应用 / Graph streaming runtime / 传输层共同形成交付契约，生产策略 Part 05）；与 Interrupt 正交（可共存、互不依赖，payload 可经流暴露但不合并语义）；同步 invoke vs 流式对照（同一张图两种观察方式）；不提前讲 astream API / 生产交付（Part 05）/ Subgraph 嵌套流（ch17 仅引用）；零 LangChain API
  - **证据诚实**：仓库无 Stream 实现证据——基于同步 invoke 代码事实（agent.py）与 references 核验记录（Streaming 刻意未使用）；未验证清单 6 项如实标注，不推断实现行为
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 16 章行+Part 3 行）、ROADMAP（v0.4.0 Chapter 16 draft / 待架构审查）
  - **PR #43 Review 七项修正（2026-08-06）**：token streaming 两层边界（生成来自模型调用；LangGraph 经 messages 流模式在图执行层交付增量并附节点与调用元数据）/ 四类流事件（State projection / Model output / Application event / Runtime event，统一交付协议非仅 State 增量流）/ 流事件生产职责（Graph Runtime 汇聚 Node-Tool-Model call-Checkpointer-task runtime 数据并按 Stream Mode 封装交付，不展开 get_stream_writer）/ Stream-Observability 不互斥（Streaming = 实时交付、可承载可观测事件与成为数据入口；Observability = 留存关联分析；Stream ≠ 完整日志系统）/ 最终 State 两类关系（State-related modes 成功终止时演进投影；non-state 不要求写入最终 State；任意流事件 ≠ State Update、不一定能重建、暂停失败取消提前终止不能假设完整最终 State；未验证一致性）/ 背压分层（Application consumer → Graph streaming runtime → Transport-server → Production policy-Part 05，"共同形成的交付契约"）/ Stream-Interrupt 组合边界（正交保留；payload / interrupted 状态可经流式协议暴露但不合并语义）——已应用并推送更新 PR #43
  - **PR #43 合并前一致性清理（2026-08-07）**：本章边界 token 旧结论统一（"token / message chunk 由模型调用产生；LangGraph 可以通过 messages 流模式在图执行层交付这些增量，并附带节点与调用元数据"）；验收标准固定主线同步（Graph Runtime 汇聚并按 Stream Mode 封装交付 / 背压分层契约）；PR #43 描述顶部直接更新（固定主线 / Q3 / Q6 / Q7 / Q10 / 关键边界 / Mermaid / Review Focus，删除 5 项旧口径）
  - **PR #43 已通过 Architecture Review 复审并 squash merge 到 main（2026-08-07，commit 94ff6e1，CI build/test 双绿）→ Chapter 16 最终完成**；本 Memory PR（docs/post-pr43-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Chapter 17 正文初稿（2026-08-07，TASK-0024，本任务；Part 03 收官章）**：
  - `docs/03-langgraph-core/ch17-subgraph.md`：17.1-17.10，Q1-Q10，5 张 Mermaid 图
  - **固定主线已逐字保持**：Subgraph 将一组 Node、State channels 与控制流封装为可组合的图级执行单元。父图负责调用与整体编排，子图维护自身内部执行结构；父子图如何交换 State，取决于共享 schema、输入输出映射与显式适配契约。Subgraph 不是普通 Node 的同义词，也不是微服务或独立 Agent 的必然边界
  - **Part 03 收官边界已守**：正文明确"Part 03 收官需在 Chapter 17 合并后单独执行 Scope Closure / 收官检查"；正文与 Memory PR **均不把 Part 03 标记为最终完成**
  - 写作约束已执行：Runtime 第一视角 / Framework 第二视角；Subgraph ≠ 普通 Node（图级组合单元 vs 单步执行单元）；父子 State 交换 = 共享 schema / 输入输出映射 / 显式适配契约（非自动全量共享）；≠ 微服务（进程内结构组合 vs 部署边界）/ ≠ 独立 Agent（控制流组合单元 vs 拥有自己 Loop 的执行主体，A2A 属 Part 06）；与 Send map-reduce 仅引用（ch13）；拆 / 不拆判据（复用 / 可读性 / 可测试性，单层图足够时就是对的）；不提前讲 Subgraph API / A2A / MCP / 生产级流程引擎（Part 04-06）；零 LangChain API
  - **证据诚实**：仓库无 Subgraph 实现证据——基于 references 核验记录（刻意未使用）与 README 第 19 节扩展方向声明；未验证清单 7 项如实标注，不推断实现行为（不因官方 examples 写成"已验证"）
  - 四源更新：mkdocs.yml（导航）、index.md（章节列表）、content-map（第 17 章行+Part 3 行，Part 03 保持进行中）、ROADMAP（v0.4.0 Chapter 17 draft / 待架构审查，标注 Part 03 收官章）
  - **PR #45 Review（REQUEST CHANGES）八项修正（2026-08-07）**：Subgraph = Graph Composition 不是大 Node（固定表述："不是 Node 的增强版，而是 Graph 的组合"；Graph 被 Graph 组合）/ Parent Graph 描述调用关系不拥有 Child 生命周期（生命周期属 Runtime）/ State Exchange 是执行契约（mapping 只是表达方式，真正重要的是 Execution Boundary，非 DTO Mapping）/ Subgraph 不产生新的 Runtime（同一 Runtime 图组合，不讨论 RemoteGraph-A2A-Multi Runtime）/ Send 与 Subgraph 不同层次（Send → Work Items → 同一 Subgraph；可组合但互不替代）/ Demo 未使用 = 没有组合需求非能力缺失 / Evidence 保持（只介绍边界不介绍实现）/ Part 03 Ending 收官句（从 Graph State 到 Subgraph 建立 Graph Runtime 执行模型，下一部分进入 StateGraph API 与框架实现层）——已应用并推送更新 PR #45
  - **PR #45 已通过 Architecture Review 复审 APPROVED 并 squash merge 到 main（2026-08-07，commit d7befd3，CI build/test 双绿）→ Chapter 17 最终完成（Part 03 全部十章完成）**；本 Memory PR（docs/post-pr45-merge-memory）收敛状态（ROADMAP / content-map / current.md）
- **Part 03 Release Audit（2026-08-07，TASK-0025，本任务）**：
  - 八项检查完成：① Runtime 概念一致性（12 个核心概念：Execution State / Graph State / Node / Edge / Reducer / Scheduler / Command / Send / Checkpoint / Interrupt / Stream / Subgraph——Checkpoint / Node / Reducer / Interrupt / Subgraph / Scheduler 定义跨章一致，Scheduler 均引用 ch06 6.7 不重定义）✅ ② 章节引用一致性（跨章引用编号无越界、方向符合 DAG；ch10→ch11、ch14→ch12、ch17→ch13 核对一致）✅ ③ Mermaid 画法一致性（关键实体标签统一）✅——**Mermaid 计数漂移口径**：历史 TASK / PR 描述存在 Mermaid 计数漂移；**正文实际 Mermaid 围栏数是事实源**（实际 42 张）；Release Audit 不修改已合并 PR 描述和 Chapter 正文；后续任务不预先承诺固定数量，交付时以实际统计为准 ④ current.md：Part 03 completed ✅ ⑤ ROADMAP：Part 03 completed（v0.4.0 清单无未完成项；StateGraph 移入 Next-stage planning / Part 04 scope input，不计入 v0.4.0 完成条件）✅ ⑥ content-map：Part 3 行 → 正式范围 = LangGraph Core Runtime Execution Model，Part 04 未修改 ✅ ⑦ v0.4.0 = Part 03 → 宣布 v0.4.0 completed ✅ ⑧ Release Audit Report 输出 ✅
  - **Release Audit Review 修正（2026-08-07）**：① v0.4.0 / StateGraph checkbox 矛盾解决（StateGraph 从 v0.4.0 完成清单移入 Next-stage planning / Part 04 scope input）② Part 03 正式范围冻结（LangGraph Core Runtime Execution Model，Chapter 08-17 承载；StateGraph 定位 = 图构建入口，Part 03 仅最小引用）③ 下一步 = **Part 04 Scope Planning**（非直接启动 Part 04）④ **Chapter 17 Ending 进入 maintenance backlog**：Ending 中"下一部分将进入 StateGraph API 与框架实现层"属于**待维护表述**——Release Audit 禁止修改正文，本 PR 不回改 Chapter 17；在 Part 04 Scope Planning 确定路线后，通过**独立 maintenance task** 修正 Ending；**不把该句子当成已确认的 ROADMAP 事实**
  - **Part 03 正式结束；下一阶段 Part 04 Scope Planning**（规划完成前不启动 Part 04 正文）
- 官方资料索引（`references/official/`）

## 下一步

1. **T05 implementation task（SQL 静态校验，首个 implementation task，TASK-0030）**：**completed**（PR #56 合并 `b2572e6`）——Gate A（PR #55）→ Gate B/C → Gate D（Ch22 T05 部分）→ Task Merge Gate 全流程通过；`examples/text2sql_state/validation.py`（`_RULE_CHECKS` 无序 registry + RULE_ORDER 唯一顺序事实源 + `_statements` total contract + 超长 LIMIT 归入 limit_exceeds）；`docs/04-text2sql/ch22-sql-validation-repair-loop.md`（T05 可证实部分，T07 接口位置预留）。**状态快照**：Evidence = Contract-level verified；Integration = **deferred**（Gate E 等 T06/T07 进 main 后关闭）；Chapter 22 = 不标最终完成（T07 未实现）；Part 04 = 进行中；v0.5.0 = 未完成。**下一步按 TASK-0029 Recommended Implementation Waves 优先进入 T01 / T03（非立刻跳 T06/T07）**。
2. **Chapter 17 Ending maintenance（TASK-0027）已完成**：Chapter 17 Ending 句已修正为与冻结决策一致（"下一部分将进入 StateGraph 构图与 Graph Runtime 执行模型——图如何被组装、compile 如何将其转换为可执行 Runtime、invoke/stream 如何驱动执行，而不是重新定义这些运行时概念"），独立 PR 合并完成（commit b93f9a5）。
3. **Chapter 18 正文初稿（2026-08-08，TASK-0028，本任务；Part 04 前置章）**：
  - `docs/04-text2sql/ch18-stategraph-graph-runtime.md`：18.1-18.10，Q1-Q10，5 张 Mermaid 图
  - **固定主线已逐字保持**：StateGraph 负责声明图结构，compile() 将图定义转换为可执行的 Graph Runtime，invoke()/stream() 通过该 Runtime 驱动 State、Node 与控制流运行；这些 API 不重新定义 Part 03 的 Runtime 语义，只负责把既有语义组装并执行
  - **链式结构已守（非方法列表）**：定义图 → 注册组件 → 连接控制流 → compile → invoke/stream → 与 Part 03 对照；只集中讲四件事（构图入口 / 组件注册与连接 / compile 语义边界 / 编译后 Runtime 执行入口）；Node/Edge/Reducer/Command/Send/Checkpoint/Interrupt/Stream 只引用 Part 03 不重新解释
  - **证据优势**：本章有真实代码直接证据（graph.py 构图/注册/连接/compile + agent.py invoke），并标注未验证清单（Runtime 内部调度 / stream 行为 / Checkpoint-interrupt 组合 / API 参数面）
  - 四源更新：mkdocs.yml（导航）、04-text2sql/index.md（前置章条目）、content-map（第 18 章行+Part 4 行）、ROADMAP（v0.5.0 Chapter 18 draft / 待架构审查）
  - **PR #51 Review 七项修正（2026-08-08）**：State schema 可见范围（图级契约 ≠ 所有 Node 读全部字段，ch09 边界不重展）/ add_node-DI 边界（add_node 注册 callable；依赖组装在注册前由应用完成；StateGraph 不是 DI Container）/ Node-Routing 两层（Demo Update+Conditional Edge vs 通用 Command routing intent；跳转解释在 Graph Runtime）/ compile 职责三层（校验 + materialize + 挂载已配置能力；不创造 Scheduler-Reducer-Failure Boundary）/ invoke-stream 执行语义（同一 compiled graph 的两个执行接口：aggregated vs streaming；Interrupt-failure-cancellation 不假设成功终态）/ 测试证据分层（代码事实 vs 观察维度等价测试——第 8 章收窄口径）/ 动态路径边界（静态 topology 完成 ≠ 运行路径唯一，Conditional Edge-Command-Send 决定）——已应用并推送更新 PR #51
  - **PR #51 合并前一致性清理（2026-08-08）**：18.4 topology 表述统一（静态 topology 可审查、实际路径由 Runtime 控制结果决定）；compile 跨章节职责引用精确化（Scheduling→ch06 / Node failure boundary→ch10 / routing→ch11 / Reducer-channel merge→ch12）；PR #51 描述顶部摘要直接同步（Q2-Q10 / 关键边界 / 证据与测试范围 / Review Focus）+ 最后一次 Description 一致性清理（invoke/stream 无旧二分口径）
  - **PR #51 已通过 Architecture Review 复审 APPROVED 并 squash merge 到 main（2026-08-08，commit 83f5ae5，CI build/test 双绿）→ Chapter 18 最终完成（Part 04 前置章）**；本 Memory PR（docs/post-pr51-merge-memory）收敛状态（ROADMAP / content-map / current.md）
3. **未决项**：① Mermaid 计数漂移（历史 TASK / PR 记录与实际围栏数不一致；正文围栏数是事实源，后续任务不预先承诺固定数量）② v1.0.0 章节数目标对账（TASK-0014 未决项延续）③ 官方 URL 发布前复核（TASK-0014 未决项延续）④ RetryPolicy 机制归属（TASK-0014 未决项延续）
2. 补 tests/ 其余测试目标（State reducer、Tool adapter、Graph path、Checkpoint recovery）
3. 核验 Anthropic《Building effective agents》与 OpenAI practical guide 的官方 URL（第 0 章 TODO）
4. 选择许可证
5. **Future Task：LangChain Scope Planning**（不立即执行，仅记录方向；本条目已按 2026-08-05 规划合并补全，不新增第二份）：
   - 目标：未来增加一个 **LangChain Framework 部分**（判断是否新增独立 Part，或仅新增 1-2 个桥接章节）；**不在 Part 03 内展开**
   - 目标路线：Agent Foundations → Runtime Semantics → LangGraph Core → **LangChain Framework** → Text-to-SQL Practice → Production Engineering
   - 预计包含：Runnable / RunnableSequence / RunnableParallel / RunnableBranch / LCEL / PromptTemplate / ChatModel / Messages / Tool Calling / Middleware / create_agent / AgentExecutor（如保留）/ Structured Output / LangSmith（如果未来规划）
   - 原则：LangGraph 可独立使用；LangChain 是更高层 Framework；Part 03 不出现 LangChain API（LangGraph Node 可包装 Runnable，仅作一句边界）
   - 约束：future planning；当前**不修改** ROADMAP Part 编号、content-map、mkdocs.yml；**不新增** TASK 正式文件、不新增章节；Part 03 完成后再单独执行 Scope Planning
6. **Future Backlog：Agent Workflow Patterns Scope Planning**（TASK-0031，proposed 登记，v0.6.0+，不立即执行）：
   - 候选 Topics（**14**，统一 7 字段模板）：ReAct / Router / Sequential Workflow / StateGraph Workflow / Planner-Executor / Reflection / Retry / Human-in-the-loop / Map-Reduce / Supervisor / Multi-Agent / Hierarchical Agent / **Evaluator-Optimizer** / **Tool Calling**
   - 分类（**七大**）：Execution / Coordination / Planning / Recovery / Human Interaction / **Evaluation** / **Tool Interaction** Patterns
   - **Pattern Taxonomy（唯一组织方式）**：未来新增 Pattern 必须先归入七类之一，不得新增孤立 Pattern；固定表述"**Pattern 是框架无关的架构与执行模式；框架提供这些 Pattern 的一种或多种实现方式**（LangGraph / OpenAI Agents SDK / Google ADK / CrewAI / AutoGen / Claude 都只是实现之一）"（Evaluator-Optimizer 不讨论供应商 Judge；Tool Calling 不讨论 Function Calling / Tool Use / MCP）
   - **Runtime-first，Framework-second**：每个 Pattern 是"一种 Runtime Workflow Pattern，LangGraph 可以表达，但 Pattern 不属于 LangGraph"；只引用 ch08-18，不重新定义冻结语义
   - Roadmap：**当前 v0.5.0 专注 Text-to-SQL Runtime Refactor；完成后才进入 Agent Workflow Patterns（v0.6.0+）**——不提前启动
   - 约束：不影响当前 T01-T12；不修改 ROADMAP / content-map / mkdocs / Runtime Handbook / Part 03-04；不启动任何 Pattern 教学

## 当前阻塞

- 尚未确定真实 LLM 供应商
- GitHub Connector 当前不可直接写入
- v0.2.0 里程碑未完成（官方参考索引），按版本规则 CHANGELOG 暂处 Unreleased
