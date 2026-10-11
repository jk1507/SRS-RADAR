from typing import List, Dict, Any, Optional

def check_logical_contradictions(requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyzes a set of requirements for numerical, temporal, or logical contradictions."""
    contradictions = []

    # Example Contradiction Pattern: Timeout / Auto-lock conflicts
    timeout_reqs = []
    for req in requirements:
        clause = req.get("clause_text", "").lower()
        if "lock" in clause or "timeout" in clause or "inactivity" in clause:
            # Extract numerical values in minutes/seconds
            import re
            match = re.search(r'(\d+)\s*(minute|min|second|sec)', clause)
            if match:
                val = int(match.group(1))
                unit = match.group(2)
                val_minutes = val if "min" in unit else val / 60.0
                timeout_reqs.append({
                    "req_id": req.get("req_id_str", req.get("id")),
                    "clause": req.get("clause_text"),
                    "minutes": val_minutes
                })

    # Compare pairs for UNSAT condition
    if len(timeout_reqs) >= 2:
        for i in range(len(timeout_reqs)):
            for j in range(i + 1, len(timeout_reqs)):
                r1 = timeout_reqs[i]
                r2 = timeout_reqs[j]
                if abs(r1["minutes"] - r2["minutes"]) > 0.1:
                    contradictions.append({
                        "issue_id_str": "ISS-001",
                        "title": f"Direct Contradiction: Session Lock Timeout ({r1['req_id']} vs {r2['req_id']})",
                        "severity": "Critical",
                        "category": "Logical Contradiction",
                        "affected_req_ids": [r1["req_id"], r2["req_id"]],
                        "root_cause": f"{r1['req_id']} specifies {r1['minutes']}m timeout while {r2['req_id']} demands state retention for {r2['minutes']}m.",
                        "evidence_json": {
                            "req_a": {"id": r1["req_id"], "clause": r1["clause"]},
                            "req_b": {"id": r2["req_id"], "clause": r2["clause"]}
                        },
                        "ai_recommendation": f"Harmonize timeouts across {r1['req_id']} and {r2['req_id']} or specify explicit device context exceptions."
                    })

    return contradictions
