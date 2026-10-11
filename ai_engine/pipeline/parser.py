"""
Document parsing per PRD Section 20.2.

PDF  -> PyMuPDF: text blocks per page, heading detection from font size,
        repeated header/footer removal, TOC skip, scanned-PDF rejection.
DOCX -> python-docx: paragraph styles Heading 1-n, tables row by row,
        page numbers are null (section numbers instead).

Output contract:
{
  "filename": str,
  "page_count": int,
  "sections": [{"number": "2.1", "heading": str, "level": int,
                "page_start": int, "page_end": int}],
  "blocks":   [{"text": str, "heading": str, "section_number": str,
                "page": int|None, "kind": "text"|"table_row"|"heading"}],
  "avg_chars_per_page": float,
}
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------- constants
TOC_DOT_LEADER = re.compile(r"\.{4,}\s*\d+\s*$")
NUMBERED_HEADING = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+([A-Z0-9].{0,80})$")
CAPTION = re.compile(r"^\s*(figure|fig\.|table|listing)\s*\d+", re.I)
NOTE_PREFIX = re.compile(r"^\s*(note|example|rationale)\s*:", re.I)


class ParseError(Exception):
    """Raised when a document cannot be parsed (e.g. scanned PDF)."""


# ---------------------------------------------------------------- helpers
def _split_sections(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a section tree from numbered headings / heading levels."""
    sections: List[Dict[str, Any]] = []
    for line in lines:
        if line.get("kind") != "heading":
            continue
        text = line["text"].strip()
        number = line.get("section_number") or ""
        level = line.get("level") or (len(number.split(".")) if number else 1)
        sections.append(
            {
                "number": number,
                "heading": text,
                "level": int(level),
                "page_start": line.get("page"),
                "page_end": line.get("page"),
            }
        )
    # extend page_end up to the next section at same-or-higher level
    for i, sec in enumerate(sections):
        end = sec["page_start"]
        for nxt in sections[i + 1:]:
            if nxt["level"] <= sec["level"]:
                break
            if nxt.get("page"):
                end = max(end or 0, nxt["page"])
        sec["page_end"] = end
    return sections


def _reject_if_scanned(pages_text: List[str], filename: str) -> None:
    total_chars = sum(len(p.strip()) for p in pages_text)
    n = max(1, len(pages_text))
    if total_chars / n < 200:
        raise ParseError(
            f"'{filename}' appears to be a scanned document (no text layer). "
            "Version 1 requires a text-based PDF or DOCX."
        )


# ---------------------------------------------------------------- PDF
def parse_pdf(path: str) -> Dict[str, Any]:
    import pymupdf  # PyMuPDF

    doc = pymupdf.open(path)
    if doc.needs_pass:
        doc.close()
        raise ParseError(f"'{Path(path).name}' is password protected / encrypted.")

    pages_text: List[str] = []
    raw_blocks: List[Dict[str, Any]] = []
    font_sizes: List[float] = []

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        # dict mode gives spans with font sizes for heading detection
        data = page.get_text("dict")
        page_lines: Dict[int, Dict[str, Any]] = {}
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(s.get("text", "") for s in spans).strip()
                if not text:
                    continue
                size = max(s.get("size", 0) for s in spans)
                bold = any("bold" in s.get("font", "").lower() for s in spans)
                key = round(line["bbox"][1], 1)
                entry = page_lines.setdefault(
                    key, {"text": "", "size": size, "bold": bold}
                )
                entry["text"] = (entry["text"] + " " + text).strip()
                entry["size"] = max(entry["size"], size)
                entry["bold"] = entry["bold"] or bold
        for key in sorted(page_lines):
            entry = page_lines[key]
            raw_blocks.append(
                {
                    "text": entry["text"],
                    "size": entry["size"],
                    "bold": entry["bold"],
                    "page": page_index + 1,
                }
            )
            font_sizes.append(entry["size"])
        pages_text.append(page.get_text("text"))
    doc.close()

    _reject_if_scanned(pages_text, Path(path).name)

    # body text size = most common font size; headings are noticeably larger
    body_size = max(set(round(s, 1) for s in font_sizes), key=font_sizes.count) if font_sizes else 11.0

    # repeated header/footer removal: text lines repeating on >=60% of pages
    page_count = max(1, len(pages_text))
    line_pages: Dict[str, set] = {}
    for idx, ptext in enumerate(pages_text):
        for ln in ptext.splitlines():
            s = ln.strip()
            if len(s) > 3:
                line_pages.setdefault(s, set()).add(idx)
    repeated = {s for s, pgs in line_pages.items() if len(pgs) / page_count >= 0.6}

    blocks: List[Dict[str, Any]] = []
    current_heading = ""
    current_section = ""
    for blk in raw_blocks:
        text = blk["text"]
        if text in repeated:
            continue
        if TOC_DOT_LEADER.search(text):
            continue
        is_caption = bool(CAPTION.match(text))
        is_heading = (
            not is_caption
            and (blk["size"] >= body_size + 1.5 or (blk["bold"] and blk["size"] >= body_size + 0.5))
            and len(text) < 100
            and not text.endswith((".", ",", ";"))
        )
        number = ""
        m = NUMBERED_HEADING.match(text)
        if m and len(m.group(2)) < 90:
            number = m.group(1)
        if is_heading:
            current_heading = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", text).strip() or text
            current_section = number or current_section
            blocks.append(
                {
                    "text": text,
                    "heading": current_heading,
                    "section_number": number or current_section,
                    "page": blk["page"],
                    "kind": "heading",
                    "section_number_raw": number,
                }
            )
            continue
        blocks.append(
            {
                "text": text,
                "heading": current_heading,
                "section_number": current_section,
                "page": blk["page"],
                "kind": "text",
            }
        )

    return {
        "filename": Path(path).name,
        "page_count": page_count,
        "sections": _split_sections(blocks),
        "blocks": blocks,
        "avg_chars_per_page": round(sum(len(p) for p in pages_text) / page_count, 1),
        "pages_text": pages_text,
    }


