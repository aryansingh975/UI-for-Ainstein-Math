from app.engine.normalizer import normalize_text, strip_connecting_words
from app.engine.vocabulary import has_irrelevant_words, RELEVANT_WORDS, MATH_INTENT


def test_normalize_currency_and_commas():
    assert normalize_text("₹21,000 - ₹1050 = ₹19,950") == "21000 - 1050=19950"
    assert normalize_text("Rs 1,050") == "1050"
    assert normalize_text("Rs. 19,950 rupees") == "19950"
    assert normalize_text("$500") == "500"


def test_normalize_math_operators():
    # Multiplication & division symbols
    assert normalize_text("21000 × 5/100") == "21000*5/100"
    assert normalize_text("21000 * 5 ÷ 100") == "21000*5/100"
    assert normalize_text("3 : 4") == "3:4"
    assert normalize_text("72 / 96") == "72/96"
    assert normalize_text("x = 6") == "*=6"
    assert normalize_text("(x - 2)(x - 3) = 0") == "(*- 2)(*- 3)=0"


def test_strip_connecting_words():
    assert strip_connecting_words("i love paris 3:4") == "3:4"
    assert strip_connecting_words("therefore the ratio is 3:4") == "ratio 3:4"


def test_has_irrelevant_words():
    # On-topic math and domain words should not be flagged as irrelevant
    assert not has_irrelevant_words(normalize_text("depreciation = 21000 * 5 / 100"))
    assert not has_irrelevant_words(normalize_text("daughter age is 6 years"))
    assert not has_irrelevant_words(normalize_text("simplify the fraction"))
    assert not has_irrelevant_words(normalize_text("cross multiply"))

    # Pure garbage or unrelated words should be flagged
    assert has_irrelevant_words(normalize_text("i love paris"))
    assert has_irrelevant_words(normalize_text("hello world"))
    assert has_irrelevant_words(normalize_text("random pizza order 3:4"))


def test_math_intent_presence():
    assert "cross" in MATH_INTENT
    assert "simplify" in MATH_INTENT
    assert "factorization" in MATH_INTENT
    assert "depreciation" in RELEVANT_WORDS
    assert "daughter" in RELEVANT_WORDS

