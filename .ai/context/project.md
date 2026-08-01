# Project Context

## 项目名称

Enterprise AI Agent Handbook

## 项目目标

帮助读者理解“开发一个 Agent 到底在开发什么”，并将手写 Text-to-SQL Agent 逐步演进为可观测、可恢复、可测试的企业级系统。

## 目标读者

- 大数据开发工程师
- Text-to-SQL 开发者
- Agent 平台开发者
- 熟悉 LLM API，但对 Runtime、Memory、MCP、A2A 边界不清楚的工程师

## 贯穿案例

以 Text-to-SQL 为唯一贯穿案例。完整流程的唯一事实源：[canonical-pipeline.md](../../docs/04-text2sql/canonical-pipeline.md)（T01-T12，含风险分支）。

摘要：

```text
用户问题 -> 输入规范化 -> 意图与语义解析 -> 元数据/业务规则检索
-> SQL 生成 -> SQL 静态校验 -> 权限与风险检查 -> 修复或人工审批
-> 执行引擎路由 -> Spark / Athena / BigQuery -> 结果质量检查
-> Python 分析 -> 结构化输出
```

## 长期原则

- 架构优先于 API
- 业务规则不能全部依赖 Prompt
- 能确定性完成的步骤，不交给模型自由决策
- 多 Agent 不是默认方案
- 所有章节必须回到 Text-to-SQL 场景
