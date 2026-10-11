"""
Rewrite generation + validation — PRD Section 20.11 / 5.2.

Rules:
- Every rewrite MUST contain: subject + shall + action + metric + threshold + condition.
- The LLM must NOT invent thresholds as facts: proposed numbers come back as
  assumptions[] needing human confirmation.
- Validation in code BEFORE showing: contains 'shall'; same actor/scope; keeps
  all original requirement IDs; NFRs contain a number + unit; re-run rules on
  the proposal and report the REAL score delta (D6).
- If validation fails twice -> "Needs human input" with the missing questions.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from ai_engine.rules.incose import evaluate_rules, VAGUE_TERMS
from ai_engine.scoring.scorer import calculate_requirement_scores

SHALL = re.compile(r"\b(shall|must)\b", re.I)
NUMBER_UNIT = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|ms|milliseconds?|s|secs?|seconds?|"
                         r"min|mins|minutes?|h|hours?|days?|kb|mb|gb)\b", re.I)

# vague term -> suggested measurable phrasing + assumption question
# Every replacement number is a PROPOSAL flagged needs_human_confirmation.
VAGUE_FIXES = {
    "rapidly": ("within 250 milliseconds", "What is the maximum acceptable processing latency (ms)?"),
    "quickly": ("within 250 milliseconds", "What is the maximum acceptable response time (ms)?"),
    "fast": ("within 250 milliseconds", "What is the maximum acceptable latency (ms)?"),
    "quick": ("within 250 milliseconds", "What is the maximum acceptable latency (ms)?"),
    "promptly": ("within 5 seconds", "What is the maximum acceptable delay (seconds)?"),
    "user-friendly": ("usable with a task success rate of at least 90% for first-time users",
                      "What usability success metric and threshold apply?"),
    "easy to use": ("usable with a task success rate of at least 90%",
                    "What usability success metric and threshold apply?"),
    "easy": ("usable with a task success rate of at least 90%",
             "What usability metric and threshold apply?"),
    "intuitive": ("with no more than 1 error per task", "Which error-rate threshold defines intuitive use?"),
    "robust": ("with 99.9% fault-free operation under the defined fault model",
               "Which fault model and tolerance define robustness?"),
    "efficient": ("using no more than 2 CPU-seconds per operation",
                  "Which resource budget defines efficiency?"),
    "seamless": ("with zero manual intervention and a synchronization delay of at most 5 seconds",
                 "What measurable integration criterion applies?"),
    "flexible": ("supporting at least 3 configurable policies without code change",
                 "Which configuration dimension and bound apply?"),
    "optimal": ("while maintaining availability of at least 99.9%",
                "Which objective is optimized and to what bound?"),
    "adequate": ("supporting at least 100 concurrent users", "What threshold defines adequate?"),
    "sufficient": ("supporting at least 100 concurrent users", "What capacity threshold is sufficient?"),
    "appropriate": ("", "Which normative reference defines 'appropriate'?"),
    "relevant": ("", "Which criteria define relevance?"),
    "ideally": ("", "'ideally' is a subjective qualifier — remove it"),
    "modern": ("", "'modern' is not verifiable — state the standard/version instead"),
    "state-of-the-art": ("", "'state-of-the-art' is not verifiable — cite the standard"),
    "high performance": ("with p95 latency of at most 200 milliseconds at 100 concurrent sessions",
                         "What latency/throughput targets apply?"),
    "minimal": ("with at most 1 manual step", "What is the maximum allowed number?"),
    "as needed": ("when explicitly triggered by the user", "What is the triggering condition?"),
}


def _detect_actor(text: str) -> str:
    m = re.match(r"^\s*((?:The\s+)?[A-Z][\w ]{2,40}?)\s+(shall|must|should|will|is|are|can)\b",
                 text, re.I)
    if m:
        return m.group(1).strip()
    return "The system"


def validate_rewrite(original: str, proposed: str, req_type: str = "",
                     category: str = "") -> Dict[str, Any]:
    """Code validation per 20.11. Returns {valid, problems[], questions[]}."""
    problems: List[str] = []
    questions: List[str] = []

    if not SHALL.search(proposed):
        problems.append("Rewrite must use a mandatory modal ('shall'/'must').")
    if not re.search(r"\b\d+(?:\.\d+)?\b", proposed):
        problems.append("Rewrite must contain a numeric value.")
        questions.append("What measurable threshold should apply?")
    if not NUMBER_UNIT.search(proposed) and not re.search(r"%|percent", proposed, re.I):
        if req_type == "Non-Functional" or re.search(
                r"perform|latency|security|availability|session|encrypt",
                f"{category} {original}", re.I):
            problems.append("Non-functional rewrite must include a unit (ms, %, min, …).")
            questions.append("Which unit applies to the threshold?")

    # same actor/scope: original actor must survive
    orig_actor = _detect_actor(original)
    if orig_actor and orig_actor.lower() not in proposed.lower():
        # allow generic fallback if actor was generic
        if orig_actor.lower() not in ("the system", "system"):
            problems.append(f"Rewrite changed the actor ('{orig_actor}' missing).")
            questions.append("Which actor should the requirement apply to?")

    # vague terms must be gone
    pl = proposed.lower()
    for term in VAGUE_TERMS:
        if len(term.split()) > 1:
            hit = term in pl
        else:
            hit = bool(re.search(r"\b" + re.escape(term) + r"\b", pl))
        if hit:
            problems.append(f"Rewrite still contains vague term '{term}'.")

    # structural requirement IDs (e.g. cross references) must be preserved
    orig_refs = set(re.findall(r"\b(?:REQ|FR|NFR|SR|SYS|TEST|ARCH)[-_ ]?\d+\b", original, re.I))
    new_refs = set(re.findall(r"\b(?:REQ|FR|NFR|SR|SYS|TEST|ARCH)[-_ ]?\d+\b", proposed, re.I))
    missing_refs = orig_refs - new_refs
    if missing_refs:
        problems.append(f"Rewrite dropped referenced IDs: {sorted(missing_refs)}")

    return {"valid": not problems, "problems": problems, "questions": questions}


def score_rewrite(original: str, proposed: str, category: str = "") -> Dict[str, Any]:
    """Real score delta by re-running the deterministic analysis on the proposal."""
    before = evaluate_rules(original, category=category)
    after = evaluate_rules(proposed, category=category)
    req_before = {"has_actor": before["has_actor"], "is_testable": before["is_testable"],
                  "missing_elements_count": before["missing_elements_count"],
                  "missing_info_count": before["missing_info_count"]}
    req_after = {"has_actor": after["has_actor"], "is_testable": after["is_testable"],
                 "missing_elements_count": after["missing_elements_count"],
                 "missing_info_count": after["missing_info_count"]}
    s_before = calculate_requirement_scores(req_before, before["rule_violations"], [])
    s_after = calculate_requirement_scores(req_after, after["rule_violations"], [])
    return {
        "before": s_before,
        "after": s_after,
        "delta": round(s_after["clarity_index"] - s_before["clarity_index"], 1),
        "violations_before": len(before["rule_violations"]),
        "violations_after": len(after["rule_violations"]),
    }


def deterministic_rewrite(text: str, category: str = "",
                          req_type: str = "Functional") -> Dict[str, Any]:
    """
    Rules-based measurable rewrite (works offline, no LLM).
    Produces proposed_text + assumptions[] — numbers are proposals, not facts.
    """
    proposals: List[Dict[str, Any]] = []
    out = text

    # 1) weak modal -> shall
    if not SHALL.search(out):
        out = re.sub(r"\bshould\b", "shall", out, flags=re.I)
        out = re.sub(r"\bmust\b", "shall", out, count=1, flags=re.I) if "shall" not in out.lower() else out
    else:
        out = re.sub(r"\bshould\b", "shall", out, flags=re.I)

    # 2) vague terms -> measurable placeholders with assumptions
    for term, fix in VAGUE_FIXES.items():
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.I)
        if pattern.search(out):
            replacement, question = fix
            if replacement:
                out = pattern.sub(replacement, out, count=1)
                proposals.append({
                    "field": term,
                    "proposed_value": replacement,
                    "rationale": f"'{term}' is not verifiable; quantified for testability.",
                    "question": question,
                    "needs_human_confirmation": True,
                })
            else:
                out = pattern.sub("", out)
                proposals.append({
                    "field": term,
                    "proposed_value": "(removed)",
                    "rationale": f"'{term}' cannot be quantified without domain input.",
                    "question": question,
                    "needs_human_confirmation": True,
                })

    # 3) NFR without threshold -> inject a placeholder metric clause
    rules = evaluate_rules(text, category=category)
    if rules["performance_requirement"] and not NUMBER_UNIT.search(out):
        out = out.rstrip(".") + " within [N] milliseconds under [N] concurrent sessions."
        proposals.append({
            "field": "threshold",
            "proposed_value": "<N> ms @ <N> concurrent sessions",
            "rationale": "Performance requirement had no metric/threshold/condition (RQ-TEST-001).",
            "question": "What latency target and load profile apply?",
            "needs_human_confirmation": True,
        })

    # 4) ensure condition present
    if not re.search(r"\b(under|when|while|during|within|given|at|for)\b", out, re.I):
        out = out.rstrip(".") + " under normal operating conditions."
        proposals.append({
            "field": "condition",
            "proposed_value": "under normal operating conditions",
            "rationale": "No applicable condition was stated (RQ-TEST-001).",
            "question": "Under which load/operating condition does this apply?",
            "needs_human_confirmation": True,
        })

    out = re.sub(r"\s+", " ", out).strip()
    if not out.endswith("."):
        out += "."

    validation = validate_rewrite(text, out, req_type=req_type, category=category)
    if not validation["valid"] and proposals:
        # attempt 2: drop the least-helpful construct (remove empty leftovers)
        out2 = re.sub(r"\s{2,}", " ", out.replace("  ", " ")).strip()
        validation = validate_rewrite(text, out2, req_type=req_type, category=category)
        out = out2

    if not validation["valid"]:
        return {
            "status": "needs_human_input",
            "proposed_text": None,
            "assumptions": proposals,
            "problems": validation["problems"],
            "questions": validation["questions"] or ["Provide the measurable acceptance criteria."],
        }

    delta = score_rewrite(text, out, category=category)
    return {
        "status": "ok",
        "proposed_text": out,
        "assumptions": proposals,
        "predicted_score_delta": delta["delta"],
        "score_preview": delta,
        "problems": [],
        "questions": [p["question"] for p in proposals],
    }


async def llm_rewrite(text: str, provider, category: str = "", req_type: str = "Functional") -> Dict[str, Any]:
    """LLM-assisted rewrite (strong tier) with code validation; falls back deterministic."""
    if provider is None:
        return deterministic_rewrite(text, category, req_type)
    schema = {
        "type": "object",
        "required": ["proposed_text", "assumptions"],
        "properties": {
            "proposed_text": {"type": "string"},
            "assumptions": {"type": "array"},
            "rationale": {"type": "string"},
        },
    }
    system = (
        "You rewrite software requirements to be measurable and testable.\n"
        "Rules: keep the same actor and scope; use 'shall'; include metric + threshold + unit + condition;\n"
        "never invent numbers as facts — put every proposed number in assumptions[] with a question;\n"
        "keep all referenced IDs (REQ-/TEST-/ARCH-).\n"
        'Output JSON: {"proposed_text": str, "assumptions": [{"field","proposed_value","rationale","question"}], "rationale": str}'
    )
    user = f"<SRS_TEXT id=\"REWRITE\">{text}</SRS_TEXT>\nCategory: {category or 'general'}"
    try:
        res = await provider.generate_json(
            task="rewrite", system=system, user=user, schema=schema, tier="reasoning")
        proposed = res.data.get("proposed_text", "") if isinstance(res.data, dict) else ""
        validation = validate_rewrite(text, proposed, req_type=req_type, category=category)
        if proposed and validation["valid"]:
            delta = score_rewrite(text, proposed, category=category)
            return {
                "status": "ok",
                "proposed_text": proposed,
                "assumptions": res.data.get("assumptions", []),
                "predicted_score_delta": delta["delta"],
                "score_preview": delta,
                "problems": [],
                "questions": [],
                "source": "llm",
            }
    except Exception:
        pass
    return deterministic_rewrite(text, category, req_type)
