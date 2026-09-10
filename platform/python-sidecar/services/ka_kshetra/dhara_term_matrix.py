"""
services/ka_kshetra/dhara_term_matrix.py — Term matrix artifact (DHARA Design §4).

The term matrix stores a per-knot, per-term decomposition of ln λ_e(t) for each
knot t_k in the global knot set K assembled by the DHARA sweep (section 2.1).

Schema (DHARA_DESIGN_v1_0.md §4.2 + Appendix C.3 + F-06/F-14 amendments):

    term_matrix[k, :] = [
        ln λ⁰_e,                    # col 0: baseline (constant, ln of lam0)
        ln P̃_e,                     # col 1: promise (constant)
        w_1 A_1 r_{1,e}(t_k),       # cols 2..2+S-1: one per clock system
        β_1 x_1(t_k), ...,          # cols 2+S..2+S+11: 12 frozen covariates
        ln(1-ρ_1·u_1(t_k)), ...,    # cols 2+S+12..T-1: one per active vighna
    ]

Column count: T = 2 + S + 12 + V
    S = applicable predictive clock systems
    12 = COVARIATE_KEYS length (frozen for W2)
    V = distinct vighna classes active for this event class

STORAGE DECISION (Appendix C.3):  the matrix stores UNWEIGHTED raw terms —
    clock:  raw w_s * A_s * r_{s,e}(t_k)  (the full weighted clock log factor)
    mod:    raw β_j * x_j(t_k)            (zero if β not in weights version)
    sup:    ln(1-ρ_m·u_m(t_k))            (embeds current ρ, rho-refit needs raw u)

F-06/F-14 AMENDMENT: .npz additionally stores:
    raw_u_matrix: float32[K, V]  raw u_m(t_k) values (ρ-free)
    rho_values:   float32[V]     ρ_m at build time (one per vighna column)

This enables rho-refit without a full field rebuild: new suppression term =
    ln(1 - ρ_new * u_m(t_k))
using only raw_u_matrix + the new ρ vector.

PURITY: no DB, no IO beyond np.savez_compressed, no RNG.

Authority: DHARA_DESIGN_v1_0.md §4, Appendix C.3.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

import numpy as np

from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.hazard import COVARIATE_KEYS

# ── Public column-id prefix constants (spec §4.3) ────────────────────────────

_COL_BASELINE = 'baseline'
_COL_PROMISE = 'promise'
_PREFIX_CLOCK = 'clock:'
_PREFIX_MOD = 'mod:'
_PREFIX_SUP = 'sup:'

# ── TermMatrixRow — per-knot snapshot that the sweep populates ────────────────

@dataclass
class TermMatrixRow:
    """One row of the term matrix, capturing every additive log-domain term at
    a single knot t_k.

    Populated by `build_term_matrix_row` from a `HazardTerms` snapshot.
    Assembled into the full matrix by `build_term_matrix`.

    Field naming follows the spec's log-domain decomposition (§4.2):

        ln λ_e(t_k) = baseline + promise
                    + sum(clock_terms)
                    + sum(modifier_terms)
                    + sum(suppression_log_terms)

    The five groups are stored separately so `build_term_matrix` can lay them
    out in the spec-mandated column order with their corresponding column_ids.

    F-06/F-14: raw_u_values + rho_values are stored alongside suppression_log_terms
    so a ρ-refit can reconstruct ln(1-ρ_new*u) without a full hazard rebuild.
    """
    baseline: float
    """ln λ⁰_e = ln(N_e / 36525) — constant over the horizon."""

    promise: float
    """ln P̃_e = ln(P_floor + (1-P_floor)*P_e) — constant over the horizon."""

    clock_terms: list[float]
    """One entry per applicable predictive clock system.  Value = w_s*A_s*r_{s,e}(t_k)."""

    clock_ids: list[str]
    """Column labels for clock_terms, e.g. ['clock:vimshottari', 'clock:chara']."""

    modifier_terms: list[float]
    """Twelve entries, one per COVARIATE_KEYS entry.  Value = β_j * x_j(t_k)."""

    modifier_ids: list[str]
    """Column labels for modifier_terms, e.g. ['mod:x1_contact_moon_ref', ...]."""

    suppression_log_terms: list[float]
    """One entry per active vighna class.  Value = ln(1 - ρ_m * u_m(t_k))."""

    suppression_ids: list[str]
    """Column labels for suppression terms, e.g. ['sup:vedha:Sa->10', ...]."""

    raw_u_values: list[float]
    """Raw u_m(t_k) ∈ [0,1], ρ-free, for F-06/F-14 rho-refit recovery."""

    rho_values: list[float]
    """ρ_m at build time, for F-14 rho-refit recovery."""


# ── Extraction from HazardTerms ───────────────────────────────────────────────

def build_term_matrix_row(
    terms: Any,   # services.ka_kshetra.hazard.HazardTerms (typed as Any to avoid
                  # circular imports in calling contexts; duck-typed on .edges)
    evaluator: Any,   # FieldEvaluator or None — not used currently; reserved for
                      # future per-knot contextual extraction
) -> TermMatrixRow:
    """Extract a TermMatrixRow from a HazardTerms snapshot at one knot.

    Reads the `edges` tuple on `terms` to collect per-term contributions without
    re-deriving any computed value (§N.5 / §N.7).  The edges are the canonical
    provenance decomposition (§5.4 reconciliation invariant) — their
    `log_contribution` fields sum to `terms.ln_lambda` by construction.

    Spec mapping:
        HazardTerms.baseline          → math.log(baseline)     → col 'baseline'
        HazardTerms.promise_term      → math.log(promise_term)  → col 'promise'
        edges[role='clock']           → log_contribution        → col 'clock:<system>'
        edges[role='modifier']        → log_contribution        → col 'mod:<key>'
        edges[role='suppression']     → log_contribution        → col 'sup:<key>'
                                         weight_value           → rho_m
                                         (1-exp(log_contribution))/rho_m → u_m

    The baseline and promise fields on HazardTerms are the LINEAR-DOMAIN values
    (lam0 and p_tilde respectively); this function takes their logs to produce
    the log-domain column values matching the spec.

    For suppression edges: the stored `log_contribution = ln(1 - ρ * u)`.  The raw
    u_m is recovered via:
        u_m = (1 - exp(log_contribution)) / ρ_m
    This is exact (the inverse of the definition, valid for ρ > 0, u ∈ [0,1]).
    When ρ = 0 (identity suppression), u is ill-defined; we store 0.0 in that case
    since the suppression edge contributes exactly 0 regardless.
    """
    baseline_log = math.log(terms.baseline)
    promise_log = math.log(terms.promise_term)

    clock_terms: list[float] = []
    clock_ids: list[str] = []
    modifier_terms: list[float] = []
    modifier_ids: list[str] = []
    suppression_log_terms: list[float] = []
    suppression_ids: list[str] = []
    raw_u_values: list[float] = []
    rho_values: list[float] = []

    for edge in terms.edges:
        role = edge.term_role
        if role == 'clock':
            # term_key format: 'clock:<system_id>:<level>:<lord>'
            # column_id convention (spec §4.3): 'clock:<system_id>'
            # The spec uses system-level granularity for columns (one column per
            # system, not per lord-level-lord tuple).  We extract system_id from
            # the term_key by splitting on ':' and taking the second segment.
            parts = edge.term_key.split(':', 2)
            system_id = parts[1] if len(parts) >= 2 else edge.term_key
            col_id = f'{_PREFIX_CLOCK}{system_id}'
            # Accumulate into the same clock column if same system appears twice
            # (should not happen, but be safe)
            if col_id in clock_ids:
                idx = clock_ids.index(col_id)
                clock_terms[idx] += edge.log_contribution
            else:
                clock_terms.append(edge.log_contribution)
                clock_ids.append(col_id)
        elif role == 'modifier':
            # term_key format: 'modifier:x{i}_{covariate_key}'
            # column_id convention: 'mod:x{i}_{covariate_key}'
            # Strip the 'modifier:' prefix and replace with 'mod:'
            raw_key = edge.term_key
            if raw_key.startswith('modifier:'):
                col_suffix = raw_key[len('modifier:'):]
            else:
                col_suffix = raw_key
            col_id = f'{_PREFIX_MOD}{col_suffix}'
            modifier_terms.append(edge.log_contribution)
            modifier_ids.append(col_id)
        elif role == 'suppression':
            # term_key format: 'suppression:<vighna_key>'
            # column_id convention: 'sup:<vighna_key>'
            raw_key = edge.term_key
            if raw_key.startswith('suppression:'):
                col_suffix = raw_key[len('suppression:'):]
            else:
                col_suffix = raw_key
            col_id = f'{_PREFIX_SUP}{col_suffix}'
            log_contrib = edge.log_contribution
            suppression_log_terms.append(log_contrib)
            suppression_ids.append(col_id)
            # F-06/F-14: recover raw u_m = (1 - exp(log_contrib)) / rho_m
            rho_m = float(edge.weight_value) if edge.weight_value is not None else 0.0
            if rho_m > 0.0:
                u_m = (1.0 - math.exp(log_contrib)) / rho_m
                # Clamp to [0,1] against float noise
                u_m = max(0.0, min(1.0, u_m))
            else:
                u_m = 0.0
            raw_u_values.append(u_m)
            rho_values.append(rho_m)
        # 'baseline', 'promise', 'route', 'gate' edges are handled via the
        # top-level baseline_log / promise_log fields; identity/route edges
        # (log_contribution = 0) do not contribute a separate column.

    return TermMatrixRow(
        baseline=baseline_log,
        promise=promise_log,
        clock_terms=clock_terms,
        clock_ids=clock_ids,
        modifier_terms=modifier_terms,
        modifier_ids=modifier_ids,
        suppression_log_terms=suppression_log_terms,
        suppression_ids=suppression_ids,
        raw_u_values=raw_u_values,
        rho_values=rho_values,
    )


# ── Matrix assembly ───────────────────────────────────────────────────────────

def build_term_matrix(
    knot_times: np.ndarray,
    rows: list[TermMatrixRow],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the full term matrix from per-knot TermMatrixRow objects.

    Column layout (spec §4.2):
        [0]          baseline
        [1]          promise
        [2..2+S-1]   clock systems (S = len(rows[0].clock_terms))
        [2+S..2+S+11] modifiers (12 fixed covariates)
        [2+S+12..]   suppression terms (V per active vighna class)

    Column order within each group is taken from rows[0]; all rows MUST have the
    same clock_ids, modifier_ids, and suppression_ids (same column structure).

    Args:
        knot_times: float64 array shape [K] — the sorted global knot set K.
        rows: list of K TermMatrixRow objects, one per knot.

    Returns:
        term_matrix:    float64 array shape [K, T]
        column_ids:     unicode ndarray shape [T]
        raw_u_matrix:   float32 array shape [K, V]
        rho_values_arr: float32 array shape [V]

    Raises:
        ValueError: if rows is empty, or if rows have inconsistent column layouts.
    """
    if len(rows) == 0:
        raise ValueError('build_term_matrix requires at least one TermMatrixRow')
    K = len(rows)
    if len(knot_times) != K:
        raise ValueError(
            f'knot_times length ({len(knot_times)}) must match rows length ({K})'
        )

    # Derive column layout from the first row
    first = rows[0]
    S = len(first.clock_terms)
    V = len(first.suppression_log_terms)
    T = 2 + S + 12 + V

    # Build column_ids array
    col_ids: list[str] = [_COL_BASELINE, _COL_PROMISE]
    col_ids.extend(first.clock_ids)
    col_ids.extend(first.modifier_ids)
    col_ids.extend(first.suppression_ids)
    assert len(col_ids) == T, (
        f'Column ID count mismatch: expected {T}, got {len(col_ids)}'
    )
    column_ids = np.array(col_ids, dtype=object).astype(str)

    # Allocate arrays
    term_matrix = np.empty((K, T), dtype=np.float64)
    raw_u_matrix = np.empty((K, V), dtype=np.float32)

    # Fill per row
    for k, row in enumerate(rows):
        # Validate layout consistency (fast path: just check lengths)
        if len(row.clock_terms) != S:
            raise ValueError(
                f'Row {k} has {len(row.clock_terms)} clock terms; expected {S}'
            )
        if len(row.modifier_terms) != 12:
            raise ValueError(
                f'Row {k} has {len(row.modifier_terms)} modifier terms; expected 12'
            )
        if len(row.suppression_log_terms) != V:
            raise ValueError(
                f'Row {k} has {len(row.suppression_log_terms)} suppression terms; expected {V}'
            )

        term_matrix[k, 0] = row.baseline
        term_matrix[k, 1] = row.promise
        for s, ct in enumerate(row.clock_terms):
            term_matrix[k, 2 + s] = ct
        for j, mt in enumerate(row.modifier_terms):
            term_matrix[k, 2 + S + j] = mt
        for v, st in enumerate(row.suppression_log_terms):
            term_matrix[k, 2 + S + 12 + v] = st
            raw_u_matrix[k, v] = float(row.raw_u_values[v])

    # rho_values: use first row's values; assert consistency (all rows share same rho)
    if V > 0:
        rho_values_arr = np.array(first.rho_values, dtype=np.float32)
        # Consistency check on a sample of rows (avoid O(K*V) scan at full cost)
        for k in (K // 4, K // 2, 3 * K // 4, K - 1):
            k = min(k, K - 1)
            row_rho = np.array(rows[k].rho_values, dtype=np.float32)
            if not np.allclose(row_rho, rho_values_arr, atol=1e-5):
                raise ValueError(
                    f'rho_values inconsistency at row {k}: '
                    f'first row has {rho_values_arr.tolist()!r}, '
                    f'row {k} has {row_rho.tolist()!r}. '
                    'rho is a weights-version constant; it must be the same at every knot.'
                )
    else:
        rho_values_arr = np.empty(0, dtype=np.float32)

    return term_matrix, column_ids, raw_u_matrix, rho_values_arr


# ── .npz save ─────────────────────────────────────────────────────────────────

def save_term_matrix(
    path: str,
    chart_id: str,
    event_class: str,
    knot_times: np.ndarray,
    rows: list[TermMatrixRow],
    weights_version: str,
    x_schema_version: str,
) -> str:
    """Assemble and write the term matrix .npz artifact (spec §4.3 + F-06/F-14).

    The .npz contains:
        knot_times       float64[K]
        term_matrix      float64[K, T]
        column_ids       str[T]
        weights_version  scalar str
        x_schema_version scalar str
        raw_u_matrix     float32[K, V]  (F-06 amendment)
        rho_values       float32[V]     (F-14 amendment)

    No DB access.  Returns the path written (identical to `path` argument).
    """
    term_matrix, column_ids, raw_u_matrix, rho_values_arr = build_term_matrix(
        knot_times, rows
    )
    np.savez_compressed(
        path,
        knot_times=knot_times.astype(np.float64),
        term_matrix=term_matrix,
        column_ids=column_ids,
        weights_version=np.array(weights_version),
        x_schema_version=np.array(x_schema_version),
        raw_u_matrix=raw_u_matrix,
        rho_values=rho_values_arr,
    )
    return path


# ── Refit path ────────────────────────────────────────────────────────────────

def refit_from_term_matrix(
    npz_path: str,
    new_weights: dict[str, float],
    old_weights: dict[str, float],
) -> list[Segment]:
    """Refit the field from a saved term matrix using updated weight values.

    Complexity: O(|K| * T) — matrix assembly + O(|K|) segment construction.
    For |K| ~ 40K, T ~ 25, this completes in milliseconds.

    The refit algorithm (spec §4.5 + Appendix C.3):

    For constant columns ('baseline', 'promise'):
        No weight; stored value is used as-is.

    For clock columns ('clock:*'):
        Stored value = w_s * A_s * r_{s,e}(t_k)  (weighted).
        Refit: if column_id in new_weights → use new_weights[column_id] as
               multiplier applied to the raw clock rate.
        NOTE: because the clock columns store the FULLY WEIGHTED value
        (w_s * A_s * r) already embedded, we follow Appendix C.3's instruction:
        new_value = (new_w / old_w) * stored_value when old_w != 0.

    For modifier columns ('mod:*'):
        Stored value = β_j * x_j(t_k).
        Refit: new_value = new_β_j * x_j = (new_β / old_β) * stored_value.
        Keyed by column_id, e.g. 'mod:x1_contact_moon_ref'.

    For suppression columns ('sup:*'):
        Stored value = ln(1 - ρ_old * u_m(t_k)).
        CANNOT be refitted by scaling — ln(1-ρ*u) is nonlinear in ρ.
        Correct refit: use raw_u_matrix[:, v] + new_rho → ln(1 - ρ_new * u).
        rho key lookup: 'rho:<vighna_class>' where vighna_class = the first
        colon-delimited segment of the vighna instance key (same as hazard._rho_weight_id).

    Segment construction (spec §4.5):
        alpha_i  = ln_lambda_new[i]
        gamma_i  = (ln_lambda_new[i+1] - ln_lambda_new[i]) / (t_{i+1} - t_i)

    Args:
        npz_path:    path to a .npz file produced by save_term_matrix
        new_weights: mapping of column_id or weight_id → new weight value
        old_weights: mapping of column_id or weight_id → old weight value
                     (used to divide out the embedded weight for weighted columns)

    Returns:
        list of Segment objects, length K-1, indexed 0..K-2.
    """
    data = np.load(npz_path, allow_pickle=False)
    knot_times = data['knot_times']           # float64[K]
    raw_matrix = data['term_matrix']          # float64[K, T]
    column_ids_arr = data['column_ids']       # str[T]
    raw_u_matrix = data['raw_u_matrix']       # float32[K, V]
    rho_values_stored = data['rho_values']    # float32[V]

    column_ids: list[str] = [str(c) for c in column_ids_arr]
    K, T = raw_matrix.shape

    # Build new weighted matrix row by row is slow; do it column-wise.
    new_matrix = raw_matrix.copy()  # float64[K, T]

    sup_col_offset = 0  # index into raw_u_matrix / rho_values_stored

    for col_idx, col_id in enumerate(column_ids):
        if col_id in (_COL_BASELINE, _COL_PROMISE):
            # Constant terms; no weight applies.
            pass

        elif col_id.startswith(_PREFIX_CLOCK):
            # Stored = w_s * A_s * r.  Refit by ratio new_w / old_w.
            # Weight key: col_id itself ('clock:<system_id>'), or could be
            # 'w_s:<system_id>' in the weights dict — check both.
            system_id = col_id[len(_PREFIX_CLOCK):]
            w_key_id = f'w_s:{system_id}'
            new_w = _get_weight(new_weights, col_id, w_key_id)
            old_w = _get_weight(old_weights, col_id, w_key_id)
            if old_w is not None and new_w is not None and old_w != 0.0:
                new_matrix[:, col_idx] *= (new_w / old_w)
            elif new_w is not None and old_w == 0.0:
                # Cannot divide out; leave stored value (safe: if old_w=0, stored=0)
                pass

        elif col_id.startswith(_PREFIX_MOD):
            # Stored = β_j * x_j(t_k).  Refit by ratio new_β / old_β.
            # The modifier column_id is 'mod:x{i}_{covariate_key}'.
            # Weight key in hazard: 'beta:x{i}' (COVARIATE_WEIGHT_IDS).
            # Accept lookup by col_id directly in new_weights, or by derived beta key.
            # Extract 'x{i}_{covariate_key}' from 'mod:x{i}_{covariate_key}'
            mod_suffix = col_id[len(_PREFIX_MOD):]  # e.g. 'x1_contact_moon_ref'
            # Extract 'x1' part for beta key
            x_part = mod_suffix.split('_')[0]         # e.g. 'x1'
            beta_key = f'beta:{x_part}'               # e.g. 'beta:x1'
            new_beta = _get_weight(new_weights, col_id, beta_key)
            old_beta = _get_weight(old_weights, col_id, beta_key)
            if new_beta is not None and old_beta is not None and old_beta != 0.0:
                new_matrix[:, col_idx] *= (new_beta / old_beta)
            elif new_beta is not None and old_beta is not None and old_beta == 0.0:
                # Stored values are 0 (β_old * x = 0); set to new_beta * x.
                # Cannot recover x from stored 0; leave as 0 (same column remains 0).
                pass

        elif col_id.startswith(_PREFIX_SUP):
            # Stored = ln(1 - ρ_old * u_m).  Cannot scale linearly — use raw u.
            # Column-to-vighna-index: sup_col_offset tracks position in raw_u_matrix.
            v = sup_col_offset
            sup_col_offset += 1

            # Determine rho key: 'rho:<vighna_class>' where vighna_class is the
            # first colon-delimited segment of the instance key.
            # col_id = 'sup:vedha:Sa->10' → vighna_class = 'vedha'
            sup_suffix = col_id[len(_PREFIX_SUP):]         # 'vedha:Sa->10'
            vighna_class = sup_suffix.split(':', 1)[0]     # 'vedha'
            rho_key = f'rho:{vighna_class}'

            new_rho = _get_weight(new_weights, rho_key)
            old_rho = _get_weight(old_weights, rho_key)

            if new_rho is not None:
                # Use raw u_m values to recompute ln(1 - ρ_new * u_m(t_k))
                u_col = raw_u_matrix[:, v].astype(np.float64)  # [K]
                new_log_sup = np.log1p(-new_rho * u_col)       # [K]
                new_matrix[:, col_idx] = new_log_sup
            # If new_rho not in new_weights, leave stored ln(1-ρ_old*u) unchanged.

    # Sum all columns → ln_lambda_new[k] for each knot
    ln_lambda_new = new_matrix.sum(axis=1)  # float64[K]

    # Build Segment list
    segments: list[Segment] = []
    for i in range(K - 1):
        alpha = float(ln_lambda_new[i])
        dt = float(knot_times[i + 1]) - float(knot_times[i])
        gamma = (float(ln_lambda_new[i + 1]) - alpha) / dt if dt > 0.0 else 0.0
        segments.append(Segment(
            index=i,
            t_start=float(knot_times[i]),
            t_end=float(knot_times[i + 1]),
            alpha=alpha,
            gamma=gamma,
        ))
    return segments


# ── Weight lookup helper ──────────────────────────────────────────────────────

def _get_weight(
    weights: dict[str, float],
    *keys: str,
) -> Optional[float]:
    """Return the first value found in `weights` for any of the given keys, or None."""
    for key in keys:
        if key in weights:
            return float(weights[key])
    return None


# ── Public API ────────────────────────────────────────────────────────────────

__all__ = [
    'TermMatrixRow',
    'build_term_matrix_row',
    'build_term_matrix',
    'save_term_matrix',
    'refit_from_term_matrix',
]
