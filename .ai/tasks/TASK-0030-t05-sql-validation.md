# TASK-0030：T05 SQL 静态校验（implementation task，首个）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-08 |
| Updated | 2026-08-08 |
| Related ADR | ADR-0004（确定性约束优先由代码保证）/ ADR-0005 |
| Related Task | TASK-0029（T01-T12 Execution Planning：T05 = Wave 1，Contract Status = Existing-to-evolve，首推） |
| Related Example | examples/text2sql_state（默认载体候选）、examples/manual_agent_loop（教学基线，ValidationResult 来源） |
| Related Test | tests/manual_agent_loop/test_validator.py（8 用例回归基线） |

## 定位

T01-T12 中**首个 implementation task**（TASK-0029 规划确认）。实施顺序**固定**：

> **Gate A Contract 冻结 → Implementation → Unit/Regression/Failure tests → Documentation → Merge → 等 T06/T07 进入 main 后做 Gate E Integration Closure**

**核心边界（必须守住）**：`ValidationResult = Existing-to-evolve`——T05 **不是"新造一个 validator 模型"**，而是**深化已有 contract**（`examples/manual_agent_loop/types.py` 的 `ValidationResult`），并**尽量保持 backward compatibility**。这是 T07 修复循环能否稳定的关键（`validation_rule` 是修复分支的输入，ch02 2.4 教训）。

---

## 一、Gate A：Architecture / Contract 冻结（当前阶段交付物）

**本阶段只冻结契约，不写代码、不改字段结构。**

### 1.1 ValidationResult 职责边界（冻结）

- **职责**：SQL 静态校验（canonical T05）的**结构化输出契约**——确定性代码产出（ADR-004：校验规则由代码保证，不交模型）
- **边界**：只表达"校验结果"（ok / error / rule）；**不表达**业务事实（权限、语义层口径——T06/T03 职责）、不表达执行结果（T09）、不改变 Part 03 Runtime 语义（ch08-18 冻结，仅引用）
- **输入**：待校验 SQL 字符串（候选 SQL 来自 T04 生成或 T07 修复——canonical 顺序）
- **输出**：`ValidationResult(ok, error, rule)`
- **消费方**：修复循环（T07 以 `validation_rule` 驱动修复分支——ch02 2.4 教训：决策需要什么信息，契约就必须显式携带）；生成（T04 以校验反馈修正候选）

### 1.2 输入输出 Contract（冻结，字段结构不在此阶段修改）

| 字段 | 现语义（manual types） | 兼容策略 |
|---|---|---|
| `ok: bool` | 校验是否通过 | **保留，不破坏** |
| `error: str | None` | 校验失败消息（给展示与审计） | **保留，不破坏** |
| `rule: str | None` | 失败规则名（给修复决策） | **保留，不破坏**——T07 修复分支的输入 |

**深化方向（Gate A 只声明，不改结构）**：新校验规则（结构 / 只读 / 行数限制）复用一个 `rule` 名空间；如后续需携带更多信息，以**向后兼容扩展**方式在 Implementation 的 Gate A 复审中决定（默认：优先复用现有三字段，避免新增字段破坏消费方）。

### 1.3 兼容策略（冻结）

- **backward compatibility 优先**：现有三字段（ok / error / rule）语义与构造方式不变；已消费方（manual runtime、修复循环）零改动
- **Existing-to-evolve 的含义**：深化 = 扩展规则集与校验器实现，**不是**改契约形状；若确需字段扩展，须在 Gate A 复审提出并经 Architecture Decision（默认不扩）
- **教学基线不动**：`manual_agent_loop` 的 `FakeSQLValidator` / `ValidationResult` 原则上不修改（矩阵 R）；T05 的深化实现落在 `examples/text2sql_state`（默认载体候选，目录结构在首个 implementation 前经 architecture adjustment 确定——本次以单包起步）

### 1.4 测试证据基线（冻结）

**已有证据（引用，非计划）**——`tests/manual_agent_loop/test_validator.py` 8 用例：
非 SELECT / missing LIMIT / LIMIT 超限 / 多语句 / 空 SQL / 通过（含 LIMIT）/ 尾分号 / 列名不触发关键字规则。

**新增测试（计划，Implementation 阶段）**：规则矩阵 Unit（每条规则一用例）+ Failure Case（组合失败）+ Regression（8 用例基线延续）+ 兼容性断言（新校验器输出仍满足三字段契约）。

### 1.5 Gate A 检查清单（自检）

- [x] 不改变 Part 03 Runtime 语义（仅引用）
- [x] ValidationResult 职责边界明确（校验结果契约，非业务事实）
- [x] 输入输出 contract 冻结（三字段保留）
- [x] 兼容策略冻结（backward compatibility 优先；教学基线不动）
- [x] 测试证据基线（已有 8 用例）与新增计划分列
- [x] 未写代码；未改字段结构；未改 examples / tests / Chapter
- [x] 未引入隐式状态；未提前进入 Part 05

---

## 二、Implementation 计划（Gate A 确认后启动）

- **载体**：`examples/text2sql_state/`（默认候选，单包起步）——校验器深度化实现
- **范围**：新校验规则（结构 / 只读 / 行数）复用 `rule` 名空间；输出保持 `ValidationResult` 三字段
- **约束**：复用 manual `FakeSQLValidator` 模式不复制实现；教学基线不动

## 三、Tests 计划（Gate A 确认后启动）

