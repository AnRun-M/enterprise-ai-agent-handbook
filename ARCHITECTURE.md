# ARCHITECTURE

## 项目结构

```text
enterprise-ai-agent-handbook/
├── .ai/                    # AI 项目记忆（不属于书籍正文）
│   ├── context/            # project / current / decisions 索引
│   ├── tasks/
│   └── templates/
├── docs/                   # 正式出版内容（MkDocs 文档站）
│   ├── adr/                # ADR 唯一事实源（ADR-####-*.md）
│   ├── 00-introduction/    # 含 content-map.md（章节—示例—测试映射）
│   ├── 01-agent-foundations/
│   ├── 02-agent-runtime/
│   ├── 03-langgraph-core/
│   ├── 04-text2sql/        # 含 canonical-pipeline.md（流程唯一事实源）
│   ├── 05-production/
│   ├── 06-mcp-a2a/
│   └── 07-ai-coding/
├── examples/               # 可运行示例（下划线包命名，可被 Python 导入）
├── references/             # 未发布研究素材与官方资料索引
├── tests/
├── AGENTS.md               # AI 协作规则唯一事实源
├── ROADMAP.md
├── TERMINOLOGY.md
├── CHANGELOG.md
├── README.md
└── mkdocs.yml
```

## 内容边界

- `docs/`：正式出版内容，由 MkDocs 构建发布。
- `references/`：未发布的研究素材与官方资料索引，不属于书籍正文。
- `.ai/`：AI 项目记忆，帮助 AI 跨会话保持上下文，不属于书籍正文。

## AI 协作流程

协作规则唯一事实源：`AGENTS.md`（强制读取顺序、按影响范围更新、ADR 规则、命名规则），此处只保留摘要：

1. 按 `AGENTS.md` 强制顺序读取
2. 读取或创建任务（`.ai/tasks/`，见模板）
3. 修改文档 / 代码 / 测试
4. 按影响范围更新记忆文件（每次任务至少更新 `current.md`）
5. Commit / PR

## Text-to-SQL 目标架构

完整流程的唯一事实源：`docs/04-text2sql/canonical-pipeline.md`（T01-T12，含风险分支与 Mermaid 图）。

摘要：

```text
用户问题 -> 输入规范化 -> 意图与语义解析 -> 元数据/业务规则检索
-> SQL 生成 -> SQL 静态校验 -> 权限与风险检查 -> 修复或人工审批
-> 执行引擎路由 -> Spark / Athena / BigQuery -> 结果质量检查
-> Python 分析 -> 结构化输出
```

## 边界

- LangGraph：Agent 内部状态和控制流
- MCP：能力调用标准接口
- A2A：完整 Agent 之间的任务协作
- RAG：按需检索上下文
- Memory：跨步骤或跨会话保留信息
- Prompt：当前模型调用的输入约束
