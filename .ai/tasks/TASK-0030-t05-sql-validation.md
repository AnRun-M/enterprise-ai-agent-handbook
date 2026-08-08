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

- [x] ① Gate A：Architecture / Contract 冻结（职责边界 / 输入输出 contract / 兼容策略 / 测试证据基线）——本阶段交付
- [ ] ② Implementation：text2sql_state 校验器深度化（Gate A 确认后）
- [ ] ③ Tests：Unit / Regression / Failure / 兼容性（三列制 + Evidence Status）
- [ ] ④ Documentation：Ch22 T05 部分（Gate D）
- [ ] ⑤ Merge（Task Merge Gate）
- [ ] ⑥ Gate E Integration Closure（T06/T07 进 main 后，deferred → closed）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过

## 完成记录

- 2026-08-08：任务创建；**Gate A：Architecture / Contract 冻结完成**（ValidationResult 职责边界 / 三字段 contract / 兼容策略 / 测试证据基线）；等待用户 Gate A 确认后进入 Implementation。
