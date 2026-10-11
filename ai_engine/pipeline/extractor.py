"""
Requirement extraction per PRD Section 20.3 (code first, LLM only for borderline).

A text unit is a requirement candidate if ANY of:
  1. It starts with an ID matching ^(REQ|FR|NFR|SR|SYS|UI|PERF|SEC)[-_ ]?\\d+[A-Za-z]?
  2. It sits in a requirements-ish section and is a full sentence
  3. It contains a modal verb (shall|must|should|will|may|can) with a subject

Excludes: headings, TOC lines, captions, Note:/Example:/Rationale: lines, glossary rows.
Continuation lines merge until next ID / heading / blank break.
Missing IDs are assigned REQ-### in document order (normalize step).
Compound requirements are flagged, never split.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

REQ_ID = re.compile(
    r"^\s*((?:REQ|FR|NFR|SR|SYS|UI|PERF|SEC|AUTH|IF|DF)[-_ ]?\d+[A-Za-z]?)\s*[.:\-)]?\s*(.*)$",
    re.IGNORECASE,
)
MODAL = re.compile(r"\b(shall|must|should|will|may|can|might|could)\b", re.IGNORECASE)
SUBJECT = re.compile(
    r"\b(system|user|users|application|platform|server|client|module|service|api|"
    r"interface|admin|administrator|database|browser|device|dashboard|portal)\b",
    re.IGNORECASE,
)
CAPTION = re.compile(r"^\s*(figure|fig\.|table|listing)\s*\d+", re.I)
NOTE_LINE = re.compile(r"^\s*(note|example|rationale|definition|glossary)\s*:", re.I)
HEADINGISH = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+[A-Z0-9].{0,80}$")
SECTION_KEYWORDS = re.compile(
    r"requirement|functional|non[- ]?functional|performance|security|interface|"
    r"constraint|system design|behavior|attribute|quality",
    re.IGNORECASE,
)
TOC_LINE = re.compile(r"\.{4,}\s*\d+\s*$")

COMPOUND_TWO_VERBS = re.compile(
    r"\b(shall|must|should)\b[^.;]{10,160}\b(shall|must|should)\b", re.IGNORECASE
)

TYPE_RULES: List[Tuple[str, re.Pattern]] = [
    ("performance", re.compile(r"latency|throughput|response time|availability|uptime|"
                               r"\bms\b|milliseconds|percent|concurrent|bandwidth|load", re.I)),
    ("security", re.compile(r"encrypt|decrypt|authenticat|authoriz|password|mfa|"
                            r"multi-factor|audit log|certificate|tls|aes|hash|lockout|session", re.I)),
    ("interface", re.compile(r"api|endpoint|interface|protocol|payload|format|json|xml|"
                             r"import|export|integrat|webhook|message bus", re.I)),
    ("constraint", re.compile(r"shall be|must be|constraint|limit|max(?:imum)? of|min(?:imum)? of|"
                              r"no more than|at least|compatib|standard|regulat", re.I)),
]


def classify_type(text: str, heading: str = "") -> str:
    """Rule-based requirement type classification (deterministic)."""
    blob = f"{heading} {text}"
    if re.search(r"non[- ]?functional", blob, re.I):
        return "Non-Functional"
    for category, pattern in TYPE_RULES:
        if pattern.search(blob):
            return "Non-Functional" if category in ("performance", "security") else "Functional"
    if MODAL.search(text):
        return "Functional"
    return "Functional"


def classify_category(text: str, heading: str = "") -> str:
    blob = f"{heading} {text}".lower()
    if "perform" in blob or "latency" in blob or "response time" in blob:
        return "Performance"
    if "secur" in blob or "auth" in blob or "password" in blob or "encrypt" in blob:
        return "Security & Auth"
    if "session" in blob or "timeout" in blob or "lock" in blob:
        return "Session Management"
    if "interfac" in blob or "api" in blob or "endpoint" in blob:
        return "Interfaces"
    if "data" in blob or "record" in blob or "store" in blob or "database" in blob:
        return "Data Management"
    if "usab" in blob or "user" in blob or "display" in blob or "ui" in blob:
        return "Usability / UI"
    if "backup" in blob or "recover" in blob or "availab" in blob:
        return "Availability / Recovery"
    return heading.strip() or "General"


def _is_candidate(text: str, kind: str, heading: str) -> Dict[str, Any]:
    """Decide whether a block is a requirement candidate; return rule that fired."""
    t = text.strip()
    if not t or len(t) < 15:
        return {"candidate": False}
    if kind == "heading":
        return {"candidate": False}
    if CAPTION.match(t) or NOTE_LINE.match(t) or TOC_LINE.search(t):
        return {"candidate": False}
    if HEADINGISH.match(t) and not MODAL.search(t) and not t.endswith("."):
        return {"candidate": False}
    # ends as a sentence?
    is_sentence = bool(re.search(r"[.!?]$", t)) or kind == "table_row"

    m_id = REQ_ID.match(t)
    if m_id:
        return {"candidate": True, "rule": "id", "code": m_id.group(1).upper().replace(" ", "-").replace("_", "-")}

    has_modal = bool(MODAL.search(t))
    has_subject = bool(SUBJECT.search(t))
    in_section = bool(SECTION_KEYWORDS.search(heading))

    if has_modal and has_subject and is_sentence:
        return {"candidate": True, "rule": "modal"}
    if in_section and is_sentence and has_modal:
        return {"candidate": True, "rule": "section"}
    if in_section and is_sentence and len(t) > 40 and t[0].isupper():
        return {"candidate": True, "rule": "section_sentence", "borderline": True}
    return {"candidate": False}


def extract_requirements(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns normalized requirement dicts:
      {code (maybe None), text, section_number, heading, page, type,
       category, compound, extraction_rule, borderline}
    """
    blocks: List[Dict[str, Any]] = parsed.get("blocks", [])
    out: List[Dict[str, Any]] = []

    i = 0
    n = len(blocks)
    while i < n:
        blk = blocks[i]
        text = blk["text"].strip()
        verdict = _is_candidate(text, blk.get("kind", "text"), blk.get("heading", ""))
        if not verdict.get("candidate"):
            i += 1
            continue

        code = verdict.get("code")
        body = text
        if code:
            body = REQ_ID.match(text).group(2).strip() or text

        # merge continuation lines: plain text blocks with no modal/ID, until blank/heading
        j = i + 1
        while j < n:
            nxt = blocks[j]
            if nxt.get("kind") == "heading":
                break
            nt = nxt["text"].strip()
            if not nt or NOTE_LINE.match(nt) or CAPTION.match(nt):
                break
            if REQ_ID.match(nt) or MODAL.search(nt):
                # a fresh candidate starts
                if REQ_ID.match(nt) or _is_candidate(nt, nxt.get("kind", "text"), nxt.get("heading", "")).get("candidate"):
                    break
            if len(nt) < 120 and not nt.endswith("."):
                body = f"{body} {nt}".strip()
                j += 1
                continue
            if len(nt) < 200 and not re.match(r"^\d", nt):
                body = f"{body} {nt}".strip()
                j += 1
                continue
            break

        body = re.sub(r"\s+", " ", body).strip()
        if len(body) < 15:
            i = j if j > i else i + 1
            continue

        compound = bool(COMPOUND_TWO_VERBS.search(body))
        out.append(
            {
                "code": code,
                "text": body,
                "section_number": blk.get("section_number") or "",
                "heading": blk.get("heading") or "",
                "page": blk.get("page"),
                "type": classify_type(body, blk.get("heading") or ""),
                "category": classify_category(body, blk.get("heading") or ""),
                "compound": compound,
                "extraction_rule": verdict.get("rule", "unknown"),
                "borderline": bool(verdict.get("borderline")),
            }
        )
        i = j if j > i else i + 1

    # dedupe identical texts
    seen = set()
    deduped = []
    for r in out:
        key = r["text"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped


def normalize_requirements(reqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assign REQ-### codes in document order when missing; keep existing IDs."""
    used = {r["code"] for r in reqs if r.get("code")}
    next_num = 1
    for r in reqs:
        if r.get("code"):
            # normalize separator style
            r["code"] = re.sub(r"^(REQ|FR|NFR|SR|SYS|UI|PERF|SEC)[-_ ]", lambda m: m.group(1) + "-", r["code"].upper())
            continue
        while f"REQ-{next_num:03d}" in used:
            next_num += 1
        r["code"] = f"REQ-{next_num:03d}"
        used.add(r["code"])
        next_num += 1
    return reqs
