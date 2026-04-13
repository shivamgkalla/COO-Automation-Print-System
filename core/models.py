from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Template models
# ---------------------------------------------------------------------------

class TemplateField(BaseModel):
    field_id: str
    label: str
    # Bounding box on the reference scan image [x, y, w, h] in pixels
    scan_bbox: List[float] = Field(default_factory=lambda: [0, 0, 0, 0])
    # Bounding box in PDF points [x, y, w, h] (ReportLab origin = bottom-left)
    pdf_bbox: List[float] = Field(default_factory=lambda: [0, 0, 0, 0])
    font_name: str = "Courier"
    font_size: float = 8.0
    max_chars_per_line: int = 40
    max_lines: int = 3
    # If True, this field is never written (stamp/signature zones)
    blank_always: bool = False
    is_table_column: bool = False


class TableColumnDef(BaseModel):
    """Defines the x-position and width of a table column in PDF points."""
    field_id: str
    label: str
    x_pt: float
    width_pt: float
    font_name: str = "Courier"
    font_size: float = 7.5
    max_chars_per_line: int = 20
    align: Literal["left", "center", "right"] = "left"


class TableLayout(BaseModel):
    first_data_row_y_pt: float   # PDF y-coord (bottom-left origin) of top of first data row
    row_height_pt: float = 20.0
    columns: List[TableColumnDef] = Field(default_factory=list)


class Template(BaseModel):
    template_id: str
    name: str
    scan_filename: str = ""          # reference scan image stored in scans/
    scan_dpi: int = 300
    scan_width_px: int = 2480        # A4 at 300 DPI
    scan_height_px: int = 3508
    page_width_pt: float = 595.28
    page_height_pt: float = 841.89
    fields: List[TemplateField] = Field(default_factory=list)
    table_layout: Optional[TableLayout] = None
    version: int = 1
    deprecated: bool = False

    def get_field(self, field_id: str) -> Optional[TemplateField]:
        for f in self.fields:
            if f.field_id == field_id:
                return f
        return None


# ---------------------------------------------------------------------------
# Transaction models
# ---------------------------------------------------------------------------

class TransportInfo(BaseModel):
    means: str = ""               # "BY SEA"
    departure_date: str = ""
    vessel_flight_no: str = ""
    port_of_loading: str = ""
    port_of_discharge: str = ""


class TableRow(BaseModel):
    item_number: str = "1"
    marks_packages: str = ""
    description: str = ""
    hs_code: str = ""
    origin_criterion: str = ""
    gross_weight: str = ""
    net_weight: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    invoice_value: str = ""        # omitted in pre_customs mode


class COOTransaction(BaseModel):
    certificate_no: str = ""
    exporter: str = ""
    producer: str = ""
    consignee: str = ""
    transport: TransportInfo = Field(default_factory=TransportInfo)
    issued_in: str = "THE GAMBIA"
    remarks: str = ""
    table_rows: List[TableRow] = Field(default_factory=list)
    declaration_country: str = "THE GAMBIA"
    page_total: str = "1"          # filled after "Page 1 of ___"
    output_mode: Literal["pre_customs", "internal"] = "pre_customs"
    template_id: str = "gacc_coo_default"

    def get_field_value(self, field_id: str) -> str:
        """Return the transaction value for a given field_id."""
        mapping = {
            "cert_no": self.certificate_no,
            "field_1_exporter": self.exporter,
            "field_2_producer": self.producer,
            "field_3_consignee": self.consignee,
            "field_4_means": self.transport.means,
            "field_4_date": self.transport.departure_date,
            "field_4_vessel": self.transport.vessel_flight_no,
            "field_4_pol": self.transport.port_of_loading,
            "field_4_pod": self.transport.port_of_discharge,
            "issued_in": self.issued_in,
            "field_5_remarks": self.remarks,
            "field_13_country": self.declaration_country,
            "page_total": self.page_total,
        }
        return mapping.get(field_id, "")
