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

Wave 1 并行任务之一（T01 / T03 均无 Strong dependency）。**Gate A：Architecture / Contract 已冻结并通过 Review（PR #59 合并）；Gate B Implementation + Gate C Tests 已完成（feature/t01-input-normalization，本分支）；Gate D Documentation 已完成（第 19 章 T01 部分，draft）；Task Merge Gate / Gate E 待后续。**

---

## 一、仓库事实核对（2026-08-11）

- **canonical T01**：输入规范化——用户问题去噪、参数化、补充会话上下文（责任方：确定性代码）
- **AgentState 现状**（`examples/manual_agent_loop/state.py`）：`user_question` / `max_iterations` / `current_sql` / `validation_error` / `validation_rule` / `execution_result` / `final_answer` / `failure_reason` / `iteration` / `status` / `history`——**不存在 normalized 字段**
- **text2sql_state 现状**：README（待实现）+ `__init__` + `validation.py`（T05 已实现）——**无 T01 代码**
- **State 语义**（ch02 / state-design）：State = 一次执行控制事实唯一来源；影响下一轮控制决策的信息必须进入 State（architecture-map 判定问题 7）
- **canonical 顺序**：T01 → T02（意图解析）→ T03（检索）→ T04（生成）——T01 的输出是 T02 的输入

## 二、职责边界（冻结，Review 收窄）

**T01 = request / input canonicalization。负责**：

- trim
- whitespace canonicalization
- empty-input detection（明确失败语义，不静默）
- **不改变业务含义的 lexical normalization**（request-level canonical form；显式保存 original 与 normalized）

**T01 不负责**（Review 明确移出）：

- **conversation history injection**、Memory、user preference、tenant context、request context assembly、Model Context assembly——这些属于 **Context / Memory / request-scoped dependency 的后续组装**（ch03 Context Builder / ch07 Memory），不是 normalization
- **semantic parameter extraction**（见三）
- Intent Classification（T02）｜Metadata Retrieval（T03）｜SQL Generation（T04）｜Validation（T05）｜Risk / Permission（T06）｜Repair（T07）

**Runtime 语义只引用不重定义**：State 字段进入 Text2SQLState（ch02 / ch09）；不改变 Part 03 Runtime 语义（ch08-18）。

## 三、参数化归属（Review 修正）

**Lexical normalization ≠ Semantic parameter extraction**：

- 如果参数是 **metric / dimension / entity / time range / filters / intent facts**——**归 T02**（意图与语义解析），**不得由 T01 提取**
- 如果"参数化"仅指 **lexical canonicalization**（如统一空白、规范化引号）——**改名**，不继续使用容易混淆的"参数化"

**固定表述：**

> **T01 不做业务语义参数抽取；T01 只做不改变业务含义的 request normalization。结构化语义参数属于 T02。**

canonical T01 旧描述中的"参数化"按此解释（属于 T02 的语义参数抽取不在 T01 范围）。

## 四、Contract Status

`NormalizationResult` 仓库**不存在** → **Status = Proposed**。本轮只冻结：

- **Ownership**：T01 拥有"规范化输入"的职责与契约
- **Semantic responsibility**：原始问题 → 规范化问题的确定性转换（去噪 / whitespace / 空识别）
- **Minimum information needed by consumers**：T02（意图解析）需要可解析的规范化问题文本；Trace/Debug/Audit 需要原始问题保留

**不提前冻结复杂 schema**（字段结构在 Gate A Review 后由 Implementation 冻结）。

## 五、Contract 方案评估（重点判断）

**是否真的需要独立 `NormalizationResult` 类型？** 不因 TASK-0029 写了名字就创建 dataclass。三方案：

| 方案 | 形态 | consumer 数 | testability | contract clarity | serialization | backward compat | 抽象成本 |
|---|---|---|---|---|---|---|---|
| A. 直接 Graph State 字段 | `normalized_question` 等字段入 State | 1（T02）+观察 | 高（State 可断言） | 高（字段语义明确） | 原生 dict | 高（新字段追加不破坏 manual/basic） | 无 |
| B. 独立 NormalizationResult | 独立 dataclass 携带规范化结果 | 1（T02） | 中（需转换层） | 中 | 需序列化映射 | 中 | 中（单一消费者下过度） |
| C. 输入 schema / state channel 组合 | 字段入 State + 可选输入 channel 划分 | 1+ | 高 | 高 | 原生 | 高 | 低 |

