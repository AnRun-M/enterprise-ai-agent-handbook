# Part 4：Text-to-SQL Refactoring

## 前置章

- [第 18 章：StateGraph 构图与 Graph Runtime 执行模型](ch18-stategraph-graph-runtime.md)（Part 03 语义如何组装成可执行 Graph：定义图 → 注册组件 → 连接控制流 → compile → invoke/stream → 与 Part 03 对照）

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
