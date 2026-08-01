"""手写 Agent Runtime：while 循环、调度、终止条件、异常处理、状态更新。

Agent Loop（TERMINOLOGY）：读取状态 -> 模型决策 -> 执行动作 -> 更新状态 -> 判断是否继续。
本模块不依赖任何框架；同一循环的 LangGraph 表示见 v0.4.0 里程碑。
"""

from __future__ import annotations

from .models import LLM
from .state import AgentState
from .tools import SQLExecutor, SQLValidator
from .types import ActionType, AgentAction, ToolResult


def build_final_answer(user_question: str, result: ToolResult) -> str:
    """T12 结构化输出（确定性代码）：由执行结果生成最终回答。"""
    data = result.data or {}
    gmv = float(data.get("gmv", 0.0))
    order_date = data.get("order_date", "")
    row_count = data.get("row_count", 0)
    return (
        f"「{user_question}」的查询结果：{order_date} 的 GMV 为 ¥{gmv:,.2f}，"
        f"共返回 {row_count} 行。"
    )


class AgentRuntime:
    """手写 Runtime：循环显式、状态显式、终止条件显式。"""

    def __init__(
        self,
        model: LLM,
        validator: SQLValidator,
        executor: SQLExecutor,
    ) -> None:
        self._model = model
        self._validator = validator
        self._executor = executor

    def run(self, state: AgentState) -> AgentState:
        while not state.is_terminal():
            # 终止条件 1：达到最大迭代次数（确定性兜底，防止模型无限循环）。
            if state.iteration >= state.max_iterations:
                state.exceed_max_iterations()
                state.record_round(note=f"max_iterations {state.max_iterations} reached without success")
                break

            state.iteration += 1
            try:
                action = self._model.decide_next(state)  # 模型决策
                self._dispatch(action, state)            # 执行动作 + 更新状态
                state.record_round(action=action.type, note=action.reason)
            except Exception as exc:  # noqa: BLE001 - 故障隔离：任何工具/模型异常都以 FAILED 终止，而不是让循环崩溃
                # 终止条件 2：未处理异常
                state.fail(f"runtime error: {exc!r}")
                state.record_round(note=f"runtime error: {exc!r}")
        return state

    def _dispatch(self, action: AgentAction, state: AgentState) -> None:
        """把模型决策翻译为工具调用，并把结果写回状态。"""
        if action.type is ActionType.GENERATE_SQL:
            sql = self._model.generate_sql(state)
            state.apply_candidate(sql)
            state.apply_validation(self._validator.validate(sql))
        elif action.type is ActionType.FIX_SQL:
            sql = self._model.fix_sql(state)
            state.apply_candidate(sql)
            state.apply_validation(self._validator.validate(sql))
        elif action.type is ActionType.FINALIZE:
            if state.current_sql is None:
                raise RuntimeError("cannot finalize without a SQL candidate")
            result = self._executor.execute(state.current_sql)
            state.apply_execution(result)
            if result.ok:
                state.complete_success(build_final_answer(state.user_question, result))
            else:
                state.fail(f"execution failed: {result.error}")
        else:
            raise RuntimeError(f"unknown action type: {action.type}")
