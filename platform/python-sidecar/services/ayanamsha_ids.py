"""Stored ayanamsha vocabulary for sidecar HTTP boundaries (Lahiri-primary, N-339).

All five ayanamshas are computed and stored; ``lahiri_chitrapaksha`` is the
PRIMARY reading at serve time for every chart and the other four are a
labelled cross-check set. This module is the single sidecar-side statement of
the STORED long ids (the values of ``chart_facts.ayanamsha_id`` and friends)
so routers do not each grow their own list.

Two boundary styles:

* strict -- ``StoredAyanamshaId`` (a ``Literal``) on a pydantic field: any
  other string is a 422. Used where the request is only ever built by our own
  callers (permission_curve, taranga).
* lenient -- ``normalize_ayanamsha_id`` maps the short / legacy spellings that
  older callers still send (``lahiri``, ``kp``, ``true_citra`` ...) to the
  stored id and raises ``ValueError`` for anything unknown. Used where legacy
  callers exist (pyhora).

The TypeScript twin is ``platform/src/lib/retrieval/chart_facts_helpers.ts``.
"""
from __future__ import annotations

from typing import Literal, Optional, get_args

StoredAyanamshaId = Literal[
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

#: Serve order: the primary first, then the four cross-check ayanamshas.
STORED_AYANAMSHA_IDS: tuple[str, ...] = tuple(get_args(StoredAyanamshaId))

PRIMARY_AYANAMSHA_ID: str = "lahiri_chitrapaksha"
CROSS_CHECK_AYANAMSHA_IDS: tuple[str, ...] = tuple(
    a for a in STORED_AYANAMSHA_IDS if a != PRIMARY_AYANAMSHA_ID
)

# Legacy / short spellings -> stored id (lower-case keys).
_ALIASES: dict[str, str] = {
    "lahiri": "lahiri_chitrapaksha",
    "chitrapaksha": "lahiri_chitrapaksha",
    "true_citra": "true_chitra",
    "true_chitra_paksha": "true_chitra",
    "chitra": "true_chitra",
    "kp": "krishnamurti",
    "surya_siddhanta": "surya_siddhanta_classical",
}


def normalize_ayanamsha_id(raw: Optional[str]) -> str:
    """Stored long id for ``raw``; ``None`` / empty means the primary (Lahiri).

    Raises ``ValueError`` listing the stored ids for anything unknown, so the
    caller can turn it into a 422 -- never a silent fallback to Lahiri.
    """
    if raw is None or not str(raw).strip():
        return PRIMARY_AYANAMSHA_ID
    key = str(raw).strip().lower()
    if key in STORED_AYANAMSHA_IDS:
        return key
    if key in _ALIASES:
        return _ALIASES[key]
    raise ValueError(
        f"Unknown ayanamsha_id {raw!r}; expected one of {list(STORED_AYANAMSHA_IDS)}"
    )
