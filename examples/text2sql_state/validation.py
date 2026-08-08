"""T05 SQL 静态校验：规则表驱动的确定性校验器（canonical T05）。

契约（TASK-0030 Gate A 冻结 + 用户硬约束）：
- **rule = control / repair decision**：机器可判定、稳定的规则标识；
  T07 修复循环只按 rule 分支，**不允许根据 error 文本做分支**。
- **error = diagnostics / presentation**：面向人类的诊断信息。
- **多规则同时失败 → first-failure priority**：RULE_ORDER 决定唯一输出 rule，
  防止修复决策随规则执行顺序漂移（有单测锁住）。

兼容性（Existing-to-evolve）：
- rule 名空间与 examples.manual_agent_loop 的 FakeSQLValidator 完全一致
  （empty / multi_statement / forbidden_keyword / select_only /
  missing_limit / limit_exceeds）——8 个既有 validator 行为回归兼容。
- 复用 manual 的 ValidationResult / AgentConfig（不复制、不新造第二套结果模型）。
- 与 manual 的差异是**实现结构**：规则表驱动 + 显式 RULE_ORDER，
  而非隐式 if-chain（深度化的实质 = 把隐式顺序固化为显式确定性契约）。
"""

from __future__ import annotations

import re
from collections.abc import Callable

from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.types import ValidationResult

FORBIDDEN_STATEMENT_KEYWORDS = frozenset(
    {"insert", "update", "delete", "drop", "alter", "truncate"}
)

# 确定性 first-failure priority（唯一事实源）。
# 顺序与 manual FakeSQLValidator 的隐式检查顺序一致（行为兼容）；
# 新增规则必须在此显式登记，且不得改变既有规则的相对顺序。
RULE_ORDER: tuple[str, ...] = (
    "empty",
    "multi_statement",
    "forbidden_keyword",
    "select_only",
    "missing_limit",
    "limit_exceeds",
)

RuleCheck = Callable[[str, AgentConfig], ValidationResult | None]


def _rule_empty(sql: str, config: AgentConfig) -> ValidationResult | None:
    if not sql.strip():
        return ValidationResult(ok=False, error="empty SQL", rule="empty")
    return None


def _rule_multi_statement(sql: str, config: AgentConfig) -> ValidationResult | None:
    # 允许末尾单个分号，拒绝任何真正的多语句。
    statements = [s.strip() for s in sql.strip().split(";") if s.strip()]
    if len(statements) > 1:
        return ValidationResult(
            ok=False, error="multi-statement is not allowed", rule="multi_statement"
        )
    return None


def _first_keyword(statement: str) -> str:
    match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)", statement)
    return match.group(1).lower() if match else ""


def _rule_forbidden_keyword(sql: str, config: AgentConfig) -> ValidationResult | None:
    statements = [s.strip() for s in sql.strip().split(";") if s.strip()]
    keyword = _first_keyword(statements[0])
    if keyword in FORBIDDEN_STATEMENT_KEYWORDS:
        return ValidationResult(
            ok=False,
            error=f"forbidden statement keyword: {keyword}",
            rule="forbidden_keyword",
        )
    return None


def _rule_select_only(sql: str, config: AgentConfig) -> ValidationResult | None:
    statements = [s.strip() for s in sql.strip().split(";") if s.strip()]
    keyword = _first_keyword(statements[0])
    if keyword != "select":
        return ValidationResult(
            ok=False,
            error=f"only SELECT is allowed, got '{keyword or '?'}'",
            rule="select_only",
        )
    return None


def _rule_missing_limit(sql: str, config: AgentConfig) -> ValidationResult | None:
    if re.search(r"\blimit\s+(\d+)", sql, flags=re.IGNORECASE) is None:
        return ValidationResult(
            ok=False, error="missing LIMIT clause", rule="missing_limit"
        )
    return None


def _rule_limit_exceeds(sql: str, config: AgentConfig) -> ValidationResult | None:
    match = re.search(r"\blimit\s+(\d+)", sql, flags=re.IGNORECASE)
    if match is not None and int(match.group(1)) > config.max_rows:
        return ValidationResult(
            ok=False,
            error=f"LIMIT {match.group(1)} exceeds max_rows {config.max_rows}",
            rule="limit_exceeds",
        )
    return None


# 规则表：顺序 = RULE_ORDER（first-failure priority 的实现载体）。
# 新增规则 = 在此登记 + 更新 RULE_ORDER；不得改变既有相对顺序。
_RULE_TABLE: tuple[tuple[str, RuleCheck], ...] = (
    ("empty", _rule_empty),
    ("multi_statement", _rule_multi_statement),
    ("forbidden_keyword", _rule_forbidden_keyword),
    ("select_only", _rule_select_only),
    ("missing_limit", _rule_missing_limit),
    ("limit_exceeds", _rule_limit_exceeds),
)


class RuleBasedSQLValidator:
    """T05 静态校验器：规则表驱动、确定性优先级、单 rule 输出。

    输出始终为 examples.manual_agent_loop.types.ValidationResult 的三字段契约
    （ok / error / rule）——与 manual 结果模型完全兼容。
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config

    def validate(self, sql: str) -> ValidationResult:
        for name, check in _RULE_TABLE:
            result = check(sql, self._config)
            if result is not None:
                return result
        return ValidationResult(ok=True)
