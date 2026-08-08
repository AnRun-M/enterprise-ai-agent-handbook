"""T05 regression：与 manual FakeSQLValidator 逐输入对照（8 个既有行为回归）。"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.tools import FakeSQLValidator
from examples.text2sql_state.validation import RuleBasedSQLValidator

# 覆盖 tests/manual_agent_loop/test_validator.py 的 8 类既有行为场景
REGRESSION_SQLS = [
    "INSERT INTO orders VALUES (1)",            # 非 SELECT（forbidden/select_only）
    "UPDATE orders SET amount = 1",             # 非 SELECT
    "DELETE FROM orders",                       # 非 SELECT
    "DROP TABLE orders",                        # 非 SELECT
    "ALTER TABLE orders ADD COLUMN x INT",      # 非 SELECT
    "SELECT * FROM orders",                     # 缺 LIMIT
    "SELECT * FROM orders LIMIT 2000",          # LIMIT 超限（max_rows=1000）
    "SELECT * FROM orders LIMIT 500",           # 通过
    "SELECT * FROM orders LIMIT 1000;",         # 尾分号通过
    "SELECT 1; DROP TABLE orders",              # 多语句
    "SELECT * FROM orders LIMIT 1000; SELECT 1 LIMIT 1",  # 多语句
    "",                                         # 空 SQL
    "SELECT column_name FROM orders LIMIT 10",  # 列名不触发关键字
    "SELECTED something",                       # 首 token 不是 SELECT
    "WITH x AS (SELECT 1) SELECT * FROM x",     # CTE 开头（非 SELECT 首 token）
    "SELECT * FROM orders LIMIT 1000",          # 边界通过（等于 max_rows）
    "SELECT * FROM orders LIMIT 1001",          # 边界失败（超 max_rows）
]


@pytest.mark.parametrize("sql", REGRESSION_SQLS)
def test_regression_matches_manual_validator(sql: str) -> None:
    """同一输入下，RuleBasedSQLValidator 与 manual FakeSQLValidator 的 (ok, rule) 完全一致。"""
    config = AgentConfig()
    manual = FakeSQLValidator(config).validate(sql)
    rule_based = RuleBasedSQLValidator(config).validate(sql)

    assert rule_based.ok == manual.ok
    assert rule_based.rule == manual.rule
    assert rule_based.error == manual.error
