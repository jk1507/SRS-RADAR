import pytest
from ai_engine.solvers.constraint_solver import compare_constraints, normalize_unit_value

def test_unit_normalization():
    val, unit = normalize_unit_value(15, "min")
    assert val == 900.0
    assert unit == "seconds"

    val, unit = normalize_unit_value(30, "minutes")
    assert val == 1800.0
    assert unit == "seconds"

    val, unit = normalize_unit_value(500, "ms")
    assert val == 0.5
    assert unit == "seconds"

def test_contradiction_detection():
    # REQ-031 session_timeout == 15 min vs REQ-042 session_timeout >= 30 min
    c1 = {"attribute": "session_timeout", "operator": "==", "value": 15, "unit": "min"}
    c2 = {"attribute": "session_timeout", "operator": ">=", "value": 30, "unit": "min"}

    res = compare_constraints(c1, c2)
    assert res == "CONTRADICTION"

def test_refinement_detection():
    # latency <= 200 ms vs latency <= 500 ms (Refinement, not conflict!)
    c1 = {"attribute": "latency", "operator": "<=", "value": 200, "unit": "ms"}
    c2 = {"attribute": "latency", "operator": "<=", "value": 500, "unit": "ms"}

    res = compare_constraints(c1, c2)
    assert res == "REFINEMENT"
