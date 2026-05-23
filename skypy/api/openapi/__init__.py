from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

_SPEC_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load_doc(name: str) -> Dict[str, Any]:
    path = _SPEC_DIR / f"{name}.yaml"
    with path.open("r", encoding="utf-8") as fh:
        spec = yaml.safe_load(fh) or {}

    responses = spec.get("responses")
    if isinstance(responses, dict):
        spec["responses"] = {
            int(code) if isinstance(code, str) and code.isdigit() else code: body
            for code, body in responses.items()
        }
    return spec


__all__ = ["load_doc"]
