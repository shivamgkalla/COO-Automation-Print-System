"""
field_validator.py
------------------
Sanity-checks template field coordinates and transaction data before
generating an overlay, returning a list of warning strings.
"""
from __future__ import annotations

from typing import List

from config import A4_WIDTH_PT, A4_HEIGHT_PT
from core.models import Template, COOTransaction


def validate_template(template: Template) -> List[str]:
    warnings: List[str] = []
    for field in template.fields:
        x, y, w, h = field.pdf_bbox
        if x < 0 or y < 0:
            warnings.append(f"Field '{field.field_id}' has negative coordinates (x={x}, y={y})")
        if x + w > template.page_width_pt + 5:
            warnings.append(f"Field '{field.field_id}' extends beyond page width")
        if y + h > template.page_height_pt + 5:
            warnings.append(f"Field '{field.field_id}' extends beyond page height")
        if w <= 0 or h <= 0:
            warnings.append(f"Field '{field.field_id}' has zero or negative size (w={w}, h={h})")
    return warnings


def validate_transaction(transaction: COOTransaction, template: Template) -> List[str]:
    warnings: List[str] = []

    if not transaction.certificate_no:
        warnings.append("Certificate number is empty")
    if not transaction.exporter:
        warnings.append("Exporter field is empty")
    if not transaction.consignee:
        warnings.append("Consignee field is empty")
    if not transaction.table_rows:
        warnings.append("No goods rows in the table (fields 6–12)")
    if transaction.output_mode == "internal":
        for i, row in enumerate(transaction.table_rows):
            if not row.invoice_number:
                warnings.append(f"Row {i+1}: invoice number is missing (internal mode)")

    return warnings
