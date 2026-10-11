import sys
import os
import asyncio
from ai_engine.pipeline.workflow import RequirementIntelligencePipeline

# Golden benchmark suite per PRD Section 20.14
GOLDEN_BENCHMARKS = [
    {
        "id": "G1",
        "name": "REQ-024 Ambiguity & Modal check",
        "input": [
            {
                "req_id_str": "REQ-024",
                "clause_text": "The system should ideally process medical telemetry packets rapidly under normal operating loads.",
                "has_actor": True,
                "is_testable": False,
                "missing_elements_count": 3,
                "missing_info_count": 3,
                "llm_ambiguities": [{"phrase": "rapidly", "severity": "High"}]
            }
        ],
        "check": lambda res: 35 <= res["requirements"][0]["scores"]["clarity_index"] <= 55
    },
    {
        "id": "G2",
        "name": "REQ-031 vs REQ-042 Conflict Detection",
        "input": [
            {
                "req_id_str": "REQ-031",
                "clause_text": "The system SHALL automatically lock user sessions after 15 minutes of inactivity.",
                "constraint": {"attribute": "session_timeout", "operator": "==", "value": 15, "unit": "min"}
            },
            {
                "req_id_str": "REQ-042",
                "clause_text": "The patient workstation SHALL maintain continuous session state for at least 30 minutes.",
                "constraint": {"attribute": "session_timeout", "operator": ">=", "value": 30, "unit": "min"}
            }
        ],
        "check": lambda res: len(res["issues"]) == 1 and res["issues"][0]["severity"] == "Critical"
    },
    {
        "id": "G6",
        "name": "Latency Refinement (200ms vs 500ms, no conflict)",
        "input": [
            {
                "req_id_str": "REQ-101",
                "clause_text": "Response time shall be <= 200 ms.",
                "constraint": {"attribute": "latency", "operator": "<=", "value": 200, "unit": "ms"}
            },
            {
                "req_id_str": "REQ-102",
                "clause_text": "Response time shall be <= 500 ms.",
                "constraint": {"attribute": "latency", "operator": "<=", "value": 500, "unit": "ms"}
            }
        ],
        "check": lambda res: len(res["issues"]) == 0 # Refinement is NOT a conflict
    }
]

def run_evaluation_benchmark():
    print("==================================================")
    print("    Requirement Radar — Accuracy Evaluation       ")
    print("==================================================")

    pipeline = RequirementIntelligencePipeline()
    passed = 0
    total = len(GOLDEN_BENCHMARKS)

    for case in GOLDEN_BENCHMARKS:
        res = asyncio.run(pipeline.execute(case["input"]))
        if case["check"](res):
            print(f"[{case['id']}] {case['name']} ... PASSED")
            passed += 1
        else:
            print(f"[{case['id']}] {case['name']} ... FAILED")

    precision = passed / total
    recall = passed / total
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("--------------------------------------------------")
    print(f"Total Cases: {total} | Passed: {passed} | Failed: {total - passed}")
    print(f"Precision: {precision * 100:.1f}%")
    print(f"Recall:    {recall * 100:.1f}%")
    print(f"F1 Score:  {f1_score:.3f}")
    print("==================================================")
    return passed == total

if __name__ == "__main__":
    success = run_evaluation_benchmark()
    sys.exit(0 if success else 1)
