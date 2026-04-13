"""
scan_preprocessor.py
--------------------
Deskew and perspective-correct a scanned COO form image so it is a clean,
upright A4 rectangle ready for field-coordinate mapping.

Input : file path to a PNG/JPG scan or a PDF (first page extracted)
Output: numpy array (BGR) of the corrected image at 300 DPI equivalent
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from config import SCAN_DPI, SCANS_DIR


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess_scan(source: Path | str, save_as: Optional[str] = None) -> np.ndarray:
    """
    Load, deskew, and perspective-correct a scan.

    Parameters
    ----------
    source   : path to an image file (.png/.jpg) or PDF (.pdf)
    save_as  : if given, save the corrected image to scans/<save_as>.png

    Returns
    -------
    BGR numpy array of the corrected A4 image
    """
    source = Path(source)
    img = _load_image(source)
    corrected = _correct_perspective(img)

    if save_as:
        SCANS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = SCANS_DIR / f"{save_as}.png"
        cv2.imwrite(str(out_path), corrected)

    return corrected


def image_dimensions(img: np.ndarray) -> tuple[int, int]:
    """Return (width_px, height_px)."""
    h, w = img.shape[:2]
    return w, h


def numpy_to_pil(img: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_image(source: Path) -> np.ndarray:
    if source.suffix.lower() == ".pdf":
        return _pdf_first_page(source)
    img = cv2.imread(str(source))
    if img is None:
        raise ValueError(f"Cannot read image: {source}")
    return img


def _pdf_first_page(path: Path) -> np.ndarray:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("pdf2image is required to process PDF scans: pip install pdf2image")
    pages = convert_from_path(str(path), dpi=SCAN_DPI, first_page=1, last_page=1)
    pil_img = pages[0].convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _correct_perspective(img: np.ndarray) -> np.ndarray:
    """
    Detect the document boundary (largest quadrilateral) and apply a
    perspective transform so the result is a flat upright rectangle.
    Falls back to the original image if detection fails.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Dilate to close small gaps in the document border
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img

    # Largest contour by area
    largest = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

    if len(approx) != 4:
        # Cannot find a clean quad; return deskewed version only
        return _deskew(img)

    corners = _order_corners(approx.reshape(4, 2).astype(np.float32))
    return _four_point_transform(img, corners)


def _deskew(img: np.ndarray) -> np.ndarray:
    """Minimal deskew using minimum area rectangle of largest contour."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Order corners: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left: smallest sum
    rect[2] = pts[np.argmax(s)]   # bottom-right: largest sum
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right: smallest diff
    rect[3] = pts[np.argmax(diff)]  # bottom-left: largest diff
    return rect


def _four_point_transform(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    tl, tr, br, bl = corners
    width = int(max(
        np.linalg.norm(br - bl),
        np.linalg.norm(tr - tl),
    ))
    height = int(max(
        np.linalg.norm(tr - br),
        np.linalg.norm(tl - bl),
    ))
    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1],
    ], dtype=np.float32)
    M = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(img, M, (width, height))
