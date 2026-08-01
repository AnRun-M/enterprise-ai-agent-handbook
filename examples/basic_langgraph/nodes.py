"""Graph 节点：读取 State -> 调用已存在的 Fake 组件 -> 返回部分 State 更新。

职责边界（本 Demo 的教学约定）：
- 节点不调用下一个节点（下一步由 conditional edge 的路由函数决定）
- 节点内部不写 while 循环
- 业务动作决策只发生在 decide 节点（调用 model.decide_next），路由函数不做业务决策
- 节点异常统一由 _failure_boundary 转换为 State 更新（status=FAILED + failure_reason
  + 正确的 iteration + 失败 history 事件），异常前已有的 current_sql /
  validation_error / execution_result / history 由 LangGraph channel 合并自动保留
- Graph Runtime 级异常（如路由函数异常）不在节点内处理，由 agent.py 层兜底

复用：FakeLLM / Validator / Executor 均来自 examples.manual_agent_loop，不复制实现。
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

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


def _failure_boundary(
    node_name: str, *, increments_round: bool
) -> Callable[[Callable[[GraphState], dict]], Callable[[GraphState], dict]]:
    """节点级异常转换（统一机制，应用于 generate_sql / fix_sql / finalize / decide）。

    任何节点异常转为 FAILED State 更新：
    - status = FAILED
    - failure_reason = "node error in <node>: <exc>"
    - iteration：decide 节点（increments_round=True）失败于「本轮决策」，
      报告本轮编号（state.iteration + 1，与手写版本一致）；动作节点失败时
      iteration 已由 decide 递增，直接使用 state.iteration
    - 追加一条失败 history 事件（action=None，与手写异常的 record_round 语义一致）
    - 异常前状态（current_sql / validation_error / execution_result / history）
      不写入任何更新字段，由 LangGraph channel 合并自动保留
    """

    def decorate(fn: Callable[[GraphState], dict]) -> Callable[[GraphState], dict]:
        @wraps(fn)
        def wrapped(state: GraphState) -> dict:
            try:
                return fn(state)
            except Exception as exc:  # noqa: BLE001 - 节点级异常边界：转为 State 而非向上抛出
                iteration = state["iteration"] + 1 if increments_round else state["iteration"]
                reason = f"node error in {node_name}: {exc!r}"
                return {
                    "iteration": iteration,
                    "status": AgentStatus.FAILED,
                    "failure_reason": reason,
                    "history": [
                        StepEvent(
                            iteration=iteration,
                            action=None,
                            status=AgentStatus.FAILED,
                            sql=state["current_sql"],
                            validation_error=state["validation_error"],
                            note=reason,
                        )
                    ],
                }

        return wrapped

    return decorate


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


def make_decide_node(model: LLM) -> Callable[[GraphState], dict]:
    """本轮决策：iteration 递增 + 调用 model.decide_next（模型拥有业务决策权）。

    等价于手写 Runtime 的「循环顶部递增 iteration + decide_next」。
    本节点不追加 history 事件（history 语义由动作节点维护，保证与手写版可比）。
    """

    @_failure_boundary("decide", increments_round=True)
    def decide(state: GraphState) -> dict:
        action = model.decide_next(StateProxy(state))
        return {
            "iteration": state["iteration"] + 1,
            "next_action": action.type,
            "decision_reason": action.reason,
        }

    return decide


def make_generate_sql_node(model: LLM, validator: SQLValidator) -> Callable[[GraphState], dict]:
    """T04 生成 + T05 校验（等价于手写 Runtime 的 GENERATE_SQL 分支）。"""

    @_failure_boundary("generate_sql", increments_round=False)
    def generate_sql(state: GraphState) -> dict:
        sql = model.generate_sql(StateProxy(state))
        updates: dict[str, object] = {"current_sql": sql}
        updates.update(_validate_update(sql, validator))
        merged = {**state, **updates}
        updates["history"] = _event(merged, _NODE_TO_ACTION["generate_sql"])
        return updates

    return generate_sql


def make_fix_sql_node(model: LLM, validator: SQLValidator) -> Callable[[GraphState], dict]:
    """T07 修复 + T05 校验（等价于手写 Runtime 的 FIX_SQL 分支）。"""

    @_failure_boundary("fix_sql", increments_round=False)
    def fix_sql(state: GraphState) -> dict:
        sql = model.fix_sql(StateProxy(state))
        updates: dict[str, object] = {"current_sql": sql}
        updates.update(_validate_update(sql, validator))
        merged = {**state, **updates}
        updates["history"] = _event(merged, _NODE_TO_ACTION["fix_sql"])
        return updates

    return fix_sql


def make_finalize_node(executor: SQLExecutor) -> Callable[[GraphState], dict]:
    """T09 执行 + T12 输出（等价于手写 Runtime 的 FINALIZE 分支）。

    可预期的执行失败转为 State（FAILED + failure_reason），不抛出异常；
    非预期异常由 _failure_boundary 统一转换。
    """

    @_failure_boundary("finalize", increments_round=False)
    def finalize(state: GraphState) -> dict:
        updates: dict[str, object] = {}
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
