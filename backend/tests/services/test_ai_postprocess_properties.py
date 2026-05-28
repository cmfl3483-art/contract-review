"""
AIService._postprocess 与 _compute_compliance_score 的 Hypothesis 属性测试

**Validates: Requirements 4.3, 4.4, 4.6, 4.7, 4.8, 4.13**

Property 3: violations 中 rule_id 必属于本次规则集合
Property 4: violations.location 与规则 rule_type 一致
Property 5: violations.severity 与规则 severity 一致
Property 6: suggested_name 强约束 (1..200)
Property 7: suggested_description 弱约束 (0..2000)
Property 8: 字段初稿空时不输出对应 location 违规
Property 11: compliance_score 算术属性
"""

from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import composite

from app.services.ai_service import AIService, _compute_compliance_score


# ─────────────────────────────────────────────────────────────────────────────
# 策略定义
# ─────────────────────────────────────────────────────────────────────────────


@composite
def rule_set_strategy(draw):
    """生成 1-20 条随机规则的列表（dict 格式，模拟 LLM 输入）"""
    n = draw(st.integers(min_value=1, max_value=20))
    return [
        {
            "id": str(uuid4()),
            "rule_type": draw(st.sampled_from(["number", "name", "description", "file"])),
            "severity": draw(st.sampled_from(["must", "should"])),
            "title": draw(st.text(min_size=1, max_size=100)),
            "requirement": draw(st.text(min_size=1, max_size=200)),
        }
        for _ in range(n)
    ]


