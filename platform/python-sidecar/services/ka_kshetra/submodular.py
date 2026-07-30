"""
services/ka_kshetra/submodular.py — greedy lazy facility-location submodular
selection (item 25 part 2), KALA_W2_FIELD_DESIGN_v1_0.md §6.2.

The objective (facility location, monotone submodular over a cardinality
constraint):

    F(S) = Σ_{c ∈ C}  u_c · max_{i ∈ S} cov(i, c)
    Δ(i | S) = Σ_{c ∈ C}  u_c · max(0, cov(i,c) − max_{j ∈ S} cov(j,c))

An "atom" c is a triple (event_class, window_family_id, driver_term_key):
`window_family_id` groups candidates whose active clock lord-stack at peak
is identical (the "same signal family" generalization of the existing
`window_families` dedup); `driver_term_key` names a term among the top-3
`|log_contribution|` provenance rows for that candidate.

Because F is monotone submodular and the constraint is a cardinality
constraint, greedy achieves F(S) >= (1 - 1/e)*F(OPT). Lazy (accelerated)
greedy (Minoux's algorithm) is an EXACT optimization of the same greedy
result — it changes speed, never the output — via a max-heap of marginal
gains that are only ever recomputed lazily, with submodularity itself
guaranteeing a recomputed gain never exceeds its heap-stored (stale) value.

This module never touches a database connection or another lane's tables —
it is a pure function of the candidate list a caller (eventually Lane C's
`ka_kshetra` orchestration) already assembled from `kala_field_windows` +
`kala_field_provenance` rows plus this lane's own `stage6_salience` output.
"""
from __future__ import annotations

import hashlib
import heapq
from dataclasses import dataclass

# The minimum fraction of the CURRENT F(S) a popped candidate's (stale)
# marginal gain must clear to keep the greedy loop running (§6.2 step 2).
DELTA_MIN_FRACTION = 0.01


@dataclass(frozen=True)
class ProvenanceTerm:
    """Mirrors the relevant slice of a `kala_field_provenance` row (§5.4) for
    one (window, term) pair -- Lane C/E's real rows carry many more columns;
    only these two matter to the atom/coverage computation."""

    term_key: str
    log_contribution: float


@dataclass(frozen=True)
class SubmodularCandidate:
    """One selectable row -- the shape a `kala_field_windows` row (§5.3) plus
    its salience (this lane's own §6.1 output) plus its Lane-B clock lord
    stack at peak (§5.1 C-3's `lord_stack(s,t)`) presents to the selector."""

    window_id: str
    event_class: str
    salience: float
    lord_stack_at_peak: tuple[str, ...]
    provenance_terms: tuple[ProvenanceTerm, ...]


@dataclass(frozen=True)
class Atom:
    event_class: str
    window_family_id: str
    driver_term_key: str


@dataclass(frozen=True)
class SelectionTraceEntry:
    window_id: str
    marginal_gain: float
    atoms_newly_covered: tuple[Atom, ...]
    rank: int


@dataclass(frozen=True)
class SubmodularResult:
    selected: tuple[str, ...]                      # window_ids, in selection order
    trace: tuple[SelectionTraceEntry, ...]
    largest_omission: tuple[str, float] | None      # (window_id, marginal_gain), or None if S == V
    coverage_fraction: float                        # F(S) / F(V)


def window_family_id(event_class: str, lord_stack_at_peak: tuple[str, ...]) -> str:
    """
    `sha256(event_class | sorted set of clock lord-stacks active at peak)[:16]`
    (§6.2) -- the principled generalization of the existing `window_families`
    dedup.
    """
    payload = f"{event_class}|{'|'.join(sorted(set(lord_stack_at_peak)))}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _top3_terms(terms: tuple[ProvenanceTerm, ...]) -> list[ProvenanceTerm]:
    """Top-3 by |log_contribution|, deterministic tie-break on term_key."""
    return sorted(terms, key=lambda t: (-abs(t.log_contribution), t.term_key))[:3]


def _build_atoms(
    candidates: list[SubmodularCandidate],
) -> dict[Atom, list[tuple[str, float]]]:
    """
    atom -> [(window_id, |log_contribution|), ...] for every candidate that
    carries that atom (i.e. whose top-3 driver terms include it, under the
    same event_class + window_family_id).
    """
    atoms: dict[Atom, list[tuple[str, float]]] = {}
    for cand in candidates:
        wfid = window_family_id(cand.event_class, cand.lord_stack_at_peak)
        for term in _top3_terms(cand.provenance_terms):
            atom = Atom(cand.event_class, wfid, term.term_key)
            atoms.setdefault(atom, []).append((cand.window_id, abs(term.log_contribution)))
    return atoms


