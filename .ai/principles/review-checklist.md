# Architecture Review Checklist

本清单沉淀自 PR #2 与 PR #4 的真实 Review。**按影响范围引用**：不是每个 PR 都逐项检查全部条目（见 Applicability 一节）。

> 2026-08-14（TASK-0035）：新增 `## Contract & Boundary` section（CB1-CB12），
> 沉淀 T01/T02/T03/T05 Review 反复验证的通用契约原则；保留原有 R/S/D/T/G/P/C 体系，不推翻。

## Runtime

- [ ] **R1. Loop 是否唯一**：循环只存在于 Runtime（manual `runtime.py` / graph 条件边回路）；节点与业务代码无隐藏 while 或隐式循环（PR #4 Review Focus："节点是否有隐藏控制流"）
- [ ] **R2. Dispatch 是否集中**：动作分发只有一处（`_dispatch` / `route_by_next_action`），没有散落的 if/elif 替代分发

## State

- [ ] **S1. State 是否唯一事实来源（执行控制状态范围）**：跨轮次的执行控制信息全部在 State；无全局变量、无聊天上下文依赖；不复制外部业务事实进 State（ADR-006；`test_state_is_pure_dataclass_no_globals`）
- [ ] **S2. History 是否完整**：每轮事件含 iteration / action / status / sql / validation_error / note；reducer 无重复追加、顺序保持（PR #4 Review Focus："reducer 是否正确"）
- [ ] **S3. Failure 是否保存**：所有失败路径（执行失败 / 模型或工具异常 / 未知动作）在最终 State 有 `failure_reason`（PR #2 Review Blocker 1）
- [ ] **S4. Iteration 是否 off-by-one**：与手写语义逐轮一致；`max_iterations` 达到时不得进入下一轮、不得执行 finalize（PR #4 Review Focus；`test_max_iterations_2_stops_before_finalize`）

## Decision 与 Tool

- [ ] **D1. Decision 是否属于模型（开放式语义决策）**：`decide_next()` 由模型执行，路由 / 业务代码不得替代（PR #4 Review Blocker 1；`test_model_decision_finalize_is_routed`）
- [ ] **D2. 确定性策略层是否由代码拥有**：权限、安全、预算、超时、审批、终止、补偿必须由代码保证（ADR-004；`route_decide_or_max` 上限检查、`AGENTS.md` 安全底线）
- [ ] **T1. Tool 是否有独立边界**：工具纵深防御独立实现（Validator 与 Executor 各自把关，PR #2 Review Blocker 2 与 SELECT 首 token Review）；工具实现不得复制（TASK-0003 禁止项）

## Graph 与等价性

- [ ] **G1. Graph 是否真正行为等价**：有与手写版的直接对照测试，断言 status / SQL / result / answer / iteration / action 序列（PR #4 Review Focus；`test_direct_equivalence_with_manual`）
- [ ] **G2. Memory 是否污染**：重复 invoke 无跨请求状态污染；无 Checkpointer 时每次全新初始 State（PR #4 Review Focus："State 是否发生跨请求污染"；`test_no_cross_invoke_pollution`）

## Contract & Boundary（TASK-0035 新增，T01/T02/T03/T05 已反复验证的通用原则）

