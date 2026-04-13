from pathlib import Path

BASE_DIR = Path(__file__).parent

TEMPLATES_DIR = BASE_DIR / "templates"
SCANS_DIR = BASE_DIR / "scans"
# On Render free tier (and any read-only filesystem), use /tmp for generated PDFs.
# Locally, use the output/ folder inside the project.
import os
_local_output = BASE_DIR / "output"
OUTPUT_DIR = _local_output if _local_output.exists() and os.access(_local_output, os.W_OK) else Path("/tmp/coo_output")

# A4 dimensions in ReportLab points (1 pt = 1/72 inch)
A4_WIDTH_PT = 595.28
A4_HEIGHT_PT = 841.89

# Standard internal DPI for scan processing
SCAN_DPI = 300

# Default template file shipped with the app
DEFAULT_TEMPLATE_ID = "gacc_coo_default"

# Global printer calibration offsets (points).
# Increase PRINTER_OFFSET_X to shift all text right.
# Increase PRINTER_OFFSET_Y to shift all text up.
PRINTER_OFFSET_X: float = 0.0
PRINTER_OFFSET_Y: float = 0.0
