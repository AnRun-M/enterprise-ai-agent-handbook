"""Part 04 Text-to-SQL 实现载体（TASK-0029：目录结构由架构调整确定，当前单包起步）。

T01 输入规范化（TASK-0032，completed）：
- normalize_question：deterministic lexical normalization（纯函数）
- normalize_input_node：Graph Node adapter（映射到既有 lifecycle / failure contract）

T03 元数据与业务规则检索（TASK-0033，本分支）：
- RetrievalOutcome / RetrievalReference / MaterializedFacts / RetrievalResult /
  RetrievalCriteria（contract 类型；RetrievalCriteria 为 Proposed consumed
  contract / fixture，非 T02 最终 schema）
- InMemoryMetadataSource（fake authoritative source，教学规模）
- MetadataRetriever（确定性检索，读取事实不创造事实）
- retrieve_metadata_node（Graph Node adapter，不触碰 shared lifecycle）

复用 examples.manual_agent_loop 的 AgentStatus / ValidationResult，不复制实现。

T05 SQL 静态校验（TASK-0030）：
- RULE_ORDER / RuleBasedSQLValidator（canonical T05）
"""

from .metadata_source import InMemoryMetadataSource, build_fixture_source
from .normalization import normalize_question
from .normalize_node import normalize_input_node
from .retrieval import MetadataRetriever
from .retrieval_node import retrieve_metadata_node
from .retrieval_types import (
    MaterializedFacts,
    RetrievalCriteria,
    RetrievalOutcome,
    RetrievalReference,
    RetrievalResult,
)
from .validation import RULE_ORDER, RuleBasedSQLValidator

__all__ = [
    "RULE_ORDER",
    "InMemoryMetadataSource",
    "MaterializedFacts",
    "MetadataRetriever",
    "RetrievalCriteria",
    "RetrievalOutcome",
    "RetrievalReference",
    "RetrievalResult",
    "RuleBasedSQLValidator",
    "build_fixture_source",
    "normalize_input_node",
    "normalize_question",
    "retrieve_metadata_node",
]
