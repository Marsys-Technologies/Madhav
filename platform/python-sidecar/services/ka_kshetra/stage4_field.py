"""
services/ka_kshetra/stage4_field.py — §5.2–§5.4 stage 4: field assembly,
segment construction, and the provenance edges (item 11).

Stage 4 is where the pipeline's separately-computed pieces become ONE object:
Lane A's kinematics/primitives/promise graph, Lane B's clocks/boundaries, the
pinned weights version, and the classical class priors compose into λ_e(t), which
is then STORED as log-linear segments (integrator.py) with every multiplicative
factor persisted as a provenance edge that must reconstruct the value it
explains.

── CIRCULARITY GUARD (§8.3, a HARD campaign gate — peer of LAW ZERO) ─────────
NOTHING on the stage 0–8 code path may read the life-event corpus. This module
issues no query against it and calls no capability that does. That is asserted
MECHANICALLY, by a textual census over every `services/ka_*` source file
(`tests/l3/test_ka_jivana_parva_circularity_guard.py`) and again,
ka_kshetra-specifically, by `tests/l3/ka_kshetra/test_circularity_guard.py`.

NOTE FOR ANYONE EDITING THIS DOCSTRING: the census is a plain token scan, so the
forbidden table/capability identifiers may not be written out even in a comment.
That is deliberate and it is the cheapest possible property to keep true — a
guard that had to parse imports would have blind spots a string scan does not.

The invariant CG-1 is stated over the field CONTENT hash: for any mutation of a
chart's lived-history corpus that leaves (corpus_pin, config_pin,
weights_version, cohort_version) unchanged, the hash is bit-identical before and
after. Stage 9 — and only stage 9 — may see lived outcomes.

── §N.5: L1/L3 ARE THE AUTHORITY ────────────────────────────────────────────
No table this module writes ever RESTATES a computed value owned by L1
(`chart_facts`, `chart_dashas`, `chart_positions`) or by the existing L3 writers
(`kala_gochara_windows`, `gochara_resonance_map`). Every dependent row stores a
REFERENCE — (source_table, source_pk, source_fact_id) — and inherits the value at
read time. The legacy sweep in particular is read as a CROSS-CHECK CORPUS only:
its `signed_intensity` is never copied into a field column, and W2 writes ZERO
rows to any legacy table (§1 rail 2, strangler-fig).

── WHY THE EVALUATOR IS A PURE, INJECTABLE OBJECT ───────────────────────────
`FieldEvaluator` holds no connection. Everything it needs is loaded ONCE per
(chart × event class) and then evaluated in memory. Two things depend on that:
  • the stage-5 null re-runs the SAME evaluator 256 times over circularly
    shifted envelopes; a DB round-trip per instant would make the null
    unaffordable and would tempt someone to approximate it, which would make
    every published p-value a different statistic from the documented one;
  • the whole thing is unit-testable without Postgres, so the numerics have real
    tests rather than integration-only smoke.

── LANE BOUNDARIES (§0 anti-collision contract) ─────────────────────────────
This module reads Lane A's and Lane B's TABLES and calls their published
FUNCTION SIGNATURES; it never reads their code. Where a lane's module has not
landed yet, the loaders fall back to the lane's table with the DESIGN
DOCUMENT's own stated aggregation (e.g. §3.3's noisy-OR over `kala_field_routes`)
and record which path was taken — never a silent guess.

Authority: KALA_W2_FIELD_DESIGN_v1_0.md §5.1–§5.4, §7.4, §8.3, §9.4.
"""
from __future__ import annotations

import bisect
import contextlib
import hashlib
import heapq
import json
import logging
import math
import os
import shutil
import struct
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence

import numpy as np

from services.ka_kshetra import hazard, integrator
from services.ka_kshetra.contracts import (
    ClockApplicability,
    PromisePrior,
    ProvenanceEdge,
    Route,
    Segment,
    SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT,
)

logger = logging.getLogger(__name__)

#: §5.2's horizon: birth → birth + 100 Julian years, matching the existing sweep
#: horizon so field windows and legacy sweep windows are directly comparable.
HORIZON_DAYS: float = 36525.0

#: §5.4's reconciliation tolerance, in NATS (log space). 1e-9 is ~30 orders of
#: magnitude above float64 noise for these summands, so a failure is a real
#: modelling defect, never a rounding artefact.
RECONCILIATION_TOLERANCE: float = 1e-9

#: Outermost-first ordering of the daśā ladder levels (§4.2's level vocabulary).
LEVEL_ORDER: tuple[str, ...] = ('MD', 'AD', 'PD', 'SD', 'PrD')
_LEVEL_RANK: dict[str, int] = {lvl: i for i, lvl in enumerate(LEVEL_ORDER)}

#: stage-1 `primitive_kind` → the frozen covariate key it feeds (§5.1 C-5).
#: `moorti_at_ingress` is resolved through its `class_label` (svarṇa/rajata/tāmra;
#: LOHA IS THE REFERENCE LEVEL AND GETS NO DUMMY — a fourth dummy would make the
#: design matrix rank-deficient and the fitted β's unidentifiable).
PRIMITIVE_TO_COVARIATE: dict[str, str] = {
    'contact_moon_ref': 'contact_moon_ref',
    'contact_lagna_ref': 'contact_lagna_ref',
    'av_kaksha_gate': 'av_kaksha_gate',
    'station_band': 'station_band',
    'sandhi_band': 'sandhi_band',
    'syzygy_band': 'syzygy_band',
    'panchanga_limb': 'panchanga_affinity',
}

MOORTI_TO_COVARIATE: dict[str, str] = {
    'svarna': 'moorti_svarna',
    'rajata': 'moorti_rajata',
    'tamra': 'moorti_tamra',
    # 'loha' deliberately absent — the reference level.
}

#: A `syzygy_band` primitive carrying this class_label also feeds x11
#: (`eclipse_contact` = syzygy_band × eclipse_candidate, §5.1 C-5 row 11).
ECLIPSE_CANDIDATE_LABEL: str = 'eclipse_candidate'


# ── errors ───────────────────────────────────────────────────────────────────

class ProvenanceReconciliationError(RuntimeError):
    """§5.4's halting failure. Raised inside the substep so the orchestrator
    rolls the savepoint back: a field row whose provenance does not reconstruct
    it must never reach a reader."""


class ClassSkipped(Exception):
    """An event class that cannot be built HONESTLY, with the reason.

    Not an error condition to be swallowed: the reason is recorded on
    `kala_field_snapshots.skipped_classes` so a reader sees WHY a class has no
    windows rather than inferring the chart has no hazard for it (LAW ZERO).
    """

    def __init__(self, event_class: str, reason: str, detail: str = ''):
        super().__init__(f'{event_class}: {reason} {detail}'.strip())
        self.event_class = event_class
        self.reason = reason
        self.detail = detail


class UpstreamStageIncomplete(RuntimeError):
    """Raised by a substep whose upstream stage has not committed its rows.

    §8.1's mandated defensive check. Computing on partial upstream data would
    produce a field that is silently wrong rather than visibly absent.
    """


# ── canonical serialization (§7.4) ───────────────────────────────────────────

def _canonical(value: Any) -> Any:
    """Recursively canonicalize for hashing.

    Floats become their `repr` STRING (Python's repr is the shortest round-trip-
    exact decimal, ≤17 significant digits), so the hash is identical across
    platforms and across a dump/restore that might re-render a float. §7.4
    requires exactly this property.
    """
    if isinstance(value, float):
        if math.isnan(value):
            return 'nan'
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    """Deterministic JSON: keys sorted, no incidental whitespace, floats as
    round-trip-exact reprs."""
    return json.dumps(_canonical(value), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, default=str)


