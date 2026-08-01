# Current Session

日期：2026-08-01

阶段：`v0.2.0` 骨架收敛重构完成（章节正文尚未开写）

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

## 正在进行

- 第 0 章：《你已经写了一个 Agent，只是你不知道》（正文未开写）
- 手写 Agent Loop Demo（`examples/manual_agent_loop`）
- LangGraph 等价 Demo（`examples/basic_langgraph`）
- 官方资料索引（`references/official/`）

## 下一步

1. 完成第 0 章正文（骨架与规范已就绪）
2. 完成手写 Agent Loop（`examples/manual_agent_loop`）
3. 完成 LangGraph 最小等价实现（`examples/basic_langgraph`）
4. 增加对照文档与测试（tests/ 目前为空）
5. 固定 LangGraph 版本
6. 选择许可证

## 当前阻塞

- 尚未固定 LangGraph 依赖版本
- 尚未确定真实 LLM 供应商
- GitHub Connector 当前不可直接写入
- v0.2.0 里程碑未完成（第 0 章、Demo、官方索引），按版本规则 CHANGELOG 暂处 Unreleased