**推荐方案：A + C（State 字段方案），不创建独立 NormalizationResult 类型。** 理由：consumer 仅 T02 一个（独立类型是 unnecessary abstraction）；State 可断言（testing-agent 原则）；字段语义即契约；新字段追加不破坏教学基线（backward compatibility 高）。归一化结果作为 State channel 字段（**`normalized_question`**，Proposed）。

**字段命名（Review 修正）**：**采用 `normalized_question`**——Text-to-SQL 中 query 一词后续容易表示 SQL query（规范化自然语言输入字段若以 query 命名，会与 `SQLCandidate` / `current_sql` 混淆）。固定语义：

> **`user_question` = 用户原始自然语言输入；`normalized_question` = 不改变业务含义的规范化自然语言输入。**

（除非仓库已有明确 naming convention 证明 query 统一表示自然语言输入——当前无此证据，故采用 `normalized_question`。）

**Architecture Decisions（Gate A 最终收敛，见十）**：① 新增 `normalized_question` State 字段：**YES** ② 保留原始 `user_question`：**YES** ③ semantic parameter extraction：**NO，属于 T02** ④ session-context assembly：**NO，不属于 T01** ⑤ empty-input failure：**复用已有 lifecycle/failure contract**（见四）。

## 六、Original vs Normalized（冻结）

**原则：Normalization 不应静默破坏原始事实。**

- **保留 `user_question` = 原始输入**（不覆盖）
- 新增 `normalized_question`（Proposed）= 规范化结果
- 理由：Trace 还原 / Debug 原始上下文 / Audit 用户真实输入（architecture-map：history 是 State 组成部分，audit 事实由外部系统负责——但原始输入保留在 State 是还原的前提）

## 七、Idempotency（保持）

- **继续保持**：`normalize(normalize(x))` 观察等价于 `normalize(x)`（deterministic + idempotent）
- **明确**：这是 **application contract / engineering property**（可测试性 / 可重放），**不是 LangGraph requirement**

## 八、Failure Contract（Gate A 冻结）

**empty / whitespace-only input = expected application input failure ≠ Runtime exception**：

- T01 **不应通过业务异常表达正常输入校验失败**——空输入是"应用输入无效"的预期结果，不是异常路径
- **优先复用已有 State lifecycle / failure contract**：`status` + `failure_reason`（ch02 / manual AgentState 既有语义）
- **不新造** `normalization_error` / `NormalizationFailureResult`——除非仓库事实证明现有契约无法承载；如无法承载，**标 Architecture Conflict，不自行扩 schema**
- 推荐语义（Gate B/C Review 修正 2026-08-11，Task Merge Gate Review 最终统一为 field ownership + transition authority 两层）：
  - **Field ownership**：`normalized_question` = **T01-owned derived field**（T01 始终拥有其派生值生命周期）；`status` / `failure_reason` = **shared lifecycle fields**（整个 Agent task 共享）。原则：**"Field write capability ≠ field ownership."**
  - **Transition authority**：T01 只拥有 **RUNNING + invalid input → FAILED** 这一个状态迁移；不拥有 FAILED → FAILED（新原因）、SUCCESS → FAILED、MAX_ITERATIONS_REACHED → FAILED 或任何其它 lifecycle replacement。原则：**"Shared field ownership can be transition-scoped, not field-wide."（共享字段的写权限可以只属于某个明确状态迁移）**
  - success（valid input）：`normalized_question` = value；**不更新 status / failure_reason**（合法 normalization 不得把任意 FAILED lifecycle 恢复为 RUNNING——permission / metadata / execution failure 非 T01 可重置）
  - failure（empty / whitespace-only）：**无条件** `normalized_question` = None（T01-owned 必须 invalidates stale 值）；**仅当 state.status is RUNNING 时**追加 `status` = FAILED + `failure_reason` = reason（invalid input 是预期 application failure，经 RUNNING → FAILED 迁移暴露给 shared lifecycle contract；不代表 T01 拥有 status/failure_reason 的完整生命周期）；已处于其它 lifecycle outcome 时**不得覆盖** shared lifecycle（不替换已有 failure cause、不把终止状态改成 FAILED）
  - lifecycle recovery（FAILED → RUNNING）属 new request initial state / retry / resume boundary / application lifecycle reset，不在 T01；已 FAILED 的原因也不由 T01 自动替换
  - 无语义解析（不进入 T02）由 failure outcome 表达

## 九、Evidence（四列制）

