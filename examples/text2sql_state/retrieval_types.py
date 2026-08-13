"""T03 检索 contract 类型（Gate B：只选择 Python representation，不改 Gate A 语义）。

Gate A 冻结（TASK-0033）：
- Retrieval Outcome 五态：complete / partial / not_found / ambiguous / unavailable
- References / Provenance：source_ref + freshness/version evidence
  （version / revision / timestamp / etag / digest / snapshot id 依 source
  capability——不强迫所有 source 存在统一 version 字段）
- Materialized Retrieval Payload：当前请求实际消费的 schema facts /
  metadata / business-rule facts——供 Context Builder → Model Context → T04

边界：
- T03 只返回 outcome，不决定继续 T04 / 终止 / retry / ask human
  （路由由后续 application control flow / policy 表达）
- RetrievalCriteria 是 Proposed consumed contract（fixture），
  模拟未来 T02 输出——不是 T02 最终 schema
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RetrievalOutcome(Enum):
    """检索结果分层（Gate A 冻结，仅语义不扩张）。"""

    COMPLETE = "complete"  # 所需事实完整
    PARTIAL = "partial"  # 部分事实可用——是否继续由消费方 / 应用策略决定
    NOT_FOUND = "not_found"  # 权威源明确无匹配（不等同 infrastructure exception）
    AMBIGUOUS = "ambiguous"  # 存在多个合法映射——需上层澄清 / 处理
    UNAVAILABLE = "unavailable"  # 权威源当前不可访问（operational failure）


@dataclass(frozen=True)
class RetrievalReference:
    """可持久化的 provenance / 追踪信息（适合进入 State）。

    **Identity 模型**（Task Merge Gate Review 修正）：
    - `entry_id`（CatalogEntry）= 稳定 **source-local fact identity**
    - `fact_id` = **source-qualified stable fact identity**——
      由 source 名 + entry_id 构造（`f"{source.name}:{entry.entry_id}"`），
      deterministic / 不依赖 object identity / 不依赖随机 UUID /
      permutation-invariant / duplicate-dedup 后稳定
    - `key` = retrieval / semantic **lookup identity**——不承担 fact-level
      unique identity（如 `catalog-v1:ambiguous_metric` 可对应多个候选）
    - `evidence` = **freshness / version evidence**——具体表现依 source
      capability（version / revision / timestamp / etag / digest /
      snapshot id）；**不承担 identity discriminator**
    - 固定原则："Fact identity ≠ freshness/version evidence."
      （事实身份不等于版本 / 新鲜度证据）

    source_ref：事实来自哪个 authoritative source / lookup identity；
    不承担 fact-level unique identity（candidate 唯一性由 fact_id 承担）。
    """

    fact_id: str  # source-qualified stable fact identity（source:entry_id）
    source_ref: str  # source / lookup identity（如 "catalog-v1:ambiguous_metric"，可对应多候选）
    evidence: str  # freshness / version evidence——不是 identity


@dataclass(frozen=True)
class MaterializedFact:
    """一条已物化的事实内容 + 稳定关联键。

    fact_id 与对应 RetrievalReference.fact_id 相同——消费者可把
    "这条事实"解析到"它的 provenance"（fact-level binding）。
    """

    fact_id: str
    content: str


@dataclass(frozen=True)
class MaterializedFacts:
    """当前请求实际取得的事实内容（request-scoped materialization）。

    **教学规模实现选择，不是生产建议**：真实生产中完整 payload 不
    无条件复制进 State（architecture-map 引用策略：ID / URI / version /
    digest / summary）；当前教学 Demo 为简化保存小型 payload，
    便于 Context Builder 直接组装 Model Context。
    """

    schema_facts: tuple[MaterializedFact, ...] = field(default_factory=tuple)
    business_rules: tuple[MaterializedFact, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievalResult:
    """T03 检索输出：outcome + provenance/references + materialized facts。

    不含：source object / repository client / runtime handle / 连接
    （不可序列化对象不得进入 result / State）。
    不含：路由意图（不决定继续 / 终止 / retry / ask human）。
    """

    outcome: RetrievalOutcome
    references: tuple[RetrievalReference, ...] = field(default_factory=tuple)
    materialized: MaterializedFacts = field(default_factory=MaterializedFacts)


@dataclass(frozen=True)
class RetrievalCriteria:
    """**Proposed consumed contract（fixture）**——模拟未来 T02 输出。

    明确：这是 fixture 结构，**不是 T02 最终 schema**（T02 尚未实现）；
    概念上对应 T02 解析出的 metric / dimensions / entities / time range
    / filters 等检索条件。Integration 状态：deferred。
    """

    keys: tuple[str, ...] = field(default_factory=tuple)
