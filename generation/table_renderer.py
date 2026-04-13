"""
table_renderer.py
-----------------
Renders the goods table (fields 6–12) onto a ReportLab canvas.

Each row's Y position is calculated from the template's table_layout:
  row_y = first_data_row_y_pt - (row_index * row_height_pt)

Invoice value is omitted when output_mode == "pre_customs".
Font size is auto-shrunk per cell so content always fits.
"""
from __future__ import annotations

from reportlab.pdfgen.canvas import Canvas

from core.models import COOTransaction, TableLayout
from generation.text_formatter import wrap_column


def render_table(
    canvas: Canvas,
    transaction: COOTransaction,
    layout: TableLayout,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> None:
    is_pre_customs = transaction.output_mode == "pre_customs"

    for row_idx, row in enumerate(transaction.table_rows):
        row_top_y = layout.first_data_row_y_pt - (row_idx * layout.row_height_pt) + offset_y
        row_data = _build_row_data(row, is_pre_customs)

        for col in layout.columns:
            cell_text = row_data.get(col.field_id, "")
            if not cell_text:
                continue

            lines, actual_size = wrap_column(cell_text, col, layout.row_height_pt)
            cell_x = col.x_pt + offset_x
            line_height = actual_size * 1.3
            text_y = row_top_y - actual_size

            row_bottom_y = row_top_y - layout.row_height_pt
            for line in lines:
                if text_y < row_bottom_y:  # hard clip — never draw below row
                    break
                canvas.setFont(col.font_name, actual_size)
                if col.align == "center":
                    canvas.drawCentredString(cell_x + col.width_pt / 2, text_y, line)
                elif col.align == "right":
                    canvas.drawRightString(cell_x + col.width_pt, text_y, line)
                else:
                    canvas.drawString(cell_x, text_y, line)
                text_y -= line_height


def _build_row_data(row, is_pre_customs: bool) -> dict:
    weight_parts = []
    if row.gross_weight:
        weight_parts.append(f"GW: {row.gross_weight}")
    if row.net_weight:
        weight_parts.append(f"NW: {row.net_weight}")
    weight_str = "\n".join(weight_parts)

    if is_pre_customs:
        invoice_str = ""
    else:
        invoice_parts = []
        if row.invoice_number:
            invoice_parts.append(row.invoice_number)
        if row.invoice_date:
            invoice_parts.append(row.invoice_date)
        if row.invoice_value:
            invoice_parts.append(row.invoice_value)
        invoice_str = "\n".join(invoice_parts)

    return {
        "item_number": row.item_number,
        "marks_packages": row.marks_packages,
        "description": row.description,
        "hs_code": row.hs_code,
        "origin_criterion": row.origin_criterion,
        "net_weight": weight_str,
        "invoice_ref": invoice_str,
    }
