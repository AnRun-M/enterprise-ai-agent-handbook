# 第 22 章：SQL 校验与修复循环

> 状态：draft（2026-08-11，T05 部分；T07 Repair Loop 待实现后补充）
> 前置阅读：第 18 章（StateGraph 构图与 Graph Runtime 执行模型）、`examples/text2sql_state/validation.py`、`tests/text2sql_state/`、`examples/manual_agent_loop/tools.py`（FakeSQLValidator 教学基线）
> 本章 Candidate Mapping 承载 **T05（SQL 静态校验）+ T07（修复或人工审批）**。**本轮只完成 T05 已有真实实现与 contract 证据可证实的部分**；T07 内容明确标注"待 T07 implementation 后补充"，不伪装为已完成。
> 只引用 Part 03 Runtime 语义（Chapter 08-18），不重新定义。

**整章主线（T05 部分固定）：**

> **SQL 静态校验不是 SQL 执行，也不是权限与业务风险判断。T05 将候选 SQL 转换为稳定的 ValidationResult：rule 提供机器可判定的控制标识，error 提供面向人的诊断信息；当多条规则同时失败时，RULE_ORDER 定义确定性的 first-failure priority，为后续 T07 Repair Decision 提供稳定输入。**

## 22.1 为什么生成后还要校验

**Runtime 语义先行**：第 21 章（T04，待实现）的 SQL 生成由 LLM 完成——模型产生候选，但模型输出具有概率性（ADR-0004）。**LLM Generation ≠ Deterministic Validation**：

| 职责 | 由谁承担 |
|---|---|
| 产生候选 SQL | 模型（生成，开放语义） |
| 保证确定性约束（只读 / LIMIT / 结构） | **确定性代码**（ADR-0004：SQL 安全、行数限制由程序强制保证，不依赖 Prompt 或模型意志） |

canonical 流程中 T05 是生成之后、执行之前的**确定性门**：候选 SQL 必须经过静态校验，才能进入权限与风险检查（T06）与执行（T09）。**校验失败 → 修复或人工审批（T07）**——这正是本章 T07 部分的接口位置（22.7）。

**为什么是"静态"**：T05 只检查 SQL 文本的**确定性文本级特征**（statement 分隔、首关键字、LIMIT 存在性与上限），**不执行 SQL、不查询数据库、不判断权限与业务风险**（那是 T06 的职责，22.8）。**注意表述边界**：这是文本级检查（split / regex），**不是 SQL syntax parsing**（22.8 的 lexical heuristic 限定）。

## 22.2 ValidationResult：控制信息与诊断信息分离

**契约（仅三字段）**——`examples/text2sql_state/validation.py` 复用 `examples/manual_agent_loop/types.py` 的 `ValidationResult`（不新造第二套结果模型）：

```python
class ValidationResult:
    """SQL 静态校验的结构化输出（canonical T05）。"""

    ok: bool
    error: str | None = None
    rule: str | None = None
```

| 字段 | 语义 | 使用方 |
|---|---|---|
| `ok: bool` | 校验是否通过 | 控制流（通过 → T06；失败 → T07） |
| **`rule: str \| None`** | **机器可判定的控制标识 / Repair Decision 输入** | 修复循环（T07）——按 rule 分支 |
| **`error: str \| None`** | **面向人的诊断信息 / presentation** | 展示与审计 |

**硬边界**：**rule = control / repair decision；error = diagnostics / presentation**——T07 的修复决策**只按 rule 分支，不允许根据 error 文本分支**（error 面向人，不面向控制流）。测试 `test_failure_fields_contract` 断言失败时 `error != rule`（语义分离）。

## 22.3 Rule Namespace

当前教学实现六条规则（`RULE_ORDER`，与 manual `FakeSQLValidator` 名空间一致）：

