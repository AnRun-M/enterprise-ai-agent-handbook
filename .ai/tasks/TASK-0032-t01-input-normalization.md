# TASK-0032：T01 输入规范化（Gate A：Architecture / Contract）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-11 |
| Updated | 2026-08-11 |
| Related ADR | ADR-0002（Text-to-SQL 唯一主案例）/ ADR-0004 / ADR-0005 |
| Related Task | TASK-0029（T01 = Wave 1）、TASK-0030（T05 首个 implementation task） |
| Related Example | examples/text2sql_state（默认载体）、examples/manual_agent_loop（State 基线） |

## 定位

Wave 1 并行任务之一（T01 / T03 均无 Strong dependency）。**本轮只完成 Gate A：Architecture / Contract 冻结——不写 implementation。**

---

## 一、仓库事实核对（2026-08-11）

- **canonical T01**：输入规范化——用户问题去噪、参数化、补充会话上下文（责任方：确定性代码）
- **AgentState 现状**（`examples/manual_agent_loop/state.py`）：`user_question` / `max_iterations` / `current_sql` / `validation_error` / `validation_rule` / `execution_result` / `final_answer` / `failure_reason` / `iteration` / `status` / `history`——**不存在 normalized 字段**
- **text2sql_state 现状**：README（待实现）+ `__init__` + `validation.py`（T05 已实现）——**无 T01 代码**
- **State 语义**（ch02 / state-design）：State = 一次执行控制事实唯一来源；影响下一轮控制决策的信息必须进入 State（architecture-map 判定问题 7）
- **canonical 顺序**：T01 → T02（意图解析）→ T03（检索）→ T04（生成）——T01 的输出是 T02 的输入

## 二、职责边界（冻结）

**T01 负责**（候选职责，以仓库设计为准）：

- 原始问题 trimming / whitespace normalization
- 空输入识别（明确失败语义，不静默）
- request-level canonical form（显式保存 original 与 normalized）
- 补充会话上下文（如需要——会话上下文来源本仓库未实现 Memory，标注为设计建议）

**T01 不负责**（明确边界）：

- Intent Classification（T02）｜Metadata Retrieval（T03）｜SQL Generation（T04）｜Validation（T05）｜Risk / Permission（T06）｜Repair（T07）

**Runtime 语义只引用不重定义**：State 字段进入 Text2SQLState（ch02 / ch09）；不改变 Part 03 Runtime 语义（ch08-18）。

## 三、Contract Status

`NormalizationResult` 仓库**不存在** → **Status = Proposed**。本轮只冻结：

- **Ownership**：T01 拥有"规范化输入"的职责与契约
- **Semantic responsibility**：原始问题 → 规范化问题的确定性转换（去噪 / whitespace / 空识别）
- **Minimum information needed by consumers**：T02（意图解析）需要可解析的规范化问题文本；Trace/Debug/Audit 需要原始问题保留

**不提前冻结复杂 schema**（字段结构在 Gate A Review 后由 Implementation 冻结）。

## 四、Contract 方案评估（重点判断）

**是否真的需要独立 `NormalizationResult` 类型？** 不因 TASK-0029 写了名字就创建 dataclass。三方案：

| 方案 | 形态 | consumer 数 | testability | contract clarity | serialization | backward compat | 抽象成本 |
|---|---|---|---|---|---|---|---|
| A. 直接 Graph State 字段 | `normalized_query` 等字段入 State | 1（T02）+观察 | 高（State 可断言） | 高（字段语义明确） | 原生 dict | 高（新字段追加不破坏 manual/basic） | 无 |
| B. 独立 NormalizationResult | 独立 dataclass 携带规范化结果 | 1（T02） | 中（需转换层） | 中 | 需序列化映射 | 中 | 中（单一消费者下过度） |
| C. 输入 schema / state channel 组合 | 字段入 State + 可选输入 channel 划分 | 1+ | 高 | 高 | 原生 | 高 | 低 |

**推荐方案：A + C（State 字段方案），不创建独立 NormalizationResult 类型。** 理由：consumer 仅 T02 一个（独立类型是 unnecessary abstraction）；State 可断言（testing-agent 原则）；字段语义即契约；新字段追加不破坏教学基线（backward compatibility 高）。归一化结果作为 State channel 字段（`normalized_query`，Proposed）。

**Architecture Decisions Required（Gate A Review 项）**：① 是否新增 `normalized_query` State 字段（推荐是）② 是否保留原始 `user_question` 不覆盖（推荐是，见五）③ 是否需要参数化产物字段（本轮不冻结，待 T02 消费需求确认）。

## 五、Original vs Normalized（冻结）

**原则：Normalization 不应静默破坏原始事实。**

- **保留 `user_question` = 原始输入**（不覆盖）
- 新增 `normalized_query`（Proposed）= 规范化结果
- 理由：Trace 还原 / Debug 原始上下文 / Audit 用户真实输入（architecture-map：history 是 State 组成部分，audit 事实由外部系统负责——但原始输入保留在 State 是还原的前提）

## 六、Idempotency（设计约束）

- **默认推荐**：`normalize(normalize(x))` 观察等价于 `normalize(x)`（deterministic + idempotent）
- 这是 normalization contract 的**设计约束**（可测试性 / 可重放），**不是 LangGraph 框架要求**（TASK-0029 冻结语义只引用）

## 七、Failure Semantics（冻结）

- **空输入识别**：空 / 仅空白输入 → 明确失败语义（类比 T05 total contract：任何输入稳定返回结构化结果，不抛异常）
- 不得靠空串 / None 混用 / 隐式 fallback 掩盖规范化失败——失败如何被 Runtime 看见（结构化失败标记）在 Gate A Review 确认

## 八、Evidence（四列制）

- **代码事实**：AgentState 无 normalized 字段；text2sql_state 无 T01 代码
- **测试事实**：manual state 测试（`test_state_is_pure_dataclass_no_globals` 等——State 卫生基线）
- **设计建议**：字段方案 / idempotent 约束 / original 保留（本文件）
- **尚未验证**：normalize 实现行为；空输入失败路径；与 T02 真实串联（Integration deferred）

## 九、Review Gate（统一）

Gate A Architecture / Contract（本文件）→ **等待 Architecture Review** → 通过后 Gate B Implementation（`examples/text2sql_state` 输入规范化实现 + 测试）→ Gate C → Gate D（Ch19 候选 T01 部分）→ Task Merge Gate → Gate E（等 T02 进 main，deferred → closed）。

## 验收标准（Gate A 阶段）

- [x] 仓库事实核对（canonical / AgentState / text2sql_state / State 语义）
- [x] 职责边界冻结（负责 / 不负责清单）
- [x] Contract Status（NormalizationResult = Proposed；只冻结 ownership / 语义职责 / 最少消费信息）
- [x] 三方案评估 + 推荐（A+C State 字段，不创建独立类型）
- [x] Original vs Normalized 边界（保留 user_question 原始输入）
- [x] Idempotency 设计约束（deterministic + idempotent，非框架要求）
- [x] Failure semantics（空输入明确失败，不静默）
- [x] Evidence 四列制；未写 implementation
- [ ] 等待 Architecture Review（含 3 项 Architecture Decisions Required）

## 完成记录

- 2026-08-11：任务创建（in_progress）；Gate A 完成；等待 Architecture Review（planning/wave1-t01-t03-contracts 分支，与 T03 同分支规划）。
