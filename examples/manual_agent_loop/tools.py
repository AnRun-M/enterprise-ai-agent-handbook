"""SQL Validator 与 SQL Executor（canonical T05 / T09）。

教学型组件：规则显式、可测试，但不得声称可直接用于生产。
生产级 SQL 安全还需要：AST 解析、权限校验、数据范围控制、扫描量限制和审计。
"""

from __future__ import annotations

import re
from typing import ClassVar, Protocol

from .config import AgentConfig
from .types import ToolResult, ValidationResult

# DML / DCL 都是语句级关键字，只需检查语句首个 token，
# 避免对列名（如 updated_at）做子串匹配造成误伤。
FORBIDDEN_STATEMENT_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "truncate")


class SQLValidator(Protocol):
    def validate(self, sql: str) -> ValidationResult: ...


class FakeSQLValidator:
    """语法级校验器：只做规则检查，不解析语义。

    规则（教学级）：
    - 只允许 SELECT
    - 禁止 INSERT / UPDATE / DELETE / DROP / ALTER / TRUNCATE
    - 必须有 LIMIT
    - 禁止多语句
    - LIMIT 不超过配置的 max_rows
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config

    def validate(self, sql: str) -> ValidationResult:
        stripped = sql.strip()
        if not stripped:
            return ValidationResult(ok=False, error="empty SQL", rule="empty")

        # 多语句检查：允许末尾单个分号，拒绝任何真正的多语句。
        statements = [s.strip() for s in stripped.split(";") if s.strip()]
        if len(statements) > 1:
            return ValidationResult(ok=False, error="multi-statement is not allowed", rule="multi_statement")
        statement = statements[0]

        first_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)", statement)
        first_keyword = first_match.group(1).lower() if first_match else ""
        if first_keyword in FORBIDDEN_STATEMENT_KEYWORDS:
            return ValidationResult(
                ok=False,
                error=f"forbidden statement keyword: {first_keyword}",
                rule="forbidden_keyword",
            )
        if first_keyword != "select":
            return ValidationResult(
                ok=False,
                error=f"only SELECT is allowed, got '{first_keyword or '?'}'",
                rule="select_only",
            )

        limit_match = re.search(r"\blimit\s+(\d+)", statement, flags=re.IGNORECASE)
        if limit_match is None:
            return ValidationResult(ok=False, error="missing LIMIT clause", rule="missing_limit")
        limit_value = int(limit_match.group(1))
        if limit_value > self._config.max_rows:
            return ValidationResult(
                ok=False,
                error=f"LIMIT {limit_value} exceeds max_rows {self._config.max_rows}",
                rule="limit_exceeds",
            )

        return ValidationResult(ok=True)


class SQLExecutor(Protocol):
    def execute(self, sql: str) -> ToolResult: ...


class FakeSQLExecutor:
    """模拟 Spark / Athena / BigQuery 执行（canonical T09），返回固定 GMV 数据。

    不连接真实数据库，结果完全可复现。sql_timeout_seconds 由生产执行引擎使用，
    本 Fake 不模拟超时。

    最小安全检查为纵深防御：与 Validator 的检查刻意独立实现（每层各自把关），
    即使上层校验被绕过，执行层也拒绝：空 SQL、非 SELECT、多语句
    （包括「SELECT 1; DROP TABLE orders」这类拼接）。

    首 token 判定：提取第一个完整 token，忽略大小写后严格等于 "select" 才允许执行，
    因此 SELECTED、SELECTevil 等前缀相似 token 同样被拒绝。

    CTE 说明：当前教学实现仅允许首 token 为 SELECT，CTE（以 WITH 开头）被明确拒绝；
    生产实现应通过 AST 解析与策略决定是否允许 CTE。

    这仍然是教学级防御，不能替代 AST 解析、权限校验、扫描量限制和审计。
    """

    FIXED_RESULT: ClassVar[dict[str, object]] = {
        "gmv": 1234567.89,
        "order_date": "2026-07-31",
        "row_count": 1,
    }

    def execute(self, sql: str) -> ToolResult:
        stripped = sql.strip()
        if not stripped:
            return ToolResult(ok=False, error="empty SQL")
        statements = [s.strip() for s in stripped.split(";") if s.strip()]
        if len(statements) > 1:
            return ToolResult(ok=False, error="multi-statement is not allowed")

        # 提取首个完整 token，严格匹配 "select"（避免 SELECTED / SELECTevil 前缀通过）。
        first_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)", statements[0])
        first_token = first_match.group(1).lower() if first_match else ""
        if first_token != "select":
            return ToolResult(
                ok=False,
                error=f"only SELECT can be executed, got '{first_token or '?'}'",
            )
        return ToolResult(ok=True, data=dict(self.FIXED_RESULT))