@dataclass(frozen=True)
class FieldPins:
    """The PIN IDENTITY of one field build (see migration 492's header for why
    there are two snapshot identities and which one CG-1 is stated over).

    Every one of these is an input to `field_snapshot_id`, so a build under
    different weights, a different corpus, a different config or a different
    cohort is a DIFFERENT snapshot — never a silent overwrite of the previous one.
    """
    chart_id: str
    corpus_pin: str
    weights_version: str
    x_schema_version: str
    config_pin: Mapping[str, Any]
    cohort_version: Optional[str] = None

    @property
    def field_snapshot_id(self) -> str:
        payload = canonical_json({
            'chart_id': self.chart_id,
            'corpus_pin': self.corpus_pin,
            'weights_version': self.weights_version,
            'x_schema_version': self.x_schema_version,
            'cohort_version': self.cohort_version,
            'config_pin': dict(self.config_pin),
        })
        return 'kfs_' + hashlib.sha256(payload.encode('utf-8')).hexdigest()[:32]


def _positive_int_env(name: str, default: int) -> int:
    """Read a positive-int tuning knob, falling back to `default` on anything
    unparseable or non-positive rather than crashing a build over a typo'd env."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning('%s=%r is not an integer — using default %d', name, raw, default)
        return default
    if value <= 0:
        logger.warning('%s=%d is not positive — using default %d', name, value, default)
        return default
    return value


#: Rows pulled per network round-trip when streaming a hashed table (F-149).
#: Only ever this many DB rows are materialized at once.
FETCH_BATCH_ROWS = _positive_int_env('KA_KSHETRA_FETCH_BATCH_ROWS', 20_000)

#: Serialized entries held in RAM before a sorted run is spilled to disk (F-149).
#: This is the ONLY quantity that bounds `field_content_hash`'s peak memory —
#: it is deliberately independent of the row count, which is the whole point of
#: the fix. 250k × ~400B ≈ 100MB, and 10.5M rows spills 42 runs, comfortably
#: under any open-file limit.
HASH_SORT_CHUNK_ENTRIES = _positive_int_env('KA_KSHETRA_HASH_SORT_CHUNK', 250_000)

#: Free-space floor a configured `KA_KSHETRA_HASH_SPILL_DIR` must clear before
#: the writer will use it (F-185). The real spill at the native chart's 10.5M
#: rows is on the order of ~3-4.2GB (see HASH_SPILL_DIR's docstring below); 5GiB
#: gives headroom above that working estimate rather than pinning the bare
#: minimum a single run happens to need today.
REQUIRED_SPILL_FREE_BYTES = 5 * (1 << 30)


def _detect_filesystem_kind(path: str) -> Optional[str]:
    """Best-effort filesystem-type lookup for `path`, by longest matching mount
    prefix in `/proc/mounts`. Returns `None` — not a filesystem name — when the
    platform has no `/proc` (e.g. macOS dev) or the mount table cannot be read.
    An undetectable condition is reported as unknown, never silently treated as
    "confirmed not tmpfs" (§N.8: a check that cannot fail on this platform must
    say so, not report green)."""
    if not os.path.exists('/proc/mounts'):
        return None
    try:
        with open('/proc/mounts', 'r') as fh:
            lines = fh.readlines()
    except OSError:
        return None
    resolved = os.path.realpath(path)
    best_match = ''
    best_kind: Optional[str] = None
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        mount_point, fs_kind = parts[1], parts[2]
        if resolved == mount_point or resolved.startswith(mount_point.rstrip('/') + '/'):
            if len(mount_point) >= len(best_match):
                best_match = mount_point
                best_kind = fs_kind
    return best_kind


def _resolve_spill_dir_env(name: str) -> Optional[str]:
    """Read, VALIDATE, and LOG the spill-directory override (F-185).

    Unlike the sibling env-var readers above (`_positive_int_env`-backed
    KA_KSHETRA_FETCH_BATCH_ROWS / KA_KSHETRA_HASH_SORT_CHUNK), the bare
    `os.environ.get(...) or None` this replaces validated nothing and logged
    nothing — a misconfigured, missing, or silently-tmpfs spill dir was
    invisible until an OOM.

    Interim disposition (F-185, no Cloud Run volume mount exists anywhere in
    this repo's infra; provisioning one is out of scope here — see
    deploy.yml's brahma-build-pipeline-job): a tmpfs-backed directory is
    ACCEPTED rather than rejected. The accompanying deploy-config change sizes
    the Cloud Run job's `--memory` to cover the RAM-backed spill instead of
    treating tmpfs as a hard failure. What must never happen again is a SILENT
    tmpfs fallback, so this always logs the resolved path and its detected
    filesystem kind at WARNING when it is tmpfs (or undetectable), and still
    fails loudly on a configured directory that does not exist, is not
    writable, or does not clear `REQUIRED_SPILL_FREE_BYTES`.
    """
    raw = os.environ.get(name)
    if not raw:
        logger.info('%s not set — spill runs use the platform TMPDIR default', name)
        return None
    if not os.path.isdir(raw):
        raise RuntimeError(f'{name}={raw!r} does not exist or is not a directory')
    if not os.access(raw, os.W_OK):
        raise RuntimeError(f'{name}={raw!r} exists but is not writable')
    free_bytes = shutil.disk_usage(raw).free
    if free_bytes < REQUIRED_SPILL_FREE_BYTES:
        raise RuntimeError(
            f'{name}={raw!r} has only {free_bytes} bytes free, below the '
            f'required {REQUIRED_SPILL_FREE_BYTES} — refusing to configure a '
            'spill directory that cannot hold a full run')
    fs_kind = _detect_filesystem_kind(raw)
    if fs_kind is None:
        logger.warning(
            '%s=%r resolved (writable, %d bytes free) but this platform has no '
            '/proc/mounts to confirm its filesystem type — proceeding without a '
            'tmpfs determination', name, raw, free_bytes)
    elif fs_kind == 'tmpfs':
        logger.warning(
            '%s=%r resolves to a tmpfs mount — spill I/O is RAM-backed. This is '
            'the accepted F-185 interim (no disk-backed Cloud Run volume mount '
            'exists yet); the deploy config provisions memory headroom for it. '
            '%d bytes free.', name, raw, free_bytes)
    else:
        logger.info('%s=%r resolves to filesystem %r, %d bytes free',
                    name, raw, fs_kind, free_bytes)
    return raw


#: Directory for the merge-sort spill files. `None` = the platform default
#: (`TMPDIR`). Set this when `/tmp` is a small tmpfs — the spill is on the order
#: of the serialized dataset (~3GB for the native chart's 10.5M rows).
HASH_SPILL_DIR = _resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')

#: Explicit I/O buffer per spill run. Pinned rather than left to the platform
#: default because that default is `st_blksize`, which is 4KB on ext4 and 128KB
#: on APFS — a 32x swing in the merge phase's per-run overhead, and the one term
#: in this function's memory profile that grows with the RUN COUNT rather than
#: with the chunk. At the shipped 250k chunk, 10.5M rows spill 42 runs = ~2.7MB,
#: which is noise beside the ~100MB chunk itself.
_SPILL_BUFFER_BYTES = 1 << 16

_RUN_HEADER = struct.Struct('<III')


def _spill_run(entries: list[tuple[str, str, str]], spill_dir: Optional[str]):
    """Write one already-sorted run to an anonymous temp file and rewind it.

    Length-prefixed rather than delimited: `canonical_json` escapes control
    characters, so a newline-delimited format would *happen* to work today, but
    it would be a correctness claim resting on a property of a different
    function. Explicit lengths cannot be broken by a future serializer change.
    """
    fh = tempfile.TemporaryFile(dir=spill_dir, buffering=_SPILL_BUFFER_BYTES)
    pack = _RUN_HEADER.pack
    write = fh.write
    for table, key_json, payload_json in entries:
        tb = table.encode('utf-8')
        kb = key_json.encode('utf-8')
        pb = payload_json.encode('utf-8')
        write(pack(len(tb), len(kb), len(pb)))
        write(tb)
        write(kb)
        write(pb)
    fh.flush()
    fh.seek(0)
    return fh


def _read_run(fh) -> Iterator[tuple[str, str, str]]:
    """Replay one spilled run in its stored (sorted) order."""
    unpack = _RUN_HEADER.unpack
    size = _RUN_HEADER.size
    read = fh.read
    while True:
        head = read(size)
        if not head:
            return
        if len(head) != size:
            raise RuntimeError('truncated content-hash spill run — refusing to '
                               'emit a hash over a partial dataset')
        lt, lk, lp = unpack(head)
        blob = read(lt + lk + lp)
        if len(blob) != lt + lk + lp:
            raise RuntimeError('truncated content-hash spill run — refusing to '
                               'emit a hash over a partial dataset')
        yield (blob[:lt].decode('utf-8'),
               blob[lt:lt + lk].decode('utf-8'),
               blob[lt + lk:].decode('utf-8'))


def _sorted_hash_entries(
    rows: Iterable[tuple[str, tuple, Mapping[str, Any]]],
    chunk_entries: int,
    spill_dir: Optional[str],
) -> Iterator[tuple[str, str, str]]:
    """Yield every entry in total `sorted()` order using bounded memory.

    A textbook external merge sort: accumulate at most `chunk_entries`
    serialized entries, sort that run, spill it, and finally k-way merge the
    runs. The emitted order is the total order over the multiset of entries, so
    it does NOT depend on `chunk_entries` — which is what makes the resulting
    digest identical to the pre-F-149 in-memory `sorted()` implementation and
    identical across every batch size a runtime might pick.

    Fast path: a dataset that fits in one chunk never touches disk at all, so
    small builds and every unit test behave exactly as before.
    """
    runs: list[Any] = []
    buf: list[tuple[str, str, str]] = []
    try:
        for table, key, payload in rows:
            buf.append((table, canonical_json(list(key)), canonical_json(dict(payload))))
            if len(buf) >= chunk_entries:
                buf.sort()
                runs.append(_spill_run(buf, spill_dir))
                buf = []
        buf.sort()
        if not runs:
            # Single-chunk fast path — no spill file is ever created.
            yield from buf
            return
        if buf:
            runs.append(_spill_run(buf, spill_dir))
        buf = []
        logger.info('field_content_hash: merging %d spilled runs (chunk=%d entries)',
                    len(runs), chunk_entries)
        yield from heapq.merge(*(_read_run(fh) for fh in runs))
    finally:
        for fh in runs:
            with contextlib.suppress(Exception):
                fh.close()


def field_content_hash(
    pin_identity: str,
    rows: Iterable[tuple[str, tuple, Mapping[str, Any]]],
    *,
    chunk_entries: Optional[int] = None,
    spill_dir: Optional[str] = None,
) -> str:
    """§7.4's FULL hash: the pin identity plus a canonical serialization of every
    stage 0–8 row, sorted by (table_name, natural key).

    `rows` yields (table_name, natural_key_tuple, payload) with the volatile
    columns (`id`, `computed_at`, `created_at`, `released_at`) ALREADY EXCLUDED by
    the caller — including them would make two identical builds hash differently
    and turn hash-replay into a permanently-red gate. `rows` MAY be a lazy
    iterator (and, from `KaKshetraWriter`, is one).

    Sorting by the natural key (not by insertion order) is what makes the hash
    independent of substep dispatch order, which the design requires because the
    orchestrator may dispatch a plan's substeps in any order.

    THIS is the value the hash-replay CI compares and the value CIRCULARITY GUARD
    CG-1 is stated over. Comparing the pin identity alone would be a claim with no
    detector behind it (§N.8).

    ── F-149: bounded memory, UNCHANGED digest ──────────────────────────────
    This used to be `sorted(<generator>)` over a caller-materialized list, i.e.
    three simultaneous full copies of the dataset (the caller's list, the
    generator's serialized tuples, and `sorted`'s output). At the native chart's
    ~10.5M stage-0–8 rows that OOM'd, which is the confirmed root cause of the
    F-141 `ka_kshetra` incident — a rebuild was *deterministically* impossible.

    The sort is now an external merge sort bounded by `chunk_entries`, and the
    caller streams its rows from server-side cursors. The digest is byte-identical
    to the old implementation for every input, at every chunk size: the merge
    reproduces the same total order `sorted()` produced. That equality is asserted
    directly by `TestContentHash` against a reference implementation of the old
    algorithm, so this is a memory fix and NOT a hash-version change — every
    previously stored `kfh_` value stays comparable.
    """
    digest = hashlib.sha256()
    digest.update(pin_identity.encode('utf-8'))
    entries = _sorted_hash_entries(
        rows,
        chunk_entries if chunk_entries is not None else HASH_SORT_CHUNK_ENTRIES,
        spill_dir if spill_dir is not None else HASH_SPILL_DIR,
    )
    for table, key_json, payload_json in entries:
        digest.update(b'\x1e')
        digest.update(table.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(key_json.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(payload_json.encode('utf-8'))
    return 'kfh_' + digest.hexdigest()[:32]


# ── stage-1 primitives and their envelopes ───────────────────────────────────

@dataclass(frozen=True)
class Primitive:
    """One `kala_field_primitives` row: an interval with a piecewise-LINEAR
    strength envelope.

    The envelope contract is FROZEN by §3.2 and stage 4 depends on it: ≥2 knots,
    `t` strictly ascending (coincident knots are permitted precisely to make a
    STEP explicit), `v ∈ [0,1]`, linear between knots, and ZERO outside the span.
    Piecewise-linearity is not a convenience — it is what makes the log-linear
    segment representation FAITHFUL rather than merely close, because a
    breakpoint is placed at every knot.
    """
    primitive_kind: str
    subject: str
    object_ref: Optional[str]
    polarity: str
    class_label: Optional[str]
    knots: tuple[tuple[float, float], ...]
    source_pk: Optional[str] = None
    source_fact_id: Optional[str] = None
    source_table: Optional[str] = None

    @property
    def t_start(self) -> float:
        return self.knots[0][0]

    @property
    def t_end(self) -> float:
        return self.knots[-1][0]

    def value_at(self, t: float) -> float:
        if len(self.knots) < 2:
            raise ValueError(
                f'{self.primitive_kind}:{self.subject} envelope has '
                f'{len(self.knots)} knot(s); the frozen §3.2 contract requires ≥2. '
                'A one-knot envelope has no defined value anywhere and would read '
                'as an honest 0 for the entire horizon.'
            )
        # L1h: range check against tuple directly before any list allocation.
        # For the ~99% of calls where t is outside this primitive's span, this
        # avoids the [k[0] for k in self.knots] allocation entirely.
        if t < self.knots[0][0] or t > self.knots[-1][0]:
            return 0.0
        ts = [k[0] for k in self.knots]
        i = bisect.bisect_right(ts, t) - 1
        if i >= len(self.knots) - 1:
            return self.knots[-1][1]
        t0, v0 = self.knots[i]
        t1, v1 = self.knots[i + 1]
        if t1 == t0:
            # Coincident knots: the STEP's right-hand value wins, matching
            # integrator.lambda_at's right-hand-limit convention.
            return v1
        return v0 + (v1 - v0) * ((t - t0) / (t1 - t0))

    def vighna_key(self) -> str:
        """`vedha:Sa->10` — CLASS:instance. `hazard._rho_weight_id` splits on the
        first ':' to find the fitted ρ, so the class must lead."""
        return (f'{self.primitive_kind}:{self.subject}->{self.object_ref}'
                if self.object_ref else f'{self.primitive_kind}:{self.subject}')


class EnvelopeIndex:
    """The in-memory stage-1 envelope index, and the ONE place the circular
    shift is applied (§5.5).

    Splitting supportive covariates from obstructive vighna at construction time
    is deliberate: it makes it structurally impossible for an obstruction to leak
    into the log-linear modifier term M_e (where it would ADD, i.e. subtract from
    λ) instead of the multiplicative thinning term S_e (where it THINS). The
    Elevation §3 stage-4 amendment exists because that leak is easy to write and
    invisible once written.
    """

    def __init__(self, primitives: Sequence[Primitive], horizon_days: float):
        self.horizon_days = float(horizon_days)
        self.supportive: list[Primitive] = []
        self.obstructive: list[Primitive] = []
        for p in primitives:
            (self.obstructive if p.polarity == 'obstructive' else self.supportive).append(p)
        # L1i: pre-built numpy arrays for vectorized range-check in covariates_at /
        # obstructions_at.  Building these once in __init__ (the EnvelopeIndex is
        # constructed once and shared across ALL stage-4 substeps and stage-5 null
        # replicates) costs ~2 ms and eliminates the O(N_primitives) Python loop
        # that previously dominated every covariates_at call.
        self._sup_t0: np.ndarray = (
            np.array([p.knots[0][0] for p in self.supportive], dtype=np.float64)
            if self.supportive else np.empty(0, dtype=np.float64)
        )
        self._sup_t1: np.ndarray = (
            np.array([p.knots[-1][0] for p in self.supportive], dtype=np.float64)
            if self.supportive else np.empty(0, dtype=np.float64)
        )
        self._obs_t0: np.ndarray = (
            np.array([p.knots[0][0] for p in self.obstructive], dtype=np.float64)
            if self.obstructive else np.empty(0, dtype=np.float64)
        )
        self._obs_t1: np.ndarray = (
            np.array([p.knots[-1][0] for p in self.obstructive], dtype=np.float64)
            if self.obstructive else np.empty(0, dtype=np.float64)
        )

    # ── evaluation ───────────────────────────────────────────────────────────

    def covariates_at(self, t: float) -> dict[str, float]:
        """The ACTIVE entries of the twelve-covariate vector at t.

        Aggregation is MAX over same-kind primitives (§5.1 C-5 row 1: "max
        envelope over active Moon-referenced contacts"). Sum would let two weak
        simultaneous contacts masquerade as one strong one; max keeps the
        covariate on its declared [0,1] scale.

        Only non-zero entries are returned. An absent key is an honest zero, and
        `hazard.modifier_log_term` reads a missing key as exactly 0 — so an
        inactive covariate contributes nothing and emits a zero-valued (still
        present, still auditable) provenance edge.
        """
        out: dict[str, float] = {}
        if self._sup_t0.size == 0:
            return out
        # L1i: vectorized range check — finds active primitives in O(N) numpy
        # rather than O(N) Python, then calls value_at only for the K << N
        # primitives whose span contains t.
        t_f = float(t)
        active_idx = np.where((self._sup_t0 <= t_f) & (t_f <= self._sup_t1))[0]
        for i in active_idx:
            p = self.supportive[int(i)]
            v = p.value_at(t_f)
            if v <= 0.0:
                continue
            for key in self._covariate_keys(p):
                if v > out.get(key, 0.0):
                    out[key] = v
        return out

    @staticmethod
    def _covariate_keys(p: Primitive) -> tuple[str, ...]:
        if p.primitive_kind == 'moorti_at_ingress':
            key = MOORTI_TO_COVARIATE.get((p.class_label or '').lower())
            return (key,) if key else ()
        key = PRIMITIVE_TO_COVARIATE.get(p.primitive_kind)
        if key is None:
            return ()
        if p.primitive_kind == 'syzygy_band' and p.class_label == ECLIPSE_CANDIDATE_LABEL:
            # x11 = syzygy_band × eclipse_candidate. A non-eclipse syzygy
            # contributes x11 = 0 by simply not appearing here.
            return (key, 'eclipse_contact')
        return (key,)

    def obstructions_at(self, t: float) -> dict[str, float]:
        """Active vighna envelopes u_m(t) ∈ (0, 1], keyed CLASS:instance.

        Inactive obstructors are ABSENT rather than present-with-zero: a u = 0
        entry contributes ln(1) = 0 to the hazard (harmless) but would emit a
        provenance edge asserting an obstruction that was not active (not
        harmless — a reader would see a reason that is not a reason).
        """
        out: dict[str, float] = {}
        if self._obs_t0.size == 0:
            return out
        # L1i: same vectorized gate as covariates_at.
        t_f = float(t)
        active_idx = np.where((self._obs_t0 <= t_f) & (t_f <= self._obs_t1))[0]
        for i in active_idx:
            p = self.obstructive[int(i)]
            v = p.value_at(t_f)
            if v <= 0.0:
                continue
            key = p.vighna_key()
            if v > out.get(key, 0.0):
                out[key] = v
        return out

    def breakpoints(self) -> list[float]:
        """Every envelope knot. Placing a breakpoint at each is what makes the
        stored log-linear field FAITHFUL to the piecewise-linear covariates
        rather than an approximation of them."""
        return sorted({k[0] for p in self.supportive + self.obstructive for k in p.knots})

    def obstruction_sources(self) -> dict[str, Primitive]:
        return {p.vighna_key(): p for p in self.obstructive}

    # ── §5.5 the circular shift ──────────────────────────────────────────────

    def circular_shift(self, delta: float) -> 'EnvelopeIndex':
        """Rebuild the index with every primitive's knots translated by −δ and
        wrapped into [0, H), i.e. x^{(r)}(t) = x((t + δ) mod H).

        A primitive whose translated span straddles the wrap point is SPLIT into
        two pieces with the crossing value interpolated, so no signal is created
        or destroyed. That conservation is not cosmetic: if a shift could weaken
        the sky, every replicate would be a slightly easier opponent and every
        published p-value would be optimistic — the null would flatter the model
        it is supposed to falsify.

        Only stage-1 envelopes move. Clock terms C_e, promise P̃_e, the baseline
        λ⁰_e and all weights are UNCHANGED (§5.5) — that asymmetry IS the null
        hypothesis.
        """
        H = self.horizon_days
        delta = float(delta) % H if H > 0 else 0.0
        if delta == 0.0:
            return EnvelopeIndex(self.supportive + self.obstructive, H)
        out: list[Primitive] = []
        for p in self.supportive + self.obstructive:
            out.extend(_shift_primitive(p, delta, H))
        return EnvelopeIndex(out, H)


def _shift_primitive(p: Primitive, delta: float, H: float) -> list[Primitive]:
    """Translate one primitive's knots by −δ, wrapping into [0, H)."""
    knots = [(t - delta, v) for t, v in p.knots]
    shift_k = -math.floor(knots[0][0] / H) * H
    knots = [(t + shift_k, v) for t, v in knots]

    if knots[-1][0] <= H:
        return [_with_knots(p, knots)]

    # Straddles the wrap: interpolate the crossing value and emit two pieces.
    cross_v = _interp(knots, H)
    head = [(t, v) for t, v in knots if t < H] + [(H, cross_v)]
    tail = [(0.0, cross_v)] + [(t - H, v) for t, v in knots if t > H]
    pieces = []
    if len(head) >= 2:
        pieces.append(_with_knots(p, head))
    if len(tail) >= 2:
        pieces.append(_with_knots(p, tail))
    return pieces


def _with_knots(p: Primitive, knots: Sequence[tuple[float, float]]) -> Primitive:
    return Primitive(
        primitive_kind=p.primitive_kind, subject=p.subject, object_ref=p.object_ref,
        polarity=p.polarity, class_label=p.class_label,
        knots=tuple((float(t), float(v)) for t, v in knots),
        source_pk=p.source_pk, source_fact_id=p.source_fact_id, source_table=p.source_table,
    )


def _interp(knots: Sequence[tuple[float, float]], t: float) -> float:
    ts = [k[0] for k in knots]
    if t <= ts[0]:
        return knots[0][1]
    if t >= ts[-1]:
        return knots[-1][1]
    i = bisect.bisect_right(ts, t) - 1
    t0, v0 = knots[i]
    t1, v1 = knots[i + 1]
    if t1 == t0:
        return v1
    return v0 + (v1 - v0) * ((t - t0) / (t1 - t0))


# ── the daśā ladder ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LadderPeriod:
    """One precision-SUPPORTED period from Lane B's `kala_field_boundaries`.

    Rule C-5: a level whose `precision_state = 'precision_unsupported'` is never
    loaded, so it simply does not appear in the running lord stack and its d_ℓ
    term is ABSENT. That is the operational form of "no claim is ever served at a
    precision the input uncertainty cannot support" — the level does not get a
    down-weighted vote, it gets no vote.
    """
    system_id: str
    level: str
    lord: str
    t_start: float
    t_end: float


class FieldEvaluator:
    """λ_e(t) for ONE (chart × event class), evaluable at any instant.

    Holds no connection: everything is loaded once and evaluated in memory. See
    the module docstring for why that is load-bearing rather than a style choice.
    """

    def __init__(
        self,
        *,
        event_class: str,
        lifetime_count: float,
        promise: PromisePrior,
        clocks: Sequence[ClockApplicability],
        ladder: Mapping[str, Sequence[LadderPeriod]],
        envelopes: EnvelopeIndex,
        weights: Mapping[str, float],
        horizon_days: float = HORIZON_DAYS,
        baseline_source: Optional[tuple[str, str, str]] = None,
        extra_breakpoints: Sequence[float] = (),
        shape_only: bool = False,
    ):
        self.event_class = event_class
        self.shape_only = shape_only  # P3-a: threaded into terms_at() → hazard.evaluate()
        self.lifetime_count = float(lifetime_count)
        self.promise = promise
        self.clocks = list(clocks)
        self.ladder = {
            sid: sorted(periods, key=lambda p: (_LEVEL_RANK.get(p.level, 99), p.t_start))
            for sid, periods in ladder.items()
        }
        self.envelopes = envelopes
        self.weights = dict(weights)
        self.horizon_days = float(horizon_days)
        self.baseline_source = baseline_source
        self.extra_breakpoints = tuple(float(t) for t in extra_breakpoints)
        # L1j: pre-built binary-search arrays per (system_id, level) for O(log N)
        # lord_stacks_at instead of the O(N) linear scan over 165K+ periods.
        # Periods in self.ladder are already sorted by (_LEVEL_RANK, t_start), so
        # grouping by level here preserves outermost-first order (MD→AD→PD→SD→PrD).
        self._ladder_bsearch: dict[str, list[tuple[str, list[float], list[float], list[str]]]] = {}
        for sid, periods in self.ladder.items():
            levels_data: list[tuple[str, list[float], list[float], list[str]]] = []
            cur_level = ''
            lvl_t_starts: list[float] = []
            lvl_t_ends: list[float] = []
            lvl_lords: list[str] = []
            for p in periods:
                if p.level != cur_level:
                    if cur_level:
                        levels_data.append((cur_level, lvl_t_starts, lvl_t_ends, lvl_lords))
                    cur_level = p.level
                    lvl_t_starts = []
                    lvl_t_ends = []
                    lvl_lords = []
                lvl_t_starts.append(p.t_start)
                lvl_t_ends.append(p.t_end)
                lvl_lords.append(p.lord)
            if cur_level:
                levels_data.append((cur_level, lvl_t_starts, lvl_t_ends, lvl_lords))
            self._ladder_bsearch[sid] = levels_data

    # ── inputs at an instant ─────────────────────────────────────────────────

    def lord_stacks_at(self, t: float) -> dict[str, list[tuple[str, str]]]:
        """The running (level, lord) stack per system at t, OUTERMOST FIRST.

        Half-open containment `[t_start, t_end)` so a boundary instant belongs to
        exactly one period — the same discipline §6.3's cohort MD-chain join
        uses, and for the same reason: a closed interval double-counts the
        boundary and an open one drops it.

        L1j: O(log N) via pre-built binary-search arrays instead of O(N) linear
        scan. For this chart 165K+ periods reduce to ~110 bisect comparisons.
        """
        out: dict[str, list[tuple[str, str]]] = {}
        for sid, levels_data in self._ladder_bsearch.items():
            stack: list[tuple[str, str]] = []
            for level, lvl_t_starts, lvl_t_ends, lvl_lords in levels_data:
                # bisect_right gives the first i where t_starts[i] > t, so
                # t_starts[idx] <= t for idx = result - 1.
                idx = bisect.bisect_right(lvl_t_starts, t) - 1
                if idx >= 0 and lvl_t_ends[idx] > t:  # [t_start, t_end) containment
                    stack.append((level, lvl_lords[idx]))
            if stack:
                out[sid] = stack
        return out

    def terms_at(self, t: float) -> hazard.HazardTerms:
        """The full §5.1 decomposition at t, including its provenance edges.

        P3-a: `self.shape_only` is threaded into `hazard.evaluate()` so that
        `HazardTerms.baseline_is_synthetic` is correctly set on every evaluation
        for shape_only classes.  The calibrated path is COMPLETELY UNCHANGED when
        `self.shape_only is False` (the default).
        """
        return hazard.evaluate(
            lifetime_count=self.lifetime_count,
            promise=self.promise,
            clocks=self.clocks,
            lord_stacks=self.lord_stacks_at(t),
            covariates=self.envelopes.covariates_at(t),
            obstructions=self.envelopes.obstructions_at(t),
            weights=self.weights,
            baseline_source=self.baseline_source,
            shape_only=self.shape_only,
        )

    def ln_lambda(self, t: float) -> float:
        return self.terms_at(t).ln_lambda

    # ── breakpoints + segments ───────────────────────────────────────────────

    def breakpoints(self) -> list[float]:
        """§5.2's breakpoint set B_e, clipped to [0, H].

        The union of: every stage-0 kinematics root (passed in as
        `extra_breakpoints`), every stage-1 envelope knot, every
        precision-supported daśā boundary, and the horizon ends. λ is smooth
        between these and kinked at them, so refining anywhere else buys nothing
        and refining nowhere else misses every real kink.
        """
        pts = {0.0, self.horizon_days}
        pts.update(self.envelopes.breakpoints())
        for periods in self.ladder.values():
            for p in periods:
                pts.add(p.t_start)
                pts.add(p.t_end)
        pts.update(self.extra_breakpoints)
        return sorted(t for t in pts if math.isfinite(t) and 0.0 <= t <= self.horizon_days)

    def build_segments(
        self,
        *,
        tau: float = integrator.DEFAULT_TAU,
        max_depth: int = integrator.DEFAULT_MAX_DEPTH,
    ) -> list[Segment]:
        return integrator.build_segments(self.breakpoints(), self.ln_lambda,
                                         tau=tau, max_depth=max_depth)


# ── §5.4 the reconciliation invariant ────────────────────────────────────────

def assert_provenance_reconciles(
    edges: Sequence[ProvenanceEdge],
    lambda_value: float,
    *,
    target_id: str,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> None:
    """THE §5.4 INVARIANT: |ln(λ) − Σ log_contribution| ≤ 1e-9.

    Asserted here (halting the substep, so the orchestrator rolls its savepoint
    back) AND in CI over both canonical charts.

    This is the §N.8 detector for the claim "this window's provenance explains
    it". The code paths that make it correctly read FALSE are real and were both
    exercised in test: a term added to λ without a matching edge, and an edge
    whose stored value drifts from what the evaluator actually multiplied in.
    Identity edges (`route`, `gate`) carry log_contribution = 0.0 by construction,
    so the sum is over ALL of the target's rows exactly as §5.4 words it.
    """
    if lambda_value <= 0.0 or not math.isfinite(lambda_value):
        raise ProvenanceReconciliationError(
            f'provenance_reconciliation_failed: target={target_id} has non-positive '
            f'lambda={lambda_value!r}. λ is strictly positive by construction (§5.1); '
            'a non-positive value means the hazard model is broken upstream.'
        )
    total = math.fsum(e.log_contribution for e in edges)
    delta = abs(math.log(lambda_value) - total)
    if delta > tolerance:
        raise ProvenanceReconciliationError(
            f'provenance_reconciliation_failed: target={target_id} '
            f'ln(lambda)={math.log(lambda_value)!r} but Σ log_contribution={total!r} '
            f'(|Δ|={delta!r} > {tolerance}). A provenance row set that does not '
            'reconstruct the value it explains is not weak evidence — it is no '
            'evidence (§5.4 / CLAUDE.md §N.8).'
        )


def require_baseline(
    lifetime_count: Optional[float],
    event_class: str,
    *,
    shape_only: bool = False,
) -> float:
    """§5.1 C-1's honest-skip gate.

    "A class with no prior row is `not_computed` and is SKIPPED ENTIRELY (no
    field rows written for it) — NEVER GIVEN A MADE-UP BASELINE."

    This is the single place that rule is enforced, and it deliberately raises
    rather than returning a sentinel: a caller that forgets to check a sentinel
    would silently build a class on a fabricated λ⁰, which is precisely the B.10
    violation the rule exists to prevent.

    P3-a (DHARA_ENGINE_SPEC_v1_0.md §4.1, SM-R-10): when `shape_only=True` is
    explicitly passed (the writer has already looked up the tier-basis table and
    confirmed this class is a shape_only tier), a missing or non-positive
    `lifetime_count` does NOT raise ClassSkipped — instead the function returns
    SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT (1.0) as the lifetime_count.  The caller
    is responsible for threading `shape_only=True` into `hazard.evaluate()` so
    the resulting `HazardTerms.baseline_is_synthetic = True` tag is set.

    CRITICAL: `shape_only=True` is passed ONLY when `lifetime_count is None`
    (class absent from bg_class_priors). Passing it when a real calibrated prior
    exists would silently replace calibrated data with synthetic — B.10 forbids
    that. The writer enforces this by checking the lookup result before deciding
    which path to take (P3-e caller contract).

    When `shape_only=False` (the default): the original ClassSkipped behaviour is
    COMPLETELY UNCHANGED.
    """
    if lifetime_count is None:
        if shape_only:
            return SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT
        raise ClassSkipped(event_class, 'no_class_prior_row',
                           'no bg_class_priors lifetime-count row for this event class')
    if not math.isfinite(lifetime_count) or lifetime_count <= 0.0:
        if shape_only:
            return SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT
        raise ClassSkipped(event_class, 'class_prior_not_positive',
                           f'lifetime_count={lifetime_count!r}')
    return float(lifetime_count)


# ── DB loaders (lane-boundary crossings are TABLE reads or published fns) ────

def _normalize_batch(cur, fetched, cols: Optional[list[str]] = None) -> list[dict]:
    """Normalize psycopg2 tuple rows and psycopg3/dict-cursor rows alike —
    the same defensive shape `ka_gochara_sweep` uses, because the sidecar runs
    against both cursor factories depending on entry point."""
    if not fetched:
        return []
    if isinstance(fetched[0], dict):
        return [dict(r) for r in fetched]
    if cols is None:
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in fetched]


def _rows(cur) -> list[dict]:
    """Eager fetch — correct and preferred for the SMALL, bounded lookups
    (weights, clocks, one snapshot row) this module's loaders do.

    Do NOT use it for a per-chart fact table: `ka_kshetra`'s largest hashed
    tables run to millions of rows for a real chart, and `fetchall()` there is
    half of the F-149 OOM. Use `iter_rows` + `streaming_cursor` for those.
    """
    return _normalize_batch(cur, cur.fetchall())


def iter_rows(cur, batch_size: Optional[int] = None) -> Iterator[dict]:
    """Stream normalized dict rows, materializing at most `batch_size` at once.

    Falls back to `_rows` for any cursor without `fetchmany` (the in-memory test
    fake is one), so this is safe to use unconditionally — but note the fallback
    is only memory-safe because such cursors hold small fixtures. The real
    memory guarantee comes from pairing this with `streaming_cursor`: on a
    CLIENT-side psycopg cursor, libpq has already buffered the entire result set
    before `fetchmany` returns its first batch, so batching alone would not have
    fixed F-149.
    """
    fetchmany = getattr(cur, 'fetchmany', None)
    if fetchmany is None:
        yield from _rows(cur)
        return
    size = batch_size if batch_size is not None else FETCH_BATCH_ROWS
    cols: Optional[list[str]] = None
    while True:
        fetched = fetchmany(size)
        if not fetched:
            return
        if cols is None and not isinstance(fetched[0], dict):
            cols = [d[0] for d in cur.description]
        yield from _normalize_batch(cur, fetched, cols)


@contextlib.contextmanager
def streaming_cursor(conn, name_hint: str = 'kfh', itersize: Optional[int] = None):
    """A server-side (named) cursor when the driver supports one, else a plain one.

    A named cursor is what actually bounds memory: it becomes a `DECLARE ...
    CURSOR` + `FETCH FORWARD n`, so the client never holds more than one batch.
    `DECLARE` is read-only and participates in the caller's transaction, so this
    stays inside the FROZEN orchestrator contract — the writer neither commits
    nor closes `ctx.db_conn`, it only opens and closes its own cursor.

    Cursor names are UUID-suffixed because a named cursor's name must be unique
    within its transaction, and this is called once per hashed table.
    """
    size = itersize if itersize is not None else FETCH_BATCH_ROWS
    cur = None
    try:
        try:
            cur = conn.cursor(name=f'{name_hint}_{uuid.uuid4().hex}')
        except Exception as exc:  # driver has no named cursors — degrade, don't fail
            # Logged rather than silent: a fallback to a client-side cursor
            # silently reinstates the F-149 memory profile on a big table, and a
            # degradation nobody can see is how that defect survived the first time.
            logger.warning('no server-side cursor for %s (%s) — falling back to a '
                           'client-side cursor; memory is NOT bounded on this path',
                           name_hint, exc)
            cur = None
        if cur is None:
            cur = conn.cursor()
        else:
            with contextlib.suppress(Exception):
                cur.itersize = size
        yield cur
    finally:
        close = getattr(cur, 'close', None)
        if close is not None:
            with contextlib.suppress(Exception):
                close()


def resolve_weights_pin(conn) -> tuple[str, dict[str, float]]:
    """§7.5 step 2 + sub-rule 5: resolve the ACTIVE weights version ONCE.

    The caller must do this in `plan_substeps` and carry the result in the plan;
    every substep reads the PINNED value from the plan and never re-queries. A
    long build that straddles an `mi_bhara` release would otherwise produce
    segments under two different weights versions in one snapshot — a
    non-deterministic field hash and a silently mixed model.

    NOTE this is a DATA dependency, not a build edge: `ka_kshetra` never lists
    `mi_bhara` in `depends_on` (that cycle would break every chart build). The
    loop closes ACROSS builds by version pin.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT version_id FROM kala_field_weight_versions "
            "WHERE status = 'active' ORDER BY activated_at DESC, version_id DESC LIMIT 1"
        )
        rows = _rows(cur)
    if not rows:
        raise RuntimeError(
            'no active kala_field_weight_versions row. migration 491 seeds '
            "'v0_classical' and MUST land before ka_kshetra ever runs — it is the "
            'acyclicity keystone (§7.5). There is deliberately no unpinned code path.'
        )
    version_id = rows[0]['version_id']
    with conn.cursor() as cur:
        cur.execute(
            'SELECT weight_id, weight_value FROM kala_field_weights WHERE version_id = %s',
            (version_id,),
        )
        weights = {r['weight_id']: float(r['weight_value']) for r in _rows(cur)}
    return version_id, weights


def load_class_lifetime_count(conn, event_class: str) -> tuple[Optional[float], Optional[tuple]]:
    """N_e — the class's expected lifetime count over 100 years (§5.1 C-1).

    Read from `brahma_class_priors` (asset `bg_class_priors`) at the reserved
    coordinate

        fact_kind = 'lifetime_count_per_100y'
        signal_type_class = <event_class>
        source_subsystem = '*'  ·  signal_tradition = '*'

    ── COVERAGE, AS OF THE `bg_class_lifetime_counts` LANE ──────────────────
    The gap this docstring used to describe ("returns None for every class until
    an L0 lane seeds the rows") is CLOSED. `brahmagyan/l0_class_lifetime_counts.py`
    + migration 522 seed SIX classes at `prior_version = 'ne_v01'`, every one of
    them written at the reserved ('*','*') coordinate: childbirth, marriage,
    separation, relocation, foreign_settlement, surgery. Every OTHER event class
    still has no row and is still honestly SKIPPED with `no_class_prior_row`
    recorded on the snapshot — that remains the shippable default (the L0
    module's own Tier N-iii), not a defect. `brahma_class_priors` (migration 387)
    additionally holds signal-salience priors under a DIFFERENT `fact_kind`,
    which is why `fact_kind` is pinned below and not merely assumed.

    ⚠ WHY ALL FOUR PREDICATES ARE PINNED, AND WHY THE ORDER IS TOTAL (§N.7
    item 2). The table's uniqueness is over the FIVE columns
    (prior_version, signal_type_class, fact_kind, source_subsystem,
    signal_tradition). Filtering on only the first three leaves the last two free,
    so any row a sibling lane writes at a NARROWER coordinate — a subsystem- or
    tradition-specific prior — becomes a live candidate for the same `LIMIT 1`,
    and `ORDER BY prior_version DESC` alone does not break the tie: Postgres may
    return either. N_e is λ⁰_e, the CHART-INDEPENDENT baseline of the whole hazard
    field, so a heap-scan-order-dependent N_e would make the field — and the §7.4
    field hash built on it — non-deterministic in a way no version pin covers.
    Hence: both coordinate columns are pinned to '*' (a narrower row is NOT a
    fallback — a class with no ('*','*') row has no chart-independent baseline and
    is skipped), and the ordering is completed with the two coordinate columns so
    it is total even if the pin is ever relaxed.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT prior_version, class_prior
                 FROM brahma_class_priors
                WHERE fact_kind = 'lifetime_count_per_100y'
                  AND signal_type_class = %s
                  AND source_subsystem = '*'
                  AND signal_tradition = '*'
                ORDER BY prior_version DESC, source_subsystem, signal_tradition
                LIMIT 1""",
            (event_class,),
        )
        rows = _rows(cur)
    if not rows:
        return None, None
    pk = f"{rows[0]['prior_version']}|lifetime_count_per_100y|{event_class}"
    return float(rows[0]['class_prior']), ('brahma_class_priors', pk, None)


def load_event_shape(conn, event_class: str) -> Optional[str]:
    """`brahma_event_ontology.temporal_shape` for this class — READ, never derived.

    The shape (point / interval / chain) is a property of the EVENT CLASS, fixed
    by the ontology (migration 456), not a property of how long a particular
    window happens to be. Deriving it from a window's duration would be exactly
    the §N.7-item-3 defect: a local constant shadowing an authoritative value,
    and one that would silently reclassify the same class differently on two
    charts. Returns None when the class has no ontology row, which the caller
    turns into an honest skip rather than a default.
    """
    with conn.cursor() as cur:
        cur.execute(
            'SELECT temporal_shape FROM brahma_event_ontology WHERE event_class_id = %s',
            (event_class,),
        )
        rows = _rows(cur)
    if not rows or not rows[0].get('temporal_shape'):
        return None
    return str(rows[0]['temporal_shape'])


def require_event_shape(shape: Optional[str], event_class: str) -> str:
    """Honest-skip gate for the ontology, mirroring `require_baseline`.

    A class with no ontology row has no known shape, no magnitude floor and no
    domain — §6.1's Consequence factor reads the same table. Guessing 'interval'
    because it is the commonest value is a plausible-sounding default standing in
    for "I don't know" (§N.7 item 6); the class is skipped instead, with the
    reason recorded on the snapshot.
    """
    if shape not in ('point', 'interval', 'chain'):
        raise ClassSkipped(event_class, 'no_event_ontology_row',
                           f'brahma_event_ontology.temporal_shape={shape!r}')
    return shape


def load_promise_prior(conn, chart_id: str, event_class: str) -> PromisePrior:
    """Lane A's promise prior (§3.3).

    Prefers Lane A's published function `stage2_promise.promise_prior` — the ONE
    function §3.3 publishes across the A→C boundary. If that module has not
    landed yet, falls back to reading Lane A's TABLE `kala_field_routes` and
    applying §3.3's OWN stated aggregation, the noisy-OR

        P_e = 1 − Π_{r ∈ routes(e)} (1 − p_r)

    Reading another lane's table is explicitly permitted by §0; re-deriving its
    routing algorithm would not be, and this does not — Yen's K-shortest-paths
    result is consumed as stored.
    """
    try:                                     # pragma: no cover - lane-landing dependent
        from services.ka_kshetra.stage2_promise import promise_prior  # type: ignore
    except Exception:
        pass
    else:                                    # pragma: no cover - lane-landing dependent
        return promise_prior(chart_id, event_class, conn)

    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, route_rank, path_node_ids, path_edge_ids, route_gain,
                      is_primary, suppressed_by
                 FROM kala_field_routes
                WHERE chart_id = %s AND event_class = %s
                ORDER BY route_rank""",
            (chart_id, event_class),
        )
        rows = _rows(cur)

    routes = tuple(
        Route(
            event_class=event_class,
            route_rank=int(r['route_rank']),
            path_node_ids=tuple(r['path_node_ids'] or ()),
            route_gain=float(r['route_gain']),
            is_primary=bool(r['is_primary']),
            suppressed_by=tuple(r['suppressed_by'] or ()),
            path_edge_ids=tuple(r['path_edge_ids'] or ()),
        )
        for r in rows
    )
    p = 1.0 - math.prod(1.0 - r.route_gain for r in routes) if routes else 0.0
    return PromisePrior(p=min(max(p, 0.0), 1.0), routes=routes, n_routes=len(routes),
                        fact_ids=tuple(f'kala_field_routes:{r["id"]}' for r in rows))


def load_clocks(conn, chart_id: str) -> list[ClockApplicability]:
    """Lane B's `kala_field_clocks`, read as a table (§0-permitted crossing)."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT system_id, applicability_state, exclusion_reason, competence_class,
                      seniority_rank, quality, quality_basis, is_predictive
                 FROM kala_field_clocks
                WHERE chart_id = %s
                ORDER BY seniority_rank, system_id""",
            (chart_id,),
        )
        rows = _rows(cur)
    return [
        ClockApplicability(
            system_id=r['system_id'],
            applicability_state=r['applicability_state'],
            competence_class=r['competence_class'],
            seniority_rank=int(r['seniority_rank']),
            is_predictive=bool(r['is_predictive']),
            quality=None if r['quality'] is None else float(r['quality']),
            quality_basis=r.get('quality_basis'),
            exclusion_reason=r.get('exclusion_reason'),
        )
        for r in rows
    ]


def load_ladder(conn, chart_id: str) -> dict[str, list[LadderPeriod]]:
    """Precision-SUPPORTED periods from Lane B's `kala_field_boundaries`.

    `precision_state = 'precision_unsupported'` rows are EXCLUDED at the query
    (rule C-5): such a level contributes no hazard factor at all, rather than a
    reduced one. A boundary row gives the period START; its end is the next
    boundary at the same (system, level), or the horizon.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT system_id, level, lord, t_boundary, period_days, precision_state
                 FROM kala_field_boundaries
                WHERE chart_id = %s AND precision_state <> 'precision_unsupported'
                ORDER BY system_id, level, t_boundary""",
            (chart_id,),
        )
        rows = _rows(cur)

    by_key: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_key.setdefault((r['system_id'], r['level']), []).append(r)

    out: dict[str, list[LadderPeriod]] = {}
    for (system_id, level), group in by_key.items():
        for i, r in enumerate(group):
            t0 = float(r['t_boundary'])
            t1 = (float(group[i + 1]['t_boundary']) if i + 1 < len(group)
                  else t0 + float(r['period_days'] or 0.0))
            if t1 <= t0:
                continue
            out.setdefault(system_id, []).append(
                LadderPeriod(system_id=system_id, level=level, lord=r['lord'],
                             t_start=t0, t_end=t1)
            )
    return out


def load_primitives(conn, chart_id: str) -> list[Primitive]:
    """Lane A's `kala_field_primitives`, parsed into evaluable envelopes."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT primitive_kind, subject, object_ref, envelope, polarity,
                      class_label, source_table, source_pk, source_fact_id
                 FROM kala_field_primitives
                WHERE chart_id = %s
                ORDER BY primitive_kind, subject, COALESCE(object_ref,''), t_start""",
            (chart_id,),
        )
        rows = _rows(cur)

    out: list[Primitive] = []
    for r in rows:
        env = r['envelope']
        if isinstance(env, str):
            env = json.loads(env)
        knots = tuple((float(k['t']), float(k['v'])) for k in env)
        if len(knots) < 2:
            # §3.2's contract is violated upstream. Skipping silently would make
            # the field quietly weaker; halting names the producing lane's bug.
            raise ValueError(
                f'kala_field_primitives envelope for {r["primitive_kind"]}:{r["subject"]} '
                f'has {len(knots)} knot(s); the frozen §3.2 contract requires ≥2.'
            )
        out.append(Primitive(
            primitive_kind=r['primitive_kind'], subject=r['subject'],
            object_ref=r.get('object_ref'), polarity=r['polarity'],
            class_label=r.get('class_label'), knots=knots,
            source_table=r.get('source_table'), source_pk=r.get('source_pk'),
            source_fact_id=r.get('source_fact_id'),
        ))
    return out