- **代码事实**：AgentState 无 normalized 字段；text2sql_state 无 T01 代码
- **测试事实**：manual state 测试（`test_state_is_pure_dataclass_no_globals` 等——State 卫生基线）
- **设计建议**：字段方案 / idempotent 约束 / original 保留（本文件）
- **尚未验证**：normalize 实现行为；空输入失败路径；与 T02 真实串联（Integration deferred）

## 十、Architecture Decisions（Gate A 最终收敛）

| # | Decision | 结果 |
|---|---|---|
| 1 | `normalized_question` State channel | **YES**（不创建独立 NormalizationResult 类型） |
| 2 | `user_question` 原始保留 | **YES**（不覆盖，Normalization 不静默破坏原始事实） |
| 3 | semantic parameter extraction | **NO，属于 T02**（T01 只做不改变业务含义的 request normalization） |
| 4 | session-context assembly | **NO，不属于 T01**（Context / Memory / request-scoped 组装是后续层） |
| 5 | empty-input failure | **复用已有 lifecycle/failure contract**（status + failure_reason；不新造 normalization_error 类型） |

## 十一、Review Gate（统一）

- Gate A Architecture / Contract：**completed**（PR #59 Architecture Review 通过并合并）
- Gate B Implementation（`examples/text2sql_state` 输入规范化实现）：**completed**（本分支，两轮 Review 修正后最终复审 APPROVED）
- Gate C Tests / Evidence：**completed**（pytest / ruff / mkdocs --strict 通过）
- Gate D Documentation（第 19 章 T01 可证实部分）：**completed**（`docs/04-text2sql/ch19-input-normalization-intent.md`，draft 状态；T02 部分 pending）
- **Task Merge Gate Review（两轮）**：发现 shared lifecycle ownership 修正（field ownership 两层：normalized_question = T01-owned；status / failure_reason = shared lifecycle；success 不覆盖 shared lifecycle）→ 最终复审进一步收窄为 **field ownership + transition authority**（T01 仅拥有 RUNNING + invalid input → FAILED 迁移；已 FAILED 的 cause 不替换、终止状态不改写）；**实现与文档正在修正，等待最终确认** → Task Merge → Gate E（等 T02 进 main，deferred → closed）

## 验收标准（Gate A 阶段）

- [x] 仓库事实核对（canonical / AgentState / text2sql_state / State 语义）
- [x] 职责边界冻结（负责 / 不负责清单——Review 收窄：不含会话上下文组装）
- [x] 参数化归属（lexical vs semantic 区分；semantic 归 T02）
- [x] Contract Status（NormalizationResult = Proposed；只冻结 ownership / 语义职责 / 最少消费信息）
- [x] 三方案评估 + 推荐（A+C State 字段 `normalized_question`，不创建独立类型）
- [x] Original vs Normalized 边界（保留 user_question 原始输入）
- [x] Idempotency（application contract / engineering property，非 LangGraph requirement）
- [x] Failure Contract 冻结（empty-input = expected application failure，复用 status + failure_reason，不新造类型）
- [x] Evidence 四列制；未写 implementation
- [x] Architecture Decisions 5 项收敛
- [x] 等待 Architecture Review 复审（**PR #59 通过并合并**）

## 完成记录

- 2026-08-11：任务创建（in_progress）；Gate A 完成；等待 Architecture Review（planning/wave1-t01-t03-contracts 分支，与 T03 同分支规划）。
- 2026-08-11：**PR #59 Architecture Review 修正**（commit：docs: refine wave1 input and retrieval contracts）：字段命名（**旧字段名 `normalized_query` 已修正为**）`normalized_question`（避免与 SQLCandidate / current_sql 混淆）；职责收窄（移除"补充会话上下文"——T01 = request/input canonicalization，会话上下文组装归 Context / Memory 层）；参数化归属（semantic parameter extraction 归 T02，T01 只做 lexical normalization）；Failure Contract 冻结（empty-input = expected application failure ≠ Runtime exception；复用 status + failure_reason，不新造 normalization_error / NormalizationFailureResult）；Idempotency 明确为 application contract 非 LangGraph requirement；Architecture Decisions 5 项收敛。
- 2026-08-11：**PR #59 合并（commit eb9d324，docs: freeze wave1 t01 t03 contracts）→ Gate A 正式通过**；T03 同分支规划文件随分支删除。
- 2026-08-11：**Gate B Implementation + Gate C Tests 完成（feature/t01-input-normalization）**：
  - State：`examples/text2sql_state/state.py` 新增 `Text2SQLState`（最小契约：`user_question` / `normalized_question` / `status` / `failure_reason`；生命周期复用 manual AgentStatus；不修改 manual/basic 教学基线）
  - 纯函数：`examples/text2sql_state/normalization.py` `normalize_question`（trim + whitespace canonicalization；空输入返回 None 显式失败标记；无任何语义改写）
  - Node adapter：`examples/text2sql_state/normalize_node.py` `normalize_input_node`（读 State → 调纯函数 → 返回 partial State Update；failure 复用 status=FAILED + failure_reason，不抛业务异常）
  - `__init__.py` 按 T05 惯例导出 T01 API
  - 测试：`tests/text2sql_state/test_normalization.py` + `test_normalize_node.py`（13 项核心 + 4 项边界；含 idempotency / determinism / partial update / 无跨调用污染 / over-normalization 边界）
  - Evidence：**Contract-level verified**；Integration = **deferred**（T02 尚未进 main，不宣称 T01→T02 integration verified）
  - 等待 Gate B/C Architecture + Implementation Review。
