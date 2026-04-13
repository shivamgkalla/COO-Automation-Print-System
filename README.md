# COO Pre-Fill & Print Alignment System

**ComAfrique Ltd — Certificate of Origin Overlay Generator**

Built by Fortizo Technologies

---

## What This System Does

The GACC Certificate of Origin (COO) form is a physical pre-printed document that must be stamped by GCCI and Gambia Customs. Previously, staff typed data directly onto forms and wasted time trial-and-error printing to get text to land in the right boxes.

This system generates a **transparent-background PDF overlay** containing only the typed text, positioned precisely so that when the physical blank COO form is fed into a printer and the overlay PDF is printed onto it, every field lands in the correct box — first time, every time.

**What the system fills:** Fields 1–5 (exporter, producer, consignee, transport, remarks), the goods table (fields 6–12), certificate number, issued-in country, declaration country, and page total.

**What the system never touches:** Field 13 signature line, Field 14 (GCCI stamp), Field 15 (Customs stamp), and the pre-printed GACC number at the bottom — these are always left blank for physical stamping.

---

## Requirements

- Python 3.11 or 3.12
- poppler (for PDF rendering in previews): `brew install poppler`
- All Python packages listed in `requirements.txt`

---

## Installation

```bash
# 1. Clone or copy the project folder
cd coo_automation_printing

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate it
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Running the App

```bash
# From the project root, with the virtual environment active:
.venv/bin/streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## Project Structure

```
coo_automation_printing/
├── app.py                     # Streamlit home page — run this to start
├── cli.py                     # Command-line interface (batch use)
├── config.py                  # Paths, printer offset, constants
│
├── pages/
│   ├── 03_New_Transaction.py  # Daily use: fill shipment data → download PDF
│   ├── 02_Fine_Tune.py        # Adjust field positions after a test print
│   ├── 01_Template_Setup.py   # Define field positions for a new form layout
│   └── 04_Manage_Templates.py # View, deprecate, restore templates
│
├── core/
│   ├── models.py              # Data models (Template, COOTransaction)
│   └── template_manager.py    # Load/save/list templates from JSON
│
├── generation/
│   ├── overlay_generator.py   # ReportLab canvas — draws text only, no background
│   ├── text_formatter.py      # Auto font-shrink to fit any content in any box
│   └── table_renderer.py      # Renders the goods table rows
│
├── detection/
│   ├── scan_preprocessor.py   # OpenCV deskew/perspective correction for scans
│   ├── coordinate_mapper.py   # Converts scan pixels → PDF points
│   └── field_validator.py     # Warns on missing or overflowing fields
│
├── templates/
│   └── gacc_coo_default.json  # Pre-calibrated default template (ships with app)
│
├── scans/                     # Reference scan images for templates
└── output/                    # Generated overlay PDFs saved here
```

---

## Daily Use — Step by Step

### Step 1 — Open the app

```bash
.venv/bin/streamlit run app.py
```

Go to **http://localhost:8501** and click **"03 New Transaction"** in the sidebar.

---

### Step 2 — Select template and output mode

- **Template:** Use `GACC COO Standard Form (Gambia → China)` for all standard GACC forms
- **Output mode:**
  - `Pre-Customs` — invoice value is omitted (used for Customs submission)
  - `Internal` — full data including invoice value (for company records)

---

### Step 3 — Fill in the form

| Section | Fields |
|---|---|
| **Header** | Certificate No., Issued in (country) |
| **Field 1** | Exporter name and address |
| **Field 2** | Producer name and address |
| **Field 3** | Consignee name and address |
| **Field 4** | Means of transport, departure date, vessel/flight no., port of loading, port of discharge |
| **Field 5** | Remarks (e.g. booking reference) |
| **Goods table** | One row per goods line: item no., marks & packages, description, HS code, origin criterion, gross weight, net weight, invoice no./date/value |
| **Declaration** | Declaration country, page total |

**Tips:**
- For multi-line address fields (exporter, producer, consignee), press Enter to start a new line — each line maps to one line in the printed form
- The system automatically shrinks the font if an address is too long to fit in its box — no manual adjustment needed
- Certificate No. format: `CH|SPT 2026|449`
- Means of transport: always `BY SEA` for Gambia shipments
- Origin criterion: always `WO` (Wholly Obtained) for sesame seeds

---

### Step 4 — Generate and download

Click **Generate Overlay PDF**. A **Download** button appears immediately below it.

The PDF is also saved automatically to the `output/` folder with a timestamped filename:
```
COO_CH_SPT_2026_449_pre_customs_20260409_143022.pdf
```

---

### Step 5 — Print

1. Feed one **blank physical GACC COO form** into your printer
2. Open the downloaded PDF in any PDF viewer (Preview, Adobe Reader, etc.)
3. Print at **100% scale — do not fit to page, do not scale**
4. The printer deposits only the typed text at the correct positions on the pre-printed form

**What should be printed:**

| Area | Expected content |
|---|---|
| Top right | Certificate number |
| Box 1 | Exporter name and address |
| Box 2 | Producer name and address |
| Box 3 | Consignee name and address |
| Right column | Issued in country |
| Right column | Remarks |
| Box 4 | Transport details across labelled rows |
| Table | All goods rows across 7 columns |
| Bottom left dotted line | Declaration country |
| Bottom right | Page total |
| Fields 13 sig / 14 / 15 | **Blank** — for physical stamps only |
| GACC number | **Untouched** — pre-printed on the form |