def load_kinematics_breakpoints(conn, chart_id: str) -> list[float]:
    """Every `kala_field_kinematics.t_days` — the stage-0 Brent roots."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT DISTINCT t_days FROM kala_field_kinematics WHERE chart_id = %s '
            'ORDER BY t_days',
            (chart_id,),
        )
        return [float(r['t_days']) for r in _rows(cur)]


def load_legacy_crosscheck(conn, chart_id: str, event_class: str) -> list[dict]:
    """READ-ONLY cross-check corpus: the legacy `kala_gochara_windows` rows.

    §5.3: W2 writes NOTHING to this table and NEVER copies `signed_intensity`
    into a field column (§N.5). It records only the CLASSIFICATION of
    agreement/divergence as a `term_role='gate'` provenance edge, so W6 has a
    reference to classify against. The equivalence corpus and the cutover are W6
    work; W2 only ensures the reference exists.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, window_start, window_end, peak_date, temporal_shape
                 FROM kala_gochara_windows
                WHERE chart_id = %s AND event_class = %s
                  AND generation = COALESCE(
                        (SELECT authoritative_generation
                           FROM kala_gochara_authority
                          WHERE chart_id = kala_gochara_windows.chart_id), 'v1')
                ORDER BY window_start, peak_date""",
            (chart_id, event_class),
        )
        return _rows(cur)


__all__ = [
    'HORIZON_DAYS', 'RECONCILIATION_TOLERANCE', 'LEVEL_ORDER',
    'PRIMITIVE_TO_COVARIATE', 'MOORTI_TO_COVARIATE', 'ECLIPSE_CANDIDATE_LABEL',
    'SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT',   # re-exported for writer convenience
    'ProvenanceReconciliationError', 'ClassSkipped', 'UpstreamStageIncomplete',
    'canonical_json', 'FieldPins', 'field_content_hash',
    'iter_rows', 'streaming_cursor',
    'Primitive', 'EnvelopeIndex', 'LadderPeriod', 'FieldEvaluator',
    'assert_provenance_reconciles', 'require_baseline', 'require_event_shape',
    'resolve_weights_pin', 'load_class_lifetime_count', 'load_event_shape',
    'load_promise_prior',
    'load_clocks', 'load_ladder', 'load_primitives',
    'load_kinematics_breakpoints', 'load_legacy_crosscheck',
]
