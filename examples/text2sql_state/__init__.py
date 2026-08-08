"""T05 SQL 静态校验（canonical T05）——Part 04 首个 implementation task 的代码载体。

默认载体候选（TASK-0029：目录结构由架构调整确定，当前单包起步）。
复用 examples.manual_agent_loop 的 ValidationResult / AgentConfig，不复制实现。
"""

from .validation import RULE_ORDER, RuleBasedSQLValidator

__all__ = ["RULE_ORDER", "RuleBasedSQLValidator"]
