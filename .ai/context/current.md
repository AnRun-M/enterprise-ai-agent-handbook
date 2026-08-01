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

## 正在进行

- 手写 Agent Loop Demo（`examples/manual_agent_loop`）
- LangGraph 等价 Demo（`examples/basic_langgraph`）
- 官方资料索引（`references/official/`）

## 下一步

1. 完成手写 Agent Loop（`examples/manual_agent_loop`，以第 0 章伪代码为蓝本）
2. 完成 LangGraph 最小等价实现（`examples/basic_langgraph`）
3. 增加对照文档与测试（tests/ 目前为空）
4. 固定 LangGraph 版本
5. 核验 Anthropic《Building effective agents》与 OpenAI practical guide 的官方 URL（第 0 章 TODO）
6. 选择许可证

## 当前阻塞

- 尚未固定 LangGraph 依赖版本
- 尚未确定真实 LLM 供应商
- GitHub Connector 当前不可直接写入
- v0.2.0 里程碑未完成（两个 Demo、官方索引），按版本规则 CHANGELOG 暂处 Unreleased
