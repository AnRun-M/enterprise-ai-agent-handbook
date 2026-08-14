"""T02 deterministic fake semantic parser（Gate B 第一版：不接真实 LLM）。

Gate A 冻结（TASK-0034）：
- T02 将 T01 产生的 normalized_question 解释为结构化语义解释与意图
  （IntentResult）；"Semantic interpretation is structured inference,
  not authoritative fact."——解析产物不是事实
- T01/T02 边界："Normalization changes representation; semantic parsing
  interprets meaning."——本 parser 假定输入已是 normalized 形式，
  不做 whitespace canonicalization / empty detection 之外的清理
- 确定性优先（十五节）：typed output contract + bounded outcome taxonomy
  （四态封顶）；Gate B 第一版使用 deterministic fake parser 验证 Contract，
  不接真实 LLM

**教学规模 grammar（bounded，确定性规则，顺序敏感）**：
1. unsupported verb 检测最先（删除/修改/更新/写入/导出 → UNSUPPORTED）
2. query intent：查询类动词 → resolved；无动词 → required-unresolved
3. metric："销售额" → ambiguous candidates（Gate A 七节 canonical 例：
   GMV / paid amount / net revenue）；GMV / 订单数 → resolved；
   未识别 → required-unresolved
4. time range：昨天/今日/上个月/最近7天 → semantic token（不解析到具体
   日历——时区/业务日历属外部事实，T02 不得静默猜测）；
   上周/本周/下个月/去年/今年 等引用（无法映射 token）→ required-unresolved
   （Gate A 八节 canonical PARTIAL 例：metric 已定、time expression 未解析）
5. entity（region）：华东 / 华南 → resolved
6. filters：已支付 / 未支付（status filter）、VIP 用户（user segment）→ resolved
7. dimension："按区域 / 按日期 / 按时间" → resolved
8. aggregation intent：总计/合计/总共 → total；平均 → average；最大/最高 → max

单类别单语义（teaching scope）：同一类别出现多个关键词时取最长匹配，
不表达"一个类别多个值"；确定性不依赖输入顺序（同一输入恒等结果）。
"""

from __future__ import annotations

from typing import ClassVar

from .semantic_types import IntentResult, SemanticValue


