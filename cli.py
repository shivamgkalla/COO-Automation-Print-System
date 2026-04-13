"""
cli.py — Command-line interface for batch/scripted COO overlay generation.

Usage:
    python cli.py generate <transaction.json> [--output OUTPUT] [--template TEMPLATE_ID]
    python cli.py list-templates
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import datetime
from typing import Optional

import typer

from config import OUTPUT_DIR
from core.models import COOTransaction
from core.template_manager import list_templates, load_template
from generation.overlay_generator import generate_overlay

app = typer.Typer(help="COO Pre-Fill & Print Alignment System — CLI")


@app.command()
def generate(
    transaction_json: Path = typer.Argument(..., help="Path to a transaction JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output PDF path"),
    template_id: Optional[str] = typer.Option(None, "--template", "-t", help="Override template ID"),
):
    """Generate an overlay PDF from a transaction JSON file."""
    if not transaction_json.exists():
        typer.echo(f"Error: {transaction_json} not found", err=True)
        raise typer.Exit(1)

    data = json.loads(transaction_json.read_text(encoding="utf-8"))
    transaction = COOTransaction.model_validate(data)

    if template_id:
        transaction.template_id = template_id

    template = load_template(transaction.template_id)

    if output is None:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_cert = transaction.certificate_no.replace("|", "_").replace("/", "_") or "draft"
        output = OUTPUT_DIR / f"COO_{safe_cert}_{transaction.output_mode}_{ts}.pdf"

    out = generate_overlay(transaction, output, template=template)
    typer.echo(f"Generated: {out}")


@app.command(name="list-templates")
def list_templates_cmd(include_deprecated: bool = typer.Option(False, "--all", help="Include deprecated")):
    """List all available templates."""
    templates = list_templates(include_deprecated=include_deprecated)
    if not templates:
        typer.echo("No templates found.")
        return
    for t in templates:
        dep = " [DEPRECATED]" if t.deprecated else ""
        typer.echo(f"  {t.template_id:<30} v{t.version}  {t.name}{dep}")


if __name__ == "__main__":
    app()
