"""
Deterministic rules engine — PRD Section 7 (ISO/IEC/IEEE 29148 + INCOSE Guide
for Writing Requirements). Machine-readable rule set, evidence-bearing output.

Rule IDs (with severity defaults):
  RQ-LANG-001  mandatory modal 'shall'            Medium
  RQ-LANG-002  no vague/subjective terms          High
  RQ-LANG-003  no escape clauses                  Medium
  RQ-LANG-004  single requirement per statement   Medium
  RQ-LANG-005  no unresolved pronouns/acronyms    Low
  RQ-TEST-001  perf req has metric+threshold+cond High
  RQ-TEST-002  verifiable acceptance criterion    Medium
  RQ-STRUCT-001 identifiable actor/subject        Medium
  RQ-STRUCT-002 unique statement (dup check)      High
  RQ-TRACE-001 linked to design/test/compliance   Medium   (evaluated by pipeline)

Lexicon hits are *candidates*: the pipeline may confirm them with the LLM
(PRD 19.5 / 23), but the rule engine always reports them as findings with
exact quoted evidence so scores remain deterministic.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# ---------------------------------------------------------------- lexicons
VAGUE_TERMS: Dict[str, str] = {
    # term -> why it is vague
    "rapidly": "No measurable latency threshold",
    "quickly": "No measurable latency threshold",
    "fast": "No measurable latency threshold",
    "quick": "No measurable latency threshold",
    "promptly": "No measurable latency threshold",
    "ideally": "Subjective qualifier, not verifiable",
    "user-friendly": "No measurable usability metric",
    "easy to use": "No measurable usability metric",
    "easy": "No measurable usability metric",
    "flexible": "No defined flexibility bounds",
    "robust": "No defined robustness criterion",
    "efficient": "No measurable efficiency criterion",
    "seamless": "No measurable integration criterion",
    "optimal": "No optimality criterion defined",
    "adequate": "No adequacy threshold defined",
    "sufficient": "No sufficiency threshold defined",
    "appropriate": "Subjective qualifier, not verifiable",
    "relevant": "Subjective qualifier, not verifiable",
    "high performance": "No measurable performance threshold",
    "state-of-the-art": "Subjective qualifier, not verifiable",
    "modern": "Subjective qualifier, not verifiable",
    "intuitive": "No measurable usability metric",
    "minimal": "No measurable bound",
    "maximum": "No measurable bound when unquantified",
    "as needed": "Open-ended condition",
    "etc.':": "Non-exhaustive list",
}

ESCAPE_CLAUSES = [
    "if possible",
    "where practical",
    "as far as possible",
    "as appropriate",
    "as needed",
    "as required",
    "if necessary",
    "when feasible",
    "and/or",
    "tbd",
    "to be determined",
    "etc.",
    "and so on",
]

WEAK_MODALS = ["should", "may", "could", "might", "can", "ought to", "would"]

UNDEFINED_PRONOUNS = re.compile(
    r"\b(it|they|them|its|their|this|that|these|those)\b", re.IGNORECASE
)
ACRONYM = re.compile(r"\b([A-Z]{2,6})\b")
ACRONYM_DEF = re.compile(r"\b([A-Z]{2,6})\s*\(([^)]+)\)")

SUBJECT_RE = re.compile(
    r"^(the\s+)?(system|user|users|application|platform|server|client|module|service|"
    r"api|interface|admin|administrator|administrator|database|browser|device|dashboard|portal|"
    r"software|hardware|network|portal|sensor|controller|engine)\b",
    re.IGNORECASE,
)
ACTOR_RE = re.compile(
    r"\b(system|user|users|administrator|admin|operator|patient|doctor|clinician|"
    r"customer|client|application|service|module|browser|sensor|controller)\b",
    re.IGNORECASE,
)

PERF_METRIC = re.compile(
    r"\b(latency|throughput|response time|availability|uptime|error rate|bandwidth|"
    r"concurrent(?:ly)?|requests? per second|rps|qps|ms|milliseconds?|seconds?|"
    r"percent|%|mbps|gb)\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|ms|s|sec|secs|seconds?|min|mins|minutes?|h|hours?|days?|kb|mb|gb)?\b", re.IGNORECASE)
CONDITION_RE = re.compile(
    r"\b(under|when|while|during|given|in the event of|with at least|"
    r"at (?:up to |at least )?(?:a )?(?:load|rate|peak))\b[^.]{3,80}",
    re.IGNORECASE,
)


def _viol(rule_id: str, vtype: str, severity: str, term: str, description: str,
          span=None, quote: str = "") -> Dict[str, Any]:
    return {
        "rule_id": rule_id,
        "type": vtype,
        "term": term,
        "severity": severity,
        "description": description,
        "quote": quote or term,
        "span": span,
    }


def _find_span(text: str, needle: str):
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return None
    return [idx, idx + len(needle)]


def evaluate_rules(text: str, category: str = "", heading: str = "",
                   known_acronyms: set | None = None) -> Dict[str, Any]:
    """
    Evaluate one requirement statement against the deterministic rule set.
    Returns {rule_violations, has_actor, is_testable, missing_elements,
             missing_information, testability_reason}
    """
    violations: List[Dict[str, Any]] = []
    t = text.strip()
    tl = t.lower()
    known_acronyms = known_acronyms or set()

    # ---- RQ-LANG-001 mandatory modal -------------------------------------
    modal_hit = None
    for m in re.finditer(r"\b(shall|must|should|may|might|could|can|will|would|ought to)\b", t, re.I):
        word = m.group(0).lower()
        if word in ("shall", "must"):
            modal_hit = "strong"
            break
        if word in WEAK_MODALS or word == "would":
            modal_hit = word
    if modal_hit and modal_hit != "strong":
        violations.append(_viol(
            "RQ-LANG-001", "Weak Modal Verb", "Medium", modal_hit,
            f"Use of non-binding modal verb '{modal_hit}' instead of binding 'shall'.",
            _find_span(t, modal_hit)))
    elif modal_hit is None:
        violations.append(_viol(
            "RQ-LANG-001", "Missing Modal Verb", "Medium", "",
            "Statement contains no mandatory modal verb ('shall'/'must').", [0, 0]))

    # ---- RQ-LANG-002 vague/subjective terms ------------------------------
    for term, why in VAGUE_TERMS.items():
        if len(term.split()) > 1:
            found = term in tl
        else:
            found = bool(re.search(r"\b" + re.escape(term) + r"\b", tl))
        if found:
            sev = "High" if term in (
                "rapidly", "quickly", "fast", "quick", "user-friendly",
                "easy to use", "intuitive", "robust", "efficient", "seamless",
                "state-of-the-art", "high performance") else "Medium"
            violations.append(_viol(
                "RQ-LANG-002", "Vague / Subjective Term", sev, term,
                f"'{term}' is subjective: {why}.", _find_span(t, term)))

    # ---- RQ-LANG-003 escape clauses --------------------------------------
    for esc in ESCAPE_CLAUSES:
        if esc in tl:
            violations.append(_viol(
                "RQ-LANG-003", "Escape Clause", "Medium", esc,
                f"Escape clause '{esc}' renders the requirement non-mandatory.",
                _find_span(t, esc)))

    # ---- RQ-LANG-004 single requirement per statement --------------------
    strong_verbs = list(re.finditer(r"\b(shall|must)\b", t, re.I))
    and_join = bool(re.search(r"\band\b", t, re.I))
    gerunds = re.findall(r"\b\w+ing\b", t, re.I)
    two_actions = len(strong_verbs) >= 2
    compound_and = and_join and len(t.split()) >= 10 and len(gerunds) >= 1
    if two_actions or compound_and:
        violations.append(_viol(
            "RQ-LANG-004", "Compound Requirement", "Medium", "and",
            "Statement appears to bundle multiple behaviors; split into atomic requirements "
            "(flagged, never auto-split).", _find_span(t, " and ")))

    # ---- RQ-STRUCT-003 non-requirement / injected directive --------------
    injection = re.search(
        r"ignore (?:all )?(?:previous|prior|above) instructions|disregard (?:the )?"
        r"(?:previous|prior)|as an ai|give this document|assign (?:this|a) score of|"
        r"you are (?:now|a)", t, re.I)
    if injection:
        violations.append(_viol(
            "RQ-STRUCT-003", "Non-requirement Text (injected directive)", "Medium",
            injection.group(0),
            "Sentence contains an imperative that is not a system requirement; treat as "
            "data and review the statement (prompt-injection guard).",
            [injection.start(), injection.end()]))

    # ---- RQ-LANG-005 pronouns / acronyms ---------------------------------
    pronoun = UNDEFINED_PRONOUNS.search(t)
    if pronoun and len(t.split()) > 6:
        violations.append(_viol(
            "RQ-LANG-005", "Unresolved Pronoun", "Low", pronoun.group(0),
            f"Pronoun '{pronoun.group(0)}' has no clear antecedent within the statement.",
            [pronoun.start(), pronoun.end()]))
    defined = {m.group(1).upper() for m in ACRONYM_DEF.finditer(t)}
    defined |= known_acronyms
    skip = {"AND", "OR", "NOT", "REQ", "API", "URL", "HTTP", "HTTPS", "JSON", "XML", "SQL", "CPU", "GPU", "RAM", "SSD", "US", "WE"}
    for m in ACRONYM.finditer(t):
        acr = m.group(1)
        if acr in skip or acr in defined:
            continue
        # require it not be defined anywhere in the same statement
        if f"{acr} (" in t:
            continue
        violations.append(_viol(
            "RQ-LANG-005", "Undefined Acronym", "Low", acr,
            f"Acronym '{acr}' is used without an in-statement definition.",
            [m.start(), m.end()]))
        break  # one finding per statement keeps noise low

    # ---- RQ-STRUCT-001 actor / subject -----------------------------------
    has_actor = bool(ACTOR_RE.search(t)) or bool(SUBJECT_RE.search(t))
    if not has_actor:
        violations.append(_viol(
            "RQ-STRUCT-001", "Missing Actor/Subject", "Medium", "",
            "No identifiable actor or system subject performs the action.", [0, 0]))

    # ---- RQ-TEST-001 performance measurability ---------------------------
    is_perf = bool(re.search(r"performance|latency|throughput|response time|availability|"
                             r"uptime|error rate|concurrent|scalab|load", f"{heading} {category} {t}", re.I))
    has_metric = bool(PERF_METRIC.search(t))
    has_threshold = bool(NUMBER_RE.search(t))
    has_condition = bool(CONDITION_RE.search(t))
    # PRD 20.8 testability elements: metric / threshold / condition
    missing_elements = []
    if not has_metric:
        missing_elements.append("metric")
    if not has_threshold:
        missing_elements.append("threshold")
    if not has_condition:
        missing_elements.append("condition")
    if is_perf and missing_elements:
        violations.append(_viol(
            "RQ-TEST-001", "Unmeasurable Performance Requirement", "High", "",
            "Performance requirement missing: " + ", ".join(missing_elements) +
            ". Provide metric + threshold + load condition.", [0, 0]))

    # ---- RQ-TEST-002 acceptance criterion --------------------------------
    # deterministic proxy: statement has a verifiable bound (number+unit) OR
    # explicit acceptance/verification phrasing
    verifiable = has_threshold or bool(re.search(
        r"\b(verified|validated|tested|measured|logged|recorded|counted|compared)\b", t, re.I))
    if not verifiable:
        violations.append(_viol(
            "RQ-TEST-002", "No Verifiable Acceptance Criterion", "Medium", "",
            "No measurable acceptance criterion or verification method stated.",
            [0, 0]))

    # ---- testability verdict ---------------------------------------------
    testable = verifiable and (not is_perf or (has_metric and has_threshold))
    missing_info: List[str] = []
    if not has_threshold:
        missing_info.append("threshold")
    if not has_condition:
        missing_info.append("condition")
    if not verifiable:
        missing_info.append("measurement method")
    if not has_actor:
        missing_info.append("explicit actor")

    reason = ""
    if not testable:
        reason = ("Statement lacks a verifiable threshold/metric"
                  + (f" (missing: {', '.join(missing_elements)})" if missing_elements else ""))

    return {
        "rule_violations": violations,
        "has_actor": has_actor,
        "is_testable": testable,
        "missing_elements_count": len(missing_elements),
        "missing_elements": missing_elements,
        "missing_information": missing_info,
        "missing_info_count": len(missing_info),
        "testability_reason": reason,
        "performance_requirement": is_perf,
    }


def evaluate_incose_rules(clause_text: str) -> Dict[str, Any]:
    """Back-compat wrapper: evaluate a single clause and derive clarity score."""
    res = evaluate_rules(clause_text)
    penalties = {"Critical": 30.0, "High": 20.0, "Medium": 10.0, "Low": 5.0}
    clarity = 100.0
    for v in res["rule_violations"]:
        if v["rule_id"].startswith("RQ-LANG") or v["rule_id"].startswith("RQ-STRUCT"):
            clarity -= penalties.get(v["severity"], 10.0)
    if not res["has_actor"]:
        clarity -= 10.0
    clarity = max(0.0, round(clarity, 1))
    return {
        "clarity_score": clarity,
        "status": "verified" if not res["rule_violations"] else "flagged",
        "rule_violations": res["rule_violations"],
        **res,
    }
