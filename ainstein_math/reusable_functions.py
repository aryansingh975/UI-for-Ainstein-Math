"""Reusable arithmetic functions for Ainstein Math solution paths."""

from math import gcd
from numbers import Integral


def hcf(*numbers: int) -> int:
    """Return the highest common factor of two or more integers."""
    if len(numbers) < 2:
        raise ValueError("hcf() requires at least two integers")
    if not all(isinstance(number, Integral) for number in numbers):
        raise TypeError("hcf() accepts integers only")

    result = 0
    for number in numbers:
        result = gcd(result, abs(int(number)))
    return result


__all__ = ["hcf"]