- 2026-08-11：**Gate B/C Review 修正已应用（feature/t01-input-normalization，等待最终复审）**：
  - **stale normalized_question 修复**：failure update 显式包含 `normalized_question: None`（Graph State merge 语义下"不返回字段"= "保留已有字段值"；不显式 invalidate 会让旧派生值在 merge 后残留，违反"empty input 不进入后续 semantic parsing"）。固定表述：**"failure 显式 invalidates derived normalized_question，防止旧派生值在 State merge 后残留"**（不再写"failure 时 normalized_question 不写入"）
  - **merge-semantics regression test**：`test_failure_invalidates_stale_normalized_question_after_merge`——初始 State 含 stale 值 + 空输入 → 断言 update 写 None 且模拟 `{**state, **update}` merge 后仍为 None
  - **partial update 边界区分 success/failure**：success 只写 `normalized_question`；failure 允许写 `normalized_question` + `status` + `failure_reason` 三个字段（`test_failure_partial_update_touches_only_contract_fields`）——**最终复审修正：本表述一度废弃**（success 曾改为三字段）**；Task Merge Gate Review 按 field ownership 恢复 success 只写 `normalized_question`**（见最终记录）
  - **evidence test 名称收窄**：`test_no_runtime_exception_on_any_input` → `test_node_handles_representative_string_inputs_without_exception`（有限 samples 不宣称"所有输入均无异常"；contract 与 test evidence 分开）
  - **whitespace policy 工程边界**：当前教学 contract 面向一般自然语言问题（连续 whitespace → 单空格）；不做 word rewriting / punctuation deletion / semantic extraction / SQL rewrite；不承诺 exact code blocks / whitespace-sensitive structured text / preformatted literals 的 whitespace-preserving 语义；不引入 quoted-string parser（`test_no_whitespace_preserving_promise_for_structured_text` 固定边界行为）
  - Gate B/C 状态保持：**等待 Review**；Status 仍 in_progress（Gate D / Merge / Gate E 未完成）。
- 2026-08-11：**Gate B/C 最终复审修正已应用（等待最终复审）**：
  - ~~**success 路径 stale failure state 修复**：success update 显式包含三字段 `{"normalized_question": <normalized>, "status": RUNNING, "failure_reason": None}`~~——**Task Merge Gate Review 推翻：此修正错误地把 shared lifecycle fields 当作 T01 私有 outcome 字段**（见最终记录，success 恢复只写 `normalized_question`）
  - ~~**success merge regression**：`test_success_clears_stale_normalization_failure_after_merge`~~——**已删除**（错误假定"合法 normalization 可以自动恢复任意 FAILED lifecycle"）
  - ~~**outcome update contract 统一**：success 与 failure 三字段对称 outcome tuple~~——**已废弃**（"Field write capability ≠ field ownership."；success 不覆盖 shared lifecycle）
  - **pure function 边界保持**：`normalize_question` 仍只返回 `str | None`；AgentStatus / failure_reason / Graph Runtime 完全不属于 pure function，lifecycle mapping 只属于 Node adapter
  - **current.md 下一步编号顺延清理**（1-10 无重复）
  - 其它复审结论保持：failure 显式 None / merge regression / representative-input evidence 命名 / whitespace policy boundary / 无 semantic extraction / 无 Context-Memory assembly / Integration deferred / T03 未实现
  - Gate B/C 状态保持：**等待最终复审**；Status 仍 in_progress（Gate D / Merge / Gate E 未完成）。