---

## Alignment Troubleshooting

If text consistently prints too far left, right, up, or down across all fields:

1. Go to **"02 Fine Tune"** in the sidebar
2. Apply a **global printer offset** (dx/dy in points):
   - Text too far **right** → negative dx (e.g. -5)
   - Text too far **left** → positive dx (e.g. +5)
   - Text too **high** → negative dy (e.g. -5)
   - Text too **low** → positive dy (e.g. +5)
   - 1 point ≈ 0.35 mm. Start with ±5 pt and adjust from there.
3. Click **Save offset** and regenerate

This offset applies globally to all fields and is stored in `config.py` as `PRINTER_OFFSET_X` / `PRINTER_OFFSET_Y`.

---

## Output Modes

| Mode | Invoice value in PDF | Use for |
|---|---|---|
| `pre_customs` | **Hidden** | Submitting to GCCI / Customs |
| `internal` | **Shown** | Company records, internal approval |

---

## Sample Transaction Data (SEDACO)

Use this to test the system on a new installation:

| Field | Value |
|---|---|
| Certificate No. | `CH\|SPT 2026\|449` |
| Issued in | `THE GAMBIA` |
| Exporter | `COMAFRIQUE LIMITED` / `OYSTER CREEK, BANJUL SERREKUNDA HIGHWAY THE GAMBIA` |
| Producer | Same as exporter |
| Consignee | `YIHAI KERRY (EAST CHINA) GRAIN AND OIL INDUSTRY CO., LTD` / `CHINA` |
| Means | `BY SEA` |
| Date | `10/04/2026` |
| Vessel | `MSC TIANA F WC610A` |
| POL | `BANJUL, GAMBIA` |
| POD | `QINGDAO, CHINA` |
| Remarks | `MEDUBQ019342` |
| Item No. | `1` |
| Marks | `7X40FT CONTAINERS` |
| Description | `3,789 PP BAGS` / `SESAME SEEDS, GAMBIA ORIGIN` |
| HS Code | `1207.40.00` |
| Origin criterion | `WO` |
| Gross weight | `189.829MT` |
| Net weight | `189.450MT` |
| Invoice No. | `INV-2026-001` |
| Invoice Date | `01/04/2026` |
| Invoice Value | `USD 194,186.25` |
| Declaration country | `THE GAMBIA` |
| Page total | `1` |

---

## CLI Usage (Batch / Scripted)

For batch generation without the web UI:

```bash
# Generate overlay from a JSON transaction file
.venv/bin/python cli.py generate path/to/transaction.json

# Specify output path
.venv/bin/python cli.py generate transaction.json --output output/my_coo.pdf

# Override template
.venv/bin/python cli.py generate transaction.json --template gacc_coo_default

# List all available templates
.venv/bin/python cli.py list-templates
```

**Transaction JSON format:**
```json
{
  "certificate_no": "CH|SPT 2026|449",
  "exporter": "COMAFRIQUE LIMITED\nOYSTER CREEK, BANJUL SERREKUNDA HIGHWAY THE GAMBIA",
  "producer": "COMAFRIQUE LIMITED\nOYSTER CREEK, BANJUL SERREKUNDA HIGHWAY THE GAMBIA",
  "consignee": "YIHAI KERRY (EAST CHINA) GRAIN AND OIL INDUSTRY CO., LTD\nCHINA",
  "transport": {
    "means": "BY SEA",
    "departure_date": "10/04/2026",
    "vessel_flight_no": "MSC TIANA F WC610A",
    "port_of_loading": "BANJUL, GAMBIA",
    "port_of_discharge": "QINGDAO, CHINA"
  },
  "issued_in": "THE GAMBIA",
  "remarks": "MEDUBQ019342",
  "table_rows": [
    {
      "item_number": "1",
      "marks_packages": "7X40FT CONTAINERS",
      "description": "3,789 PP BAGS\nSESAME SEEDS, GAMBIA ORIGIN",
      "hs_code": "1207.40.00",
      "origin_criterion": "WO",
      "gross_weight": "189.829MT",
      "net_weight": "189.450MT",
      "invoice_number": "INV-2026-001",
      "invoice_date": "01/04/2026",
      "invoice_value": "USD 194,186.25"
    }
  ],
  "declaration_country": "THE GAMBIA",
  "page_total": "1",
  "output_mode": "pre_customs",
  "template_id": "gacc_coo_default"
}
```

---

## Template Management

The default template (`gacc_coo_default`) ships pre-calibrated for the standard GACC COO form used by GCCI Gambia. It covers all shipments with the standard form layout.

If GCCI issues a new form batch with a different layout:

1. Go to **"01 Template Setup"** in the sidebar
2. Upload a scan of the blank new form (300 DPI recommended)
3. The system will deskew and correct perspective automatically
4. Enter field coordinates by clicking or typing bounding boxes
5. Save as a new template with a unique ID (e.g. `gacc_coo_2027_batch`)

To deprecate an old template: go to **"04 Manage Templates"** and click **Deprecate**. Deprecated templates are hidden from the transaction form but kept on disk and can be restored.

---

## No External Dependencies

This system has no API keys, no internet requirement, and no external service calls. Everything runs locally. The only external tools needed are Python packages (installed via pip) and poppler (for PDF-to-image conversion in previews).

---

## Support

For issues or changes, contact Fortizo Technologies.
