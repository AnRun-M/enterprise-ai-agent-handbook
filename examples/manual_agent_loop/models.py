"""LLM 接口与 FakeLLM：Demo 不连接真实模型，行为完全可预测。

真实 LLM 客户端可通过依赖注入替换（AGENTS.md 代码规范）。
"""

from __future__ import annotations

import re
from typing import Protocol

from .config import AgentConfig
from .state import AgentState
from .types import ActionType, AgentAction


class LLM(Protocol):
    """模型接口：决策 + 生成 / 修复 SQL。"""

    def decide_next(self, state: AgentState) -> AgentAction: ...

    def generate_sql(self, state: AgentState) -> str: ...

    def fix_sql(self, state: AgentState) -> str: ...


class FakeLLM:
    """确定性 Fake 模型（教学场景「查询昨天的 GMV」）。

    行为脚本：
    1. 第一轮生成缺少 LIMIT 的 SQL。注：真实系统中「错误字段 / 错误口径」由语义层
       （canonical T03 元数据检索 / T06 权限与风险检查）拦截，语法级 Validator
       只能拦截语法类规则——本 Demo 的语法错误（缺 LIMIT）即代表「第一版 SQL 有错」。
    2. Validator 返回 missing_limit 错误。
    3. 第二轮根据 validation_error 修复：补上 LIMIT。
    4. 校验通过后由 Runtime 进入 FINALIZE。
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config

    def decide_next(self, state: AgentState) -> AgentAction:
        if state.current_sql is None:
            return AgentAction(ActionType.GENERATE_SQL, reason="no candidate yet")
        if state.validation_error is not None:
            return AgentAction(ActionType.FIX_SQL, reason=f"validation failed: {state.validation_error}")
        if state.execution_result is None:
            return AgentAction(ActionType.FINALIZE, reason="validation passed")
        return AgentAction(ActionType.FINALIZE, reason="already executed")

    def generate_sql(self, state: AgentState) -> str:
        # 第一版 SQL 故意缺少 LIMIT：Validator 将返回 missing_limit。
        return (
            "SELECT order_date, SUM(amount) AS gmv "
            "FROM orders WHERE order_date = '2026-07-31'"
        )

    def fix_sql(self, state: AgentState) -> str:
        sql = state.current_sql or ""
        if state.validation_rule == "missing_limit":
            return f"{sql} LIMIT {self._config.max_rows}"
        if state.validation_rule == "limit_exceeds":
            return re.sub(
                r"\blimit\s+\d+",
                f"LIMIT {self._config.max_rows}",
                sql,
                flags=re.IGNORECASE,
            )
        return sql
