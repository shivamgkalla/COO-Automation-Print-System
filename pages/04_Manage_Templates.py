"""
Page 04 — Manage Templates
List, inspect, and deprecate templates.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import streamlit as st

from config import SCANS_DIR
from core.template_manager import list_templates, load_template, deprecate_template, save_template

st.set_page_config(page_title="Manage Templates", layout="wide")
st.title("Manage Templates")

# Active templates
st.subheader("Active templates")
active = list_templates(include_deprecated=False)
if not active:
    st.info("No active templates.")
else:
    for t in active:
        with st.expander(f"{t.name}  [{t.template_id}]  v{t.version}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"- **ID:** `{t.template_id}`")
                st.markdown(f"- **Version:** {t.version}")
                st.markdown(f"- **Fields:** {len(t.fields)}")
                st.markdown(f"- **Scan file:** `{t.scan_filename or 'none'}`")
                st.markdown(f"- **Page:** {t.page_width_pt:.0f} × {t.page_height_pt:.0f} pt")

                scan_path = SCANS_DIR / t.scan_filename if t.scan_filename else None
                if scan_path and scan_path.exists():
                    from PIL import Image
                    st.image(Image.open(scan_path), caption="Reference scan", width=400)

                with st.expander("View raw JSON"):
                    st.code(t.model_dump_json(indent=2), language="json")

            with col2:
                if t.template_id != "gacc_coo_default":
                    if st.button("Deprecate", key=f"dep_{t.template_id}"):
                        deprecate_template(t.template_id)
                        st.success(f"Template '{t.template_id}' deprecated.")
                        st.rerun()
                else:
                    st.caption("Default template — cannot deprecate")

# Deprecated templates
st.divider()
st.subheader("Deprecated templates")
all_templates = list_templates(include_deprecated=True)
deprecated = [t for t in all_templates if t.deprecated]
if not deprecated:
    st.info("No deprecated templates.")
else:
    for t in deprecated:
        with st.expander(f"[DEPRECATED] {t.name} [{t.template_id}]"):
            if st.button("Restore", key=f"restore_{t.template_id}"):
                t.deprecated = False
                save_template(t)
                st.success(f"Template '{t.template_id}' restored.")
                st.rerun()
