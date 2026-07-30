"""
weights.py — WEIGHTS VERSIONING AND THE WEIGHTS-VERSION ACYCLICITY MECHANISM (§7.5).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.5; brief `SHAD_DARSHANA_BRIEF_v2_0.md` §2.5.4 and
its §7 rail "weights are versioned artifacts — a field build pins its weights version; silent
weight mutation = drift failure".

═══════════════════════════════════════════════════════════════════════════════════════════
  THE PROBLEM THIS MODULE EXISTS TO SOLVE
═══════════════════════════════════════════════════════════════════════════════════════════
`mi_bhara` (L5) fits weights from `ka_kshetra`'s (L3) field. `ka_kshetra` needs weights to
build that field. Expressed as DAG edges that is `ka_kshetra → mi_bhara → ka_kshetra`, a cycle
`resolveBuildPlan`'s `topoSort` rejects — and it would reject **every plan containing either
asset**, i.e. break every future chart build, not merely this wave's.

The loop closes by VERSION PIN, not by DAG edge:

  1. `weights v0_classical` is seeded **by migration** (Lane C's 476), not by a writer. So
     every chart's very first build finds an ACTIVE weights version. There is no NULL-weights
     code path and no build order in which `ka_kshetra` needs `mi_bhara` to have run.
  2. `ka_kshetra` READS the newest active version — a DATA dependency, not a build dependency.
  3. `mi_bhara` WRITES a new version row. INSERT only; never UPDATE an existing version.
  4. The NEXT `ka_kshetra` rebuild pins the newer version.

  ⇒ the calibration loop closes ACROSS builds while the DAG stays acyclic WITHIN every build.

═══════════════════════════════════════════════════════════════════════════════════════════
  SUB-RULE 5 — RESOLVE ONCE, IN `plan_substeps`. THE STRADDLING-BUILD BUG.
═══════════════════════════════════════════════════════════════════════════════════════════
`ka_kshetra` is a heavy writer whose stage-4/5 substeps can run for many minutes. If each
substep re-queried `kala_field_weight_versions`, a build that STRADDLED an `mi_bhara` release
would write some `kala_field` segments under `v0_classical` and the rest under `v1_…` — one
snapshot, two models, and a `field_snapshot_id` that is not reproducible. Nothing would report
an error; the field would simply be quietly wrong.

So the version is resolved EXACTLY ONCE, in `plan_substeps`, and carried in the substep plan
payload. Every substep reads the pin FROM THE PLAN and never re-queries.

`pin_once` + `WeightsPinnedPlan` below are that mechanism, and they are deliberately usable by
ANY heavy field writer rather than being private to `mi_bhara`: `ka_kshetra` is Lane C's file,
but the mechanism is Lane E's, and one implementation is the only way two writers can be sure
they pinned the same way. The detector is
`tests/l5/test_mi_bhara_weights_acyclicity.py::test_pin_is_resolved_once_even_when_a_new_version_lands_mid_build`,
which drives a connection whose answer CHANGES between calls and asserts every substep still
sees the first answer.

═══════════════════════════════════════════════════════════════════════════════════════════
  SUB-RULE 6 — THE GUARD IS A POSITIVE ASSERTION
═══════════════════════════════════════════════════════════════════════════════════════════
`assert_no_weights_cycle` asserts (a) `'mi_bhara' NOT IN ka_kshetra.depends_on` and (b) a plan
containing `{ka_kshetra, mi_bhara, mi_sankalpa}` topo-sorts WITHOUT error. (b) is the half that
matters: a guard that only checks (a) would pass by not-noticing if the edge were added under
a different name, whereas a topo-sort either produces an order or raises.

Everything here except `resolve_weights_version` is a pure function; that one takes a
connection-like object and issues exactly one SELECT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

#: The version seeded by migration 476 (Lane C's keystone). Every chart's first build finds it.
V0_CLASSICAL = "v0_classical"

STATUS_ACTIVE = "active"
STATUS_SUPERSEDED = "superseded"
STATUS_REJECTED = "rejected"

SCOPE_GLOBAL = "global"
SCOPE_PER_CHART = "per_chart"

#: §7.5's selection query. Per-chart versions win over global ones; among equals, the most
#: recently activated. Ordering by `version_id` as the tiebreak makes it total, so two
#: processes resolving at the same instant cannot disagree.
_SELECT_ACTIVE = """
    SELECT version_id, scope, fitted_from_chart_id, x_schema_version, activated_at
      FROM kala_field_weight_versions
     WHERE status = 'active'
       AND (scope = 'global' OR fitted_from_chart_id = %s)
     ORDER BY (fitted_from_chart_id = %s) DESC, activated_at DESC, version_id DESC
     LIMIT 1