| rule | 触发条件 | 性质 |
|---|---|---|
| `empty` | 无有效语句（空 / 空白 / 仅分号） | 输入完整性 |
| `multi_statement` | 存在多于一条语句 | 语句完整性 |
| `forbidden_keyword` | 首关键字为 INSERT / UPDATE / DELETE / DROP / ALTER / TRUNCATE | 只读底线（AGENTS.md） |
| `select_only` | 首关键字不是 SELECT | 只读底线 |
| `missing_limit` | 缺少 LIMIT 子句 | 行数约束 |
| `limit_exceeds` | LIMIT 值超过配置 `max_rows` | 行数约束 |

**边界声明**：这是**当前教学实现的 rule namespace，不是生产 SQL 安全规则全集**——未覆盖 AST 解析 / 列与表级授权 / 语义正确性 / 租户数据范围策略 / 扫描与成本估算 / 方言校验 / 注入与安全完备性 / 生产审计（22.8）。新规则 = 在 `_RULE_CHECKS` 注册 + 追加到 `RULE_ORDER`（registry 完整性由测试锁住）。

## 22.4 Deterministic First-Failure Priority

**问题**：多条规则可能同时失败（如 `"DELETE FROM orders"` 同时命中 `forbidden_keyword` 与 `missing_limit`），而当前契约**只返回一个 rule**。

**解法**：`RULE_ORDER` 是 first-failure precedence 的**唯一顺序事实源**；`_RULE_CHECKS`（registry）不携带顺序，校验器按 `for rule in RULE_ORDER: _RULE_CHECKS[rule](...)` 依次检查，返回**第一个失败**的 rule：

```
empty → multi_statement → forbidden_keyword → select_only → missing_limit → limit_exceeds
```

**为什么需要 deterministic precedence**：

- **测试稳定**：同一输入的输出不随执行环境漂移（`test_first_failure_priority_is_deterministic`：组合失败输入 × 3 次重复，断言返回同一 rule）
- **Repair Decision 稳定**：T07 的修复分支输入是唯一 rule——若 rule 随规则执行顺序漂移，修复决策随之漂移
- **Replay / Debug 更可解释**：给定输入与 RULE_ORDER，输出可精确复现

**重要澄清**：**不要把 first-failure priority 误解为"最高优先级错误一定是业务上最严重错误"**——它只是当前 contract 的 **deterministic evaluation order**（例如 `empty` 最先，是输入完整性的前置条件，不是业务严重性排序）。

## 22.5 Total Contract 与边界输入

**Total contract（设计契约 vs 测试证据，区分）**：**设计契约**——对于 contract 范围内的 `sql: str` 输入，validator 应稳定返回 ValidationResult，不得抛异常；**测试证据**——当前测试覆盖空输入、separator-only、超长 LIMIT 等**已知边界路径**，不宣称"所有可能的 SQL 字符串均已验证"（测试有限覆盖不能证明数学意义上的全集）。

边界输入的处理（`_statements` helper：分号切分 + 去空白，返回有效语句元组；`_rule_empty` 按"有效语句数量 == 0"判定）：

| 输入 | 结果 |
|---|---|
| `""` / `"   "` | `ok=False, rule="empty"` |
| `";"` / `";;;"` / `" ; ; "` | `ok=False, rule="empty"`（separator-only 归类 empty，不抛 IndexError） |
| 超长 LIMIT 十进制数字（如 `"9" × 5000`） | `ok=False, rule="limit_exceeds"`（无法安全转换的 LIMIT 归入现有 namespace，error 为人类可读诊断，不抛 ValueError） |
| 正常 SQL | 按规则表评估 |

测试：`test_total_contract_known_boundary_inputs`（"" / 空白 / ";" / ";;;" / " ; ; " 参数化）+ `test_total_contract_huge_limit_numeric_literal`（超长 LIMIT）——全部断言不抛异常、rule 正确、error 非空。

## 22.6 当前实现与测试证据

**证据四列制**（只依据仓库当前真实代码 / 测试）：

