"""T05 三字段契约兼容断言：输出始终为 manual ValidationResult 三字段契约。

rule = control / repair decision（机器可判定、稳定标识）；
error = diagnostics / presentation（面向人类）。
"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.types import ValidationResult
from examples.text2sql_state.validation import RuleBasedSQLValidator


def make_validator() -> RuleBasedSQLValidator:
    return RuleBasedSQLValidator(AgentConfig())


def test_return_type_is_manual_validation_result() -> None:
    """不新造第二套结果模型：返回类型就是 manual 的 ValidationResult。"""
    for sql in ["", "SELECT 1", "SELECT * FROM orders LIMIT 1000"]:
        assert isinstance(make_validator().validate(sql), ValidationResult)


def test_success_fields_contract() -> None:
    result = make_validator().validate("SELECT * FROM orders LIMIT 1000")
    assert result.ok is True
    assert result.error is None
    assert result.rule is None


@pytest.mark.parametrize(
    ("sql", "expected_rule"),
    [
        ("", "empty"),
        ("SELECT 1; SELECT 2", "multi_statement"),
        ("DELETE FROM orders", "forbidden_keyword"),
        ("SELECTED something", "select_only"),
        ("SELECT 1", "missing_limit"),
        ("SELECT 1 LIMIT 2000", "limit_exceeds"),
    ],
)
def test_failure_fields_contract(sql: str, expected_rule: str) -> None:
    """失败时：rule 为稳定规则标识（机器可判定），error 为人类诊断信息。"""
    result = make_validator().validate(sql)
    assert result.ok is False
    assert result.rule == expected_rule  # rule = control / repair decision
    assert isinstance(result.error, str) and result.error  # error = diagnostics
    assert result.error != result.rule  # 二者语义分离：T07 不得按 error 文本分支


@pytest.mark.parametrize("sql", ["", "   ", ";", ";;;", " ; ; "])
def test_total_contract_known_boundary_inputs(sql: str) -> None:
    """total contract：已知边界输入（空 / 空白 / separator-only）必须安全返回
    ValidationResult（rule="empty"），不得抛异常。

    contract 只针对 sql: str 输入——不声称"所有 Python 对象输入"。
    """
    result = make_validator().validate(sql)
    assert result.ok is False
    assert result.rule == "empty"  # rule = machine decision
    assert isinstance(result.error, str) and result.error  # error = human diagnostics


def test_total_contract_huge_limit_numeric_literal() -> None:
    """total contract：超长 LIMIT 十进制数字不得抛 ValueError。

    无法安全转换的超长 LIMIT → rule = "limit_exceeds"（现有 namespace，不新增），
    error 为人类可读诊断。
    """
    huge_limit = "9" * 5000
    result = make_validator().validate(f"SELECT * FROM orders LIMIT {huge_limit}")
    assert result.ok is False
    assert result.rule == "limit_exceeds"
    assert isinstance(result.error, str) and result.error
