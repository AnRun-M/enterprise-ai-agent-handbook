# Current Session

日期：2026-08-01

阶段：`v0.2.0` 骨架收敛重构完成，第 0 章正文初稿完成

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
- Chapter 06：Runtime Scheduler & Orchestration（2026-08-01，TASK-0011，分支 feature/chapter-06-runtime-scheduler，draft 待架构审查）：
  - 6.1-6.10 结构，回答 Q1-Q10（Loop=重复执行结构 / Routing 与 Lifecycle Guard 共同维持 / 调度对象是可执行步骤 / Workflow 与 Scheduler 非对立 / Control Plane 职责与可能路径 / Routing Decision 纯函数 vs Scheduling Execution / 替换契约收窄）
  - 4 张 Mermaid 图（Control Plane 总图 / 调度循环 / 组件编排 / Scheduler-Policy-LLM 职责边界）
  - **Part 02 阶段性编排总览**（不提前宣布 Part 02 收官——是否结束待 Merge 后对齐 ROADMAP / Part index / 剩余主题）
  - 诚实标注：Demo 无独立 Scheduler；TASK-0003 仅验证教学 Demo 范围
  - 零 LangGraph API 泄漏；零新增代码
- 官方资料索引（`references/official/`）

## 下一步

1. 等待 Chapter 06 架构审查通过后 Merge
2. Merge 后单独对齐：Part 02 剩余语义（Context Management / Retry / Memory 与 Context）与 ROADMAP v0.3.0 / Part 02 index 差异，决定是否正式结束 Part 02
3. 补 tests/ 其余测试目标（State reducer、Tool adapter、Graph path、Checkpoint recovery）
4. 核验 Anthropic《Building effective agents》与 OpenAI practical guide 的官方 URL（第 0 章 TODO）
5. 选择许可证

## 当前阻塞

- 尚未确定真实 LLM 供应商
- GitHub Connector 当前不可直接写入
- v0.2.0 里程碑未完成（官方参考索引），按版本规则 CHANGELOG 暂处 Unreleased