- 2026-08-11：**Gate B/C 最终复审 APPROVED**。
- 2026-08-11：**Gate D Documentation 完成（feature/t01-input-normalization）**：
  - 创建 `docs/04-text2sql/ch19-input-normalization-intent.md`（状态：**draft**，T01 部分；T02 pending 明确标注）——按 TASK-0029 Candidate Mapping（Ch19 = T01 + T02）只完成 T01 可证实部分
  - 结构 19.1-19.10：从原始请求到规范化输入 / Original vs Derived / Lexical Normalization Contract / Pure Function-Node Adapter / Outcome State Update / Stale State-Merge Semantics / Failure-Idempotency / Evidence 与测试边界 / T02 接口 / 当前边界
  - 固定主线逐字保持；四列制证据；已验证 12 项 / 未验证 6 项；正文不写死 pytest 数量
  - 关键工程语义落正文：完整 outcome update（success 清 stale failure / failure 清 stale normalized）+ merge 语义原则 + Whitespace Policy 冻结边界 + "T01 ends where semantic interpretation begins."——**Task Merge Gate Review 修正：正文已改为 field ownership 两层（success 不覆盖 shared lifecycle；failure 清理 T01-owned stale normalized）**
  - 3 张 Mermaid（pipeline / outcome→merge / stale 清理）——**修正后：outcome 图 success 分支只写 normalized_question；stale 图仅 failure 方向**
  - `docs/04-text2sql/index.md` 新增"输入与意图"分区；`mkdocs.yml` 新增第 19 章导航
  - content-map 未修改（仓库无 ch19-ch25 逐章行惯例，Part 4 聚合行保持"进行中"）
  - **未提前宣布 Chapter 19 completed**（T02 pending）；未修改 ROADMAP
  - Evidence：**Contract-level verified**；Integration：**deferred**
  - 等待 Task Merge Gate 最终 Review；Status 仍 in_progress。
- 2026-08-11：**Task Merge Gate Review 修正（feature/t01-input-normalization，field ownership 架构修正，等待最终复审）**：
  - **纠正 T01 field ownership**：`normalized_question` = **T01-owned derived field**（T01 始终拥有其派生值生命周期）；`status` / `failure_reason` = **shared lifecycle fields**（整个 Agent task 共享，非 T01 私有）。固定原则：**"Field write capability ≠ field ownership."**；**"Invalidate stale state according to field ownership, not superficial symmetry."（按字段所有权清理 stale state，而不是为了结果对称而对共享字段做对称覆盖）**——T01 曾在 failure 时写它们，不代表 T01 拥有全部 lifecycle authority
  - **success update 修正**：恢复为 `{"normalized_question": normalized}`——不得无条件写 RUNNING / failure_reason=None（State 当前 FAILED 可能是 permission / metadata / execution failure，T01 无权限把整个 task 恢复 RUNNING；不得通过字符串合法性重置全局 lifecycle）
  - **failure update 保持**：`{"normalized_question": None, "status": FAILED, "failure_reason": reason}`——两层理由：① normalized_question 是 T01-owned，必须 invalidates stale 值 ② invalid input 是预期 application failure，暴露给 shared lifecycle contract（不代表拥有后续恢复语义）——**最终复审修正：failure 对 shared lifecycle 的写入收窄为 transition-scoped（仅 RUNNING 时追加 status/failure_reason；已 FAILED 的 cause 不替换）**（见下一条记录）
  - **删除错误 regression**：`test_success_clears_stale_normalization_failure_after_merge`（错误假定合法 normalization 可自动恢复任意 FAILED lifecycle）
  - **新增 lifecycle non-overwrite regression**：`test_success_does_not_override_existing_lifecycle_state`——State 含 FAILED + "some unrelated failure" + 合法输入 → update 只有 normalized_question；merge 后 status 仍 FAILED / failure_reason 保留（T01 不越权）
  - **恢复 success partial-update contract test**：`test_success_partial_update_does_not_touch_other_fields`（set(update) == {normalized_question}；user_question / status / failure_reason 不覆盖）
  - **保留** `test_failure_invalidates_stale_normalized_question_after_merge`（normalized_question 是 T01-owned derived field，该测试仍有效）
  - **retry / new request boundary**：FAILED → RUNNING 不由 normalize_input_node 自动完成——属 new request initial state / retry / resume boundary / application lifecycle reset 显式建立新 RUNNING 上下文；具体 retry/resume 实现不在 T01 展开
  - **Chapter 19 修正**：19.5 outcome update 改 field ownership 两层表述（固定表述："T01 始终拥有 normalized_question 的派生值生命周期；status / failure_reason 是共享 lifecycle contract，T01 仅在 invalid-input failure 时写入，不在 success 时自动重置其它阶段可能产生的 lifecycle 状态"）；19.6 删除"success 必须清理 stale FAILED / failure_reason"，通用原则升级为按所有权清理；19.6 增加 retry/new-request boundary；19.8 Evidence merge simulation 收窄（Python dict overwrite 模拟当前无 reducer channel 的预期覆盖结果，**不是 actual LangGraph integration evidence**——T01 尚未接入 compiled graph 与 T02，实际 Graph Runtime integration 仍 deferred）
  - **同步**：TASK-0032 八 / 十一 / 完成记录、current.md、PR #60 Description 统一为 ownership 表述；删除"success 清理 stale failure / success 写 RUNNING / 三字段对称 outcome tuple / T01 owns status/failure_reason / 双向 stale-safe"旧事实
  - Gate 状态：**Gate A/B/C 已通过结论需按 field ownership 重新表述，实现与文档正在修正，等待最终复审**；TASK-0032 仍 in_progress。
