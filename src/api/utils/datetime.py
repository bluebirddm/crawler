"""Date/time utilities for API query parsing."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union
import math


def parse_datetime_param(
    value: Optional[Union[str, int, float]],
    param_name: str,
) -> Optional[datetime]:
    """Parse query parameters that may contain ISO strings or Unix timestamps.

    Accepts second or millisecond epoch values and normalises everything to
    second-level precision. Returns ``None`` for missing/blank inputs and
    raises ``ValueError`` for invalid payloads so callers can translate into
    HTTP errors.
    """

    if value is None:
        return None

    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        value = trimmed

    numeric_candidate: Optional[float] = None
    try:
        numeric_candidate = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        numeric_candidate = None

    if numeric_candidate is not None and math.isfinite(numeric_candidate):
        # Treat sufficiently large numbers as milliseconds.
        if abs(numeric_candidate) >= 1_000_000_000_000:
            numeric_candidate /= 1000.0

        seconds = int(numeric_candidate)
        try:
            return datetime.fromtimestamp(seconds)
        except (OverflowError, OSError, ValueError) as exc:  # pragma: no cover
            raise ValueError(f"Invalid {param_name}: {value}") from exc

    if isinstance(value, str):
        normalised = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalised)
        except ValueError as exc:
            raise ValueError(f"Invalid {param_name}: {value}") from exc

        if parsed.tzinfo:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    raise ValueError(f"Invalid {param_name}: {value}")


def apply_datetime_filters(query, column, start: Optional[datetime], end: Optional[datetime]):
    """Apply optional ``start``/``end`` bounds to a SQLAlchemy query."""

    if start is not None:
        query = query.filter(column >= start)
    if end is not None:
        query = query.filter(column <= end)
    return query
