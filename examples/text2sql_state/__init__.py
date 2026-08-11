"""Part 04 Text-to-SQL 实现载体（TASK-0029：目录结构由架构调整确定，当前单包起步）。

T01 输入规范化（TASK-0032，本分支）：
- normalize_question：deterministic lexical normalization（纯函数）
- normalize_input_node：Graph Node adapter（映射到既有 lifecycle / failure contract）
复用 examples.manual_agent_loop 的 AgentStatus / ValidationResult，不复制实现。

T05 SQL 静态校验（TASK-0030）：
- RULE_ORDER / RuleBasedSQLValidator（canonical T05）
"""

from .normalization import normalize_question
from .normalize_node import normalize_input_node
from .validation import RULE_ORDER, RuleBasedSQLValidator

__all__ = [
    "RULE_ORDER",
    "RuleBasedSQLValidator",
    "normalize_input_node",
    "normalize_question",
]
