from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings


@lru_cache
def load_policy() -> dict[str, Any]:
    policy_path = Path(get_settings().policy_path)
    return yaml.safe_load(policy_path.read_text(encoding="utf-8"))
