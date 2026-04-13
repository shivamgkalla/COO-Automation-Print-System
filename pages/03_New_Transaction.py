"""
Page 03 — New Transaction
Fill in COO data, select template, choose output mode, download overlay PDF.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import datetime
from io import BytesIO

import streamlit as st

from config import OUTPUT_DIR
from core.models import COOTransaction, TransportInfo, TableRow
from core.template_manager import list_templates
from detection.field_validator import validate_transaction
from generation.overlay_generator import generate_overlay

st.set_page_config(page_title="New COO Transaction", layout="wide")
st.title("New COO Transaction")

# ---------------------------------------------------------------------------
# Template selection
# ---------------------------------------------------------------------------
templates = list_templates()
if not templates:
    st.error("No templates found. Please add the default template or create one in Template Setup.")
    st.stop()

template_map = {t.template_id: t for t in templates}
selected_id = st.selectbox(
    "Form template",
    options=list(template_map.keys()),
    format_func=lambda k: f"{template_map[k].name} [{k}]",
)
template = template_map[selected_id]

output_mode = st.radio(
    "Output mode",
    options=["pre_customs", "internal"],
    format_func=lambda x: "Pre-Customs (no invoice value)" if x == "pre_customs" else "Internal (full data)",
    horizontal=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Header fields
# ---------------------------------------------------------------------------
st.subheader("Header")
col1, col2 = st.columns(2)
cert_no      = col1.text_input("Certificate No.", placeholder="e.g. CH|SPT 2026|449")
issued_in    = col2.text_input("Issued in (country)", value="THE GAMBIA")

col3, col4 = st.columns(2)
exporter = col3.text_area("1. Exporter name & address",
    value="COMAFRIQUE LIMITED\nOYSTER CREEK, BANJUL SERREKUNDA HIGHWAY THE GAMBIA",
    height=100)
producer = col4.text_area("2. Producer name & address",
    value="COMAFRIQUE LIMITED\nOYSTER CREEK, BANJUL SERREKUNDA HIGHWAY THE GAMBIA",
    height=100)

consignee = st.text_area("3. Consignee name & address", height=100,
    placeholder="Company name, address, USCI")

st.divider()

# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------
st.subheader("4. Transport details")
c1, c2, c3 = st.columns(3)
means        = c1.text_input("Means of transport", value="BY SEA")
dep_date     = c2.text_input("Departure Date", placeholder="DD/MM/YYYY")
vessel       = c3.text_input("Vessel / Flight No.", placeholder="e.g. MSC TIANA F WC610A")

c4, c5 = st.columns(2)
pol = c4.text_input("Port of Loading",   placeholder="e.g. BANJUL, GAMBIA")
pod = c5.text_input("Port of Discharge", placeholder="e.g. QINGDAO, CHINA")

remarks      = st.text_input("5. Remarks", placeholder="e.g. booking ref MEDUBQ019342")

st.divider()

# ---------------------------------------------------------------------------
# Goods table (fields 6–12)
# ---------------------------------------------------------------------------
st.subheader("Goods Table (Fields 6–12)")
num_rows = st.number_input("Number of goods rows", min_value=1, max_value=10, value=1)

table_rows = []
for i in range(int(num_rows)):
    st.markdown(f"**Row {i+1}**")
    r1, r2, r3 = st.columns(3)
    item_no    = r1.text_input("Item No.",       key=f"item_{i}",  value=str(i + 1))
    marks      = r2.text_input("Marks & Pkg No.",key=f"marks_{i}", placeholder="e.g. 7X40FT CONTAINERS")
    description= r3.text_area("Description",     key=f"desc_{i}",  height=80,
                               placeholder="3,789 PP BAGS\nSESAME SEEDS, GAMBIA ORIGIN")

    r4, r5, r6, r7 = st.columns(4)
    hs_code    = r4.text_input("HS Code",        key=f"hs_{i}",    placeholder="1207.40.00")
    origin     = r5.text_input("Origin criterion",key=f"orig_{i}", value="WO")
    gw         = r6.text_input("Gross weight",   key=f"gw_{i}",    placeholder="189.829MT")
    nw         = r7.text_input("Net weight",     key=f"nw_{i}",    placeholder="189.450MT")

    inv_no = inv_date = inv_val = ""
    if output_mode == "internal":
        ri1, ri2, ri3 = st.columns(3)
        inv_no   = ri1.text_input("Invoice No.",  key=f"invno_{i}")
        inv_date = ri2.text_input("Invoice Date", key=f"invdate_{i}")
        inv_val  = ri3.text_input("Invoice Value",key=f"invval_{i}", placeholder="USD 194,186.25")

    table_rows.append(TableRow(
        item_number=item_no, marks_packages=marks, description=description,
        hs_code=hs_code, origin_criterion=origin,
        gross_weight=gw, net_weight=nw,
        invoice_number=inv_no, invoice_date=inv_date, invoice_value=inv_val,
    ))

st.divider()

# ---------------------------------------------------------------------------
# Declaration / page
# ---------------------------------------------------------------------------
st.subheader("Declaration")
c_a, c_b = st.columns(2)
decl_country = c_a.text_input("Declaration country (field 13 dotted line)", value="THE GAMBIA")
page_total   = c_b.text_input("Page total (for 'Page 1 of ___')", value="1")

# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------
st.divider()
if st.button("Generate Overlay PDF", type="primary"):
    transaction = COOTransaction(
        certificate_no=cert_no,
        exporter=exporter,
        producer=producer,
        consignee=consignee,
        transport=TransportInfo(
            means=means, departure_date=dep_date,
            vessel_flight_no=vessel, port_of_loading=pol, port_of_discharge=pod,
        ),
        issued_in=issued_in,
        remarks=remarks,
        table_rows=table_rows,
        declaration_country=decl_country,
        page_total=page_total,
        output_mode=output_mode,
        template_id=selected_id,
    )

    warnings = validate_transaction(transaction, template)
    if warnings:
        for w in warnings:
            st.warning(w)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_tag = "pre_customs" if output_mode == "pre_customs" else "internal"
    filename = f"COO_{cert_no.replace('|','_').replace('/','_') or 'draft'}_{mode_tag}_{ts}.pdf"
    out_path = OUTPUT_DIR / filename

    try:
        with st.spinner("Generating PDF..."):
            generate_overlay(transaction, out_path, template=template)

        with open(out_path, "rb") as f:
            pdf_bytes = f.read()

        st.success(f"PDF generated: {filename}")
        st.download_button(
            label="Download Overlay PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
        )

        # Virtual print preview — uses PyMuPDF (no system dependencies)
        st.divider()
        st.subheader("Virtual Print Preview")
        try:
            import numpy as np
            from PIL import Image
            import fitz  # PyMuPDF
            from pathlib import Path

            blank_path = Path(__file__).parent.parent / "SRS_Docs" / "alex dft sample.pdf"
            if not blank_path.exists():
                st.info("Reference blank form not found — preview unavailable. Download the PDF above and check it manually.")
            else:
                with st.spinner("Generating preview..."):
                    def pdf_to_image(path: str, dpi: int = 120) -> Image.Image:
                        doc = fitz.open(path)
                        page = doc[0]
                        mat = fitz.Matrix(dpi / 72, dpi / 72)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    blank   = pdf_to_image(str(blank_path))
                    overlay = pdf_to_image(str(out_path))
                    overlay = overlay.resize(blank.size, Image.LANCZOS)
                    composite = Image.fromarray(np.minimum(np.array(blank), np.array(overlay)))
                st.image(composite, caption="Virtual print — text overlaid on blank form", use_container_width=True)
        except Exception as prev_err:
            st.info(f"Preview unavailable: {prev_err}")

    except Exception as e:
        st.error(f"Failed to generate PDF: {e}")
        raise
