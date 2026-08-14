# TASK-0035：Project Hygiene / Development Workflow Improvement

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-14 |
| Updated | 2026-08-14 |
| Related | TASK-0034（T02 主线，Gate B/C 等待最终确认）、TASK-0031（Pattern Backlog，proposed） |
| Related Principle | review-checklist.md（本轮升级对象）、AGENTS.md（验证命令） |
| 类型 | **横切治理任务（非 T01-T12 implementation task）** |

## 定位

**Project Hygiene / Development Workflow Improvement**——不是 Text-to-SQL capability 本身，而是解决已观察到的三个工程问题：

1. **Review 原则已沉淀，但 checklist 落后于当前架构成熟度**（T01/T02/T03/T05 Review 反复验证的通用契约原则未进入 checklist）
2. **本地验证与 CI 缺少统一入口**；mypy 已配置（strict）但未进入稳定门禁
3. **`.ai/context/current.md` 已从"当前快照"膨胀成"状态 + 历史流水账"**，与 TASK / PR Description 重复

固定原则：

> "治理任务应减少后续认知与验证成本，而不是创造新的流程层级。"

> "current.md is a recovery snapshot, not an event log."（current.md 是恢复快照，不是事件日志）

> "One verification workflow, one source of truth."

> "New quality gate must have a passing baseline before it becomes mandatory."（新的质量门禁必须先建立可通过的 baseline，再变成强制门禁）

## 一、前置条件验证（2026-08-14）

| 条件 | 结果 |
|---|---|
| main == origin/main | ✅ `c7897b2` == `c7897b2` |
| working tree clean | ✅ |
| T02 implementation / documentation PR 状态 | ✅ PR #65 OPEN / CLEAN（未 merge；T02 主线 Gate B/C 等待最终确认） |
| 治理改动不在未合并 feature branch 上 | ✅ 独立分支 `chore/project-hygiene-workflow`（从 main 创建） |
| Part 04 | ✅ in progress |
| v0.5.0 | ✅ incomplete |
| TASK-0031 Pattern Backlog | ✅ proposed |
| 不修改任何 T01-T12 capability contract | ✅（本任务仅治理文件） |

## 二、第一部分：Review Checklist 升级（落地）

- `.ai/principles/review-checklist.md` 新增 **## Contract & Boundary** section（CB1-CB12，见该文件）——保留现有 R/S/D/T/G/P/C 体系，不推翻
- Applicability 表新增三行：Domain Contract / Schema PR → CB1-CB6（必要时 CB7-CB12）+ P1 + C1；Integration / Adapter PR → CB7-CB12 + C1；Documentation PR → 描述 contract/state/integration evidence 时检查对应 CB 条目
- 强制使用方式（最小规则，不引入机器人）：每个 implementation PR 的 PR Description 或 TASK Review Gate 增加 "Applicable Review Checklist"（如 `Applicable: CB1 / CB2 / CB3 / CB5 / CB10 / C1`），Review 时引用条目编号
- 目标：Review principle 从"记忆在 Reviewer 脑中"变为"显式引用"

## 三、第二部分：统一本地验证入口（落地）

- 仓库无 `scripts/` 目录（新建）
- 现有 CI 事实（未改）：`tests.yml`（pytest + ruff）、`docs.yml`（mkdocs build --strict）——**不合并、不重复新增**；保持 CI job 职责清晰、可并行、无单点脚本故障
- 新增 **`scripts/verify.py`**（Python 单脚本，跨平台，Windows/Bash 通用——避免 verify.sh + verify.ps1 双事实源）
- 第一版执行：`python -m pytest -q` / `ruff check .` / `mkdocs build --strict` / `git diff --check`
- **不默认 git status 为 failure**（未提交合法工作树不应让开发验证失败）；最后打印 `git status --short` 作为信息
- `--typing` optional mode：`mypy --explicit-package-bases examples/text2sql_state`（不阻塞主验证）

## 四、第三部分：mypy baseline（audit 数据）

运行命令（pyproject `strict = true` 生效）：`mypy --explicit-package-bases .`