"""


class WeightsResolutionError(RuntimeError):
    """No active weights version exists.

    This is a HALT, not a fallback. Migration 476 seeds `v0_classical` precisely so this
    cannot happen; if it does, the seed did not run, and building a field against invented
    weights would produce a hash that means nothing (§1 rail 8, §N.8).
    """


@dataclass(frozen=True)
class WeightsPin:
    """The resolved, pinned weights version for ONE build.

    Immutable by construction: this object is created once per build and read many times. It
    is also the object that enters the §7.4 field-hash input, so `to_payload`/`from_payload`
    are a stable, order-independent serialization (`sort_keys=True`).
    """

    version_id: str
    scope: str
    x_schema_version: str
    fitted_from_chart_id: str | None = None

    def to_payload(self) -> str:
        return json.dumps(
            {
                "version_id": self.version_id,
                "scope": self.scope,
                "x_schema_version": self.x_schema_version,
                "fitted_from_chart_id": self.fitted_from_chart_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def from_payload(payload: str) -> "WeightsPin":
        d = json.loads(payload)
        return WeightsPin(
            version_id=d["version_id"],
            scope=d["scope"],
            x_schema_version=d["x_schema_version"],
            fitted_from_chart_id=d.get("fitted_from_chart_id"),
        )


def resolve_weights_version(conn: Any, chart_id: str) -> WeightsPin:
    """§7.5 step 2 — read the newest active version for this chart. ONE SELECT, no writes.

    Per-chart-scoped versions are preferred over global ones (§7.5 "Per-chart vs global
    scope"), and the selection rule is part of the field-hash input because it determines
    `weights_version`.
    """
    with conn.cursor() as cur:
        cur.execute(_SELECT_ACTIVE, (chart_id, chart_id))
        row = cur.fetchone()
    if row is None:
        raise WeightsResolutionError(
            "no active row in kala_field_weight_versions — migration 476 seeds "
            f"'{V0_CLASSICAL}' exactly so this cannot happen. Building a field against "
            "invented weights would produce a field_snapshot_id that means nothing; halting."
        )
    if isinstance(row, Mapping):
        get = row.__getitem__
    else:  # tuple row factory
        keys = ("version_id", "scope", "fitted_from_chart_id", "x_schema_version", "activated_at")
        as_map = dict(zip(keys, row))
        get = as_map.__getitem__
    fitted = get("fitted_from_chart_id")
    return WeightsPin(
        version_id=str(get("version_id")),
        scope=str(get("scope")),
        x_schema_version=str(get("x_schema_version")),
        fitted_from_chart_id=str(fitted) if fitted is not None else None,
    )


@dataclass
class WeightsPinnedPlan:
    """A substep plan that carries its weights pin — the SUB-RULE 5 mechanism.

    Constructed ONCE per build (in `plan_substeps`). `pin` is resolved at construction and is
    never re-resolved; `substep_key` embeds it so the pin survives even a plan that is
    persisted and resumed across process restarts (`build_substep_progress` keys on the
    substep key, so a resumed build reads the ORIGINAL pin, not today's newest version).
    """

    pin: WeightsPin
    _resolutions: int = 0

    @staticmethod
    def pin_once(conn: Any, chart_id: str) -> "WeightsPinnedPlan":
        return WeightsPinnedPlan(pin=resolve_weights_version(conn, chart_id), _resolutions=1)

    def substep_key(self, stage: str, unit: str = "") -> str:
        """`'<stage>[:<unit>]@<version_id>'` — the pin travels with the key."""
        base = f"{stage}:{unit}" if unit else stage
        return f"{base}@{self.pin.version_id}"

    @staticmethod
    def version_from_substep_key(key: str) -> str:
        """The inverse. Raises on a key with no pin — an unpinned substep must never be run
        with a silently-defaulted version."""
        if "@" not in key:
            raise ValueError(
                f"substep key {key!r} carries no weights pin. Every substep of a field build "
                f"must read its version FROM THE PLAN (§7.5 sub-rule 5); re-querying the "
                f"table per substep is the straddling-build bug this rule exists to prevent."
            )
        return key.rsplit("@", 1)[1]

    def resolutions(self) -> int:
        """How many times the version has been resolved for this build. MUST stay 1."""
        return self._resolutions

    def assert_resolved_once(self) -> None:
        if self._resolutions != 1:
            raise AssertionError(
                f"weights version was resolved {self._resolutions} times in one build — "
                f"§7.5 sub-rule 5 requires exactly once, in plan_substeps. A build that "
                f"straddles an mi_bhara release would otherwise mix two weights versions "
                f"into one snapshot and produce a non-deterministic field hash."
            )


def assert_single_weights_version(rows: Iterable[Mapping[str, Any]]) -> str:
    """Assert every field row of one snapshot carries the SAME `weights_version`.

    The CI-side half of sub-rule 5: build a chart while inserting a new active version
    mid-build, then run this over that snapshot's `kala_field` rows.
    """
    versions = {str(r["weights_version"]) for r in rows}
    if not versions:
        raise ValueError("no rows to check — an empty snapshot proves nothing")
    if len(versions) > 1:
        raise AssertionError(
            f"one field snapshot carries {len(versions)} weights versions "
            f"({sorted(versions)}) — the build straddled a weights release and mixed two "
            f"models into one snapshot (§7.5 sub-rule 5)."
        )
    return versions.pop()


# ── SUB-RULE 6 — the acyclicity guard, as a POSITIVE assertion ─────────────────────────

def topo_sort(asset_ids: Sequence[str], depends_on: Mapping[str, Sequence[str]]) -> list[str]:
    """A faithful Python mirror of `platform/src/lib/build/plan.ts`'s `topoSort`.

    Same traversal, same in-scope filtering, same cycle detection (a dependency not in scope
    is skipped, exactly as the TypeScript does). Mirrored rather than imported because the
    Python writer side cannot call the TS resolver — and the TS side has its own test
    (`platform/tests/unit/build/w2_weights_acyclicity.test.ts`) asserting the real
    `resolveBuildPlan` on the real seed, so neither implementation stands alone as the proof.
    """
    in_scope = set(asset_ids)
    visited: set[str] = set()
    out: list[str] = []

    def visit(node: str, stack: set[str]) -> None:
        if node in stack:
            raise ValueError(f"Cycle detected involving asset: {node}")
        if node in visited:
            return
        stack.add(node)
        for dep in depends_on.get(node, ()):
            if dep in in_scope:
                visit(dep, stack)
        stack.discard(node)
        visited.add(node)
        out.append(node)

    for a in asset_ids:
        visit(a, set())
    return out


def assert_no_weights_cycle(depends_on: Mapping[str, Sequence[str]]) -> list[str]:
    """§7.5 sub-rule 6, both halves. Returns the topo order so a caller can assert on it.

    (a) `'mi_bhara' NOT IN ka_kshetra.depends_on` — the specific edge the design names.
    (b) `{ka_kshetra, mi_bhara, mi_sankalpa}` topo-sorts without error — the general half,
        which catches the same cycle introduced under any other name or via any longer path.
    """
    ka_deps = list(depends_on.get("ka_kshetra", ()))
    if "mi_bhara" in ka_deps:
        raise AssertionError(
            "ka_kshetra.depends_on contains 'mi_bhara' — that edge, with the required "
            "mi_bhara.depends_on = ['ka_kshetra'], forms the cycle ka_kshetra → mi_bhara → "
            "ka_kshetra, and topoSort would then reject EVERY build plan containing either "
            "asset. Weights flow by version pin across builds (§7.5), never by DAG edge."
        )
    scope = [a for a in ("ka_kshetra", "mi_bhara", "mi_sankalpa") if a in depends_on]
    return topo_sort(scope, depends_on)


# ── writing a new version (§7.5 step 3 — INSERT only, never UPDATE) ────────────────────

@dataclass(frozen=True)
class WeightRow:
    version_id: str
    weight_id: str
    weight_value: float
    prior_value: float
    n_eff: int
    clipped: bool


@dataclass(frozen=True)
class NewWeightsVersion:
    """A version row plus its parameter rows, ready to INSERT.

    Nothing in this dataclass can express an UPDATE. That is deliberate: weights are versioned
    artifacts and silent mutation is a drift failure (brief §7 rail). A correction is a NEW
    version whose predecessor is marked `superseded`, so the history is auditable.
    """

    version_id: str
    status: str
    scope: str
    x_schema_version: str
    fitted_from_chart_id: str | None
    n_events_used: int
    n_prospective_used: int
    tau_shrinkage: float
    any_clipped: bool
    fit_loglik: float | None
    holdout_loglik: float | None
    notes: str
    weights: tuple[WeightRow, ...]


def next_version_id(chart_label: str, iso_date: str, existing: Iterable[str]) -> str:
    """`'v<N>_<YYYY-MM-DD>_<chart_label>'` (§7.5's own example naming).

    `N` is one past the highest numeric prefix already present, so ids sort chronologically
    and a rerun on the same day does not collide with itself.
    """
    highest = 0
    for vid in existing:
        head = vid.split("_", 1)[0]
        if head.startswith("v") and head[1:].isdigit():
            highest = max(highest, int(head[1:]))
    return f"v{highest + 1}_{iso_date}_{chart_label}"
