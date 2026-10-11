"""
Constraint extraction + attribute registry per PRD Sections 20.5 and 26.

Natural language -> normalized constraint:
  {attribute, operator, value, unit, scope:{subject, context}, condition, quote}

Unit normalization is deterministic (time -> seconds, data -> bytes,
percent -> percent). Unknown units fall back to no numeric comparison
(LLM/scope path handled by the pipeline).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ai_engine.solvers.constraint_solver import normalize_unit_value

# ---------------------------------------------------------------- registry
ATTRIBUTE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "session_inactivity_timeout": {
        "unit_family": "time",
        "aliases": [
            "session timeout", "session_timeout", "idle timeout", "idle lock",
            "auto-lock", "autolock", "automatically lock", "lock after",
            "inactivity timeout", "timeout after inactivity", "log out after",
            "logged out", "remain logged in", "stay logged in",
            "session state", "session duration", "remain authenticated",
            "session expiry", "session expiration", "lock user sessions",
            "without activity", "of inactivity", "without auto-locking",
            "uninterrupted session",
        ],
    },
    "response_latency": {
        "unit_family": "time",
        "aliases": [
            "latency", "response time", "response times", "round-trip", "rtt",
            "render time", "load time", "within ms", "milliseconds",
            "processing time", "query time",
        ],
    },
    "throughput": {
        "unit_family": "rate",
        "aliases": ["throughput", "requests per second", "transactions per second",
                    "messages per second", "records per second", "mbps", "gbps"],
    },
    "availability_uptime": {
        "unit_family": "percent",
        "aliases": ["availability", "uptime", "availability of", "operational availability",
                    "service availability", "system availability"],
    },
    "backup_interval": {
        "unit_family": "time",
        "aliases": ["backup interval", "backed up every", "backup every", "backup frequency",
                    "snapshot every"],
    },
    "recovery_time_objective": {
        "unit_family": "time",
        "aliases": ["rto", "recovery time", "restore within", "recover within",
                    "recovery objective"],
    },
    "recovery_point_objective": {
        "unit_family": "time",
        "aliases": ["rpo", "data loss", "recovery point"],
    },
    "password_min_length": {
        "unit_family": "count",
        "aliases": ["password length", "password shall be at least", "minimum password",
                    "characters long", "character password"],
    },
    "max_concurrent_users": {
        "unit_family": "count",
        "aliases": ["concurrent users", "simultaneous users", "concurrent sessions",
                    "concurrent connections", "concurrent requests"],
    },
    "data_retention_period": {
        "unit_family": "time",
        "aliases": ["retention", "retain for", "retained for", "kept for",
                    "purged after", "deleted after"],
    },
    "encryption_algorithm": {
        "unit_family": "text",
        "aliases": ["encrypt", "encryption", "encrypted using", "cipher"],
    },
    "auth_factor_count": {
        "unit_family": "count",
        "aliases": ["multi-factor", "mfa", "two-factor", "2fa", "factors"],
    },
    "error_rate": {
        "unit_family": "percent",
        "aliases": ["error rate", "failure rate", "error percentage"],
    },
    "max_payload_size": {
        "unit_family": "data",
        "aliases": ["payload size", "file size", "message size", "attachment size",
                    "upload size", "max size"],
    },
}

UNIT_RE = r"(ms|milliseconds?|s|secs?|seconds?|min|mins|minutes?|h|hrs?|hours?|days?|weeks?|months?|kb|mb|gb|tb|kbytes?|mbytes?|gbytes?|%|percent|percentage|users|sessions|requests|characters|chars|connections|per second|per minute)"
NUM_RE = r"(\d+(?:\.\d+)?)"

OPERATOR_PATTERNS = [
    (re.compile(rf"(≤|=<|less than or equal to)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), "<="),
    (re.compile(rf"(≥|=>|greater than or equal to)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), ">="),
    (re.compile(rf"(?:exactly|equals?|is|=)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), "=="),
    (re.compile(rf"{NUM_RE}\s*{UNIT_RE}?\s*(?:or\s*less|or\s*fewer)", re.I), "<="),
    (re.compile(rf"(?:at\s*most|no\s*more\s*than|within|up\s*to|max(?:imum)?(?:\s*of)?)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), "<="),
    (re.compile(rf"{NUM_RE}\s*{UNIT_RE}?\s*(?:or\s*more|or\s*greater)", re.I), ">="),
    (re.compile(rf"(?:at\s*least|min(?:imum)?(?:\s*of)?|no\s*less\s*than)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), ">="),
    (re.compile(rf"(?:under|less\s*than|below|under\s*than)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), "<"),
    (re.compile(rf"(?:over|more\s*than|above|greater\s*than)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), ">"),
    (re.compile(rf"(?:after|in)\s*{NUM_RE}\s*(?:minutes?|min|hours?|h|seconds?|s|days?)\b(?:\s*of\s*(?:inactivity|idle|no\s*(?:activity|use)))?", re.I), "=="),
    (re.compile(rf"{NUM_RE}\s*{UNIT_RE}?\s*(?:or\s*between|-|to)\s*{NUM_RE}\s*{UNIT_RE}?", re.I), "between"),
]

CONDITION_RE = re.compile(
    r"\b(if|when|while|during|under|given|except|unless|for)\b\s+[^,.;]{3,70}", re.I)


def canonical_attribute(text: str) -> Optional[str]:
    tl = text.lower()
    best, best_hits = None, 0
    for canonical, meta in ATTRIBUTE_REGISTRY.items():
        hits = sum(1 for a in meta["aliases"] if a in tl)
        if canonical.replace("_", " ") in tl:
            hits += 2
        if hits > best_hits:
            best, best_hits = canonical, hits
    if best is None or best_hits == 0:
        return None
    return best


def _detect_scope(text: str) -> Dict[str, Optional[str]]:
    """
    Scope = who/what the constraint applies to. Deterministic subject check:
    admins vs clinical terminals vs all users etc. (PRD 20.5 scope check / G8)
    """
    tl = text.lower()
    subjects = []
    for name, pats in [
        ("administrator", ["administrator", "admin user", "admins", "administrators"]),
        ("clinical_terminal", ["clinical terminal", "clinician terminal", "clinician",
                               "doctor", "physician", "nursing", "patient bedside",
                               "bedside terminal", "medical device",
                               "telemetry workstation", "clinical workstation"]),
        ("standard_user", ["standard user", "regular user", "general user", "end user",
                           "end-user", "patient user"]),
        ("all_users", ["all users", "any user", "every user", "users", "user sessions",
                       "session", "sessions", "authenticated user"]),
    ]:
        for p in pats:
            if p in tl:
                subjects.append(name)
                break
    subject = subjects[0] if subjects else None
    if "all_users" in subjects and len(subjects) > 1:
        subject = "all_users"
    condition = None
    cm = CONDITION_RE.search(text)
    if cm:
        condition = re.sub(r"\s+", " ", cm.group(0)).strip().lower()
    return {"subject": subject, "context": None, "condition": condition}


def scopes_overlap(s1: Dict[str, Any], s2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic scope compatibility check (PRD 20.5 / G8).
    Semantics: two constraints are compared iff their populations INTERSECT.
    - named vs named distinct  -> disjoint (G8: admins vs clinical terminals)
    - universal ('all users'/unscoped) vs anything -> overlap
    Returns {equal: bool, confidence: float, note: str|None}
    """
    a = (s1 or {}).get("subject")
    b = (s2 or {}).get("subject")
    if a is None and b is None:
        # both unscoped: assume system-wide (same population), medium confidence
        return {"equal": True, "confidence": 0.7, "note": None}
    if a is None or b is None:
        # one unscoped: treat as universal -> overlaps the named population
        return {"equal": True, "confidence": 0.75, "note": None}
    if a == b:
        return {"equal": True, "confidence": 0.9, "note": None}
    if "all_users" in (a, b):
        # universal population contains every named population -> overlap
        return {"equal": True, "confidence": 0.9, "note": None}
    # distinct named populations (admins vs clinical) => do not compare
    return {"equal": False, "confidence": 0.85, "note": "possible_scope_mismatch"}