| 类别 | 内容 |
|---|---|
| **代码事实** | `examples/text2sql_state/validation.py`：`_statements` helper / `_RULE_CHECKS` registry（6 条规则函数）/ `RULE_ORDER`（唯一顺序事实源）/ `RuleBasedSQLValidator.validate`（按序检查，首个失败返回）——复用 manual `ValidationResult` / `AgentConfig` |
| **测试事实** | `tests/text2sql_state/`：rule matrix（每条规则正 / 负用例 + registry 完整性）/ manual 回归对照（**17 个输入逐项 (ok, rule, error) 与 manual 一致**）/ precedence 锁单测（9 组组合失败 × 3 重复 + observed 顺序与 RULE_ORDER 一致）/ 三字段兼容断言（返回类型 / 字段契约 / error ≠ rule）/ separator-only total contract |
| **设计约束** | rule = control、error = diagnostics（T07 不得按 error 文本分支）；RULE_ORDER 唯一顺序源；total contract；教学基线 manual 零修改 |
| **尚未验证** | 生产 SQL 安全（22.8）；与 T07 的真实串联（Integration deferred，见 22.7） |

**Manual compatibility（收窄表述）**：新实现复用 `ValidationResult` / `AgentConfig`，rule namespace 与 manual 一致，**17 个 regression 输入当前观察结果一致**——**不宣称"新实现与 manual 在所有 SQL 上完全等价"**（证据只覆盖现有测试输入）。

## 22.7 与 Repair Loop 的接口边界

**T05 已证实的接口贡献**：`ValidationResult.rule` 是未来 **T07 Repair Decision 的输入 contract**——修复分支按 rule（如 `missing_limit` → 补 LIMIT）选择修复动作。

**本轮明确不做（待 T07 implementation 后补充）**：

- ❌ 实现 T07（repair algorithm / Human Approval）
- ❌ 定义 RepairDecision schema
- ❌ 写 repair algorithm
- ❌ 声称 T05 → T07 integration 已验证

**Evidence Status**：T05 当前 = **Contract-level verified**；T05 → T07 真实串联 = **Integration deferred**（等 T06 / T07 进入 main 后，经 Integration Closure Gate 验证 validation → risk → repair / approval 真实路径后方可关闭；未关闭不得标记 end-to-end verified）。

> 本节 T07 相关内容待 T07 implementation 后补充，不伪装为已完成。

## 22.8 当前能力边界

**T05 是教学级 static validation，不是生产 SQL 安全系统。** 未覆盖：

- SQL AST parsing
- column / table authorization
- semantic correctness
- tenant / data-scope policy
- scan / cost estimation
- SQL dialect validation
- injection / security completeness
- production audit

**Lexical heuristic 限定（明确）**：当前实现是 **textual / lexical validator，不是 SQL parser**——`split(";")`、first-keyword regex、LIMIT regex 属于教学级 heuristic；**字符串字面量、SQL comments、复杂 dialect syntax 可能造成误判**。这是本任务的明确边界，不是本任务要求解决的问题；**不引入 AST parser**。

**边界归属**：权限与风险（含审批触发）属于 **T06**（canonical T06），**不塞入 T05**；扫描 / 成本 / 审计等生产能力属于 Part 05 / v0.6.0 里程碑；真实引擎执行属于 T09（Fake 实现 + 架构引用）。

---

**本章 T05 部分验收**：

- [x] 固定主线逐字保持（校验 ≠ 执行 ≠ 权限风险；rule/error 分离；RULE_ORDER 确定性）
- [x] 只讲 T05 可证实内容（代码 / 测试 / 契约 / 边界），四列制证据
- [x] 7 个问题全部覆盖（生成后为何校验 / ValidationResult 契约 / Rule Namespace / First-failure Priority / Total Contract / Manual compatibility 收窄 / Production boundary）
- [x] T07 接口位置预留（22.7），未实现 T07 未定义 RepairDecision，未声称 integration 已验证
- [x] Evidence Status：Contract-level verified；Integration deferred
- [x] 不写死全量 pytest 数量；术语与 TERMINOLOGY 一致；只引用 Part 03
- [ ] T07 部分：待 T07 implementation 后补充（不在本章伪装完成）

**本章边界**：权限与风险（T06）——第 23 章候选；引擎路由与执行（T08 / T09）——第 24 章候选；结果质量（T10）——第 25 章候选；生产 SQL 安全 / 审计——Part 05；LangChain——Future LangChain Scope Planning，不在本章展开。