- 2026-08-11：**Task Merge Gate 最终复审修正（transition-scoped lifecycle authority，等待最终确认）**：
  - **收窄 shared lifecycle authority**：T01 对 status / failure_reason 的写权限限定为**明确的状态迁移**——固定原则：**"Shared field ownership can be transition-scoped, not field-wide."（共享字段的写权限可以只属于某个明确状态迁移，而不是拥有整个字段生命周期）**
  - **冻结 T01 lifecycle transition authority**：T01 只拥有 **RUNNING + invalid input → FAILED + T01 failure_reason**；不拥有 FAILED → FAILED（新原因）、SUCCESS → FAILED、MAX_ITERATIONS_REACHED → FAILED 或任何其它 lifecycle replacement——**只有 state.status is RUNNING 且 normalization invalid 时** T01 才写 status / failure_reason
  - **实现行为**：`normalized_question` 始终由 T01 管理（success 写值 / failure 写 None）；`status` / `failure_reason` 仅在 RUNNING 时追加（`update.update(status=FAILED, failure_reason=...)`）；非 RUNNING 时 failure update 只有 `{"normalized_question": None}`
  - **测试三种 contract case**：Case A RUNNING+valid → 仅 normalized_question；Case B RUNNING+empty → 三字段；Case C 已 FAILED（"permission denied"）+ stale normalized + empty → 只清 normalized_question、不覆盖 status/failure_reason（merge 后 status 仍 FAILED、failure_reason == "permission denied"）——新增 `test_invalid_input_does_not_override_existing_failure_cause` / `test_non_running_failure_touches_only_normalized_question`
  - **覆盖其它非 RUNNING 状态**：参数化 `test_invalid_input_does_not_override_terminal_status`（SUCCESS / MAX_ITERATIONS_REACHED + empty input → 不改成 FAILED）——T01 的 failure authority 明确限定在 RUNNING → FAILED，不扩展 lifecycle enum
  - **修正 failure partial-update 测试**：不再写"failure 永远三字段"——RUNNING failure 三字段、non-RUNNING failure 仅 normalized_question（`test_running_failure_touches_normalized_and_lifecycle_contract_fields`）
  - **Chapter 19 修正**：19.5 增加 Transition authority 层（表格 + 固定表述："T01 始终拥有 normalized_question 的派生值生命周期；对于 shared status / failure_reason，T01 只拥有 invalid input 导致的 RUNNING → FAILED 状态迁移，而不拥有这些字段的完整生命周期"）；19.6 stale-state 原则升级为 **"Invalidate stale state according to field ownership and transition authority."（按字段所有权与状态迁移权限处理 stale state）** + "已 FAILED 的原因也不由 T01 自动替换"；19.7 failure 表述加 RUNNING 前提；19.8 已验证列表更新
  - **清理旧事实**：failure 永远三字段 / invalid input 无条件覆盖 lifecycle / T01 在任何状态都可写 FAILED / shared lifecycle fields 在 failure 时无条件由 T01 写入
  - Evidence：dict overwrite 仍只是 State Update contract simulation，≠ actual Graph Runtime integration；Integration 仍 deferred
  - retry boundary 保持：FAILED → RUNNING 由 new request / retry / resume / application lifecycle reset 负责；已 FAILED 的原因不由 T01 自动替换
  - Gate 状态：**实现与文档正在修正，等待 Task Merge Gate 最终确认**；TASK-0032 仍 in_progress。
