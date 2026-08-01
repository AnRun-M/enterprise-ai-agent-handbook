# AGENTS.md

## 项目使命

构建一份长期可维护的企业级 AI Agent 架构与工程实践手册，并配套可运行示例。

## AI 强制读取顺序

任何 AI 修改项目之前必须读取：

1. `AGENTS.md`
2. `.ai/context/project.md`
3. `.ai/context/current.md`
4. `.ai/context/decisions.md`
5. `ROADMAP.md`
6. `TERMINOLOGY.md`
7. 当前任务相关文件

禁止仅依赖聊天上下文直接修改仓库。

## AI 完成任务后的强制动作

每次完成任务后：

1. 更新 `.ai/context/current.md`
2. 若产生长期决策，更新 `.ai/context/decisions.md`
3. 若改变路线，更新 `ROADMAP.md`
4. 若新增术语，更新 `TERMINOLOGY.md`
5. 若改变架构，更新 `ARCHITECTURE.md`
6. 若版本行为变化，更新 `CHANGELOG.md`

## 写作规范

每章优先使用：

1. 本章解决什么问题
2. 从现有 Text-to-SQL 系统出发
3. 不使用框架时如何实现
4. LangGraph 如何抽象
5. 执行流程图
6. 最小可运行示例
7. 生产级版本
8. 常见错误
9. 适用边界
10. 官方参考
11. 验收标准

## 内容约束

必须：

- 先讲为什么，再讲 API
- 区分确定性流程与模型自主决策
- 明确哪些规则必须由程序保证
- 讨论权限、安全、幂等、重试、超时、恢复和可观测性
- 版本相关事实必须核验
- 优先引用官方文档、规范和源码

禁止：

- 使用无关天气 Demo 作为主案例
- 把所有规则都塞进 Prompt
- 把多个函数简单称为多 Agent
- 把 MCP 解释为 Agent Runtime
- 把 A2A 解释为 LLM API
- 声称框架消除上下文成本

## 代码规范

- Python 3.11+
- 必须有类型标注
- 关键路径必须有错误处理
- SQL 默认只读
- 不允许硬编码密钥
- Tool 输入输出优先结构化
- LLM 和执行引擎支持依赖注入
- 核心逻辑必须可测试

## Text-to-SQL 安全底线

- 只允许 `SELECT`
- 禁止 DDL / DML / DCL
- 限制扫描量、执行时间和返回行数
- 必须做语义层和权限校验
- 必须记录 SQL、引擎、耗时和错误
- 高风险查询支持人工审批
- 未校验 SQL 不得直接进入生产执行
