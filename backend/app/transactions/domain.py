"""Pure transaction logic: no database, no HTTP."""

from __future__ import annotations

import re
import unicodedata

_LEGAL_SUFFIXES = re.compile(
    r"\b(ltda|me|epp|eireli|s/?a|sa|mei|comercio|com|industria|ind)\b", re.IGNORECASE
)
_CARD_NOISE = re.compile(r"[*#]+\d*|\b\d{2,}\b")
_NON_ALNUM = re.compile(r"[^a-z0-9 ]")


def normalize_merchant(raw: str | None) -> str | None:
    """Collapse a merchant string into a stable key.

    Card statements decorate the same merchant in many ways ('IFOOD *1234 SAO
    PAULO'), and recurrence detection and duplicate detection both depend on
    those collapsing to one key.
    """
    if raw is None:
        return None
    text = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode().lower()
    text = _CARD_NOISE.sub(" ", text)
    text = _LEGAL_SUFFIXES.sub(" ", text)
    text = _NON_ALNUM.sub(" ", text)
    normalized = " ".join(text.split())
    return normalized or None
