"""对外接口：LangGraphAgent.invoke(question) -> 最终 GraphState。

错误边界（本 Demo 的分层约定）：
- 节点内部可预期的失败（如执行失败）已转为 State（FAILED + failure_reason）；
- 非预期异常由 LangGraph 向上抛出，在 invoke 层捕获并转换为 FAILED State；
- 无 Checkpointer 时异常不保留部分执行状态——这是本 Demo 的明确边界
  （Checkpoint 能力在 v0.4.0 / v0.6.0 里程碑引入）。
"""

from __future__ import annotations

from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.models import LLM, FakeLLM
from examples.manual_agent_loop.tools import (
    FakeSQLExecutor,
    FakeSQLValidator,
    SQLExecutor,
    SQLValidator,
)
from examples.manual_agent_loop.types import AgentStatus

from .graph import build_graph
from .state import GraphState, build_initial_state


class LangGraphAgent:
    """与 manual_agent_loop.Agent 行为等价的 LangGraph 实现（依赖注入同构）。"""

    def __init__(
        self,
        config: AgentConfig | None = None,
        model: LLM | None = None,
        validator: SQLValidator | None = None,
        executor: SQLExecutor | None = None,
    ) -> None:
        self._config = config or AgentConfig()
        self._graph = build_graph(
            model=model or FakeLLM(self._config),
            validator=validator or FakeSQLValidator(self._config),
            executor=executor or FakeSQLExecutor(),
        )

    def invoke(self, question: str) -> GraphState:
        """运行图并返回最终 State（类型：GraphState 字典）。"""
        initial = build_initial_state(question, self._config.max_iterations)
        try:
            return self._graph.invoke(initial)
        except Exception as exc:  # noqa: BLE001 - 错误边界：节点内的非预期异常由此层统一转为 FAILED（见 README 第 13 节）
            return {
                **initial,
                "status": AgentStatus.FAILED,
                "failure_reason": f"graph runtime error: {exc!r}",
            }
