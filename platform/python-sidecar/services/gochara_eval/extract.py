"""Generation-extract input adapter (protocol v2.3 §4, §9.1).

Loads a scored-extract JSON (the '3.0' baseline format: header + rows with
event_class, ws, we, pk, si, valence, adv, resolution, temporal_shape), then:

  * MEASURES the file's sha256 at load and compares it to the declared pin
    (condition C4 / §9.1 — measured, not asserted; INPUT_REJECTED on mismatch);
  * validates every row's class against the §2 27-class universe
    (INPUT_REJECTED on any unknown class);
  * runs the §4.5 sign-convention adapter on RAW rows before merging: any raw
    row with si < 0 is a machine-readable INPUT_REJECTED stop;
  * merges overlapping/abutting same-class windows (§4.2 dedup), merge
    representative = max si, ties → earliest peak, ONE tie tolerance 1e-9;
  * freezes candidate-set membership per §4.6 (span-years-clipped, mask-clipped)
    via metrics.candidate_set — one set for N, hit and rank.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .registry import CLASSES_27, TIE_TOL


class InputRejected(ValueError):
    """Machine-readable INPUT_REJECTED stop (protocol §4.5, §9.1).

    Carries the reason and any offending rows so the CLI can write them to the
    result file before exiting non-zero.
    """

    def __init__(self, reason: str, offending_rows: list | None = None):
        super().__init__(reason)
        self.reason = reason
        self.offending_rows = offending_rows or []


def measure_sha256(raw_bytes: bytes) -> str:
    """The extract hash is MEASURED at load, never asserted (protocol §9.1)."""
    return hashlib.sha256(raw_bytes).hexdigest()


@dataclass(frozen=True)
class MergedWindow:
    """One merged candidate window: (class, ws, we, pk, si) on IST dates.

    mechanism: optional label carried from raw extract rows (per-mechanism
    attribution, protocol §10 B5.4 disclosures) — None when the extract does
    not label mechanisms.
    """

    cls: str
    ws: dt.date
    we: dt.date
    pk: dt.date
    si: float
    mechanism: str | None = None

    def overlaps(self, lo: dt.date, hi: dt.date) -> bool:
        return self.ws <= hi and self.we >= lo

    def days_in_horizon(self, h0: dt.date, h1: dt.date) -> int:
        lo, hi = max(self.ws, h0), min(self.we, h1)
        return max(0, (hi - lo).days + 1)


@dataclass
class Extract:
    """Validated extract: merged candidates per class + audit record."""

    merged: dict[str, list[MergedWindow]]
    raw_counts: dict[str, int]         # raw rows per class (pre-merge)
    sha256: dict                       # {declared_pin, measured, match}
    valence_domain: dict[str, int]     # raw valence tally (descriptive only)
    dedup_table: dict[str, list[int]]  # class -> [raw_rows, merged_candidates]
    row_count: int
    meta: dict = field(default_factory=dict)  # header minus rows


def load_extract(path: str | Path, declared_pin: str | None = None) -> Extract:
    """Load, hash-check, class-check, sign-check, and merge an extract.

    Raises InputRejected on hash mismatch, unknown class, or any raw si < 0.
    """
    path = Path(path)
    raw_bytes = path.read_bytes()
    measured = measure_sha256(raw_bytes)
    sha_block = {"declared_pin": declared_pin, "measured": measured,
                 "match": (declared_pin is None) or (measured == declared_pin)}
    if declared_pin is not None and measured != declared_pin:
        raise InputRejected("extract sha256 differs from the declared pin "
                            f"(measured {measured}, declared {declared_pin})")

    doc = json.loads(raw_bytes)
    rows = doc["rows"]

    unknown = sorted({r["event_class"] for r in rows} - set(CLASSES_27))
    if unknown:
        raise InputRejected(
            f"extract classes outside the 27-class universe: {unknown}")

    # §4.5 sign-convention adapter on RAW rows, before merging.
    bad = [r for r in rows if float(r["si"]) < 0]
    if bad:
        raise InputRejected("raw rows with si < 0 (§4.5 sign-convention adapter)",
                            offending_rows=bad[:5])

    valence_domain: dict[str, int] = {}
    for r in rows:
        v = r.get("valence")
        valence_domain[v] = valence_domain.get(v, 0) + 1

    merged = merge_windows(rows)
    raw_counts: dict[str, int] = {}
    for r in rows:
        raw_counts[r["event_class"]] = raw_counts.get(r["event_class"], 0) + 1
    dedup_table = {c: [raw_counts[c], len(merged[c])] for c in sorted(merged)}

    meta = {k: v for k, v in doc.items() if k != "rows"}
    return Extract(merged=merged, raw_counts=raw_counts, sha256=sha_block,
                   valence_domain=valence_domain, dedup_table=dedup_table,
                   row_count=len(rows), meta=meta)


def merge_windows(rows: list[dict]) -> dict[str, list[MergedWindow]]:
    """§4.2 dedup: merge overlapping/abutting same-class windows before counting.

    Merge representative: the merged candidate carries the peak date and si of
    its highest-si member; ties go to the earliest peak date. Rows are sorted
    by (ws, we, pk, si) before merging (same ordering as the v2.3 scorer).
    Mechanism labels are taken from the representative row when present.
    """
    by_cls: dict[str, list[tuple]] = {}
    for r in rows:
        w = (dt.date.fromisoformat(r["ws"]), dt.date.fromisoformat(r["we"]),
             dt.date.fromisoformat(r["pk"]), float(r["si"]), r.get("mechanism"))
        by_cls.setdefault(r["event_class"], []).append(w)

    merged: dict[str, list[MergedWindow]] = {}
    for c, ws in by_cls.items():
        ws.sort()
        cur: list[list] = []
        for w in ws:
            if cur and w[0] <= cur[-1][1] + dt.timedelta(days=1):
                p = cur[-1]
                # merge representative: max si; ties -> earliest peak (§4.2)
                if w[3] > p[3] + TIE_TOL:
                    pk, si, mech = w[2], w[3], w[4]
                elif abs(w[3] - p[3]) <= TIE_TOL:
                    pk, si, mech = min(p[2], w[2]), p[3], p[4]
                else:
                    pk, si, mech = p[2], p[3], p[4]
                cur[-1] = [p[0], max(p[1], w[1]), pk, si, mech]
            else:
                cur.append(list(w))
        merged[c] = [MergedWindow(cls=c, ws=w[0], we=w[1], pk=w[2], si=w[3],
                                  mechanism=w[4]) for w in cur]
    return merged
