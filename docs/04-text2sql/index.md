# Part 4：Text-to-SQL Refactoring

## 前置章

- [第 18 章：StateGraph 构图与 Graph Runtime 执行模型](ch18-stategraph-graph-runtime.md)（Part 03 语义如何组装成可执行 Graph：定义图 → 注册组件 → 连接控制流 → compile → invoke/stream → 与 Part 03 对照）

## 输入与意图

- [第 19 章：输入规范化与意图识别](ch19-input-normalization-intent.md)（T01：Original vs Derived State、Lexical Normalization Contract、Outcome Update、Stale State / Merge Semantics、Failure / Idempotency；T02 Intent / Semantic Extraction 待实现后补充）

## 检索与生成

- [第 20 章：元数据与业务规则检索](ch20-metadata-business-rule-retrieval.md)（T03：Retrieval Outcome 五态、References / Provenance、Materialized Facts、Criteria Set 语义、Source Contract 五层、Provenance Identity Chain；T04 / Context Builder 仅接口位置）

## 校验与修复

- [第 22 章：SQL 校验与修复循环](ch22-sql-validation-repair-loop.md)（T05：rule/error 分离、Rule Namespace、First-Failure Priority、Total Contract；T07 Repair Loop 待补充）

## 重构流程

```text
输入规范化
-> 意图识别
-> 语义与规则检索
-> SQL 生成
-> SQL 校验
-> 权限检查
-> 引擎路由
-> SQL 执行
-> 结果检查
-> Python 分析
-> 结构化输出
```
