"""Unit and time/data size normalization library per PRD section 20.5."""
import re
from typing import Optional, Tuple, Dict, Any

TIME_UNITS = {
    "ms": 0.001, "millisecond": 0.001, "milliseconds": 0.001,
    "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
    "min": 60.0, "minute": 60.0, "minutes": 60.0,
    "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0,
    "day": 86400.0, "days": 86400.0
}

DATA_UNITS = {
    "b": 1, "byte": 1, "bytes": 1,
    "kb": 1000, "kbyte": 1000, "kbytes": 1000,
    "mb": 1000000, "mbyte": 1000000, "mbytes": 1000000,
    "gb": 1000000000, "gbyte": 1000000000, "gbytes": 1000000000
}

def normalize_unit_value(val: float, unit: str) -> Tuple[Optional[float], str]:
    """Normalizes time to seconds, data to bytes, percent to percent."""
    u = unit.lower().strip()
    if u in TIME_UNITS:
        return val * TIME_UNITS[u], "seconds"
    if u in DATA_UNITS:
        return val * DATA_UNITS[u], "bytes"
    if u in ["%", "percent", "percentage"]:
        return val, "percent"
    return val, unit

class Interval:
    """Mathematical interval representation for requirement bounds."""
    def __init__(self, low: float, high: float, low_inc: bool = True, high_inc: bool = True):
        self.low = low
        self.high = high
        self.low_inc = low_inc
        self.high_inc = high_inc

    def intersect(self, other: 'Interval') -> Optional['Interval']:
        max_low = max(self.low, other.low)
        min_high = min(self.high, other.high)
        if max_low > min_high:
            return None
        if max_low == min_high:
            # Check open boundary single point conflict
            low_inc = self.low_inc if max_low == self.low else other.low_inc
            high_inc = self.high_inc if min_high == self.high else other.high_inc
            if not (low_inc and high_inc):
                return None
        return Interval(max_low, min_high)

    def is_subset_of(self, other: 'Interval') -> bool:
        return self.low >= other.low and self.high <= other.high

def compare_constraints(c1: Dict[str, Any], c2: Dict[str, Any]) -> str:
    """
    Compares two normalized numeric constraints on the exact same attribute/scope.
    Returns: CONTRADICTION | REFINEMENT | OVERLAP | DUPLICATE
    """
    if c1.get("attribute") != c2.get("attribute"):
        return "NO_COMPARISON"

    v1, u1 = normalize_unit_value(c1["value"], c1.get("unit", ""))
    v2, u2 = normalize_unit_value(c2["value"], c2.get("unit", ""))

    if u1 != u2 or v1 is None or v2 is None:
        return "UNKNOWN_UNITS"

    # Map operators to intervals
    def to_interval(op: str, val: float) -> Interval:
        inf = float('inf')
        if op == "==":
            return Interval(val, val, True, True)
        elif op in ["<=", "at most", "within"]:
            return Interval(-inf, val, False, True)
        elif op == "<":
            return Interval(-inf, val, False, False)
        elif op in [">=", "at least"]:
            return Interval(val, inf, True, False)
        elif op == ">":
            return Interval(val, inf, False, False)
        return Interval(val, val, True, True)

    i1 = to_interval(c1.get("operator", "=="), v1)
    i2 = to_interval(c2.get("operator", "=="), v2)

    if i1.low == i2.low and i1.high == i2.high:
        return "DUPLICATE"

    intersection = i1.intersect(i2)
    if intersection is None:
        return "CONTRADICTION"
    if i1.is_subset_of(i2) or i2.is_subset_of(i1):
        return "REFINEMENT"

    return "OVERLAP"
