"""Port of calc/macros.rs (calc-only subset) + shared constants.

Covers num!/pct!/plural + YEAR_MIN/MAX + POUND2TON + year_adj.
Report helpers (addto!/addif!) and Display prose are out of scope.
"""
from __future__ import annotations

import math

YEAR_MIN: int = 1850
YEAR_MAX: int = 1950

# Pounds in a long ton (Ship::POUND2TON in ship.rs).
POUND2TON: float = 2240.0


def num(val: float, digits: int = 0) -> str:
    """Format with commas and `digits` decimals; strip all-zero fraction."""
    s = f"{float(val):,.{int(digits)}f}"
    if "." in s:
        head, tail = s.split(".", 1)
        if tail and all(c == "0" for c in tail):
            return head
    return s


def pct(val: float, digits: int = 0) -> str:
    """Treat number as fraction, format as percent value (no '%' sign)."""
    return num(float(val) * 100.0, digits)


def plural(n: int) -> str:
    return "" if n == 1 else "s"


def year_adj(year: int) -> float:
    """Year adjustment factor (Ship::year_adj in ship.rs)."""
    if YEAR_MIN <= year <= 1890:
        return 1.0 - (1890 - year) / 66.666664
    if year <= YEAR_MAX:
        return 1.0
    return 0.0


def to_place(n: float, digits: int) -> float:
    """Round to `digits` places (test helper from mod.rs test_support)."""
    mult = 10.0**digits
    return math.floor(n * mult + 0.5) / mult if n >= 0 else math.ceil(n * mult - 0.5) / mult


def rpow(base: float, exp: float) -> float:
    """Rust f64::powf semantics: negative base + fractional exp => NaN.

    Python's `**` would return a complex instead (and `math.pow` raises),
    so guard explicitly. Integer-valued exponents on negative bases are fine.
    """
    if base < 0.0 and float(exp) != float(int(float(exp))):
        return float("nan")
    try:
        return base**exp
    except (ValueError, ZeroDivisionError, OverflowError):
        return float("nan")


def rsqrt(x: float) -> float:
    """Rust f64::sqrt semantics: sqrt of negative => NaN (no exception)."""
    if x != x:  # NaN stays NaN
        return float("nan")
    if x < 0.0:
        return float("nan")
    return math.sqrt(x)


def rhalf(n: int) -> int:
    """Rust-style `round(n / 2)`: half away from zero (Python round() is banker's)."""
    return int(math.floor(n / 2.0 + 0.5))


def rmin(a: float, b: float) -> float:
    """Rust f64::min semantics: if either arg is NaN, return the other."""
    if a != a:
        return b
    if b != b:
        return a
    return a if a <= b else b


def rmax(a: float, b: float) -> float:
    """Rust f64::max semantics: if either arg is NaN, return the other."""
    if a != a:
        return b
    if b != b:
        return a
    return a if a >= b else b
