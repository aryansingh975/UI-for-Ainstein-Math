import pytest
from app.engine.evaluator import eval_arithmetic
from app.engine.normalizer import normalize_text
from app.engine.claims import extract_claims


def test_eval_arithmetic_basic_and_powers():
    assert eval_arithmetic("3*96") == pytest.approx(288.0)
    assert eval_arithmetic("72/24") == pytest.approx(3.0)
    assert eval_arithmetic("gcd(72,96)") == pytest.approx(24.0)
    assert eval_arithmetic("hcf(72,96)") == pytest.approx(24.0)
    assert eval_arithmetic("2^3*3^2") == pytest.approx(72.0)
    assert eval_arithmetic("2^5*3") == pytest.approx(96.0)
    assert eval_arithmetic("3+4") == pytest.approx(7.0)
    assert eval_arithmetic("(3+4)*2") == pytest.approx(14.0)
    assert eval_arithmetic("3/4") == pytest.approx(0.75)
    assert eval_arithmetic("72/96") == pytest.approx(0.75)


def test_eval_arithmetic_invalid_and_div_zero():
    assert eval_arithmetic("hello world") is None
    assert eval_arithmetic("5/0") is None
    assert eval_arithmetic("") is None


def test_extract_claims_truth_checking():
    norm = normalize_text

    # False GCD claim
    c1 = extract_claims(norm("gcd(72,96) is 25"), context_pair=(72, 96))
    assert len(c1) == 1
    assert c1[0].is_true is False

    # Bare HCF with context
    c2 = extract_claims(norm("hcf is 24"), context_pair=(72, 96))
    assert len(c2) == 1
    assert c2[0].is_true is True

    # Natural language HCF
    c3 = extract_claims(norm("hcf of 72 and 96 is 24"))
    assert len(c3) == 1
    assert c3[0].is_true is True

    # Ratio equality
    c4 = extract_claims(norm("3:4=72:96"))
    assert len(c4) == 1
    assert c4[0].is_true is True

    c5 = extract_claims(norm("3:4=3:5"))
    assert len(c5) == 1
    assert c5[0].is_true is False

    # Arithmetic equality
    c6 = extract_claims(norm("3+4=7"))
    assert len(c6) == 1
    assert c6[0].is_true is True

    c7 = extract_claims(norm("3*96=287"))
    assert len(c7) == 1
    assert c7[0].is_true is False

    # Multiple statements separated by "and"
    c8 = extract_claims(norm("72/24=3 and 96/24=4"))
    assert len(c8) == 2
    assert all(c.is_true for c in c8)

    c9 = extract_claims(norm("72 = 24 × 3 and 96 = 24 × 4"))
    assert len(c9) == 2
    assert all(c.is_true for c in c9)

    # Word operators
    c10 = extract_claims(norm("3 times 96 is 288"))
    assert len(c10) == 1
    assert c10[0].is_true is True

    # Negated ratio
    c11 = extract_claims(norm("3:4 ≠ 72:96"))
    assert len(c11) == 1
    assert c11[0].is_true is False

    # TV Depreciation step
    c12 = extract_claims(norm("₹21,000 - ₹1050 = ₹19,950"))
    assert len(c12) == 1
    assert c12[0].is_true is True
    assert c12[0].lhs_val == pytest.approx(19950.0)
    assert c12[0].rhs_val == pytest.approx(19950.0)
