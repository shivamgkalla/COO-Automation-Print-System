"""
Page 01 — Template Setup
Upload a scan → deskew → manually define field positions → save as template.

If using the standard GACC COO form, staff can skip this page entirely
and use the pre-calibrated 'gacc_coo_default' template.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile

import cv2
import streamlit as st
from PIL import Image

from config import SCANS_DIR, A4_WIDTH_PT, A4_HEIGHT_PT
from core.models import Template, TemplateField, TableLayout, TableColumnDef
from core.template_manager import save_template, template_exists
from detection.scan_preprocessor import preprocess_scan, image_dimensions, numpy_to_pil
from detection.coordinate_mapper import scan_bbox_to_pdf

st.set_page_config(page_title="Template Setup", layout="wide")
st.title("Template Setup")
st.caption(
    "Use this page only if your physical form has a **different layout** from the standard GACC COO form. "
    "For the standard form, the default template is already ready — go to **New Transaction** directly."
)

# ---------------------------------------------------------------------------
# Step 1: Upload scan
# ---------------------------------------------------------------------------
st.header("Step 1 — Upload a blank form scan")
uploaded = st.file_uploader("Upload PNG, JPG, or PDF scan of the blank physical form", type=["png", "jpg", "jpeg", "pdf"])

if not uploaded:
    st.info("Upload a scan of the blank COO form to begin.")
    st.stop()

with tempfile.NamedTemporaryFile(suffix=Path(uploaded.name).suffix, delete=False) as tmp:
    tmp.write(uploaded.read())
    tmp_path = Path(tmp.name)

with st.spinner("Processing scan..."):
    try:
        img = preprocess_scan(tmp_path)
    except Exception as e:
        st.error(f"Failed to process scan: {e}")
        st.stop()

w_px, h_px = image_dimensions(img)
pil_img = numpy_to_pil(img)

st.success(f"Scan processed: {w_px} × {h_px} px")
st.image(pil_img, caption="Corrected scan (use this as reference for coordinates)", use_column_width=True)

# ---------------------------------------------------------------------------
# Step 2: Template metadata
# ---------------------------------------------------------------------------
st.header("Step 2 — Template details")
col1, col2 = st.columns(2)
with col1:
    template_id = st.text_input("Template ID (no spaces)", value="my_coo_template_v1")
with col2:
    template_name = st.text_input("Template name", value="Custom COO Form v1")

# ---------------------------------------------------------------------------
# Step 3: Define field positions
# ---------------------------------------------------------------------------
st.header("Step 3 — Define field bounding boxes")
st.markdown(
    "For each field, enter its position on the **scan image** in pixels `[x, y, width, height]` "
    "(top-left origin). Coordinates are auto-converted to PDF points."
)
st.markdown("Use an image viewer (e.g. Preview → Tools → Show Inspector) to measure pixel coordinates.")

FIELD_DEFS = [
    ("cert_no",           "Certificate No.",               False, 1,  30),
    ("field_1_exporter",  "1. Exporter (name + address)",  False, 5,  42),
    ("field_2_producer",  "2. Producer (name + address)",  False, 5,  42),
    ("field_3_consignee", "3. Consignee (name + address)", False, 6,  42),
    ("issued_in",         "Issued in (country)",           False, 1,  30),
    ("field_4_means",     "4. Means of transport",         False, 1,  15),
    ("field_4_date",      "Departure Date",                False, 1,  20),
    ("field_4_vessel",    "Vessel/Flight No.",             False, 1,  42),
    ("field_4_pol",       "Port of Loading",               False, 1,  42),
    ("field_4_pod",       "Port of Discharge",             False, 1,  42),
    ("field_5_remarks",   "5. Remarks",                    False, 3,  38),
    ("field_13_country",  "Declaration country (field 13 dotted line)", False, 1, 30),
    ("page_total",        "Page total (after 'Page 1 of')", False, 1, 5),
]

field_entries = {}
for fid, label, blank, max_lines, max_chars in FIELD_DEFS:
    with st.expander(f"{label} [{fid}]", expanded=False):
        cols = st.columns([1, 1, 1, 1, 1, 1])
        x   = cols[0].number_input("x (px)", key=f"{fid}_x",   min_value=0, value=0)
        y   = cols[1].number_input("y (px)", key=f"{fid}_y",   min_value=0, value=0)
        w   = cols[2].number_input("w (px)", key=f"{fid}_w",   min_value=1, value=100)
        h   = cols[3].number_input("h (px)", key=f"{fid}_h",   min_value=1, value=30)
        fs  = cols[4].number_input("Font pt", key=f"{fid}_fs", min_value=4.0, max_value=20.0, value=8.0)
        bold = cols[5].checkbox("Bold", key=f"{fid}_bold", value=(fid == "cert_no"))
        field_entries[fid] = dict(x=x, y=y, w=w, h=h, font_size=fs, bold=bold,
                                  max_lines=max_lines, max_chars=max_chars)

# Table layout
st.subheader("Table layout (fields 6–12)")
t_col1, t_col2 = st.columns(2)
with t_col1:
    first_row_y_px = st.number_input("Y of first data row (px, top-left origin)", min_value=0, value=1000)
    row_height_px  = st.number_input("Row height (px)", min_value=5, value=80)
with t_col2:
    st.markdown("Column start X positions (px)")
    col_x = {
        "item_number":     st.number_input("Item No. x", min_value=0, value=30),
        "marks_packages":  st.number_input("Marks x",    min_value=0, value=100),
        "description":     st.number_input("Description x", min_value=0, value=240),
        "hs_code":         st.number_input("HS Code x",  min_value=0, value=570),
        "origin_criterion":st.number_input("Origin x",   min_value=0, value=720),
        "net_weight":      st.number_input("Weight x",   min_value=0, value=870),
        "invoice_ref":     st.number_input("Invoice x",  min_value=0, value=1120),
    }

# ---------------------------------------------------------------------------
# Step 4: Save
# ---------------------------------------------------------------------------
st.header("Step 4 — Save template")

if st.button("Save template", type="primary"):
    if not template_id.strip():
        st.error("Template ID cannot be empty.")
        st.stop()
    if template_exists(template_id) and not st.checkbox("Overwrite existing template?"):
        st.warning("Template already exists. Check 'Overwrite' to replace it.")
        st.stop()

    # Save reference scan
    scan_save_name = template_id
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    scan_path = SCANS_DIR / f"{scan_save_name}.png"
    pil_img.save(str(scan_path))

    # Build TemplateField objects
    fields = []
    for fid, label, blank, max_lines, max_chars in FIELD_DEFS:
        e = field_entries[fid]
        scan_bbox = [e["x"], e["y"], e["w"], e["h"]]
        pdf_bbox = scan_bbox_to_pdf(scan_bbox, w_px, h_px)
        fn = "Courier-Bold" if e["bold"] else "Courier"
        fields.append(TemplateField(
            field_id=fid, label=label,
            scan_bbox=scan_bbox, pdf_bbox=pdf_bbox,
            font_name=fn, font_size=e["font_size"],
            max_chars_per_line=e["max_chars"], max_lines=e["max_lines"],
            blank_always=blank,
        ))

    # Build table layout
    scale_y = A4_HEIGHT_PT / h_px
    scale_x = A4_WIDTH_PT / w_px
    first_row_y_pt = A4_HEIGHT_PT - (first_row_y_px + row_height_px) * scale_y
    row_h_pt = row_height_px * scale_y

    col_labels = {
        "item_number": "Item No.", "marks_packages": "Marks & Pkgs",
        "description": "Description", "hs_code": "HS Code",
        "origin_criterion": "Origin", "net_weight": "Weight",
        "invoice_ref": "Invoice",
    }
    col_max_chars = {
        "item_number": 3, "marks_packages": 10, "description": 19,
        "hs_code": 10, "origin_criterion": 8, "net_weight": 16, "invoice_ref": 24,
    }
    columns = []
    col_ids = list(col_x.keys())
    for i, cid in enumerate(col_ids):
        x_px = col_x[cid]
        next_x_px = col_x[col_ids[i + 1]] if i + 1 < len(col_ids) else w_px - 30
        w_pt = (next_x_px - x_px) * scale_x
        columns.append(TableColumnDef(
            field_id=cid, label=col_labels[cid],
            x_pt=x_px * scale_x, width_pt=max(w_pt, 20.0),
            font_size=7.5, max_chars_per_line=col_max_chars[cid],
        ))

    table_layout = TableLayout(
        first_data_row_y_pt=first_row_y_pt,
        row_height_pt=row_h_pt,
        columns=columns,
    )

    template = Template(
        template_id=template_id,
        name=template_name,
        scan_filename=f"{scan_save_name}.png",
        scan_width_px=w_px,
        scan_height_px=h_px,
        fields=fields,
        table_layout=table_layout,
    )
    save_template(template)
    st.success(f"Template '{template_id}' saved successfully.")
