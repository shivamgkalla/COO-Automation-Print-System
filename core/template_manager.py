from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from config import TEMPLATES_DIR
from core.models import Template


def _template_path(template_id: str) -> Path:
    return TEMPLATES_DIR / f"{template_id}.json"


def save_template(template: Template) -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    path = _template_path(template.template_id)
    path.write_text(template.model_dump_json(indent=2), encoding="utf-8")


def load_template(template_id: str) -> Template:
    path = _template_path(template_id)
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {template_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Template.model_validate(data)


def list_templates(include_deprecated: bool = False) -> List[Template]:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    templates = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            t = Template.model_validate(data)
            if not t.deprecated or include_deprecated:
                templates.append(t)
        except Exception:
            continue
    return templates


def deprecate_template(template_id: str) -> None:
    t = load_template(template_id)
    t.deprecated = True
    save_template(t)


def get_active_template_ids() -> List[str]:
    return [t.template_id for t in list_templates(include_deprecated=False)]


def template_exists(template_id: str) -> bool:
    return _template_path(template_id).exists()
