import json
from django import template
from django.conf import settings
from pathlib import Path

register = template.Library()

@register.simple_tag
def vite_asset(entry):
    manifest_path = Path(settings.BASE_DIR) / "static/frontend/.vite/manifest.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    file = manifest[entry]["file"]
    return f"frontend/{file}"