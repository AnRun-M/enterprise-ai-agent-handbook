"""T01 Graph Node adapter：把 pure normalization 映射到 Graph State lifecycle。

分层（Gate A 冻结）：
- pure normalization function（normalization.py）：lexical normalization，无 Runtime 逻辑
- Node adapter（本文件）：读取 State → 调用 pure function → 返回 partial State Update

Failure contract（Gate A 冻结 + Review 修正）：
- empty / whitespace-only = expected application input failure ≠ Runtime exception
- 复用 status + failure_reason（AgentStatus），不新造 normalization_error 类型
- 不抛业务异常

Field ownership（Task Merge Gate Review 修正）：
- normalized_question = **T01-owned derived field**——T01 始终拥有其派生值生命周期
- status / failure_reason = **shared lifecycle fields**——T01 仅在
  invalid-input failure 时写入（把失败暴露给 shared lifecycle contract），
  **不在 success 时自动重置其它阶段可能产生的 lifecycle 状态**
- 原则："Field write capability ≠ field ownership."
"""

from __future__ import annotations

from examples.manual_agent_loop.types import AgentStatus

from .normalization import normalize_question
from .state import Text2SQLState

_INVALID_INPUT_REASON = "empty question: no valid input after normalization"


def normalize_input_node(state: Text2SQLState) -> dict:
    """读 user_question → 规范化 → 返回部分 State Update。

    field ownership 两层：
    - normalized_question = T01-owned derived field
    - status / failure_reason = shared lifecycle fields（T01 仅 failure 时写入）

    success（valid input）：
        {"normalized_question": <normalized>}
        （不覆盖 user_question；不重置 status / failure_reason——
        合法 normalization 不得把任意 FAILED lifecycle 恢复为 RUNNING）

    failure（empty / whitespace-only）：
        {"normalized_question": None,
         "status": AgentStatus.FAILED,
         "failure_reason": <reason>}
        （normalized_question = None：T01-owned derived field 必须
        invalidates stale 值；status / failure_reason：invalid input 是
        预期 application failure，需要暴露给 shared lifecycle contract）
    """
    normalized = normalize_question(state["user_question"])
    if normalized is None:
        return {
            "normalized_question": None,
            "status": AgentStatus.FAILED,
            "failure_reason": _INVALID_INPUT_REASON,
        }
    return {"normalized_question": normalized}
