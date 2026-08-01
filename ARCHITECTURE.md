# ARCHITECTURE

## 项目结构

```text
enterprise-ai-agent-handbook/
├── .ai/
│   ├── context/
│   ├── tasks/
│   └── templates/
├── docs/
│   ├── adr/
│   └── ...
├── examples/
├── diagrams/
├── references/
├── tests/
├── AGENTS.md
├── ROADMAP.md
├── TERMINOLOGY.md
└── mkdocs.yml
```

## AI 协作流程

```mermaid
flowchart LR
    U[用户] --> AI[ChatGPT / Codex / Claude Code]
    AI --> A[读取 AGENTS.md]
    A --> C[读取 .ai/context]
    C --> T[读取任务]
    T --> W[修改文档/代码/测试]
    W --> S[更新 current.md]
    S --> D[必要时更新 decisions.md]
    D --> G[Commit / PR]
```

## Text-to-SQL 目标架构

```mermaid
flowchart TD
    A[用户问题] --> B[输入规范化]
    B --> C[意图与语义解析]
    C --> D[元数据/业务规则检索]
    D --> E[SQL 生成]
    E --> F[SQL 静态校验]
    F --> G{风险是否可接受}
    G -- 否 --> H[修复或人工审批]
    H --> E
    G -- 是 --> I[执行引擎路由]
    I --> J[Spark / Athena / BigQuery]
    J --> K[结果质量检查]
    K --> L{是否需要分析}
    L -- 是 --> M[Python 分析]
    L -- 否 --> N[结果组织]
    M --> N
    N --> O[结构化前端输出]
```

## 边界

- LangGraph：Agent 内部状态和控制流
- MCP：能力调用标准接口
- A2A：完整 Agent 之间的任务协作
- RAG：按需检索上下文
- Memory：跨步骤或跨会话保留信息
- Prompt：当前模型调用的输入约束