def llm_violations_strategy(rules):
    """
    生成随机 LLM violations 列表，包含合法和非法的 rule_id/location/severity。
    rule_id 混合：50% 来自真实规则，50% 随机字符串（模拟 LLM 幻觉）。
    """
    real_ids = [r["id"] for r in rules]
    rule_id_st = st.one_of(
        st.sampled_from(real_ids) if real_ids else st.text(max_size=50),
        st.text(max_size=50),
    )
    return st.lists(
        st.fixed_dictionaries({
            "rule_id": rule_id_st,
            "location": st.sampled_from(["number", "name", "description", "file", "invalid"]),
            "excerpt": st.text(max_size=600),
            "description": st.text(max_size=600),
            "suggestion": st.text(max_size=600),
            "severity": st.sampled_from(["must", "should", "critical"]),
        }),
        max_size=30,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Property 3+4+5+6+7+8 综合测试
# ─────────────────────────────────────────────────────────────────────────────


@settings(max_examples=200)
@given(
    rules=rule_set_strategy(),
    drafts=st.fixed_dictionaries({
        "number_draft": st.one_of(st.none(), st.text(max_size=100)),
        "name_draft": st.one_of(st.none(), st.text(max_size=200)),
        "description_draft": st.one_of(st.none(), st.text(max_size=2000)),
    }),
)
def test_postprocess_invariants(rules, drafts):
    """
    **Validates: Requirements 4.3, 4.4, 4.6, 4.7, 4.8**

    P3: ∀ v ∈ out["violations"]: v["rule_id"] ∈ rule_map
    P4: ∀ v ∈ out["violations"]: v["location"] == rule_map[v["rule_id"]]["rule_type"]
    P5: ∀ v ∈ out["violations"]: v["severity"] == rule_map[v["rule_id"]]["severity"]
    P6: 1 <= len(out["suggested_name"]) <= 200
    P7: 0 <= len(out["suggested_description"]) <= 2000
    P8: 若 drafts[f"{loc}_draft"] 为空，则 ∀ v ∈ out["violations"]: v["location"] != loc
    """
    # 构造 rule_map 用于断言
    rule_map = {r["id"]: r for r in rules}

    # 构造随机 LLM violations（包含合法和非法 rule_id/location/severity）
    from hypothesis import find
    import random

    # 直接构造一批混合 violations（合法 + 非法）
    violations_input = []
    for r in rules:
        # 合法 violation（rule_id 和 location 都正确）
        violations_input.append({
            "rule_id": r["id"],
            "location": r["rule_type"],
            "excerpt": "excerpt text",
            "description": "desc",
            "suggestion": "suggestion",
            "severity": r["severity"],
        })
        # 非法 violation（location 与 rule_type 不一致）
        wrong_locations = [loc for loc in ["number", "name", "description", "file"] if loc != r["rule_type"]]
        if wrong_locations:
            violations_input.append({
                "rule_id": r["id"],
                "location": wrong_locations[0],
                "excerpt": "wrong location",
                "description": "desc",
                "suggestion": "suggestion",
                "severity": r["severity"],
            })
    # 非法 rule_id
    violations_input.append({
        "rule_id": "nonexistent-rule-id-xyz",
        "location": "file",
        "excerpt": "",
        "description": "fake",
        "suggestion": "",
        "severity": "must",
    })

    parsed = {
        "violations": violations_input,
        "suggested_name": "x",
        "suggested_description": "",
    }

    service = AIService.__new__(AIService)  # 不调用 __init__（避免连接 AI 服务）
    out = service._postprocess(parsed, rules, drafts, extracted_text="some extracted text")

    # P3: 所有输出 violation 的 rule_id 必须在规则集合中
    for v in out["violations"]:
        assert v["rule_id"] in rule_map, (
            f"P3 violated: rule_id={v['rule_id']!r} not in rule_map"
        )

    # P4: location 与规则 rule_type 一致
    for v in out["violations"]:
        expected_type = rule_map[v["rule_id"]]["rule_type"]
        assert v["location"] == expected_type, (
            f"P4 violated: location={v['location']!r} != rule_type={expected_type!r}"
        )

    # P5: severity 与规则 severity 一致（强制覆写）
    for v in out["violations"]:
        expected_severity = rule_map[v["rule_id"]]["severity"]
        assert v["severity"] == expected_severity, (
            f"P5 violated: severity={v['severity']!r} != rule severity={expected_severity!r}"
        )

    # P6: suggested_name 长度约束 1..200
    name = out["suggested_name"]
    assert isinstance(name, str), "P6 violated: suggested_name must be str"
    assert 1 <= len(name) <= 200, (
        f"P6 violated: len(suggested_name)={len(name)} not in [1, 200]"
    )

    # P7: suggested_description 长度约束 0..2000
    desc = out["suggested_description"]
    assert isinstance(desc, str), "P7 violated: suggested_description must be str"
    assert 0 <= len(desc) <= 2000, (
        f"P7 violated: len(suggested_description)={len(desc)} not in [0, 2000]"
    )

    # P8: 字段初稿为空时，不输出对应 location 的 violation
    for loc in ("number", "name", "description"):
        draft_val = drafts.get(f"{loc}_draft")
        draft_is_empty = not draft_val or not str(draft_val).strip()
        if draft_is_empty:
            for v in out["violations"]:
                assert v["location"] != loc, (
                    f"P8 violated: location={loc!r} violation present but draft is empty"
                )


# ─────────────────────────────────────────────────────────────────────────────
# Property 11: compliance_score 算术属性
# ─────────────────────────────────────────────────────────────────────────────


@settings(max_examples=300)
@given(
    must_count=st.integers(min_value=0, max_value=50),
    should_count=st.integers(min_value=0, max_value=50),
)
def test_compliance_score_properties(must_count, should_count):
    """
    **Validates: Requirements 4.13**

    P11: score == max(0, min(100, 100 - 10*must - 2*should))
         且 0 <= score <= 100
         且空 violations → score == 100
    """
    violations = (
        [{"severity": "must"}] * must_count
        + [{"severity": "should"}] * should_count
    )

    score = _compute_compliance_score(violations)

    # 范围约束
    assert 0 <= score <= 100, f"P11 violated: score={score} not in [0, 100]"

    # 算术公式
    expected = max(0, min(100, 100 - 10 * must_count - 2 * should_count))
    assert score == expected, (
        f"P11 violated: score={score} != expected={expected} "
        f"(must={must_count}, should={should_count})"
    )


def test_compliance_score_empty_violations():
    """
    **Validates: Requirements 4.13**

    空 violations → score == 100
    """
    assert _compute_compliance_score([]) == 100


def test_compliance_score_only_must():
    """must 违规每条扣 10 分，10 条以上 clamp 到 0"""
    assert _compute_compliance_score([{"severity": "must"}] * 5) == 50
    assert _compute_compliance_score([{"severity": "must"}] * 10) == 0
    assert _compute_compliance_score([{"severity": "must"}] * 20) == 0


def test_compliance_score_only_should():
    """should 违规每条扣 2 分，50 条以上 clamp 到 0"""
    assert _compute_compliance_score([{"severity": "should"}] * 10) == 80
    assert _compute_compliance_score([{"severity": "should"}] * 50) == 0
    assert _compute_compliance_score([{"severity": "should"}] * 100) == 0
