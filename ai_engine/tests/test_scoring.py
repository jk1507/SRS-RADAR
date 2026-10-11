import pytest
from ai_engine.scoring.scorer import calculate_requirement_scores, calculate_project_score

def test_req_024_worked_example():
    """
    Tests exact worked example REQ-024 from PRD section 20.8:
    "The system should ideally process medical telemetry packets rapidly under normal operating loads."
    Violations: LANG-001 (should, med), LANG-002 (fast/rapid response, high), LANG-004 (two behaviors/ideally, med)
    Not testable; 3 missing fields (threshold, condition, metric).
    """
    req = {"has_actor": True, "is_testable": False, "missing_elements_count": 3, "missing_info_count": 3}
    rule_violations = [
        {"rule_id": "LANG-001", "severity": "Medium"},
        {"rule_id": "LANG-002", "severity": "High"},
        {"rule_id": "LANG-004", "severity": "Medium"}
    ]
    ambiguities = [{"phrase": "rapidly", "severity": "High"}]

    scores = calculate_requirement_scores(
        req=req,
        rule_violations=rule_violations,
        grounded_ambiguities=ambiguities
    )

    # Check calculated values matching PRD worked example
    assert scores["clarity"] == 60.0    # 100 - 20(high) - 10(med) - 10(med) = 60
    assert scores["testability"] == 14.0 # 50 - 12*3 = 14
    assert scores["unambiguity"] == 70.0 # 100 - 30 = 70
    assert scores["completeness"] == 55.0 # 100 - 15*3 = 55
    assert scores["clarity_index"] == 50 # round((60+14+70+55)/4) = 50

def test_project_scoring():
    r1 = {"unambiguity": 70.0, "clarity": 60.0, "testability": 14.0, "completeness": 55.0, "consistency": 100.0, "standards": 80.0, "traceability": None}
    r2 = {"unambiguity": 100.0, "clarity": 100.0, "testability": 100.0, "completeness": 100.0, "consistency": 100.0, "standards": 100.0, "traceability": None}

    proj_score = calculate_project_score([r1, r2])
    assert 75.0 <= proj_score <= 90.0
