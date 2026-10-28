from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from app.engine.evaluator import eval_arithmetic, EPS


class Claim:
    def __init__(
        self,
        kind: str,
        text: str,
        is_true: bool,
        op: str = "=",
        lhs: Optional[str] = None,
        rhs: Optional[str] = None,
        lhs_val: Optional[float] = None,
        rhs_val: Optional[float] = None,
        a: Optional[float] = None,
        b: Optional[float] = None,
        c: Optional[float] = None,
        d: Optional[float] = None,
    ):
        self.kind = kind
        self.text = text
        self.is_true = is_true
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.lhs_val = lhs_val
        self.rhs_val = rhs_val
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "kind": self.kind,
            "text": self.text,
            "isTrue": self.is_true,
            "op": self.op,
        }
        if self.kind == "arith":
            d.update({
                "lhs": self.lhs,
                "rhs": self.rhs,
                "lhsVal": self.lhs_val,
                "rhsVal": self.rhs_val,
            })
        elif self.kind == "ratio_eq":
            d.update({
                "a": self.a,
                "b": self.b,
                "c": self.c,
                "d": self.d,
            })
        return d


def preprocess_gcd_phrases(s: str) -> str:
    """Rewrite 'hcf of 72 and 96' -> 'gcd(72,96)'."""
    pattern = r"\b(?:highest common factor|greatest common divisor|hcf|gcd)\b(?:\s*of\s*)?(\d+(?:\.\d+)?)\s*(?:,|and)\s*(\d+(?:\.\d+)?)"
    return re.sub(pattern, r"gcd(\1,\2)", s)


def canonicalize_side(side: str, default_gcd_pair: Optional[tuple[float, float]] = None) -> Optional[str]:
    t = str(side).strip()
    if not t:
        return None
    if re.search(r"\b(hcf|gcd|highest common factor|greatest common divisor)\b", t):
        nums = re.findall(r"\d+(?:\.\d+)?", t)
        if len(nums) >= 2:
            return f"gcd({nums[0]},{nums[1]})"
        if default_gcd_pair:
            return f"gcd({default_gcd_pair[0]},{default_gcd_pair[1]})"
        return None
    if re.search(r"[a-z]", t):
        stripped = re.sub(r"\b(gcd|hcf|lcm|sqrt|abs|min|max)\b", "", t)
        if re.search(r"[a-z]", stripped):
            return None  # non-math words -> not evaluable
    return t


def extract_claims(normalized: str, context_pair: Optional[tuple[float, float]] = None) -> List[Claim]:
    """Extract arithmetic and ratio equality claims, checking their mathematical truth."""
    s = f" {normalized} "

    # Word operators -> symbols
    s = re.sub(r"\btimes\b", "*", s)
    s = re.sub(r"\bmultiplied by\b", "*", s)
    s = re.sub(r"\bdivided by\b", "/", s)
    s = re.sub(r"\bover\b", "/", s)
    s = re.sub(r"\bplus\b", "+", s)
    s = re.sub(r"\bminus\b", "-", s)

    # Preprocess gcd phrases BEFORE 'and' becomes a separator
    s = preprocess_gcd_phrases(s)

    # Comparators
    s = re.sub(r"\s*(?:≠|!=|<>)\s*", "≠", s)
    s = re.sub(r"\bis not\b", "≠", s)
    s = re.sub(r"\bdoes not equal\b", "≠", s)
    s = re.sub(r"\bisn't\b", "≠", s)
    s = re.sub(r"\bnot equal to\b", "≠", s)
    s = re.sub(r"\bare not\b", "≠", s)
    s = re.sub(r"\bis\b", "=", s)
    s = re.sub(r"\bequals\b", "=", s)
    s = re.sub(r"\bgives\b", "=", s)
    s = re.sub(r"\bmakes\b", "=", s)
    s = re.sub(r"\s*=\s*", "=", s)
    s = re.sub(r"\s*≠\s*", "≠", s)

    # 'and' separates two statements
    s = re.sub(r"\band\b", ";", s)
    s = s.strip()

    claims: List[Claim] = []

    # Ratio-equality claims: a:b = c:d (or ≠)
    ratio_eq_re = r"(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)(=|≠)(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)"
    cleaned = s
    for m in re.finditer(ratio_eq_re, s):
        a = float(m.group(1))
        b = float(m.group(2))
        op = m.group(3)
        c = float(m.group(4))
        d = float(m.group(5))
        equal = abs(a * d - b * c) < EPS
        is_true = equal if op == "=" else not equal
        claims.append(Claim(
            kind="ratio_eq",
            text=m.group(0),
            is_true=is_true,
            op=op,
            a=a, b=b, c=c, d=d
        ))
        cleaned = cleaned.replace(m.group(0), " ")

    # Arithmetic equality claims: split on = ≠ ; at top level
    parts = re.split(r"(=|≠|;)", cleaned)
    lhs: Optional[str] = None
    pending_op: Optional[str] = None

    for part in parts:
        p = part.strip()
        if p in ("=", "≠"):
            pending_op = p
            continue
        if p == ";":
            lhs = None
            pending_op = None
            continue
        if not p:
            continue
        if lhs is None:
            lhs = p
            continue

        if pending_op and re.search(r"[a-z\d]", lhs) and re.search(r"\d", p):
            cl = canonicalize_side(lhs, context_pair)
            cr = canonicalize_side(p, context_pair)
            lv = eval_arithmetic(cl) if cl is not None else None
            rv = eval_arithmetic(cr) if cr is not None else None

            if lv is not None and rv is not None:
                equal = abs(lv - rv) < EPS
                is_true = equal if pending_op == "=" else not equal
                claims.append(Claim(
                    kind="arith",
                    text=f"{lhs} {'=' if pending_op == '=' else '≠'} {p}",
                    is_true=is_true,
                    op=pending_op,
                    lhs=lhs,
                    rhs=p,
                    lhs_val=lv,
                    rhs_val=rv
                ))

        lhs = p
        pending_op = None

    return claims