- [ ] **CB1. Static annotation ≠ runtime validation**：涉及 domain object / dataclass / Typed Contract 时——Enum discriminant 是否 runtime validate；payload container 是否 validate；leaf type 是否 validate；direct constructor 是否能绕过 factory invariant（T02 `SemanticValue` / `RetrievalRequirement` / `IntentResult` `__post_init__`）
- [ ] **CB2. Discriminant + payload shape**：有 tagged/domain state 时，不仅检查状态标签，还检查该状态允许携带的 payload shape（如 `AMBIGUOUS_CANDIDATES` 只能带 ≥2 候选、`resolved` 恒 None）
- [ ] **CB3. Cross-field invariant**：固定 "Payload shape validity ≠ semantic combination validity."——category/purpose、state/payload、outcome/unresolved fields 不得各自合法但组合非法（T02 `_CATEGORY_PURPOSE_MATRIX`）
- [ ] **CB4. Factory ≠ contract boundary**：factory convenience 不能是 domain invariant 唯一保障；direct constructor 必须遵守相同 contract（"Factory convenience must not be the only thing enforcing a domain invariant."）
- [ ] **CB5. Field write capability ≠ field ownership**：Node 写过某字段 ≠ Node 拥有整个字段 lifecycle；shared lifecycle 字段必须明确 transition authority（T01 `normalized_question` / shared `status` 模式）
- [ ] **CB6. Stale derived state invalidation**：derived state 必须按 field ownership + transition authority 处理 stale value；不得为了"表面对称"清理不属于本 Node 的 shared field（T01 显式写 None / T02 整体 overwrite）
- [ ] **CB7. Interpretation ≠ authoritative fact**：模型 / parser 产生的 interpretation / candidate / intent 不得写成 authoritative business fact（T02 "Semantic interpretation is structured inference, not authoritative fact."）
- [ ] **CB8. Semantic resolution ≠ grounding completeness**：语义已解析不代表 timezone / calendar / business rule / schema / permission 等执行事实已齐全（T02 `GROUND_EXECUTION_CONTEXT`）
- [ ] **CB9. Data contract ≠ routing**：Requirement / Outcome / Decision Data 不得自动拥有 route / invoke downstream / retry / terminate 权限（T02 "Retrieval requirement is data, not routing."；T03 Outcome ≠ Agent lifecycle）
- [ ] **CB10. Domain validity ≠ adapter/source availability**：domain object 合法与当前 adapter 是否有 mapping 必须分层（T02 `RetrievalRequirement` 不预检 adapter vocabulary）
- [ ] **CB11. Identity ≠ freshness/version evidence**：涉及 provenance 时，lookup key / source identity / fact identity / version-freshness evidence 不得混为一体（T03 `fact_id` / `key` / `evidence` 分离）
- [ ] **CB12. Evidence honesty**：必须区分 unit/contract evidence、adapter evidence、integration evidence、compiled runtime evidence、real-source evidence、production evidence；不得用前者替代后者（T01/T03 "Contract-level verified；Integration deferred"）

## 测试与 CI

- [ ] **P1. 测试是否覆盖行为**：断言 State Transition，而非 Prompt 内容（见 testing-agent.md）
- [ ] **C1. CI 是否验证**：`tests.yml`（pytest + ruff）与 `docs.yml`（mkdocs build --strict）在 PR 上双绿；本地统一入口 `python scripts/verify.py`

## Applicability（按影响范围引用）

| PR 类型 | 必须检查的条目 | 可跳过 |
|---|---|---|
| Runtime / State / Agent 代码 PR | R1-R2、S1-S4、D1-D2、T1、G1-G2、P1、C1 | 无 |
| **Domain Contract / Schema PR** | **CB1-CB6、必要时 CB7-CB12、P1、C1** | R2、S4、G2 等纯代码条目 |
| **Integration / Adapter PR** | **CB7-CB12、C1** | CB1-CB4（除非新增 domain 类型） |
| **Documentation PR** | **正文描述 contract / state / integration evidence 时检查对应 CB 条目**（不能因为"只是文档"跳过 Contract 一致性）、C1 | 纯叙事条目 |
| 概念文档 PR | 相关原则（runtime-design / state-design / llm-vs-runtime 对应条目）、C1 | R2、S4、G2 等纯代码条目 |
| 纯维护 PR（改名 / 依赖 / CI） | 范围、构建、CI（C1） | 全部行为条目 |

Review 评论中注明引用的条目编号即可，不要求逐项复述。

## 强制 Review 使用方式（TASK-0035）

- 每个 implementation PR 的 **PR Description 或 TASK Review Gate** 必须增加 **"Applicable Review Checklist"** 一行，例如：

  ```
  Applicable: CB1 / CB2 / CB3 / CB5 / CB10 / C1
  ```

- Review 时按条目编号引用，不要求把全部 checklist 粘贴进 PR
- 目标：Review principle 从"记忆在 Reviewer 脑中"变为"显式引用"

## 引用

- PR #2 Architecture Review：failure_reason 进入 State（Blocker 1）、Executor 最小安全检查（Blocker 2）、SELECT 首 token 严格匹配（后续 Review）
- PR #4 Architecture Review：模型决策语义（Blocker 1）、节点级异常转换保留 State（Blocker 2）
- T01/T03/T05 Review（TASK-0032/0033/0030）：field ownership / transition authority / fact identity 分离 / Outcome ≠ lifecycle
- T02 Review（TASK-0034）：CB1-CB12 全部原则的逐轮沉淀
- 本集其他文档：runtime-design / state-design / llm-vs-runtime / testing-agent
