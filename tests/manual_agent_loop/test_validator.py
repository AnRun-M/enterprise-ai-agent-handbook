"""FakeSQLValidator 规则测试（canonical T05 静态校验）。"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.tools import FakeSQLValidator


@pytest.fixture
def validator() -> FakeSQLValidator:
    return FakeSQLValidator(AgentConfig(max_rows=1000))


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO orders (id) VALUES (1)",
        "UPDATE orders SET amount = 0 WHERE id = 1",
        "DELETE FROM orders",
        "DROP TABLE orders",
        "ALTER TABLE orders ADD COLUMN x INT",
        "TRUNCATE TABLE orders",
    ],
)
def test_rejects_non_select_statements(validator: FakeSQLValidator, sql: str) -> None:
    result = validator.validate(sql)
    assert not result.ok
    assert result.rule in ("forbidden_keyword", "select_only")


def test_rejects_missing_limit(validator: FakeSQLValidator) -> None:
    result = validator.validate("SELECT order_date FROM orders")
    assert not result.ok
    assert result.rule == "missing_limit"


def test_rejects_limit_exceeds_config(validator: FakeSQLValidator) -> None:
    result = validator.validate("SELECT order_date FROM orders LIMIT 5000")
    assert not result.ok
    assert result.rule == "limit_exceeds"


def test_rejects_multi_statement(validator: FakeSQLValidator) -> None:
    result = validator.validate("SELECT 1 LIMIT 1; DROP TABLE orders")
    assert not result.ok
    assert result.rule == "multi_statement"


def test_rejects_empty_sql(validator: FakeSQLValidator) -> None:
    result = validator.validate("   ")
    assert not result.ok
    assert result.rule == "empty"


def test_accepts_select_with_limit(validator: FakeSQLValidator) -> None:
    result = validator.validate(
        "SELECT order_date, SUM(amount) AS gmv FROM orders WHERE order_date = '2026-07-31' LIMIT 1000"
    )
    assert result.ok


def test_accepts_trailing_semicolon(validator: FakeSQLValidator) -> None:
    result = validator.validate("SELECT 1 LIMIT 1;")
    assert result.ok


def test_column_name_does_not_trigger_keyword_rule(validator: FakeSQLValidator) -> None:
    # 校验器只检查语句首 token，避免对列名（如 updated_at）误伤。
    result = validator.validate("SELECT updated_at FROM orders LIMIT 10")
    assert result.ok
