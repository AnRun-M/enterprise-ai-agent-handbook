"""T05 rule matrix：每条规则一个正/负用例，锁定 rule 名空间。"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.config import AgentConfig
from examples.text2sql_state.validation import RULE_ORDER, RuleBasedSQLValidator


def make_validator() -> RuleBasedSQLValidator:
    return RuleBasedSQLValidator(AgentConfig())


@pytest.mark.parametrize(
    ("sql", "expected_rule"),
    [
        ("", "empty"),
        ("   ", "empty"),
        ("SELECT 1; DELETE FROM orders", "multi_statement"),
        ("SELECT 1 LIMIT 10; SELECT 2 LIMIT 10", "multi_statement"),
        ("DELETE FROM orders LIMIT 1000", "forbidden_keyword"),
        ("DROP TABLE orders", "forbidden_keyword"),
        ("UPDATE orders SET amount = 1 LIMIT 10", "forbidden_keyword"),
        ("WITH x AS (SELECT 1) SELECT * FROM x", "select_only"),
        ("SELECTED something", "select_only"),
        ("SELECT 1", "missing_limit"),
        ("SELECT * FROM orders", "missing_limit"),
        ("SELECT * FROM orders LIMIT 1001", "limit_exceeds"),
        ("SELECT * FROM orders LIMIT 5000", "limit_exceeds"),
    ],
)
def test_rule_matrix_failure_cases(sql: str, expected_rule: str) -> None:
    result = make_validator().validate(sql)
    assert result.ok is False
    assert result.rule == expected_rule


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM orders LIMIT 1000",
        "SELECT * FROM orders LIMIT 10",
        "SELECT * FROM orders LIMIT 1000;",
        "SELECT column_name FROM orders LIMIT 10",  # 列名不触发关键字规则
    ],
)
def test_rule_matrix_accept_cases(sql: str) -> None:
    result = make_validator().validate(sql)
    assert result.ok is True
    assert result.error is None
    assert result.rule is None


def test_rule_registry_complete_and_consistent() -> None:
    """Registry 完整性：RULE_ORDER 与 _RULE_CHECKS 双向覆盖、无重复、无未注册规则。

    RULE_ORDER 是 first-failure precedence 的唯一事实源；_RULE_CHECKS 只提供查找。
    """
    from examples.text2sql_state.validation import _RULE_CHECKS

    assert set(RULE_ORDER) == set(_RULE_CHECKS)  # 双向覆盖：无 order 未注册 / 无 registry 未进 order
    assert len(RULE_ORDER) == len(set(RULE_ORDER))  # 无重复 rule
    assert len(_RULE_CHECKS) == len(RULE_ORDER)  # registry 与 order 数量一致
    assert RULE_ORDER[0] == "empty"  # 空输入最先，其余顺序不得随意变更
