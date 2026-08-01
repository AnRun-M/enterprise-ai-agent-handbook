"""AgentState：一次任务执行中显式保存和传递的数据（TERMINOLOGY：State）。

状态通过 dataclass 显式传递，不使用任何全局变量。
所有状态变更都必须经过本类的更新方法，保证更新路径可测试。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import ActionType, AgentStatus, StepEvent, ToolResult, ValidationResult


@dataclass
class AgentState:
    """一次 Agent 任务的完整状态。"""

    user_question: str
    max_iterations: int
    current_sql: str | None = None
    validation_error: str | None = None
    validation_rule: str | None = None
    execution_result: ToolResult | None = None
    final_answer: str | None = None
    iteration: int = 0
    status: AgentStatus = AgentStatus.RUNNING
    history: list[StepEvent] = field(default_factory=list)

    # -- 状态更新 API --------------------------------------------------

    def is_terminal(self) -> bool:
        """循环是否应该停止：三种终止状态（success / failed / max_iterations_reached）。"""
        return self.status in (
            AgentStatus.SUCCESS,
            AgentStatus.FAILED,
            AgentStatus.MAX_ITERATIONS_REACHED,
        )

    def apply_candidate(self, sql: str) -> None:
        """写入模型新生成的 SQL，并清空上一轮的校验错误。"""
        self.current_sql = sql
        self.validation_error = None
        self.validation_rule = None

    def apply_validation(self, result: ValidationResult) -> None:
        """记录 T05 静态校验结果：错误消息（供展示）与规则名（供模型修复决策）。"""
        self.validation_error = None if result.ok else result.error
        self.validation_rule = None if result.ok else result.rule

    def apply_execution(self, result: ToolResult) -> None:
        """记录 T09 执行结果。"""
        self.execution_result = result

    def complete_success(self, answer: str) -> None:
        """成功终止：写入最终回答（T12 结构化输出）。"""
        self.final_answer = answer
        self.status = AgentStatus.SUCCESS

    def fail(self, reason: str) -> None:
        """失败终止：执行失败或未处理异常。"""
        self.status = AgentStatus.FAILED

    def exceed_max_iterations(self) -> None:
        """确定性兜底终止：达到最大迭代次数。"""
        self.status = AgentStatus.MAX_ITERATIONS_REACHED

    def record_round(self, action: ActionType | None = None, note: str = "") -> None:
        """把当前一轮的关键事件追加到 history。"""
        self.history.append(
            StepEvent(
                iteration=self.iteration,
                action=action,
                status=self.status,
                sql=self.current_sql,
                validation_error=self.validation_error,
                note=note,
            )
        )
