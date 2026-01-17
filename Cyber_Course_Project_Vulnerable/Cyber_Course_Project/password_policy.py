from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class PasswordPolicy:
    min_length: int
    max_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_digits: bool
    require_special_chars: bool
    special_chars: str
    min_special_chars: int
    min_digits: int
    min_uppercase: int
    min_lowercase: int
    forbidden_patterns: list[str]
    max_repeated_chars: int
    password_history_count: int


def _policy_file_path() -> Path:
    """
    Supports both layouts:
      - <BASE_DIR>/Cyber_Course_Project/config/password_config.json
      - <BASE_DIR>/config/password_config.json
    """
    base = Path(settings.BASE_DIR)
    candidates = [
        base / "Cyber_Course_Project" / "config" / "password_config.json",
        base / "config" / "password_config.json",
    ]
    for p in candidates:
        if p.exists():
            return p

    raise ImproperlyConfigured(
        "password_config.json not found. Looked in:\n" + "\n".join(f" - {c}" for c in candidates)
    )


def _require(p: dict[str, Any], name: str, typ) -> Any:
    if name not in p:
        raise ImproperlyConfigured(f"password_policy missing required key: {name}")
    value = p[name]
    if not isinstance(value, typ):
        raise ImproperlyConfigured(f"password_policy.{name} must be {typ.__name__}")
    return value


@lru_cache(maxsize=1)
def load_password_policy() -> PasswordPolicy:
    cfg_path = _policy_file_path()

    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ImproperlyConfigured(f"Failed to parse {cfg_path}: {e}") from e

    if not isinstance(raw, dict):
        raise ImproperlyConfigured(f"{cfg_path}: root must be a JSON object")

    pp = raw.get("password_policy")
    if not isinstance(pp, dict):
        raise ImproperlyConfigured(f"{cfg_path}: missing or invalid 'password_policy' object")

    phc = pp.get("password_history_count", 3)
    if not isinstance(phc, int) or phc < 0:
        raise ImproperlyConfigured(f"{cfg_path}: password_policy.password_history_count must be int >= 0")

    policy = PasswordPolicy(
        min_length=_require(pp, "min_length", int),
        max_length=_require(pp, "max_length", int),
        require_uppercase=_require(pp, "require_uppercase", bool),
        require_lowercase=_require(pp, "require_lowercase", bool),
        require_digits=_require(pp, "require_digits", bool),
        require_special_chars=_require(pp, "require_special_chars", bool),
        special_chars=_require(pp, "special_chars", str),
        min_special_chars=_require(pp, "min_special_chars", int),
        min_digits=_require(pp, "min_digits", int),
        min_uppercase=_require(pp, "min_uppercase", int),
        min_lowercase=_require(pp, "min_lowercase", int),
        forbidden_patterns=_require(pp, "forbidden_patterns", list),
        max_repeated_chars=_require(pp, "max_repeated_chars", int),
        password_history_count=phc,
    )

    if policy.min_length < 1:
        raise ImproperlyConfigured(f"{cfg_path}: password_policy.min_length must be >= 1")
    if policy.max_length < policy.min_length:
        raise ImproperlyConfigured(f"{cfg_path}: password_policy.max_length must be >= min_length")
    if policy.max_repeated_chars < 1:
        raise ImproperlyConfigured(f"{cfg_path}: password_policy.max_repeated_chars must be >= 1")

    return policy