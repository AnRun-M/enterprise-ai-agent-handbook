# LangGraph 官方资料核验记录

## 核验信息

- 核验日期：2026-08-01
- 固定版本：`langgraph==1.2.9`（PyPI，精确固定，不允许 `>=` / `~=`）
- Python 要求：`>=3.10`（本仓库 requires-python `>=3.11`，CI 使用 3.11，满足）
- 运行时依赖（PyPI 元数据）：`langchain-core>=1.4.7,<2`（传递依赖，本仓库代码不使用 LangChain API）、`langgraph-checkpoint>=4.1.0,<5`、`langgraph-prebuilt>=1.1.0,<1.2`、`langgraph-sdk>=0.4.2,<0.5`、`pydantic>=2.7.4`、`xxhash>=3.5.0`

## 官方文档名称

- LangGraph Graph API（State / Node / Edge / Conditional Edge / START / END / compile / invoke）：https://docs.langchain.com/oss/python/langgraph/graph-api （2026-08-01 核验）
- LangGraph 安装与其余概念页面位于同一官方文档站：https://docs.langchain.com/oss/python/langgraph （发布前复查具体页面路径与最新版本）

## 本 Demo 使用的 API

- `langgraph.graph.StateGraph`
- `langgraph.graph.START` / `langgraph.graph.END`
- `add_node` / `add_edge` / `add_conditional_edges`（含 path map）
- `compile()` / `.invoke(state)`
- TypedDict State schema + `Annotated[list[StepEvent], operator.add]` reducer

## 未使用的高级能力（刻意）

- Checkpointer / Checkpoint（恢复）
- Interrupt（Human-in-the-loop）
- Streaming（`astream` / `astream_events`）
- `Send` / `Command`（动态 fan-out / 状态更新 + 路由组合）
- Subgraph
- RetryPolicy / fallback
- RecursionLimit 调整（本 Demo 用业务 `max_iterations` 控制，不使用图递归上限）

## 版本升级前需要重新验证的项目

1. `add_conditional_edges` 签名与 path map 行为
2. TypedDict State + `Annotated` reducer 的合并语义（是否仍为 old + new 追加）
3. `invoke` 返回类型与缺失 channel 的处理
4. `tests/basic_langgraph/` 全量通过（尤其迭代 off-by-one 与等价对照测试）
5. `tests/manual_agent_loop/` 不受影响（不依赖 langgraph）
6. `references/official/langgraph.md` 本文件同步更新核验日期与版本
7. 升级时以官方 changelog / migration guide 为准，升级后重新跑 `mkdocs build --strict`
