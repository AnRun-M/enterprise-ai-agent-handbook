# TERMINOLOGY

## Agent

围绕目标接收输入、进行决策、调用能力、维护状态并返回结果的执行单元。

## Agent Loop

```text
读取状态 -> 决策 -> 执行动作 -> 更新状态 -> 判断是否继续
```

## Agent Runtime

负责执行 Agent Loop 的运行环境，包括状态、调度、工具、错误、Checkpoint、Interrupt、Streaming 和 Trace。

## Workflow

预定义步骤和控制关系的流程。可以包含 LLM，也可以不包含。

## State

一次任务执行中需要显式保存和传递的数据。

## Context

当前一次模型调用可见的信息。

## Memory

跨步骤、跨任务或跨会话保存的信息。

## Tool

Agent 可以调用的外部或确定性能力。

## MCP

Model Context Protocol。标准化模型或 Agent 与工具、资源、Prompt 等外部能力之间的连接。

## A2A

Agent-to-Agent Protocol。标准化完整 Agent 之间的发现、任务协作和结果交换。

## RAG

根据当前任务按需检索相关知识，再提供给模型。

## Checkpoint

在执行过程中保存可恢复状态的机制。

## Node

Graph 中的可执行处理单元。

## Edge

Graph 中的控制流关系。

## Reducer

定义同一 State 字段多个更新如何合并的函数。

## Human-in-the-loop

在关键步骤暂停，等待人工确认、修改或拒绝后继续。