def extract_constraints(text: str) -> List[Dict[str, Any]]:
    """Extract normalized numeric constraints from a statement."""
    attribute = canonical_attribute(text)
    if attribute is None:
        return []
    family = ATTRIBUTE_REGISTRY[attribute]["unit_family"]
    scope = _detect_scope(text)
    found: List[Dict[str, Any]] = []
    seen = set()

    for pattern, op in OPERATOR_PATTERNS:
        for m in pattern.finditer(text):
            groups = [g for g in m.groups() if g is not None]
            nums = [g for g in groups if re.fullmatch(r"\d+(?:\.\d+)?", g)]
            if not nums:
                continue
            units = [g for g in groups if g and re.fullmatch(UNIT_RE, g, re.I)]
            if op == "between":
                if len(nums) < 2:
                    continue
                value = [float(nums[0]), float(nums[1])]
                unit = (units[0] if units else "")
            else:
                value = float(nums[0])
                unit = (units[0] if units else "")
            key = (op, str(value), unit)
            if key in seen:
                continue
            seen.add(key)
            quote = m.group(0).strip()
            if not unit:
                # some operator patterns capture the unit non-capturing; recover it
                um = re.search(UNIT_RE, quote, re.I)
                if um:
                    unit = um.group(0)
            entry: Dict[str, Any] = {
                "attribute": attribute,
                "operator": op,
                "value": value,
                "unit": unit,
                "unit_family": family,
                "scope": scope,
                "quote": quote,
            }
            if unit:
                norm_val, norm_unit = normalize_unit_value(
                    value if not isinstance(value, list) else value[0], unit)
                entry["normalized_value"] = norm_val
                entry["normalized_unit"] = norm_unit
                if op == "between" and isinstance(value, list) and len(value) == 2:
                    hi, hi_unit = normalize_unit_value(value[1], unit)
                    entry["normalized_value"] = [norm_val, hi]
            found.append(entry)
        if found:
            break  # first operator family that fires wins (avoid dup operators)
    return found
