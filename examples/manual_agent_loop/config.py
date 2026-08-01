"""配置：Runtime 旋钮。本 Demo 不读取任何密钥；真实 LLM / 数据库凭证由生产系统注入。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """默认值仅用于教学 Demo，不代表生产建议值。"""

    max_iterations: int = 3
    max_rows: int = 1000
    sql_timeout_seconds: int = 30
