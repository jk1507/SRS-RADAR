"""
7-dimension deterministic quality scoring module per PRD Section 8.2 & 20.8.
"""
from typing import Dict, Any, List, Optional

def calculate_requirement_scores(
    req: Dict[str, Any],
    rule_violations: List[Dict[str, Any]],
    grounded_ambiguities: List[Dict[str, Any]],
    confirmed_conflicts_count: int = 0,
    needs_review_conflicts_count: int = 0,
    traceability_categories_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Computes per-requirement quality scores across 7 dimensions (0-100 scale).
    """
    # 1. Unambiguity: 100 - 30*(high ambiguities) - 15*(medium ambiguities)
    high_amb = sum(1 for a in grounded_ambiguities if a.get("severity") == "High")
    med_amb = sum(1 for a in grounded_ambiguities if a.get("severity") == "Medium")
    unambiguity = max(0.0, 100.0 - (30.0 * high_amb) - (15.0 * med_amb))

    # 2. Clarity: 100 - 20*(high RQ-LANG) - 10*(medium) - 5*(low) - 10 if no actor
    lang_violations = [v for v in rule_violations if "LANG" in str(v.get("rule_id", ""))]
    high_lang = sum(1 for v in lang_violations if v.get("severity") == "High")
    med_lang = sum(1 for v in lang_violations if v.get("severity") == "Medium")
    low_lang = sum(1 for v in lang_violations if v.get("severity") == "Low")
    no_actor = 10.0 if not req.get("has_actor", True) else 0.0
    clarity = max(0.0, 100.0 - (20.0 * high_lang) - (10.0 * med_lang) - (5.0 * low_lang) - no_actor)

    # 3. Testability: 100 - 50 if not testable - 12*(missing metric/threshold/condition, max 3)
    is_testable = req.get("is_testable", True)
    missing_elements = req.get("missing_elements_count", 0)
    testability_base = 100.0 if is_testable else 50.0
    testability = max(0.0, testability_base - (12.0 * min(3, missing_elements)))

    # 4. Completeness: 100 - 15*(missing_information items, max 6)
    missing_info_count = req.get("missing_info_count", 0)
    completeness = max(0.0, 100.0 - (15.0 * min(6, missing_info_count)))

    # 5. Consistency: 100 - 60*(confirmed conflicts) - 30*(needs_review conflicts)
    consistency = max(0.0, 100.0 - (60.0 * confirmed_conflicts_count) - (30.0 * needs_review_conflicts_count))

    # 6. Standards: 100 - 20*critical - 15*high - 8*medium - 3*low
    crit_std = sum(1 for v in rule_violations if v.get("severity") == "Critical")
    high_std = sum(1 for v in rule_violations if v.get("severity") == "High")
    med_std = sum(1 for v in rule_violations if v.get("severity") == "Medium")
    low_std = sum(1 for v in rule_violations if v.get("severity") == "Low")
    standards = max(0.0, 100.0 - (20.0 * crit_std) - (15.0 * high_std) - (8.0 * med_std) - (3.0 * low_std))

    # 7. Traceability: min(100, 50 * distinct confirmed link categories)
    if traceability_categories_count is None:
        traceability = None
    else:
        traceability = min(100.0, 50.0 * traceability_categories_count)

    # Semantic Quality Index = round(mean(Clarity, Testability, Unambiguity, Completeness))
    clarity_index = round((clarity + testability + unambiguity + completeness) / 4.0)

    return {
        "unambiguity": unambiguity,
        "clarity": clarity,
        "testability": testability,
        "completeness": completeness,
        "consistency": consistency,
        "standards": standards,
        "traceability": traceability,
        "clarity_index": clarity_index
    }

def calculate_project_score(requirements_scores: List[Dict[str, Any]], weights: Optional[Dict[str, float]] = None) -> float:
    """
    Computes overall project quality score using 7-dimension weighted formula.
    """
    if not requirements_scores:
        return 100.0

    default_weights = {
        "unambiguity": 0.20,
        "clarity": 0.15,
        "testability": 0.20,
        "completeness": 0.15,
        "consistency": 0.15,
        "standards": 0.10,
        "traceability": 0.05
    }
    w = weights or default_weights

    # Mean score per dimension
    means = {}
    for dim in ["unambiguity", "clarity", "testability", "completeness", "consistency", "standards"]:
        vals = [r[dim] for r in requirements_scores if r.get(dim) is not None]
        means[dim] = sum(vals) / len(vals) if vals else 100.0

    trace_vals = [r["traceability"] for r in requirements_scores if r.get("traceability") is not None]
    if trace_vals:
        means["traceability"] = sum(trace_vals) / len(trace_vals)
    else:
        # Redistribute weight if no traceability targets present
        total_w = sum(w[k] for k in w if k != "traceability")
        w = {k: (w[k] / total_w if k != "traceability" else 0.0) for k in w}
        means["traceability"] = 0.0

    total_score = sum(means[dim] * w[dim] for dim in w)
    return round(total_score, 1)
