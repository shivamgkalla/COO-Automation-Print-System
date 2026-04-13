"""
Page 02 — Fine-Tune
Adjust per-field coordinate offsets and font sizes on an existing template.
Use this after a test print to correct any misalignment.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from config import SCANS_DIR
from core.template_manager import list_templates, load_template, save_template

st.set_page_config(page_title="Fine-Tune Template", layout="wide")
st.title("Fine-Tune Template")
st.caption("Adjust field positions after a test print. Positive dx = move right; positive dy = move up.")

templates = list_templates()
if not templates:
    st.warning("No templates found. Create one in Template Setup or use the default.")
    st.stop()

template_names = {t.template_id: t.name for t in templates}
selected_id = st.selectbox("Select template to fine-tune", options=list(template_names.keys()),
                           format_func=lambda k: f"{template_names[k]} [{k}]")

template = load_template(selected_id)

# Show reference scan if available
scan_path = SCANS_DIR / template.scan_filename if template.scan_filename else None
if scan_path and scan_path.exists():
    from PIL import Image
    st.image(Image.open(scan_path), caption="Reference scan", use_column_width=True)

st.subheader("Global printer calibration offset")
st.markdown("Applied to **all** fields. Use this first for consistent printer margin issues.")
g_col1, g_col2 = st.columns(2)
global_dx = g_col1.number_input("Global dx (pt, right +)", value=0.0, step=0.5, key="global_dx")
global_dy = g_col2.number_input("Global dy (pt, up +)",    value=0.0, step=0.5, key="global_dy")

st.divider()
st.subheader("Per-field adjustments")
st.markdown("Fine-tune individual fields. These are **additive** to the global offset.")

field_adjustments = {}
for field in template.fields:
    if field.blank_always:
        continue
    with st.expander(f"{field.label} [{field.field_id}]"):
        col1, col2, col3, col4 = st.columns(4)
        dx = col1.number_input("dx (pt)", key=f"{field.field_id}_dx", value=0.0, step=0.5)
        dy = col2.number_input("dy (pt)", key=f"{field.field_id}_dy", value=0.0, step=0.5)
        fs = col3.number_input("Font size", key=f"{field.field_id}_fs",
                               value=float(field.font_size), min_value=4.0, max_value=20.0, step=0.5)
        st.markdown(
            f"Current PDF bbox: `x={field.pdf_bbox[0]:.1f}, y={field.pdf_bbox[1]:.1f}, "
            f"w={field.pdf_bbox[2]:.1f}, h={field.pdf_bbox[3]:.1f}`"
        )
        field_adjustments[field.field_id] = {"dx": dx, "dy": dy, "fs": fs}

if st.button("Apply adjustments and save", type="primary"):
    for field in template.fields:
        if field.blank_always:
            continue
        adj = field_adjustments.get(field.field_id, {})
        dx = adj.get("dx", 0.0) + global_dx
        dy = adj.get("dy", 0.0) + global_dy
        fs = adj.get("fs", field.font_size)
        field.pdf_bbox[0] += dx
        field.pdf_bbox[1] += dy
        field.font_size = fs

    if template.table_layout:
        template.table_layout.first_data_row_y_pt += global_dy
        for col in template.table_layout.columns:
            col.x_pt += global_dx

    template.version += 1
    save_template(template)
    st.success(f"Template '{selected_id}' updated to version {template.version}.")
    st.info("Re-generate and test-print to verify alignment.")
