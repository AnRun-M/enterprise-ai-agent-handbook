"""T02 语义解释 contract 类型（Gate B：只选择 Python representation，不改 Gate A 语义）。

Gate A 冻结（TASK-0034）：
- IntentResult = **T02-owned derived state**，单个 State channel 进入 Text2SQLState
  （字段名 Gate B 落地：`intent_result`）
- outcome taxonomy 四态：COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED——
  四者都必须产生**完整** IntentResult（None 不表示任何 expected outcome）
- 语义类别（教学规模）：metric / dimension / entity / time range / filters /
  aggregation intent / query intent——每个类别必须能表达四种**可区分**的
  语义状态：resolved / ambiguous candidates / required but unresolved /
  not applicable
- T02 产出是 structured semantic interpretation，不是 authoritative fact：
  术语约定——T02 产出不得称为 fact / semantic fact / structured fact
  （除否定 / 对比上下文）；"fact" 表述只属 T03 authoritative facts
- retrieval requirements = **source-agnostic 逻辑契约层**，不绑定任何 source
  vocabulary；source-specific RetrievalCriteria 由 integration / source-
  specific adapter 产生（Gate B 不得删除这一层）
- 原则："Semantic interpretation ≠ retrieval requirement ≠ source-specific
  retrieval criteria." / "Retrieval requirement is data, not routing."

**非法状态组合的自然防止（Gate B 设计决策）**：
- `outcome` 是**派生属性**（不是可写字段）——由类别语义状态推导：
  存在 REQUIRED_UNRESOLVED 时 outcome 必然是 PARTIAL，因此
  "outcome = COMPLETE 却仍存在 required-unresolved" 结构上不可表达
- `SemanticValue` 的 AMBIGUOUS_CANDIDATES 只承载 `candidates`（≥2）且
  `resolved` 恒为 None——没有可被"静默选择"的单一 resolved 值，
  因此 "outcome = AMBIGUOUS 却静默选择 resolved candidate" 不可表达
- `retrieval_requirements` 是派生属性，UNSUPPORTED 恒为空；adapter 对空
  requirements 返回 None（不生成普通 RetrievalCriteria），因此
  "outcome = UNSUPPORTED 却自动生成普通 RetrievalCriteria" 不可表达
- 其余不变式（unsupported 不得携带类别语义 / SemanticValue 形状一致）在
  构造边界 fail-fast（与 T03 CatalogEntry 的 source-boundary 校验同构：
  "Static type annotation ≠ runtime contract validation."），不是
  在实现层用 if/assert 修补 outcome 矛盾
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

_FACT_GROUNDED_CATEGORIES = frozenset(
    {
        "metric",
        "dimension",
        "entity",
        "filter",
    }
)


class IntentOutcome(Enum):
    """T02 semantic interpretation outcome（Gate A 冻结四态，不机械复制 T03 五态）。

    四态都是 expected application outcome，都产生完整 IntentResult；
    None 只表示"不存在合法 T02 semantic result"，不是任何 expected outcome。
    """

    COMPLETE = "complete"  # 当前请求所需 semantic requirements 均已充分表达
    PARTIAL = "partial"  # 有有效 interpretation，但至少一个 required requirement 未解析
    AMBIGUOUS = "ambiguous"  # 存在多个合理 interpretation candidates，不静默选择
    UNSUPPORTED = "unsupported"  # 请求不属于 T02 支持的 semantic capability


class SemanticState(Enum):
    """单个语义类别的可区分语义状态（Gate A 冻结四种，字段名 Gate B 落地）。"""

    RESOLVED = "resolved"  # 语义已唯一确定（如 metric = GMV）
    AMBIGUOUS_CANDIDATES = "ambiguous_candidates"  # 存在多个合理候选（不静默选择）
    REQUIRED_UNRESOLVED = "required_unresolved"  # 当前请求需要，但尚未解析
    NOT_APPLICABLE = "not_applicable"  # 当前 query intent 根本不需要该类别


class SemanticCategory(Enum):
    """语义类别（Gate A 冻结，教学规模）。"""

    METRIC = "metric"
    DIMENSION = "dimension"
    ENTITY = "entity"
    TIME_RANGE = "time_range"
    FILTER = "filter"
    AGGREGATION_INTENT = "aggregation_intent"
    QUERY_INTENT = "query_intent"


@dataclass(frozen=True)
class SemanticValue:
    """一个语义类别的 interpretation 值（四种语义状态之一）。

    构造契约（classmethod 是推荐路径，直接构造由 `__post_init__` 兜底）：
    - `SemanticValue.make_resolved(value)`：唯一确定语义
    - `SemanticValue.make_ambiguous(*candidates)`：≥2 个合理候选，无单一 resolved 值
    - `SemanticValue.make_required_unresolved()`：当前请求需要但未解析
    - `SemanticValue.make_not_applicable()`：当前请求不需要

    自然防止：AMBIGUOUS_CANDIDATES 永远没有可被静默选择的 resolved 值。
    """

    state: SemanticState
    resolved: str | None = None
    candidates: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def make_resolved(cls, value: str) -> SemanticValue:
        return cls(state=SemanticState.RESOLVED, resolved=value, candidates=())

    @classmethod
    def make_ambiguous(cls, *candidates: str) -> SemanticValue:
        return cls(
            state=SemanticState.AMBIGUOUS_CANDIDATES,
            resolved=None,
            candidates=tuple(candidates),
        )

    @classmethod
    def make_required_unresolved(cls) -> SemanticValue:
        return cls(state=SemanticState.REQUIRED_UNRESOLVED, resolved=None, candidates=())

    @classmethod
    def make_not_applicable(cls) -> SemanticValue:
        return cls(state=SemanticState.NOT_APPLICABLE, resolved=None, candidates=())

    def __post_init__(self) -> None:
        if self.state is SemanticState.RESOLVED:
            if not self.resolved or self.resolved != self.resolved.strip():
                raise ValueError(
                    "resolved semantic value must be non-empty trimmed text: "
                    f"{self.resolved!r}"
                )
            if self.candidates:
                raise ValueError("resolved semantic value must not carry candidates")
        elif self.state is SemanticState.AMBIGUOUS_CANDIDATES:
            if len(self.candidates) < 2:
                raise ValueError(
                    "ambiguous semantic value requires at least two candidates"
                )
            if any(not c or c != c.strip() for c in self.candidates):
                raise ValueError(
                    "ambiguous semantic candidates must be non-empty trimmed text"
                )
            if len(set(self.candidates)) != len(self.candidates):
                raise ValueError("ambiguous semantic candidates must be distinct")
            if self.resolved is not None:
                raise ValueError(
                    "ambiguous semantic value must not carry a single resolved value"
                )
        else:  # REQUIRED_UNRESOLVED / NOT_APPLICABLE
            if self.resolved is not None or self.candidates:
                raise ValueError(
                    f"{self.state.value} semantic value must not carry values"
                )


class RetrievalPurpose(Enum):
    """source-agnostic retrieval requirement 的目的（逻辑契约层，非 source vocabulary）。"""

    VERIFY_DEFINITION = "verify_definition"  # 已解析语义需要权威定义/映射验证
    RESOLVE_AMBIGUITY = "resolve_ambiguity"  # 候选集需要权威源确认哪些是正式事实
    COMPLETE_INTERPRETATION = "complete_interpretation"  # 补齐 unresolved required 语义所需权威事实


@dataclass(frozen=True)
class RetrievalRequirement:
    """source-agnostic retrieval requirement（逻辑契约层）。

    - `category`：哪个语义类别需要权威事实
    - `semantic_ref`：语义引用（resolved 值 / 候选集 / 类别标签）——
      **不是 source lookup key**（fake source key vocabulary 不得进入本层）
    - `purpose`：为什么需要（verify / resolve ambiguity / complete interpretation）

    固定原则："Semantic interpretation ≠ retrieval requirement ≠
    source-specific retrieval criteria."——本对象只表达逻辑需求，
    source-specific 映射由 integration / source-specific adapter 完成。
    """

    category: SemanticCategory
    semantic_ref: str
    purpose: RetrievalPurpose


@dataclass(frozen=True)
class IntentResult:
    """T02 输出：结构化语义解释与意图（T02-owned derived state，单 State channel）。

    固定原则："Semantic interpretation is structured inference, not
    authoritative fact."——本对象是推断结果，不因结构化而获得事实地位；
    不得称为 fact（除否定 / 对比上下文）。

    字段：七个语义类别 + unsupported_reason（仅 UNSUPPORTED 使用）。

    **派生属性（Gate B 设计，自然防止非法组合）**：
    - `outcome`：由类别语义状态推导，不可独立写入——
      UNSUPPORTED（unsupported_reason 非空）> AMBIGUOUS（任一类别存在候选歧义）
      > PARTIAL（任一类别 required-unresolved）> COMPLETE
    - `retrieval_requirements`：source-agnostic retrieval requirements——
      UNSUPPORTED 恒为空；RESOLVED（metric/dimension/entity/filter）→
      VERIFY_DEFINITION；AMBIGUOUS_CANDIDATES → RESOLVE_AMBIGUITY；
      REQUIRED_UNRESOLVED → COMPLETE_INTERPRETATION；NOT_APPLICABLE → 无
    - time / aggregation / query intent 的 resolved 解释视为 interpretation-
      complete：time 的日历 / 时区 / 新鲜度裁决属外部事实，T02 不得静默猜测
      （Gate A 十一节：留 T02→T03 integration 边界）
    """

    metric: SemanticValue
    dimension: SemanticValue
    entity: SemanticValue
    time_range: SemanticValue
    filters: SemanticValue
    aggregation_intent: SemanticValue
    query_intent: SemanticValue
    unsupported_reason: str | None = None

    @classmethod
    def unsupported(cls, reason: str) -> IntentResult:
        """构造 UNSUPPORTED 结果：不携带任何类别语义（唯一合法路径）。"""
        if not reason or reason != reason.strip():
            raise ValueError("unsupported reason must be non-empty trimmed text")
        not_applicable = SemanticValue.make_not_applicable()
        return cls(
            metric=not_applicable,
            dimension=not_applicable,
            entity=not_applicable,
            time_range=not_applicable,
            filters=not_applicable,
            aggregation_intent=not_applicable,
            query_intent=not_applicable,
            unsupported_reason=reason,
        )

    def __post_init__(self) -> None:
        if self.unsupported_reason is not None:
            for _category, value in self._category_values():
                if value.state is not SemanticState.NOT_APPLICABLE:
                    raise ValueError(
                        "unsupported IntentResult must not carry category semantics "
                        f"(category {_category.value} is {value.state.value})"
                    )

    def _category_values(self) -> tuple[tuple[SemanticCategory, SemanticValue], ...]:
        return (
            (SemanticCategory.METRIC, self.metric),
            (SemanticCategory.DIMENSION, self.dimension),
            (SemanticCategory.ENTITY, self.entity),
            (SemanticCategory.TIME_RANGE, self.time_range),
            (SemanticCategory.FILTER, self.filters),
            (SemanticCategory.AGGREGATION_INTENT, self.aggregation_intent),
            (SemanticCategory.QUERY_INTENT, self.query_intent),
        )

    @property
    def outcome(self) -> IntentOutcome:
        """派生 outcome（不可独立写入）——自然防止 outcome 与语义状态矛盾。

        优先级（唯一推导规则，非实现层补丁）：
        UNSUPPORTED > AMBIGUOUS > PARTIAL > COMPLETE。
        - 任一类别 AMBIGUOUS_CANDIDATES（含可选类别）→ AMBIGUOUS：
          请求存在多个合理解读时，T02 必须显式暴露歧义，不得静默选择
        - 任一类别 REQUIRED_UNRESOLVED → PARTIAL：
          至少一个 required semantic requirement 未解析
        - 否则 COMPLETE（可选类别 NOT_APPLICABLE 不影响 COMPLETE）
        """
        if self.unsupported_reason is not None:
            return IntentOutcome.UNSUPPORTED
        if any(
            value.state is SemanticState.AMBIGUOUS_CANDIDATES
            for _category, value in self._category_values()
        ):
            return IntentOutcome.AMBIGUOUS
        if any(
            value.state is SemanticState.REQUIRED_UNRESOLVED
            for _category, value in self._category_values()
        ):
            return IntentOutcome.PARTIAL
        return IntentOutcome.COMPLETE

    @property
    def retrieval_requirements(self) -> tuple[RetrievalRequirement, ...]:
        """source-agnostic retrieval requirements（派生，逻辑契约层）。

        - UNSUPPORTED → 恒为空（不得自动生成普通 downstream retrieval
          requirements；Gate A 八节 eligibility 冻结）
        - RESOLVED（metric/dimension/entity/filter）→ VERIFY_DEFINITION
          （time/aggregation/query intent 的 resolved 解释视为完整 interpretation，
          日历等外部事实裁决留 integration 边界）
        - AMBIGUOUS_CANDIDATES → RESOLVE_AMBIGUITY（candidate-scoped：
          "需要验证哪些候选是正式企业指标"）
        - REQUIRED_UNRESOLVED → COMPLETE_INTERPRETATION（补齐 unresolved
          required semantics 所需权威事实；不假装 interpretation 已 complete）
        - NOT_APPLICABLE → 无

        固定原则："Retrieval requirement is data, not routing."——本属性只是
        数据契约，不授权 T02 调用 / 路由 T03。
        """
        if self.unsupported_reason is not None:
            return ()
        requirements: list[RetrievalRequirement] = []
        for category, value in self._category_values():
            if value.state is SemanticState.RESOLVED:
                if (
                    category.value in _FACT_GROUNDED_CATEGORIES
                    and value.resolved is not None
                ):
                    requirements.append(
                        RetrievalRequirement(
                            category=category,
                            semantic_ref=value.resolved,
                            purpose=RetrievalPurpose.VERIFY_DEFINITION,
                        )
                    )
            elif value.state is SemanticState.AMBIGUOUS_CANDIDATES:
                requirements.append(
                    RetrievalRequirement(
                        category=category,
                        semantic_ref=", ".join(value.candidates),
                        purpose=RetrievalPurpose.RESOLVE_AMBIGUITY,
                    )
                )
            elif value.state is SemanticState.REQUIRED_UNRESOLVED:
                requirements.append(
                    RetrievalRequirement(
                        category=category,
                        semantic_ref=category.value,
                        purpose=RetrievalPurpose.COMPLETE_INTERPRETATION,
                    )
                )
        return tuple(requirements)
