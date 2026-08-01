# Enterprise AI Agent Handbook

> 从手写 Agent Loop 到企业级 Agent Runtime：以 Text-to-SQL 为贯穿案例，系统理解 LangGraph、MCP、A2A、Memory、RAG 与生产级 Agent 工程。

## 项目定位

这不是一本只介绍 LangGraph API 的教程，而是一份面向企业落地的 AI Agent 架构与工程实践手册。

项目主线：

```text
手写 Agent Loop
  -> 显式 State
  -> 可测试 Workflow
  -> LangGraph Runtime
  -> Checkpoint / HITL / Observability
  -> MCP / A2A
  -> 企业级 Text-to-SQL Agent
```

贯穿案例的完整流程（T01-T12，唯一事实源）：[Text-to-SQL Canonical Pipeline](docs/04-text2sql/canonical-pipeline.md)。

## 先读什么

任何人或 AI 进入项目，先按顺序阅读：

1. `AGENTS.md`
2. `.ai/context/project.md`
3. `.ai/context/current.md`
4. `.ai/context/decisions.md`
5. `ROADMAP.md`
6. `ARCHITECTURE.md`
7. `TERMINOLOGY.md`

## 核心原则

- Architecture First
- Official Sources First
- Text-to-SQL First
- Runnable Examples
- Deterministic by Default
- Progressive Delivery
- AI-Native Collaboration

## 本地预览

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[docs]"
mkdocs serve
```

## 当前状态

版本：`v0.2.0`

当前阶段：AI-Native 仓库骨架初始化。
