"""
app.py — Main Streamlit entrypoint

Run with:
    streamlit run app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="COO Pre-Fill System — ComAfrique",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("COO Pre-Fill & Print Alignment System")
st.markdown("**ComAfrique Ltd** — Certificate of Origin overlay generator")

st.markdown("""
### Quick start

1. **New Transaction** — Fill in shipment data and download the print-ready overlay PDF
2. **Fine-Tune** — Adjust field positions after a test print
3. **Template Setup** — Define positions for a non-standard form layout
4. **Manage Templates** — View and manage saved templates

---

### How to print

1. Generate the overlay PDF from **New Transaction**
2. Feed the blank physical GACC COO form into your printer
3. Print the overlay PDF — the printer will deposit only the typed text onto the pre-printed form
4. Hand the printed form to the authorized signatory and submit for GCCI stamping

> Stamp areas (fields 13 signature, 14 GCCI, 15 Customs) are **always left blank** in the overlay.

---

### Alignment troubleshooting

If text lands outside the correct boxes:
- Go to **Fine-Tune** and apply a global `dx`/`dy` offset (in points; 1 pt ≈ 0.35 mm)
- Positive dx = shift right, positive dy = shift up
- Typical printer margin issues are fixed with ±5–15 pt adjustments
""")

st.info("Use the sidebar to navigate between pages.")
