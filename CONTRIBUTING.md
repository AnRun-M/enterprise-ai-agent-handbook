# CONTRIBUTING

协作规则唯一事实源是 `AGENTS.md`，本文只保留人工流程摘要。

## 流程

1. 阅读 `AGENTS.md` 与 `.ai/context/`（强制）
2. 创建或认领任务文件（`.ai/tasks/`，见 `.ai/templates/task-template.md`）
3. 完成任务（文档、代码、测试）
4. 按影响范围更新记忆文件（每次任务至少更新 `.ai/context/current.md`；完整规则见 `AGENTS.md`）
5. 提交 PR

## 分支命名

```text
docs/chapter-agent-runtime
feat/text2sql-sql-validator
test/sql-validator-cases
refactor/tool-registry
```

## PR 必须说明

- 解决的问题
- 主要改动
- 设计理由
- 测试方法
- 对项目记忆的影响
- 尚未解决的问题
