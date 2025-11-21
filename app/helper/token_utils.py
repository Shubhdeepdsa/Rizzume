from __future__ import annotations

from math import ceil


def estimate_tokens(text: str) -> int:
    """
    Very rough token estimate based on character length.

    For UX (progress bars / warnings) we do not need exact model tokens,
    just an approximate scale. A common rule of thumb is ~4 characters
    per token for English-like text.
    """
    if not text:
        return 0
    return int(ceil(len(text) / 4))

