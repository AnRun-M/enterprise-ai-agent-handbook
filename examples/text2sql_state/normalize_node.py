"""T01 Graph Node adapter：把 pure normalization 映射到 Graph State lifecycle。

分层（Gate A 冻结）：
- pure normalization function（normalization.py）：lexical normalization，无 Runtime 逻辑
- Node adapter（本文件）：读取 State → 调用 pure function → 返回 partial State Update

Failure contract（Gate A 冻结）：
- empty / whitespace-only = expected application input failure ≠ Runtime exception
- 复用 status + failure_reason（AgentStatus.FAILED），不新造 normalization_error 类型
- 不抛业务异常
"""

from __future__ import annotations

from examples.manual_agent_loop.types import AgentStatus

from .normalization import normalize_question
from .state import Text2SQLState

_INVALID_INPUT_REASON = "empty question: no valid input after normalization"


def normalize_input_node(state: Text2SQLState) -> dict:
    """读 user_question → 规范化 → 返回部分 State Update。

    success：
        {"normalized_question": <normalized>}
        （user_question 保持不变；status 保持 RUNNING；不覆盖其它字段）

    failure（empty / whitespace-only）：
        {"status": AgentStatus.FAILED,
         "failure_reason": <reason>}
        （user_question 保留；normalized_question 不写入——不进入后续语义解析）
    """
    normalized = normalize_question(state["user_question"])
    if normalized is None:
        return {
            "status": AgentStatus.FAILED,
            "failure_reason": _INVALID_INPUT_REASON,
        }
    return {"normalized_question": normalized}
