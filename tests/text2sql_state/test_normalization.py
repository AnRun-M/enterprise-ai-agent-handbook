"""T01 纯函数测试：lexical normalization、idempotency、over-normalization 边界。"""

from __future__ import annotations

import pytest

from examples.text2sql_state.normalization import normalize_question

# ---------------------------------------------------------------- 基本行为

def test_normal_question_semantically_unchanged() -> None:
    assert normalize_question("查询昨天的 GMV") == "查询昨天的 GMV"


def test_leading_and_trailing_whitespace() -> None:
    assert normalize_question("  查询昨天的 GMV  ") == "查询昨天的 GMV"


def test_repeated_spaces_canonicalized() -> None:
    assert normalize_question("查询  昨天  的  GMV") == "查询 昨天 的 GMV"


def test_tabs_and_newlines_canonicalized() -> None:
    assert normalize_question("查询\t昨天的\nGMV") == "查询 昨天的 GMV"


# ---------------------------------------------------------------- 失败语义

@pytest.mark.parametrize("question", ["", "   ", "\t\n ", "  \t  "])
def test_empty_or_whitespace_only_returns_none(question: str) -> None:
    # None = explicit invalid result（非空串混用；调用方走 lifecycle failure）
    assert normalize_question(question) is None


# ---------------------------------------------------------------- idempotency / determinism

@pytest.mark.parametrize(
    "question",
    [
        "查询昨天的 GMV",
        "  查询  昨天  的  GMV  ",
        "查询\t昨天的\nGMV",
        "上个月华东区销售额是多少",
        "SELECT * FROM orders",
        "   ",
    ],
)
def test_idempotency(question: str) -> None:
    once = normalize_question(question)
    twice = normalize_question(once) if once is not None else normalize_question(question)
    assert once == twice


@pytest.mark.parametrize(
    "question",
    ["查询昨天的 GMV", "  SELECT *  FROM  orders ", "上个月 华东 GMV"],
)
def test_deterministic_repeated_execution(question: str) -> None:
    assert normalize_question(question) == normalize_question(question)


# ---------------------------------------------------------------- over-normalization 边界

def test_unicode_and_chinese_preserved() -> None:
    assert normalize_question("查询「华东区」的 GMV") == "查询「华东区」的 GMV"


def test_punctuation_preserved() -> None:
    assert normalize_question("昨天 GMV 是多少？") == "昨天 GMV 是多少？"


def test_no_lowercase_of_full_text() -> None:
    # 禁止 lowercase 全文本（可能改变业务含义）
    assert normalize_question("查询 GMV 和 Orders") == "查询 GMV 和 Orders"


def test_no_sql_normalization_on_natural_language() -> None:
    # SQL-like 文本在自然语言问题中不做 SQL normalization（无语法/关键字改写）
    assert normalize_question("如何写 SELECT * FROM orders") == "如何写 SELECT * FROM orders"


def test_semantic_words_not_rewritten() -> None:
    # 禁止同义词替换 / 指标名映射 / 语义简化
    assert normalize_question("上个月华东 GMV") == "上个月华东 GMV"


def test_no_stopword_removal() -> None:
    assert normalize_question("请查询昨天的 GMV") == "请查询昨天的 GMV"


def test_no_whitespace_preserving_promise_for_structured_text() -> None:
    # 教学 contract 不承诺 exact code blocks / whitespace-sensitive 文本的
    # whitespace-preserving 语义——连续 whitespace 一律折叠为单空格
    # （非 SQL rewrite，关键字与内容不改写，仅空白折叠；无 quoted-string parser）
    assert normalize_question("SELECT  a,\n    b\nFROM  t") == "SELECT a, b FROM t"
