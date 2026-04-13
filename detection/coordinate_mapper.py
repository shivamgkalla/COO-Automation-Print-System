"""
coordinate_mapper.py
--------------------
Converts bounding-box coordinates between scan-pixel space and
ReportLab PDF-point space.

ReportLab uses a bottom-left origin, so Y must be flipped:
    pdf_y = page_height_pt - (scan_y + scan_h) * scale_y

All bbox lists follow [x, y, w, h] convention.
"""
from __future__ import annotations

from typing import List

from config import A4_WIDTH_PT, A4_HEIGHT_PT


def scan_bbox_to_pdf(
    scan_bbox: List[float],
    scan_width_px: int,
    scan_height_px: int,
    page_width_pt: float = A4_WIDTH_PT,
    page_height_pt: float = A4_HEIGHT_PT,
) -> List[float]:
    """
    Convert a [x, y, w, h] bounding box from scan-pixel coords to PDF points.

    Parameters
    ----------
    scan_bbox      : [x, y, w, h] in pixels (top-left origin)
    scan_width_px  : full scan image width in pixels
    scan_height_px : full scan image height in pixels
    page_width_pt  : PDF page width in points (default A4)
    page_height_pt : PDF page height in points (default A4)

    Returns
    -------
    [x, y, w, h] in PDF points (bottom-left origin)
    """
    x, y, w, h = scan_bbox
    scale_x = page_width_pt / scan_width_px
    scale_y = page_height_pt / scan_height_px

    pdf_x = x * scale_x
    pdf_w = w * scale_x
    pdf_h = h * scale_y
    # Flip Y: top-left scan origin → bottom-left PDF origin
    pdf_y = page_height_pt - (y + h) * scale_y

    return [pdf_x, pdf_y, pdf_w, pdf_h]


def pdf_bbox_to_scan(
    pdf_bbox: List[float],
    scan_width_px: int,
    scan_height_px: int,
    page_width_pt: float = A4_WIDTH_PT,
    page_height_pt: float = A4_HEIGHT_PT,
) -> List[float]:
    """Inverse of scan_bbox_to_pdf — for UI display purposes."""
    x, y, w, h = pdf_bbox
    scale_x = scan_width_px / page_width_pt
    scale_y = scan_height_px / page_height_pt

    scan_x = x * scale_x
    scan_w = w * scale_x
    scan_h = h * scale_y
    # Flip Y back
    scan_y = (page_height_pt - y - h) * scale_y

    return [scan_x, scan_y, scan_w, scan_h]


def apply_printer_offset(
    pdf_bbox: List[float],
    offset_x: float,
    offset_y: float,
) -> List[float]:
    """
    Shift a pdf_bbox by the global printer calibration offset.
    offset_x positive = move right, offset_y positive = move up.
    """
    x, y, w, h = pdf_bbox
    return [x + offset_x, y + offset_y, w, h]
