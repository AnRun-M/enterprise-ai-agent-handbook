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

## 正在进行

- LangGraph 等价 Demo（`examples/basic_langgraph`）——实现完成，PR #4 待架构审查
- 官方资料索引（`references/official/`）

## 下一步

1. 等待 PR #4（basic_langgraph）架构审查通过后 Merge
2. 正式进入 Chapter 01（docs/01-agent-foundations/ch01-*，主题以任务书为准）
3. 补 tests/ 其余测试目标（State reducer、Tool adapter、Graph path、Checkpoint recovery）
4. 核验 Anthropic《Building effective agents》与 OpenAI practical guide 的官方 URL（第 0 章 TODO）
5. 选择许可证

## 当前阻塞

- 尚未固定 LangGraph 依赖版本
- 尚未确定真实 LLM 供应商
- GitHub Connector 当前不可直接写入
- v0.2.0 里程碑未完成（basic_langgraph 等价 Demo、官方参考索引），按版本规则 CHANGELOG 暂处 Unreleased
