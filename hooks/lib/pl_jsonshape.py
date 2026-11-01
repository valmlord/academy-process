"""Narrow decoded JSON (typed `object`) to concrete shapes, so the hook code needs no `Any`.

Imports nothing from lib/: every module may use it without an import cycle.
"""
from typing import Optional


def as_object(value: object) -> Optional[dict[str, object]]:
    """A JSON object, or None for any other value."""
    return value if isinstance(value, dict) else None


def as_str(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


def as_list(value: object) -> list[object]:
    """A JSON array, or an empty list for any other value."""
    return value if isinstance(value, list) else []
