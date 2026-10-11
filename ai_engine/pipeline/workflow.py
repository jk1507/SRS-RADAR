from typing import List, Dict, Any
from ai_engine.rules.incose import evaluate_incose_rules
from ai_engine.solvers.constraint_solver import compare_constraints
from ai_engine.scoring.scorer import calculate_requirement_scores, calculate_project_score
from ai_engine.pipeline.grounding import ground_llm_findings

class RequirementIntelligencePipeline:
    """6-stage SpecSentinel AI requirement analysis pipeline with deterministic verification."""

    def __init__(self, mode: str = "Standard Audit", standard: str = "ISO/IEC/IEEE 29148"):
        self.mode = mode
        self.standard = standard

    async def execute(self, requirements_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_ids = [r["req_id_str"] for r in requirements_data]
        analyzed_reqs = []
        all_req_scores = []
        detected_issues = []

        # Stage 1 & 2: INCOSE Rule Verification & Grounding
        for req in requirements_data:
            text = req["clause_text"]
            incose = evaluate_incose_rules(text)

            # Ground LLM ambiguities if provided
            raw_ambiguities = req.get("llm_ambiguities", [])
            grounded_amb = ground_llm_findings(text, raw_ambiguities, valid_ids)

            # Compute per-requirement deterministic scores
            scores = calculate_requirement_scores(
                req=req,
                rule_violations=incose["rule_violations"],
                grounded_ambiguities=grounded_amb
            )

            analyzed_reqs.append({
                **req,
                "clarity_score": incose["clarity_score"],
                "rule_violations": incose["rule_violations"],
                "grounded_ambiguities": grounded_amb,
                "scores": scores
            })
            all_req_scores.append(scores)

        # Stage 3: Logical & Constraint Pair Comparisons
        for i in range(len(requirements_data)):
            for j in range(i + 1, len(requirements_data)):
                r1 = requirements_data[i]
                r2 = requirements_data[j]
                c1 = r1.get("constraint")
                c2 = r2.get("constraint")

                if c1 and c2:
                    rel = compare_constraints(c1, c2)
                    if rel == "CONTRADICTION":
                        detected_issues.append({
                            "issue_id_str": f"ISS-CONF-{i}-{j}",
                            "title": f"Direct Contradiction: {r1['req_id_str']} vs {r2['req_id_str']}",
                            "severity": "Critical",
                            "category": "Logical Contradiction",
                            "affected_req_ids": [r1["req_id_str"], r2["req_id_str"]],
                            "evidence_json": {
                                "quote_a": r1["clause_text"],
                                "quote_b": r2["clause_text"],
                                "constraint_a": c1,
                                "constraint_b": c2
                            },
                            "status": "confirmed",
                            "verification_type": "rule-verified"
                        })

        # Stage 4: Aggregated Metrics
        overall_score = calculate_project_score(all_req_scores)

        return {
            "status": "completed",
            "overall_quality_score": overall_score,
            "parsed_requirements_count": len(analyzed_reqs),
            "requirements": analyzed_reqs,
            "issues": detected_issues
        }
