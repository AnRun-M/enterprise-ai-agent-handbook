# TASK-0027：Chapter 17 Ending 待维护表述修正（maintenance task）

## 元信息

| 字段 | 值 |
|---|---|
| Status | proposed |
| Owner | AnRun-M |
| Created | 2026-08-08 |
| Updated | 2026-08-08 |
| Related ADR | ADR-0001 |
| Related Chapter | Chapter 17（Subgraph，Part 03 收官章） |
| Related Task | TASK-0025（Part 03 Release Audit，记录本待维护表述）、TASK-0026（Part 04 Scope Planning，冻结决策） |

## 背景

Part 03 Release Audit（TASK-0025）已记录：Chapter 17 Ending 中"下一部分将进入 StateGraph API 与框架实现层，而不是重新定义这些运行时概念"属于**待维护表述**——Release Audit 禁止修改正文，故未回改。Part 04 Scope Planning（TASK-0026）已冻结决策：Part 04 第一章命名为「StateGraph 构图与 Graph Runtime 执行模型」。

## 目标

将 Chapter 17 Ending 的待维护表述修正为与冻结决策一致的表述：

- **现表述**："下一部分将进入 StateGraph API 与框架实现层，而不是重新定义这些运行时概念。"
- **目标表述**："下一部分将进入 StateGraph 构图与 Graph Runtime 执行模型——图如何被组装、compile 如何将其转换为可执行 Runtime、invoke/stream 如何驱动执行，而不是重新定义这些运行时概念。"

## 需要修改

- `docs/03-langgraph-core/ch17-subgraph.md`（仅 Part 03 Ending 句，一行）

## 约束

- 仅修改 Chapter 17 Ending 句；不修改其他正文
- **独立 PR 执行**（maintenance task 与 Part 04 正文任务不混在一个 PR）
- 修改后运行 `mkdocs build --strict` / `git diff --check` / `pytest` / `ruff check .`

## 验收标准

- [ ] Chapter 17 Ending 表述与 Part 04 冻结决策一致
- [ ] 独立 PR 创建（不与 Part 04 正文混）
- [ ] 验证通过
- [ ] `.ai/context/current.md` 已更新（记录 maintenance 完成）

## 完成记录

- 2026-08-08：任务登记（proposed，待独立 PR 执行）。
