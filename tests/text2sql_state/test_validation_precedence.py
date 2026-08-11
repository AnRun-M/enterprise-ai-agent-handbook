"""T05 first-failure priority：确定性 precedence 锁单测。

多条规则同时失败时，RULE_ORDER 决定唯一输出 rule——
防止 T07 修复决策随规则执行顺序漂移（用户硬约束 2）。
"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.config import AgentConfig
from examples.text2sql_state.validation import RULE_ORDER, RuleBasedSQLValidator


def make_validator() -> RuleBasedSQLValidator:
    return RuleBasedSQLValidator(AgentConfig())


# 9 组 priority / combined-failure inputs（每组 = 命中该规则，且若同时命中后续规则
# 必须返回 RULE_ORDER 中较前的规则；重复执行确认确定性，不随执行状态漂移）。
COMBINED_FAILURES = [
    # empty（最先）vs 其余：空输入同时"缺 LIMIT"
    ("", "empty"),
    # multi_statement vs forbidden_keyword / select_only / missing_limit
    ("DELETE FROM orders; SELECT 1", "multi_statement"),
    ("SELECT 1; SELECT 2", "multi_statement"),
    # forbidden_keyword vs select_only / missing_limit
    ("DELETE FROM orders", "forbidden_keyword"),
    ("DELETE FROM orders LIMIT 1000", "forbidden_keyword"),
    # select_only vs missing_limit
    ("SELECTED something", "select_only"),
    ("WITH x AS (SELECT 1) SELECT * FROM x LIMIT 10", "select_only"),
    # missing_limit：独立验证其 precedence 位置（缺 LIMIT 与 LIMIT 超限在同一 SQL 中
    # 不能同时成立——missing LIMIT 与 limit exceeds 是互斥状态）
    ("SELECT * FROM orders", "missing_limit"),
    # limit_exceeds：后置规则，单独覆盖（其组合场景已被 forbidden_keyword /
    # select_only / missing_limit 的 precedence 覆盖）
    ("SELECT * FROM orders LIMIT 2000", "limit_exceeds"),
]


@pytest.mark.parametrize(("sql", "expected_rule"), COMBINED_FAILURES)
def test_first_failure_priority_is_deterministic(sql: str, expected_rule: str) -> None:
    for _ in range(3):  # 9 组 × 3 重复执行，确认不随执行状态漂移
        result = make_validator().validate(sql)
        assert result.ok is False
        assert result.rule == expected_rule


# 注：COMBINED_FAILURES 当前为 9 组 precedence cases（描述性事实，非产品不变量）——
# 测试用例数量由测试内容决定，不把"9"锁定为 contract。


def test_rule_order_matches_observed_priority() -> None:
    """observed 优先级必须与 RULE_ORDER 常量一致（常量是唯一事实源）。"""

    config = AgentConfig()
    validator = RuleBasedSQLValidator(config)
    observed_order: list[str] = []
    for sql, _ in COMBINED_FAILURES:
        result = validator.validate(sql)
        if result.rule not in observed_order:
            observed_order.append(result.rule)
    # 组合用例覆盖的规则子集按 RULE_ORDER 出现（可能跳过未覆盖的）
    covered = [r for r in RULE_ORDER if r in observed_order]
    assert observed_order == covered
