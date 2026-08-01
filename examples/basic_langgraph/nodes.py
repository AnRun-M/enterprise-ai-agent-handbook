"""Graph 节点：读取 State -> 调用已存在的 Fake 组件 -> 返回部分 State 更新。

职责边界（本 Demo 的教学约定）：
- 节点不调用下一个节点（下一步由 conditional edge 的路由函数决定）
- 节点内部不写 while 循环
- 可预期的工具失败转为 State（FAILED + failure_reason）
- 非预期异常不在节点内捕获：由 LangGraph 向上抛出，在 agent.py 层统一转为 FAILED
  （错误边界详见 README 与 docs/03-langgraph-core/manual-vs-langgraph.md）

复用：FakeLLM / Validator / Executor 均来自 examples.manual_agent_loop，
不复制实现。
"""

from __future__ import annotations

from collections.abc import Callable

from examples.manual_agent_loop.models import LLM
from examples.manual_agent_loop.runtime import build_final_answer
from examples.manual_agent_loop.tools import SQLExecutor, SQLValidator
from examples.manual_agent_loop.types import ActionType, AgentStatus, StepEvent

from .state import GraphState, StateProxy

# 节点名 -> 语义等价的手写动作（保证 history 与 manual_agent_loop 可比较）。
_NODE_TO_ACTION: dict[str, ActionType] = {
    "generate_sql": ActionType.GENERATE_SQL,
    "fix_sql": ActionType.FIX_SQL,
    "finalize": ActionType.FINALIZE,
}


def _validate_update(sql: str, validator: SQLValidator) -> dict[str, str | None]:
    """执行 T05 静态校验，返回 validation_error / validation_rule 的部分更新。"""
    result = validator.validate(sql)
    return {
        "validation_error": None if result.ok else result.error,
        "validation_rule": None if result.ok else result.rule,
    }


def _event(state: GraphState, action: ActionType | None, note: str = "") -> list[StepEvent]:
    """按当前 State 快照生成一条 history 事件（每节点只追加一条）。"""
    return [
        StepEvent(
            iteration=state["iteration"],
            action=action,
            status=state["status"],
            sql=state["current_sql"],
            validation_error=state["validation_error"],
            note=note,
        )
    ]


def make_generate_sql_node(model: LLM, validator: SQLValidator) -> Callable[[GraphState], dict]:
    """T04 生成 + T05 校验（等价于手写 Runtime 的 GENERATE_SQL 分支）。"""

    def generate_sql(state: GraphState) -> dict:
        sql = model.generate_sql(StateProxy(state))
        updates: dict[str, object] = {
            "current_sql": sql,
            "iteration": state["iteration"] + 1,
        }
        updates.update(_validate_update(sql, validator))
        merged = {**state, **updates}
        updates["history"] = _event(merged, _NODE_TO_ACTION["generate_sql"])
        return updates

    return generate_sql


def make_fix_sql_node(model: LLM, validator: SQLValidator) -> Callable[[GraphState], dict]:
    """T07 修复 + T05 校验（等价于手写 Runtime 的 FIX_SQL 分支）。"""

    def fix_sql(state: GraphState) -> dict:
        sql = model.fix_sql(StateProxy(state))
        updates: dict[str, object] = {
            "current_sql": sql,
            "iteration": state["iteration"] + 1,
        }
        updates.update(_validate_update(sql, validator))
        merged = {**state, **updates}
        updates["history"] = _event(merged, _NODE_TO_ACTION["fix_sql"])
        return updates

    return fix_sql


def make_finalize_node(executor: SQLExecutor) -> Callable[[GraphState], dict]:
    """T09 执行 + T12 输出（等价于手写 Runtime 的 FINALIZE 分支）。

    可预期的执行失败转为 State（FAILED + failure_reason），不抛出异常。
    """

    def finalize(state: GraphState) -> dict:
        updates: dict[str, object] = {"iteration": state["iteration"] + 1}
        if state["current_sql"] is None:
            updates["status"] = AgentStatus.FAILED
            updates["failure_reason"] = "cannot finalize without a SQL candidate"
        else:
            result = executor.execute(state["current_sql"])
            updates["execution_result"] = result
            if result.ok:
                updates["status"] = AgentStatus.SUCCESS
                updates["final_answer"] = build_final_answer(state["user_question"], result)
            else:
                updates["status"] = AgentStatus.FAILED
                updates["failure_reason"] = f"execution failed: {result.error}"
        merged = {**state, **updates}
        updates["history"] = _event(merged, _NODE_TO_ACTION["finalize"])
        return updates

    return finalize


def make_max_iterations_node() -> Callable[[GraphState], dict]:
    """确定性兜底终止：达到最大迭代次数（不增加 iteration，与手写语义一致）。"""

    def max_iterations(state: GraphState) -> dict:
        return {
            "status": AgentStatus.MAX_ITERATIONS_REACHED,
            "history": [
                StepEvent(
                    iteration=state["iteration"],
                    action=None,
                    status=AgentStatus.MAX_ITERATIONS_REACHED,
                    sql=state["current_sql"],
                    validation_error=state["validation_error"],
                    note=f"max_iterations {state['max_iterations']} reached without success",
                )
            ],
        }

    return max_iterations
