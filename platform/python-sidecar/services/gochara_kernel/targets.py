"""Canonical-target grammar for the '5.0' identity bytes (AM-2,
GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5; migration 1153's
kgpo_target_form_ck).

The applied CHECK admits exactly three SQL shapes:

    point:<λ>   ^point:([0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9])(\\.[0-9]+)?$
    span:<…>    ^span:[a-z0-9_]+$
    star:<1-27> ^star:([1-9]|1[0-9]|2[0-7])$

The CHECK is looser than the contract for `span:` — AM-2 pins span targets to the
ABSOLUTE sign numerals `span:1` … `span:12` (1 = Meṣa; no leading zero) and makes
every other `span:` value a WRITER/validator obligation, "not a database guarantee":
this module is that validator, and `PhysicalObjectId` runs it on construction so no
identity with a non-canonical target can exist in the writer at all. Rejected
(O-RX-1a negatives): `sign:7` (fails the SQL shape), `span:13`, `span:07`,
`span:libra` (a sign NAME is not an identity token — it is a rendering).

Point targets carry the solved longitude at FULL precision as one decimal string with
no exponent (`repr`'s shortest round-trip digits; an exponent form such as `1e-05`
would fail the CHECK). No quantization happens here — the rounding/seam question is
the draft's follow-up F-3, not settled in this module.
"""
from __future__ import annotations

import re
from decimal import Decimal

from services.gochara_rules.frames import SIGNS

_POINT_RE = re.compile(
    r"^point:([0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9])(\.[0-9]+)?$")
_SPAN_RE = re.compile(r"^span:([1-9]|1[0-2])$")
_STAR_RE = re.compile(r"^star:([1-9]|1[0-9]|2[0-7])$")

SIGN_NAMES: tuple[str, ...] = tuple(s.lower() for s in SIGNS)   # index + 1 = absolute sign


def span_target(sign: str | int) -> str:
    """`span:<n>` for an absolute sign — a name ('Libra'/'libra') or 1..12."""
    if isinstance(sign, int) and not isinstance(sign, bool):
        n = sign
    else:
        name = str(sign).lower()
        if name not in SIGN_NAMES:
            raise ValueError(f"unknown sign {sign!r}")
        n = SIGN_NAMES.index(name) + 1
    if not 1 <= n <= 12:
        raise ValueError(f"absolute sign must be 1..12, got {sign!r}")
    return f"span:{n}"


def span_sign_index(target: str) -> int:
    """The absolute sign number (1 = Meṣa) of a `span:<n>` target; any other
    shape raises."""
    m = _SPAN_RE.match(target)
    if m is None:
        raise ValueError(
            f"non-canonical span target {target!r}: AM-2 admits span:1 … span:12 only")
    return int(m.group(1))


def span_sign_name(target: str) -> str:
    """Lowercase sign name of a `span:<n>` target (a rendering, never identity)."""
    return SIGN_NAMES[span_sign_index(target) - 1]


def point_target(longitude_deg: float) -> str:
    """`point:<λ>` — full precision, decimal, no exponent; λ wrapped to [0, 360)."""
    lam = float(longitude_deg) % 360.0
    text = repr(lam)
    if "e" in text or "E" in text:
        text = format(Decimal(text), "f")
    return f"point:{text}"


def validate_canonical_target(target: str) -> str:
    """Return `target` if it is a canonical identity token, else raise."""
    if _POINT_RE.match(target) or _SPAN_RE.match(target) or _STAR_RE.match(target):
        return target
    raise ValueError(
        f"non-canonical target {target!r}: expected point:<λ> (full precision, "
        "no exponent), span:1…span:12 (absolute sign, no leading zero) or "
        "star:1…star:27 (AM-2; kgpo_target_form_ck)")


__all__ = ["SIGN_NAMES", "point_target", "span_sign_index", "span_sign_name",
           "span_target", "validate_canonical_target"]