# ---------------------------------------------------------------- DOCX
def parse_docx(path: str) -> Dict[str, Any]:
    import docx  # python-docx

    document = docx.Document(path)
    blocks: List[Dict[str, Any]] = []
    current_heading = ""
    current_section = ""

    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower()
        is_heading = style.startswith("heading")
        level = 1
        if is_heading:
            m = re.search(r"(\d+)", style)
            level = int(m.group(1)) if m else 1
        number = ""
        m2 = NUMBERED_HEADING.match(text)
        if m2:
            number = m2.group(1)
            if not is_heading:
                # numbered line that looks like a heading
                is_heading = len(text) < 100 and not text.endswith((".", ",", ";"))
        if is_heading:
            current_heading = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", text).strip() or text
            current_section = number or current_section
            blocks.append(
                {
                    "text": text,
                    "heading": current_heading,
                    "section_number": number or current_section,
                    "page": None,
                    "kind": "heading",
                    "level": level,
                    "section_number_raw": number,
                }
            )
        else:
            blocks.append(
                {
                    "text": text,
                    "heading": current_heading,
                    "section_number": current_section,
                    "page": None,
                    "kind": "text",
                }
            )

    # tables: header containing ID + Requirement/Description => rows are requirements
    for table in document.tables:
        rows = [[c.text.strip() for c in row.cells] for row in table.rows]
        if not rows:
            continue
        header = [h.lower() for h in rows[0]]
        id_col = next((i for i, h in enumerate(header) if h in ("id", "req id", "requirement id", "req")), None)
        text_col = next(
            (i for i, h in enumerate(header) if any(k in h for k in ("requirement", "description", "statement", "text"))),
            None,
        )
        if id_col is None or text_col is None:
            # store as plain rows anyway (still useful provenance)
            for r in rows[1:]:
                joined = " | ".join(r).strip()
                if joined:
                    blocks.append(
                        {
                            "text": joined,
                            "heading": current_heading,
                            "section_number": current_section,
                            "page": None,
                            "kind": "table_row",
                        }
                    )
            continue
        for r in rows[1:]:
            if len(r) <= max(id_col, text_col):
                continue
            body = f"{r[id_col]} {r[text_col]}".strip()
            if body:
                blocks.append(
                    {
                        "text": body,
                        "heading": current_heading,
                        "section_number": current_section,
                        "page": None,
                        "kind": "table_row",
                    }
                )

    text_only = [b["text"] for b in blocks if b["kind"] != "heading"]
    avg = sum(len(t) for t in text_only) / max(1, len(text_only))
    if avg < 40 and len(text_only) < 5:
        raise ParseError(f"'{Path(path).name}' contains no readable paragraph text.")

    return {
        "filename": Path(path).name,
        "page_count": None,
        "sections": _split_sections(blocks),
        "blocks": blocks,
        "avg_chars_per_page": round(avg, 1),
        "pages_text": [],
    }


def parse_document(path: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Dispatch by extension; validates magic bytes loosely by suffix."""
    name = filename or Path(path).name
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(path)
    if ext == ".docx":
        return parse_docx(path)
    raise ParseError(f"Unsupported file type '{ext}'. Allowed: .pdf, .docx")