- Unit：规则矩阵（每条规则独立用例）
- Regression：manual validator 8 用例延续
- Failure Case：组合失败路径
- 兼容性：新校验器输出满足三字段契约断言

## 四、Documentation 计划（Gate C/D 阶段）

- 承载：Ch22（SQL 校验与修复循环）——T05 部分；Implementation 完成后按 Doc Mapping（Candidate）更新
- 每章落地时同步 ROADMAP / content-map / current（但本任务阶段不动三源——按 Gate D 统一执行）

## 五、Review Gate（按 TASK-0029 统一流程）

Gate A（本文件）→ Gate B Implementation → Gate C Tests / Evidence（Contract-level verified）→ Gate D Documentation → Merge → **Gate E Integration Closure（等 T06/T07 进入 main 后触发，验证真实 validation → risk → repair 串联路径；未关闭不得标 end-to-end verified）**

## 验收标准

- [x] ① Gate A：Architecture / Contract 冻结（职责边界 / 输入输出 contract / 兼容策略 / 测试证据基线）——PR #55 已合并
- [x] ② Implementation：text2sql_state 校验器深度化（规则表驱动 + RULE_ORDER 显式确定性优先级；复用 manual ValidationResult / AgentConfig，不复制不新造）
- [x] ③ Tests：rule matrix / manual 回归对照 / precedence 锁单测 / 三字段兼容断言（全量 110 passed：57 原有 + 53 新增）
- [ ] ④ Documentation：Ch22 T05 部分（Gate D——先钉 contract 行为再写文档，用户指定顺序）
- [ ] ⑤ Merge（Task Merge Gate）
- [ ] ⑥ Gate E Integration Closure（T06/T07 进 main 后，deferred → closed）
- [x] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过

## 完成记录

- 2026-08-08：任务创建；**Gate A：Architecture / Contract 冻结完成**（ValidationResult 职责边界 / 三字段 contract / 兼容策略 / 测试证据基线）；等待用户 Gate A 确认后进入 Implementation。
- 2026-08-08：**Gate A APPROVED**（用户确认：ValidationResult 继续 Existing-to-evolve / 三字段兼容 / 权限风险不塞入 / 执行结果不塞入 / manual baseline 不动 / 新实现进 text2sql_state）。**两条硬约束纳入**：① rule = control / repair decision、error = diagnostics（T07 不得按 error 文本分支）② 多规则同时失败须确定性 first-failure priority（单测锁住，防 T07 决策漂移）。
- 2026-08-08：**Gate B Implementation 完成**（commit：feat: implement t05 sql validator with deterministic rules）：
  - `examples/text2sql_state/validation.py`：规则表驱动 `RuleBasedSQLValidator` + `RULE_ORDER`（empty / multi_statement / forbidden_keyword / select_only / missing_limit / limit_exceeds——与 manual 名空间完全一致）+ 单 rule 输出（first-failure priority）
  - 复用 manual `ValidationResult` / `AgentConfig`（不复制、不新造第二套结果模型）；教学基线 manual 零改动
  - **Gate C Tests 完成**：`tests/text2sql_state/` 四件套——rule matrix（13 失败 + 4 接受 + registry 完整性）/ manual 回归对照（17 输入逐项 (ok, rule, error) 一致）/ precedence 锁单测（**9 组组合失败 × 3 重复** + observed 顺序与 RULE_ORDER 一致）/ 三字段兼容断言（返回类型 / 成功失败字段契约 / error ≠ rule 语义分离）
  - 全量 `pytest` 110 passed（57 原有 + 53 新增）；`ruff check .` / `mkdocs build --strict` / `git diff --check` 全过
  - **Ch22 文档按 TASK-0029 冻结流程在 Gate D 阶段完成**（先钉 contract 行为，再写文档）
- 2026-08-11：**PR #56 Gate B/C Review 修正**（commit：fix: enforce validator rule precedence contract）：
  1. **RULE_ORDER 单一事实源**：`_RULE_TABLE`（第二份有序 tuple）移除 → `_RULE_CHECKS: dict[str, RuleCheck]`（注册表，不携带顺序）；`RULE_ORDER` = runtime first-failure precedence 的唯一事实源；validate 按 `for rule in RULE_ORDER: _RULE_CHECKS[rule](...)` 执行——不再维护两份有序结构靠测试同步
  2. **Registry 完整性测试**：`test_rule_registry_complete_and_consistent`——`set(RULE_ORDER) == set(_RULE_CHECKS)`（双向覆盖）/ 无重复 rule / registry 与 order 数量一致 / 首条 empty
  3. **Review Gate 顺序恢复**：按 TASK-0029 冻结流程——**Gate B/C 通过 → Gate D Documentation（Ch22）→ Task Merge Gate → Merge → Gate E Integration Closure**；本轮修正后 PR #56 仍不 Merge（等待 Gate B/C 复审通过后进入 Gate D）
  4. **precedence 证据数量修正（以代码事实为准）**：COMBINED_FAILURES 实际 **9 组**（非 10）——补 `test_combined_failures_count` 锁住；清理 "missing_limit vs limit_exceeds" 注释（同一 SQL 中缺 LIMIT 与 LIMIT 超限互斥）——missing_limit 独立验证其 precedence 位置，limit_exceeds 为后置规则单独覆盖
  5. 边界保持：三字段契约 / rule-error 语义分离 / manual 零修改 / Integration Status = deferred / 不宣称 e2e verified / 不进入 T06-T07 / 不扩展 AST-生产 SQL 安全
