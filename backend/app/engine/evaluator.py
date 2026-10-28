from __future__ import annotations

import math
import re
from typing import Any, List, Optional

EPS = 1e-9


def gcd_int(a: float, b: float) -> int:
    ia = abs(int(round(a)))
    ib = abs(int(round(b)))
    return math.gcd(ia, ib)


def apply_fn(name: str, args: List[float]) -> Optional[float]:
    if name in ("gcd", "hcf"):
        if len(args) < 2:
            return None
        res = int(args[0])
        for x in args[1:]:
            res = gcd_int(res, x)
        return float(res)

    if name == "lcm":
        if len(args) < 2:
            return None
        res = int(args[0])
        for x in args[1:]:
            g = gcd_int(res, x)
            if g == 0:
                return None
            res = abs(res * int(x)) // g
        return float(res)

    if name == "sqrt":
        return math.sqrt(args[0]) if len(args) == 1 and args[0] >= 0 else None

    if name == "abs":
        return abs(args[0]) if len(args) == 1 else None

    if name == "min":
        return min(args) if args else None

    if name == "max":
        return max(args) if args else None

    return None


class Token:
    def __init__(self, kind: str, value: Any = None):
        self.kind = kind
        self.value = value


def tokenize_math(src: str) -> Optional[List[Token]]:
    tokens: List[Token] = []
    s = str(src)
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or ch == ".":
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] == "."):
                j += 1
            try:
                v = float(s[i:j])
                tokens.append(Token("num", v))
                i = j
                continue
            except ValueError:
                return None

        if ch.isalpha():
            j = i
            while j < len(s) and s[j].isalpha():
                j += 1
            tokens.append(Token("id", s[i:j].lower()))
            i = j
            continue

        if ch in "+-*/^(),":
            tokens.append(Token(ch))
            i += 1
            continue

        # Unknown char -> not evaluable
        return None

    return tokens


def eval_arithmetic(src: str) -> Optional[float]:
    """Safely evaluates an arithmetic expression using recursive descent. Zero eval()."""
    tokens = tokenize_math(src)
    if not tokens:
        return None

    pos = 0

    def peek() -> Optional[Token]:
        return tokens[pos] if pos < len(tokens) else None

    def next_tk() -> Optional[Token]:
        nonlocal pos
        tk = peek()
        pos += 1
        return tk

    def parse_expr() -> Optional[float]:
        v = parse_term()
        if v is None:
            return None
        while peek() and peek().kind in ("+", "-"):
            op = next_tk().kind
            r = parse_term()
            if r is None:
                return None
            v = v + r if op == "+" else v - r
        return v

    def parse_term() -> Optional[float]:
        v = parse_factor()
        if v is None:
            return None
        while peek() and peek().kind in ("*", "/"):
            op = next_tk().kind
            r = parse_factor()
            if r is None:
                return None
            if op == "/":
                if abs(r) < EPS:
                    return None  # Division by zero
                v = v / r
            else:
                v = v * r
        return v

    def parse_factor() -> Optional[float]:
        if peek() and peek().kind == "-":
            next_tk()
            v = parse_factor()
            return -v if v is not None else None
        if peek() and peek().kind == "+":
            next_tk()
            return parse_factor()
        return parse_power()

    def parse_power() -> Optional[float]:
        base = parse_primary()
        if base is None:
            return None
        if peek() and peek().kind == "^":
            next_tk()
            e = parse_factor()
            if e is None:
                return None
            try:
                return math.pow(base, e)
            except Exception:
                return None
        return base

    def parse_primary() -> Optional[float]:
        tk = peek()
        if not tk:
            return None
        if tk.kind == "num":
            next_tk()
            return tk.value
        if tk.kind == "(":
            next_tk()
            v = parse_expr()
            if v is None or not peek() or peek().kind != ")":
                return None
            next_tk()
            return v
        if tk.kind == "id":
            fn_name = tk.value
            next_tk()
            if peek() and peek().kind == "(":
                next_tk()
                args = []
                if peek() and peek().kind != ")":
                    a = parse_expr()
                    if a is None:
                        return None
                    args.append(a)
                    while peek() and peek().kind == ",":
                        next_tk()
                        a = parse_expr()
                        if a is None:
                            return None
                        args.append(a)
                if not peek() or peek().kind != ")":
                    return None
                next_tk()
                return apply_fn(fn_name, args)
            return None
        return None

    v = parse_expr()
    if v is None or pos != len(tokens):
        return None
    return v