def select_submodular(
    candidates: list[SubmodularCandidate],
    k: int,
    delta_min_fraction: float = DELTA_MIN_FRACTION,
) -> SubmodularResult:
    """
    Greedy lazy facility-location selection (§6.2). `k` is the row budget.
    Deterministic: identical input always produces identical output, and
    every tie (equal marginal gain) resolves to the lexicographically lower
    `window_id`.
    """
    if not candidates:
        return SubmodularResult(selected=(), trace=(), largest_omission=None, coverage_fraction=0.0)

    atoms = _build_atoms(candidates)
    salience_by_id = {c.window_id: c.salience for c in candidates}

    # u_c = max salience among candidates carrying c.
    u: dict[Atom, float] = {
        atom: max(salience_by_id[wid] for wid, _ in carriers) for atom, carriers in atoms.items()
    }
    # max_j |log_contribution_j(c)| among carriers -- the cov() normalizer.
    max_contrib: dict[Atom, float] = {
        atom: max(v for _, v in carriers) for atom, carriers in atoms.items()
    }

    # Per-atom (window_id -> contribution) lookup, for O(1) cov(i,c).
    contrib_by_atom: dict[Atom, dict[str, float]] = {
        atom: dict(carriers) for atom, carriers in atoms.items()
    }
    # Reverse index: window_id -> atoms it carries (avoids an O(atoms) scan
    # per marginal-gain recomputation).
    atoms_by_window: dict[str, list[Atom]] = {}
    for atom, carriers in atoms.items():
        for wid, _ in carriers:
            atoms_by_window.setdefault(wid, []).append(atom)

    cov_max: dict[Atom, float] = {atom: 0.0 for atom in atoms}
    selected: list[str] = []
    selected_set: set[str] = set()
    trace: list[SelectionTraceEntry] = []
    f_s = 0.0

    def marginal_gain(wid: str) -> tuple[float, list[Atom]]:
        gain = 0.0
        newly_covered: list[Atom] = []
        for atom in atoms_by_window.get(wid, ()):
            cov_i = contrib_by_atom[atom][wid] / max_contrib[atom]
            delta_cov = cov_i - cov_max[atom]
            if delta_cov > 0:
                gain += u[atom] * delta_cov
                newly_covered.append(atom)
        return gain, newly_covered

    heap: list[tuple[float, str]] = []
    for cand in candidates:
        g, _ = marginal_gain(cand.window_id)
        heapq.heappush(heap, (-g, cand.window_id))

    rank = 0
    while heap and len(selected) < k:
        neg_stale, wid = heapq.heappop(heap)
        delta_stale = -neg_stale
        if delta_stale < delta_min_fraction * f_s:
            break  # §6.2 step 2: "the popped Delta < delta_min"

        g_actual, newly_covered = marginal_gain(wid)
        if heap:
            peek_neg, _peek_wid = heap[0]
            peek_delta = -peek_neg
            accept = g_actual >= peek_delta
        else:
            accept = True

        if accept:
            rank += 1
            selected.append(wid)
            selected_set.add(wid)
            for atom in newly_covered:
                cov_i = contrib_by_atom[atom][wid] / max_contrib[atom]
                if cov_i > cov_max[atom]:
                    cov_max[atom] = cov_i
            f_s += g_actual
            trace.append(SelectionTraceEntry(
                window_id=wid, marginal_gain=g_actual,
                atoms_newly_covered=tuple(newly_covered), rank=rank,
            ))
        else:
            heapq.heappush(heap, (-g_actual, wid))

    # Largest omission: highest-Delta unselected candidate against the FINAL S.
    largest_omission: tuple[str, float] | None = None
    unselected = [c for c in candidates if c.window_id not in selected_set]
    if unselected:
        best_wid, best_gain = None, -1.0
        for cand in sorted(unselected, key=lambda c: c.window_id):
            g, _ = marginal_gain(cand.window_id)
            if g > best_gain:
                best_gain, best_wid = g, cand.window_id
        largest_omission = (best_wid, best_gain)

    f_v = sum(u.values())  # F(V): every atom covered at cov=1.0 by its top contributor
    coverage_fraction = (f_s / f_v) if f_v > 0 else 0.0

    return SubmodularResult(
        selected=tuple(selected),
        trace=tuple(trace),
        largest_omission=largest_omission,
        coverage_fraction=coverage_fraction,
    )
