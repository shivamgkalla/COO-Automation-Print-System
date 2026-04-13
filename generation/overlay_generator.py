"""
overlay_generator.py
--------------------
Generates a print-ready overlay PDF using ReportLab.

The PDF contains ONLY text objects (no background fill), so when the
physical pre-printed COO form is fed through the printer, the printer
deposits only the typed data at the correct positions.

Stamp/signature areas (blank_always=True) are never written.
Invoice value is omitted in pre_customs mode.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

import config
from core.models import COOTransaction, Template
from core.template_manager import load_template
from generation.text_formatter import wrap_field
from generation.table_renderer import render_table


def generate_overlay(
    transaction: COOTransaction,
    output_path: Path | str,
    template: Optional[Template] = None,
    offset_x: Optional[float] = None,
    offset_y: Optional[float] = None,
) -> Path:
    """
    Generate an overlay PDF for the given transaction.

    Parameters
    ----------
    transaction  : filled COOTransaction
    output_path  : where to write the output PDF
    template     : Template object; loaded from disk if None
    offset_x/y   : printer calibration offsets in points (defaults to config)

    Returns
    -------
    Path to the generated PDF
    """
    if template is None:
        template = load_template(transaction.template_id)

    if offset_x is None:
        offset_x = config.PRINTER_OFFSET_X
    if offset_y is None:
        offset_y = config.PRINTER_OFFSET_Y

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    canvas = Canvas(
        str(output_path),
        pagesize=(template.page_width_pt, template.page_height_pt),
    )
    canvas.setFillColorRGB(0, 0, 0)  # black text

    _draw_fields(canvas, transaction, template, offset_x, offset_y)

    if template.table_layout and transaction.table_rows:
        render_table(canvas, transaction, template.table_layout, offset_x, offset_y)

    canvas.save()
    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _draw_fields(
    canvas: Canvas,
    transaction: COOTransaction,
    template: Template,
    offset_x: float,
    offset_y: float,
) -> None:
    is_pre_customs = transaction.output_mode == "pre_customs"

    for field in template.fields:
        if field.blank_always:
            continue
        if field.field_id == "invoice_ref" and is_pre_customs:
            continue

        value = transaction.get_field_value(field.field_id)
        if not value:
            continue

        lines, actual_size = wrap_field(value, field)
        if not lines:
            continue

        x = field.pdf_bbox[0] + offset_x
        # pdf_bbox y is bottom of box; we draw from near the top
        box_bottom_y = field.pdf_bbox[1] + offset_y
        box_top_y = box_bottom_y + field.pdf_bbox[3]
        line_height = actual_size * 1.3
        text_y = box_top_y - actual_size

        for line in lines:
            if text_y < box_bottom_y:  # hard clip — never draw below box
                break
            canvas.setFont(field.font_name, actual_size)
            canvas.drawString(x, text_y, line)
            text_y -= line_height
