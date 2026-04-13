"""
text_formatter.py
-----------------
Word-wrap and auto font-shrink logic that ensures text always fits
within a field's bounding box without manual fine-tuning.

Strategy:
1. Wrap text at max_chars_per_line using the configured font size.
2. If wrapped lines exceed max_lines OR any line is wider than the box,
   reduce font size by 0.5pt steps down to MIN_FONT_SIZE and re-wrap
   with the proportionally wider char budget.
3. Return (lines, actual_font_size) so the caller can draw at the
   correct size.
"""
from __future__ import annotations

import textwrap
from typing import List, Tuple

from reportlab.pdfbase.pdfmetrics import stringWidth

from core.models import TemplateField, TableColumnDef

MIN_FONT_SIZE = 6.0   # never go below this (below 6pt is barely legible)
FONT_SIZE_STEP = 0.5  # shrink increment


def wrap_field(text: str, field: TemplateField) -> Tuple[List[str], float]:
    """
    Wrap text for a TemplateField, auto-shrinking font if needed.

    Returns
    -------
    (lines, font_size)  — draw all lines at font_size
    """
    return _fit(
        text,
        font_name=field.font_name,
        font_size=field.font_size,
        box_width=field.pdf_bbox[2],
        box_height=field.pdf_bbox[3],
        max_lines=field.max_lines,
    )


def wrap_column(text: str, col: TableColumnDef, row_height: float) -> Tuple[List[str], float]:
    """
    Wrap text for a table column, auto-shrinking font if needed.

    Returns
    -------
    (lines, font_size)
    """
    return _fit(
        text,
        font_name=col.font_name,
        font_size=col.font_size,
        box_width=col.width_pt,
        box_height=row_height,
        max_lines=None,   # determined by box height
    )


# ---------------------------------------------------------------------------
# Core fitting engine
# ---------------------------------------------------------------------------

def _fit(
    text: str,
    font_name: str,
    font_size: float,
    box_width: float,
    box_height: float,
    max_lines: int | None,
) -> Tuple[List[str], float]:
    """
    Try wrapping at font_size; if it doesn't fit, shrink and retry.
    Returns (lines, actual_font_size).
    """
    if not text:
        return [], font_size

    size = font_size
    while size >= MIN_FONT_SIZE:
        lines = _wrap_at_size(text, font_name, size, box_width)
        line_height = size * 1.3
        max_by_height = max(1, int(box_height / line_height))
        effective_max = min(max_lines, max_by_height) if max_lines else max_by_height

        if len(lines) <= effective_max:
            return lines[:effective_max], size

        size -= FONT_SIZE_STEP

    # Last resort: clamp to min size, truncate lines
    lines = _wrap_at_size(text, font_name, MIN_FONT_SIZE, box_width)
    line_height = MIN_FONT_SIZE * 1.3
    max_by_height = max(1, int(box_height / line_height))
    effective_max = min(max_lines, max_by_height) if max_lines else max_by_height
    return lines[:effective_max], MIN_FONT_SIZE


def _wrap_at_size(text: str, font_name: str, font_size: float, box_width: float) -> List[str]:
    """
    Wrap text so no line exceeds box_width points at the given font size.
    Uses character-count wrapping as primary method, then trims any line
    that still overflows by splitting it further.
    """
    # Estimate chars that fit: use 'M' width as conservative measure
    try:
        char_w = stringWidth("M", font_name, font_size)
        max_chars = max(1, int(box_width / char_w))
    except Exception:
        max_chars = max(1, int(box_width / (font_size * 0.6)))

    paragraphs = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: List[str] = []
    for para in paragraphs:
        if not para.strip():
            continue
        wrapped = textwrap.wrap(para, width=max_chars, break_long_words=True)
        lines.extend(wrapped if wrapped else [""])

    # Second pass: split any line that still physically overflows
    final: List[str] = []
    for line in lines:
        while stringWidth(line, font_name, font_size) > box_width and len(line) > 1:
            # Binary-search the cut point
            lo, hi = 1, len(line)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if stringWidth(line[:mid], font_name, font_size) <= box_width:
                    lo = mid
                else:
                    hi = mid - 1
            final.append(line[:lo])
            line = line[lo:]
        final.append(line)

    return final
