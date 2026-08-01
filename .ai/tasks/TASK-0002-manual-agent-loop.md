# TASK-0002：手写 Text-to-SQL Agent Loop Demo

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0004（确定性约束由代码保证） |
| Related Chapter | 第 0 章 |
| Related Example | examples/manual_agent_loop |
| Related Test | tests/manual_agent_loop |

## 目标

实现一个最小但工程结构清晰的手写 Agent Runtime，演示 Agent Loop、State 传递、模型决策转动作、Tool 调用、修复循环、最大迭代终止与错误处理；围绕 Text-to-SQL 场景，全部使用 Fake / Deterministic 组件。

## 需要新增

- `examples/manual_agent_loop/`：types / config / state / models / tools / runtime / agent / main / README
- `tests/manual_agent_loop/`：test_agent_loop.py、test_validator.py
- `tests/conftest.py`（仓库根目录可导入）
- `.github/workflows/tests.yml`（pytest + ruff 门禁）

## 需要修改

- `docs/00-introduction/content-map.md`（manual_agent_loop 状态一行）
- `ROADMAP.md`（勾选「手写 Agent Loop Demo」）
- `.ai/context/current.md`

## 约束

- 不接真实 LLM、不使用 API Key、不访问真实数据库
- 不实现 LangGraph / MCP / A2A / RAG / Memory
- 不修改第 0 章正文
- 校验器为教学级，README 必须声明生产级安全要求
- 依赖优先只用 Python 标准库；测试可用 pytest
- 配置不读取真实密钥

## 验收标准

- [x] `python -m examples.manual_agent_loop.main` 可运行且输出可复现
- [x] `pytest` 通过（首轮失败第二轮修复 / 最大迭代终止 / 非 SELECT 拒绝 / 缺 LIMIT 拒绝 / 固定 GMV / history 事件）
- [x] `ruff check .` 通过
- [x] `mkdocs build --strict` 通过
- [x] PR #2 已创建并推送（https://github.com/AnRun-M/enterprise-ai-agent-handbook/pull/2），tests/docs CI 双绿
- [ ] Architecture Review 通过（Blocker：failure_reason、Executor 加固——已修复待复审）
- [ ] PR #2 Merge 到 main
- 合并前不得标记 completed
