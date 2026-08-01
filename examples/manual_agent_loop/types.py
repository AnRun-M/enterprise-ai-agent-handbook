"""共享值类型：动作、状态、工具与校验的结构化结果。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """模型可以做出的决策，由 Runtime 翻译为动作。"""

    GENERATE_SQL = "generate_sql"
    FIX_SQL = "fix_sql"
    FINALIZE = "finalize"


class AgentStatus(Enum):
    """一次 Agent 任务的生命周期状态。"""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"


@dataclass(frozen=True)
class AgentAction:
    """模型决策的结构化表示：做什么 + 为什么。"""

    type: ActionType
    reason: str = ""


@dataclass
class ToolResult:
    """工具调用的结构化输出（canonical T09 执行结果）。"""

    ok: bool
    data: dict[str, object] | None = None
    error: str | None = None


@dataclass
class ValidationResult:
    """SQL 静态校验的结构化输出（canonical T05）。"""

    ok: bool
    error: str | None = None
    rule: str | None = None


@dataclass(frozen=True)
class StepEvent:
    """State.history 中的一条记录：某一轮循环发生了什么。"""

    iteration: int
    status: AgentStatus
    action: ActionType | None = None
    sql: str | None = None
    validation_error: str | None = None
    note: str = ""