def fmt_num(n: float | int | None) -> str:
    """Format numbers without trailing decimal zeros, matching JS fmt()."""
    if n is None:
        return ""
    if isinstance(n, int) or (isinstance(n, float) and n.is_integer()):
        return str(int(n))
    return f"{n:.4f}".rstrip("0").rstrip(".")


def explain_claim(c: Claim | dict | None) -> str:
    """Produce student-facing explanation of why an equality/claim holds or fails."""
    if not c:
        return ""
    if isinstance(c, dict):
        kind = c.get("kind")
        is_true = c.get("is_true")
        text = c.get("text", "")
        if kind == "arith":
            lhs = str(c.get("lhs", "")).strip()
            rhs = str(c.get("rhs", "")).strip()
            lv = fmt_num(c.get("lhs_val"))
            rv = fmt_num(c.get("rhs_val"))
            verdict_text = "holds." if is_true else "doesn't hold."
            return f"{lhs} is {lv} and {rhs} is {rv} - so \"{text}\" {verdict_text}"
        elif kind == "ratio_eq":
            a, b, c_val, d = c.get("a"), c.get("b"), c.get("c"), c.get("d")
            ad = fmt_num(a * d) if a is not None and d is not None else ""
            bc = fmt_num(b * c_val) if b is not None and c_val is not None else ""
            verdict_text = "holds." if is_true else "doesn't hold."
            return f"Cross products: {a}x{d} = {ad} and {b}x{c_val} = {bc} - so \"{text}\" {verdict_text}"
        elif kind == "value":
            verdict_text = "holds." if is_true else "doesn't hold."
            return f"\"{text}\" {verdict_text}"
    else:
        if c.kind == "arith":
            lhs = (c.lhs or "").strip()
            rhs = (c.rhs or "").strip()
            lv = fmt_num(c.lhs_val)
            rv = fmt_num(c.rhs_val)
            verdict_text = "holds." if c.is_true else "doesn't hold."
            return f"{lhs} is {lv} and {rhs} is {rv} - so \"{c.text}\" {verdict_text}"
        elif c.kind == "ratio_eq":
            ad = fmt_num(c.a * c.d) if c.a is not None and c.d is not None else ""
            bc = fmt_num(c.b * c.c) if c.b is not None and c.c is not None else ""
            verdict_text = "holds." if c.is_true else "doesn't hold."
            return f"Cross products: {c.a}x{c.d} = {ad} and {c.b}x{c.c} = {bc} - so \"{c.text}\" {verdict_text}"
        elif c.kind == "value":
            verdict_text = "holds." if c.is_true else "doesn't hold."
            return f"\"{c.text}\" {verdict_text}"
    return ""
