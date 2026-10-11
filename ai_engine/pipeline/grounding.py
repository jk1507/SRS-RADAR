"""
Grounding validation engine per PRD section 19.5 & 20.15.
Prevents LLM hallucinations by enforcing quote matching and phrase grounding.
"""
from typing import Dict, Any, List

def ground_llm_findings(
    clause_text: str,
    llm_findings: List[Dict[str, Any]],
    valid_req_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Validates every LLM finding against exact substring occurrence in clause_text.
    Rejects or flags ungrounded findings.
    """
    grounded = []
    text_lower = clause_text.lower()

    for finding in llm_findings:
        phrase = finding.get("phrase", "")
        # Grounding Rule 1: Quoted phrase MUST be exact substring of clause text
        if phrase and phrase.lower() not in text_lower:
            finding["grounding_status"] = "rejected_unquoted"
            finding["grounding_error"] = f"Claimed phrase '{phrase}' not found in source text."
            continue

        # Grounding Rule 2: Affected requirement IDs must exist
        affected_ids = finding.get("affected_req_ids", [])
        invalid_ids = [rid for rid in affected_ids if rid not in valid_req_ids]
        if invalid_ids:
            finding["grounding_status"] = "rejected_invalid_req_id"
            finding["grounding_error"] = f"Referenced unknown IDs: {invalid_ids}"
            continue

        finding["grounding_status"] = "grounded"
        grounded.append(finding)

    return grounded