| 范围 | 结果 |
|---|---|
| 全仓 `mypy .` | ❌ 模块解析冲突（`examples/manual_agent_loop/config.py` 双重 module name）——需 `--explicit-package-bases` |
| 全仓 `mypy --explicit-package-bases .` | **68 errors / 16 files（checked 47 source files）** |
| examples/basic_langgraph | **~57 errors（graph.py 34 / nodes.py 19 / agent.py 2 / main.py 1 / state.py 1）——历史 typing debt 主源（约 84%）** |
| tests | ~32 error 行（test_semantic_contract 15 / test_retrieval 6 / test_normalize_node 5 / test_langgraph_agent 4 / 其余 2；含部分 note 行需复核） |
| examples/manual_agent_loop | 2 errors（main.py / runtime.py，历史 debt） |
| **examples/text2sql_state（单独）** | **4 errors / 3 files（checked 13 source files）**：`normalize_node.py:33` `-> dict` 泛型、`normalize_node.py:59` `update()` 标注、`retrieval_node.py:28` `-> dict` 泛型、`semantic_node.py:37` `-> dict` 泛型 |

**结论**：新代码目录（examples/text2sql_state）距 strict pass 仅 **4 个 trivial annotation errors**（行为零变化的标注修正）；历史代码（basic_langgraph / manual_agent_loop / tests）是主要 debt 来源。

## 五、mypy 三方案比较与推荐

| 方案 | 内容 | 评估 |
|---|---|---|
| A. `mypy .` 直接进 CI | 全仓 strict | ❌ baseline 68 errors（basic_langgraph 占 ~84%），不满足 "passing baseline before mandatory" |
| B. `mypy examples/text2sql_state` 进 CI | 新代码目录作为 typing gate | ⭐ **推荐为最终目标**——仅 4 trivial annotation errors（13 files），修复后 baseline 可清零；但修复涉及 T01/T02/T03 文件 annotation，属**范围外**（本任务禁止修改 capability 文件），需阶段 2 Workflow Review 批准范围后落地 |
| C. 暂不进 CI，verify.py `--typing` optional mode + 登记 debt | 过渡形态 | ✅ **本轮落地形态**——baseline 未清零前不设强制门禁，遵守 "New quality gate must have a passing baseline before it becomes mandatory." |

**推荐结论**：方案 B 为最终目标（examples/text2sql_state 4 trivial errors 支持该判断），但进入 CI 前需：① 阶段 2 Review 批准"修复 4 个 annotation（行为不变）"的范围；② baseline 清零后最小修改 `tests.yml` 加 mypy 步骤。**本轮不改 CI**。

## 六、第四部分：current.md 审计

### 数据（2026-08-14）

| 指标 | 值 |
|---|---|
| 总行数 | 259 |
| 总字符数 | ~49,766（约 50KB） |
| `## 已完成` | 行 7-71（**65 行历史流水账**，约 25%） |
| `## 正在进行` | 行 72-218（**147 行**，约 57%——但其中绝大多数是已合并 Chapter/Task 的每轮 Review 详情，属历史） |
| `## 下一步` | 行 220-253（34 行，含未来方向与 backlog） |
| `## 当前阻塞` | 行 254-258（5 行） |
| **历史内容比例** | **约 80%+**（"已完成" + "正在进行"中的历史 Review 详情） |
| 与 active TASK 重复 | T02 每轮 Review 详情与 TASK-0034 完全重复 |
| 与已完成 TASK 重复 | T01/T03/T05 及 Chapter 01-18 的每轮 Review 详情与对应 TASK-0005~0033 重复 |

### 问题

- current.md = "当前状态 + 全量历史"，每轮 AI 被迫全量读取 50KB，90% 是历史
- TASK（lifecycle 事实源）与 PR/Git（审计事实源）已存在——current.md 的历史是**第三份重复叙事**

### 推荐结构（thin snapshot，阶段 2 Review 确认后落地）

```text
# Current Session
日期
## Current Phase        # Part / Version / 当前主线
## Active Task          # TASK-xxxx / PR / Gate / Branch / Evidence Status / Integration Status
## Current Capability Status   # 只保留 T01 completed / T02 current / ... 一行一条，不展开每轮 Review
## Next Actions          # 最多 5-8 条
## Blockers / Deferred Integration  # 只列当前仍未关闭
## Future Backlog        # 只保留 pointer（TASK-0031）
## Historical Pointer    # 历史查看：.ai/tasks/、Git history、merged PRs
```

### 历史保留策略

