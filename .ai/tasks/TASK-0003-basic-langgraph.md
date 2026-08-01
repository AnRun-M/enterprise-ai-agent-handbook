# TASK-0003：LangGraph 等价 Text-to-SQL Agent Demo

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0003（LangGraph 是核心实践框架，但不是唯一主题） |
| Related Chapter | 第 0 章、Part 3（LangGraph Core） |
| Related Example | examples/basic_langgraph |
| Related Test | tests/basic_langgraph |

## 目标

把 `examples/manual_agent_loop/` 的手写 Agent Loop 迁移为**行为等价**的 LangGraph Graph API 实现：相同业务场景、相同 Fake 组件（复用，不复制）、相同输入、相同最终结果、相同终止状态、相同最大迭代约束。固定 `langgraph==1.2.9`。

## 需要新增

- `examples/basic_langgraph/`：state / nodes / routing / graph / agent / main / README
- `tests/basic_langgraph/test_langgraph_agent.py`（含与 manual 版的直接对照测试）
- `references/official/langgraph.md`（版本核验记录）
- `docs/03-langgraph-core/manual-vs-langgraph.md`（对照文档）+ mkdocs nav
- `.ai/tasks/TASK-0003-basic-langgraph.md`（本文件）

## 需要修改

- `pyproject.toml`：`dependencies = ["langgraph==1.2.9"]` + `[tool.setuptools] packages = []`
- `.github/workflows/tests.yml`：`pip install -e ".[dev]"`（单一依赖事实源）
- `ROADMAP.md`、`docs/00-introduction/content-map.md`、`.ai/context/current.md`

## 约束

- 不引入 LangChain（langgraph 自带 langchain-core 传递依赖，代码不使用其 API）
- 不使用预构建 Agent API（create_react_agent 等）
- 不使用 Checkpointer / Memory / HITL / Streaming / Subgraph / MCP / A2A / 真实 LLM
- 不修改 manual_agent_loop 行为、不复制 Fake 工具实现
- 不修改第 0 章正文

## 验收标准

- [x] `python -m examples.basic_langgraph.main` 输出与 manual 版一致
- [x] `pytest` 通过（含等价对照、off-by-one、无状态污染、reducer、错误边界）
- [x] `ruff check .` 通过
- [x] `mkdocs build --strict` 通过
- [x] `langgraph` 版本验证输出 1.2.9
- [x] PR #4 创建并等待架构审查（不 Merge）
- [x] Architecture Review 通过（Blocker 全部修复并复审通过：decide 节点恢复模型决策语义、节点级异常转换保留异常前 State、终止状态守卫）
- [x] PR #4 squash merge 到 main（commit 5c1d627），远程 feature/basic-langgraph 已删除
- 合并后方可标记 completed（本次已合并）
