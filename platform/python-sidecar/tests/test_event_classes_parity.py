"""
test_event_classes_parity.py — ADHIṢṬHĀNA Lane A4 · Event-class contract.

Guards `l0_ghatana.EVENT_CLASSES` (27 life-event classes; the SSoT for event
classification) against its TypeScript serve-side mirror
`platform/src/lib/event_classes.ts`.

Before this test + mirror pair, `l0_ghatana.EVENT_CLASSES` had NO TypeScript
counterpart: any TS code needing the same 27 classes either hardcoded a stale
subset (`lel_event_writer.ts`'s now-corrected "22 classes" comments) or did
not validate against them at all. This is the permanent CI regression gate
(mirrors `tests/test_domain_vocabulary.py`'s build<->serve parity pattern)
that keeps the two in lockstep going forward: change one side's id set,
this test fails until the other side is updated to match.
"""
from __future__ import annotations

import pathlib
import re
import sys

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_REPO = _SIDECAR.parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.l0_ghatana import EVENT_CLASSES  # noqa: E402

_EVENT_CLASSES_TS = _REPO / "platform" / "src" / "lib" / "event_classes.ts"


def _python_event_class_ids() -> set[str]:
    return {e["event_class_id"] for e in EVENT_CLASSES}


# ── 1. the Python source itself ────────────────────────────────────────────────


def test_python_event_classes_has_exactly_27_members():
    assert len(EVENT_CLASSES) == 27


def test_python_event_class_ids_are_unique():
    ids = [e["event_class_id"] for e in EVENT_CLASSES]
    assert len(ids) == len(set(ids)), (
        f"duplicate event_class_id(s) in l0_ghatana.EVENT_CLASSES: "
        f"{sorted({i for i in ids if ids.count(i) > 1})}"
    )


def test_every_event_class_carries_domain_and_lel_category():
    for e in EVENT_CLASSES:
        assert e.get("domain"), f"{e['event_class_id']}: missing domain"
        assert e.get("lel_category"), f"{e['event_class_id']}: missing lel_category"
        assert e.get("signature_model") is not None, (
            f"{e['event_class_id']}: missing signature_model"
        )


# ── 2. build <-> serve parity ────────────────────────────────────────────────────

_TS_ID_RE = re.compile(r"event_class_id:\s*'([a-z_]+)'", re.MULTILINE)
_TS_ENTRY_RE = re.compile(
    r"event_class_id:\s*'([a-z_]+)'.*?domain:\s*'([a-z_]+)'.*?lel_category:\s*'([a-z_]+)'",
    re.MULTILINE,
)


def _parse_ts_event_class_ids() -> set[str]:
    """Extract event_class_id values from the TS EVENT_CLASSES mirror."""
    text = _EVENT_CLASSES_TS.read_text()
    start = text.index("EVENT_CLASSES")
    return set(_TS_ID_RE.findall(text[start:]))


def _parse_ts_event_class_entries() -> dict[str, tuple[str, str]]:
    """Extract {event_class_id: (domain, lel_category)} from the TS mirror."""
    text = _EVENT_CLASSES_TS.read_text()
    start = text.index("EVENT_CLASSES")
    return {
        eid: (domain, lel_category)
        for eid, domain, lel_category in _TS_ENTRY_RE.findall(text[start:])
    }


def test_ts_mirror_exists():
    assert _EVENT_CLASSES_TS.is_file(), (
        f"TS mirror not found: {_EVENT_CLASSES_TS}. l0_ghatana.EVENT_CLASSES has no "
        f"TypeScript counterpart — create it (ADHIṢṬHĀNA Lane A4)."
    )


def test_python_and_typescript_event_class_ids_are_identical():
    ts_ids = _parse_ts_event_class_ids()
    py_ids = _python_event_class_ids()
    assert ts_ids == py_ids, (
        "l0_ghatana.EVENT_CLASSES and the TS mirror have drifted.\n"
        f"  only in python: {sorted(py_ids - ts_ids)}\n"
        f"  only in ts:     {sorted(ts_ids - py_ids)}"
    )


def test_ts_mirror_has_exactly_27_members():
    assert len(_parse_ts_event_class_ids()) == 27


def test_python_and_typescript_domain_and_lel_category_are_identical():
    """The TS mirror's domain/lel_category fields must match the Python source
    per-class, not just the id set — a silently-drifted classification field
    would be a real (if quieter) parity break."""
    ts_entries = _parse_ts_event_class_entries()
    py_entries = {
        e["event_class_id"]: (e["domain"], e["lel_category"]) for e in EVENT_CLASSES
    }
    assert ts_entries == py_entries, (
        "domain/lel_category mismatch between l0_ghatana.EVENT_CLASSES and the TS mirror:\n"
        + "\n".join(
            f"  {eid}: python={py_entries.get(eid)!r} ts={ts_entries.get(eid)!r}"
            for eid in sorted(set(py_entries) | set(ts_entries))
            if py_entries.get(eid) != ts_entries.get(eid)
        )
    )