class FakeSemanticParser:
    """deterministic rule-based fake semantic parser（无状态，无 LLM）。"""

    _QUERY_VERBS: ClassVar[tuple[str, ...]] = ("查询", "统计", "看看", "计算", "汇总", "分析")
    _UNSUPPORTED_VERBS: ClassVar[tuple[str, ...]] = ("删除", "删掉", "修改", "更新", "写入", "导出")

    _METRIC_AMBIGUOUS: ClassVar[dict[str, tuple[str, ...]]] = {
        "销售额": ("GMV", "paid_amount", "net_revenue"),
    }
    _METRIC_RESOLVED: ClassVar[dict[str, str]] = {
        "GMV": "GMV",
        "gmv": "GMV",
        "订单数": "订单数",
    }
    _REGION_ENTITY: ClassVar[dict[str, str]] = {
        "华东": "华东",
        "华南": "华南",
    }
    _TIME_TOKENS: ClassVar[dict[str, str]] = {
        "昨天": "yesterday",
        "今日": "today",
        "上个月": "last_month",
        "最近7天": "last_7_days",
        "近7天": "last_7_days",
    }
    _TIME_REFERENCE_MARKERS: ClassVar[tuple[str, ...]] = ("上周", "本周", "下个月", "去年", "今年")
    _FILTER_TOKENS: ClassVar[dict[str, str]] = {
        "已支付": "已支付",
        "未支付": "未支付",
        "VIP用户": "VIP用户",
        "VIP": "VIP",
    }
    _DIMENSION_PATTERNS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("按区域", "区域"),
        ("按日期", "日期"),
        ("按时间", "日期"),
    )
    _AGGREGATION_TOKENS: ClassVar[dict[str, str]] = {
        "总计": "total",
        "合计": "total",
        "总共": "total",
        "平均": "average",
        "最大": "max",
        "最高": "max",
    }

    @staticmethod
    def _match_first(text: str, keywords: tuple[str, ...]) -> str | None:
        """返回 text 中第一个出现的关键词（最长优先，确定性）。"""
        for keyword in sorted(keywords, key=len, reverse=True):
            if keyword in text:
                return keyword
        return None

    def parse(self, normalized_question: str) -> IntentResult:
        """把 normalized_question 解析为完整 IntentResult（纯函数，无副作用）。

        consumed-contract violation：空 / whitespace-only 输入 → ValueError
        （normalized_question=None 由 Node adapter 保证契约，本 parser 只收 str；
        空 str 属于契约外输入，不进入 outcome taxonomy）。
        """
        if not isinstance(normalized_question, str) or not normalized_question.strip():
            raise ValueError(
                "normalized_question must be non-empty text "
                "(consumed-contract violation)"
            )

        unsupported = self._match_first(normalized_question, self._UNSUPPORTED_VERBS)
        if unsupported is not None:
            return IntentResult.unsupported(
                reason=f"unsupported request intent: {unsupported}"
            )

        return IntentResult(
            metric=self._parse_metric(normalized_question),
            dimension=self._parse_dimension(normalized_question),
            entity=self._parse_entity(normalized_question),
            time_range=self._parse_time_range(normalized_question),
            filters=self._parse_filters(normalized_question),
            aggregation_intent=self._parse_aggregation(normalized_question),
            query_intent=self._parse_query_intent(normalized_question),
        )

    def _parse_query_intent(self, text: str) -> SemanticValue:
        verb = self._match_first(text, self._QUERY_VERBS)
        if verb is not None:
            return SemanticValue.make_resolved("query")
        return SemanticValue.make_required_unresolved()

    def _parse_metric(self, text: str) -> SemanticValue:
        # 歧义表优先（"销售额" 是 canonical ambiguity 例）
        for keyword in sorted(self._METRIC_AMBIGUOUS, key=len, reverse=True):
            if keyword in text:
                return SemanticValue.make_ambiguous(*self._METRIC_AMBIGUOUS[keyword])
        for keyword in sorted(self._METRIC_RESOLVED, key=len, reverse=True):
            if keyword in text:
                return SemanticValue.make_resolved(self._METRIC_RESOLVED[keyword])
        return SemanticValue.make_required_unresolved()

    def _parse_time_range(self, text: str) -> SemanticValue:
        keyword = self._match_first(text, tuple(self._TIME_TOKENS))
        if keyword is not None:
            return SemanticValue.make_resolved(self._TIME_TOKENS[keyword])
        # 识别到时间引用但无法映射 semantic token → required-unresolved
        marker = self._match_first(text, self._TIME_REFERENCE_MARKERS)
        if marker is not None:
            return SemanticValue.make_required_unresolved()
        return SemanticValue.make_not_applicable()

    def _parse_entity(self, text: str) -> SemanticValue:
        keyword = self._match_first(text, tuple(self._REGION_ENTITY))
        if keyword is not None:
            return SemanticValue.make_resolved(self._REGION_ENTITY[keyword])
        return SemanticValue.make_not_applicable()

    def _parse_filters(self, text: str) -> SemanticValue:
        keyword = self._match_first(text, tuple(self._FILTER_TOKENS))
        if keyword is not None:
            return SemanticValue.make_resolved(self._FILTER_TOKENS[keyword])
        return SemanticValue.make_not_applicable()

    def _parse_dimension(self, text: str) -> SemanticValue:
        for pattern, ref in sorted(
            self._DIMENSION_PATTERNS, key=lambda item: len(item[0]), reverse=True
        ):
            if pattern in text:
                return SemanticValue.make_resolved(ref)
        return SemanticValue.make_not_applicable()

    def _parse_aggregation(self, text: str) -> SemanticValue:
        keyword = self._match_first(text, tuple(self._AGGREGATION_TOKENS))
        if keyword is not None:
            return SemanticValue.make_resolved(self._AGGREGATION_TOKENS[keyword])
        return SemanticValue.make_not_applicable()
