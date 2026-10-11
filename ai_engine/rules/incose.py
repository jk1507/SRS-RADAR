import re
from typing import List, Dict, Any

# INCOSE Rules Definition (ISO/IEC/IEEE 29148 & INCOSE Guide for Writing Requirements)
SUBJECTIVE_LEXICON = [
    "rapidly", "ideally", "user-friendly", "flexible", "robust",
    "efficient", "seamless", "easy to use", "state-of-the-art",
    "optimal", "adequate", "sufficient", "appropriate"
]

WEAK_MODALS = ["should", "may", "could", "might", "can", "ought to"]
ESCAPE_CLAUSES = ["if possible", "where practical", "as far as possible", "as appropriate"]

def evaluate_incose_rules(clause_text: str) -> Dict[str, Any]:
    """Evaluates a requirement clause against INCOSE structural & syntactic rules."""
    violations = []
    text_lower = clause_text.lower()
    
    # Rule 1: Subjective / Vagueness Check
    for word in SUBJECTIVE_LEXICON:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            violations.append({
                "rule_id": "INCOSE-R01",
                "type": "Subjective Lexicon",
                "term": word,
                "severity": "High" if word in ["rapidly", "ideally", "user-friendly"] else "Medium",
                "description": f"The term '{word}' is subjective and non-verifiable without exact quantitative bounds."
            })
            
    # Rule 2: Weak Modal Verbs (must use 'shall')
    for modal in WEAK_MODALS:
        if re.search(r'\b' + re.escape(modal) + r'\b', text_lower):
            violations.append({
                "rule_id": "INCOSE-R05",
                "type": "Weak Modal Verb",
                "term": modal,
                "severity": "Medium",
                "description": f"Use of non-binding modal verb '{modal}' instead of binding 'SHALL'."
            })

    # Rule 3: Escape Clauses
    for escape in ESCAPE_CLAUSES:
        if escape in text_lower:
            violations.append({
                "rule_id": "INCOSE-R08",
                "type": "Escape Clause",
                "term": escape,
                "severity": "High",
                "description": f"Escape clause '{escape}' renders requirement non-mandatory and ambiguous."
            })

    # Calculate Clarity Score (100 base - penalties per violation)
    penalty_weights = {"Critical": 35.0, "High": 25.0, "Medium": 15.0, "Low": 5.0}
    total_penalty = sum(penalty_weights.get(v["severity"], 10.0) for v in violations)
    clarity_score = max(0.0, round(100.0 - total_penalty, 1))

    status = "verified" if clarity_score >= 85.0 and not violations else "flagged"

    return {
        "clarity_score": clarity_score,
        "status": status,
        "rule_violations": violations
    }