**推荐 A：直接删除历史流水账**——TASK + Git/PR 已是历史事实源，不制造 `history.md` 第四事实源。仅当发现 current.md 存在 TASK/PR 未保存的独有历史信息时才创建 archive（当前审计未发现独有信息）。

## 七、第五部分：ROADMAP 状态语义审计（只规划，不修改）

### 问题

v0.5.0 checkbox（Text2SQLState / 意图识别 / 元数据检索 / SQL 校验 等）仍为 `[ ]`，但 T01/T02/T03/T05 已 implementation complete + integration deferred——ROADMAP 长期显示"错误"状态。

### 推荐语义

**checkbox = milestone capability complete**：只有 implementation + required integration evidence + documentation + release closure 满足时才 `[x]`。ROADMAP 需增加解释：

> Task-level progress 看 `current.md` / TASK；ROADMAP checkbox 只表示 milestone closure。

这样 T03 implementation complete 但 ROADMAP "元数据检索" 未勾选不再是"状态错误"，而是明确语义。

**本轮不修改 ROADMAP**（需 Workflow Review 确认语义后落地）。

## 八、Integration Debt 风险登记

**当前最高路线风险**：T01 / T02 / T03 / T05 contract / implementation 趋于成熟，但 **compiled Graph Runtime integration 仍不足**。

固定原则：

> "Task-level completeness must not hide milestone-level integration debt."

建议下一轮 capability work：T02 完成后优先安排最小 integration slice——**T01 → T02 → T03 进入真实 StateGraph compiled graph**。本治理任务不实现该 integration。

## 九、执行阶段

- **阶段 1（本轮）**：Audit only + 最小落地——checklist upgrade、verify.py、TASK-0035 登记（audit 输出）；**不修改 current.md（瘦身）/ CI / ROADMAP**
- **阶段 2（Review 确认后）**：current.md thin snapshot、可选 mypy gate（方案 B，需范围批准）、ROADMAP 语义说明落地

## 十、允许修改（本轮）

`.ai/tasks/TASK-0035-*.md`、`.ai/principles/review-checklist.md`、`scripts/verify.py`、`AGENTS.md` / `README.md`（verify 命令一条）、`.ai/context/current.md`（仅登记本任务一行指针，非瘦身）。CI / ROADMAP / capability 文件本轮零改动。

## 十一、禁止修改

`examples/text2sql_state` capability logic、tests capability behavior、Chapter 19/20、ROADMAP（本轮仅 audit）、content-map、ADR、architecture-map、Pattern Backlog、T01/T02/T03/T05 TASK 内容、T04/T06/T07、Part 03。

## 十二、验收标准

- [x] 前置条件 8 项全过
- [x] review-checklist.md 新增 Contract & Boundary（CB1-CB12）+ Applicability 三行 + 强制使用方式
- [x] scripts/verify.py 统一验证入口（pytest / ruff / mkdocs --strict / git diff --check；--typing optional；不默认 git status failure）
- [x] mypy baseline 记录（全仓 68 / text2sql_state 4）+ 三方案比较 + 推荐（B 目标 / C 过渡）
- [x] current.md 审计（行数/字符/历史比例/重复）+ thin snapshot 方案 + 历史保留策略（推荐 A）
- [x] ROADMAP checkbox 语义审计（推荐 milestone closure）+ 本轮不改
- [x] Integration Debt 风险登记
- [x] 验证：`python scripts/verify.py` 全绿 + 单项确认 pytest / ruff / mkdocs --strict / git diff --check

## 完成记录

- 2026-08-14：任务创建（in_progress，chore/project-hygiene-workflow 分支）。阶段 1 完成：前置条件验证全过；checklist 升级（CB1-CB12 + Applicability + 强制使用方式）；scripts/verify.py（Python 单脚本跨平台）；mypy baseline（全仓 68 errors / examples/text2sql_state 4 errors）+ 方案推荐（B 目标 / C 过渡，CI 本轮不改）；current.md 审计（259 行 / ~50KB / 历史 ~80% / 与 TASK-PR 重复）+ thin snapshot 方案（推荐历史直接由 TASK+Git 承载）；ROADMAP checkbox 语义审计（推荐 milestone closure，本轮不改）；Integration Debt 登记（compiled graph 不足，建议 T01→T02→T03 最小 integration slice）。等待 Workflow Review（阶段 2 决策：current.md 瘦身 / mypy 方案 B 范围 / ROADMAP 语义落地）。
