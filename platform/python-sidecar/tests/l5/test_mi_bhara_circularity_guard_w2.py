"""
test_mi_bhara_circularity_guard_w2 — ṢAḌ-DARŚANA W2 Lane E · THE CIRCULARITY GUARD, extended
from its W1 proxy to the real W2 field pipeline.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §8.3 (CG-1 and its detector), §6.4 (the
`biographical_echo` carve-out), §7.4 (the field hash). Rail: `SHAD_DARSHANA_BRIEF_v2_0.md` §7
— "CIRCULARITY GUARD — the field never reads the LEL; CI invariance test is itself an
untouchable gate, live from W1 with item 10."

═══════════════════════════════════════════════════════════════════════════════════════════
  THE INVARIANT (CG-1, verbatim)
═══════════════════════════════════════════════════════════════════════════════════════════
  Let `H(chart, corpus_pin, config_pin, weights_version, cohort_version)` be the §7.4 field
  hash — SHA-256 over the canonical serialization of every row written by stages 0–8 for that
  chart, EXCLUDING rows with `lel_derived = TRUE` and excluding `id / computed_at /
  created_at / released_at`.

  For any mutation μ of that chart's LEL — insert, update, or delete of any life-event row —
  that leaves `(corpus_pin, config_pin, weights_version, cohort_version)` unchanged, `H` is
  BIT-IDENTICAL before and after.

═══════════════════════════════════════════════════════════════════════════════════════════
  RELATIONSHIP TO THE W1 TEST — READ THIS BEFORE ASSUMING EITHER IS REDUNDANT
═══════════════════════════════════════════════════════════════════════════════════════════
`tests/l3/test_ka_jivana_parva_circularity_guard.py` (item 10, W1, PR #889) is the ORIGINAL
guard. Its own module docstring says, honestly, that `ka_jivana_parva` is a PROXY subject
because `ka_kshetra` did not exist yet, and that it "MUST BE RE-POINTED AT `ka_kshetra` (or
`mi_bhara`'s weighted output) ONCE W2 LANDS."

This file is the W2 extension, and it EXTENDS rather than replaces: the W1 test keeps running
against the production writer it was written for, and this one adds the W2 surface. Both halves
of §8.3 are covered here:

  • STATIC (§1) — a source census over the stage 0–8 code path asserting no LEL reference,
    with `services/mi_bhara/db.py` as the SINGLE named whitelisted crossing. Always-on,
    DB-free, and it catches a path that happens not to fire on a fixture chart.
  • DYNAMIC (§2) — the empirical invariance proof. It runs against the real stage 0–8 tables
    when they exist and SKIPS HONESTLY when they do not, because at the time this lane was
    written `ka_kshetra`'s migrations (474–481) were Lane C's and had not landed. A skip is
    reported as a skip; it is never laundered into a pass.
  • VACUITY (§3) — §8.3's own `ASSERT S₁ != S₀` half: without it, the dynamic test passes even
    if stage 9 is DEAD CODE, which would make the Guard a signal with no detector (§N.8). §3
    proves stage 9 genuinely moves when the LEL moves, using the real fitting stack and no DB.

The §1 census here covers `services/ka_kshetra/` — which the W1 census's glob
(`services/ka_*`) also happens to match — plus `pipeline/orchestrator/writers/ka_kshetra*.py`.
That overlap is deliberate: the two censuses are independent tripwires with different
whitelists, and W1's would fail loudly if `services/mi_bhara/` were ever moved under a `ka_*`
name.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import pytest

SIDECAR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SIDECAR))

from services.mi_bhara.basis import FieldBasis, ParameterVector, SegmentBasis  # noqa: E402
from services.mi_bhara.fit import ScoredEvent, fit_event_class  # noqa: E402

LEL_TOKENS = ("life_events", "lel_query", "brahma_prospective_ledger", "life_events_staging")

#: The ONE module permitted to read the LEL (§2: "Stage 9 is the only stage that may see the
#: LEL"), named by path so the whitelist is a fact rather than a judgement call.
LEL_WHITELIST = {"services/mi_bhara/db.py"}


def lel_references_in_code(source: str) -> list[tuple[int, str]]:
    """Every LEL token occurrence in EXECUTABLE code, as `(lineno, token)`.

    Tokenised rather than grepped, and the difference is load-bearing in both directions:

      • A grep flags this very file, and flags `living_lel.py`'s docstring for explaining that
        `brahma_prospective_ledger` carries a `lapsed_unobserved` status. Documenting the
        boundary is not crossing it, and a census that cannot tell them apart gets silenced
        by whitelisting — which is how a real guard becomes a rubber stamp.
      • A line-prefix heuristic (`line.startswith('#')`) misses the INTERIOR lines of a
        triple-quoted docstring entirely, so it under-reports in exactly the place a reader
        would assume it was safe.

    `tokenize` gives the exact answer: STRING and COMMENT tokens are prose; everything else is
    code. A token appearing in an f-string's literal part is still prose; appearing in an
    identifier, an attribute, or a SQL string passed to `execute` — which IS a STRING token —
    needs one more rule, so `execute`/`cursor` calls are treated as code regardless of how
    their SQL is quoted (see `_sql_carrying_lines`).
    """
    import io
    import tokenize

    hits: list[tuple[int, str]] = []
    sql_lines = _sql_carrying_lines(source)
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError):  # pragma: no cover - malformed source
        return [(0, "unparseable")]
    for tok in toks:
        is_prose = tok.type in (tokenize.STRING, tokenize.COMMENT)
        # a string literal that is part of a SQL statement is CODE, not prose
        if is_prose and tok.start[0] not in sql_lines:
            continue
        for needle in LEL_TOKENS:
            if needle in tok.string:
                hits.append((tok.start[0], needle))
    return hits


def _sql_carrying_lines(source: str) -> set[int]:
    """Line numbers spanned by a string literal that is an argument to `.execute(`.

    Deliberately generous: any string literal appearing anywhere inside a statement that also
    contains `.execute(` counts. Over-inclusion here is safe (it can only make the census
    stricter); under-inclusion would let an LEL read hide inside a quoted query.
    """
    import io
    import tokenize

    lines: set[int] = set()
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError):  # pragma: no cover
        return lines
    execute_lines = {
        t.start[0] for t in toks if t.type == tokenize.NAME and t.string in ("execute", "executemany")
    }
    for t in toks:
        if t.type != tokenize.STRING:
            continue
        # a multi-line SQL literal starts on or just after the `.execute(` line
        if any(t.start[0] - 3 <= e <= t.end[0] for e in execute_lines):
            lines.update(range(t.start[0], t.end[0] + 1))
    return lines


def _stage_0_to_8_sources() -> list[Path]:
    """Every file on the stage 0–8 code path that exists today.

    Returns the `services/ka_kshetra/` package plus any `ka_kshetra*` writer module. Lanes
    A–D's stage modules land in that package, so this census automatically covers them as they
    arrive — a new stage file cannot be added outside the guard's reach without also being
    added outside the package the design assigns it to.
    """
    files: list[Path] = []
    pkg = SIDECAR / "services" / "ka_kshetra"
    if pkg.exists():
        files.extend(sorted(pkg.rglob("*.py")))
    writers = SIDECAR / "pipeline" / "orchestrator" / "writers"
    if writers.exists():
        files.extend(sorted(writers.glob("ka_kshetra*.py")))
    return files


# ── §1 — THE STATIC HALF ───────────────────────────────────────────────────────────────

def test_no_stage_0_to_8_module_references_the_lel():
    """CG-1's static detector over the W2 field pipeline.

    A hit here means someone wired an LEL read into a stage that must be a pure function of
    `(chart, corpus_pin, config_pin, weights_version, cohort_version)`. That is a hard-stop
    bug, not a stored divergence.
    """
    files = _stage_0_to_8_sources()
    assert files, (
        "the stage 0–8 census found zero files — the path assumption is broken and this "
        "guard's silence would mean nothing. Fix _stage_0_to_8_sources() before trusting it."
    )
    offenders = []
    for path in files:
        rel = str(path.relative_to(SIDECAR))
        for lineno, token in lel_references_in_code(path.read_text(encoding="utf-8")):
            offenders.append(f"{rel}:{lineno}: references {token!r} in CODE")
    assert offenders == [], (
        "CIRCULARITY GUARD VIOLATION — stages 0–8 must never read the LEL "
        "(SHAD_DARSHANA_BRIEF_v2_0.md §7; KALA_W2_FIELD_DESIGN_v1_0.md §8.3):\n"
        + "\n".join(offenders)
    )


def test_the_lel_read_is_confined_to_exactly_one_named_module():
    """The whitelist is a FACT, not a judgement call. If a second module in
    `services/mi_bhara/` starts reading the LEL, this fails and the whitelist must be widened
    deliberately — which is the point."""
    pkg = SIDECAR / "services" / "mi_bhara"
    readers = {
        str(path.relative_to(SIDECAR))
        for path in sorted(pkg.rglob("*.py"))
        if lel_references_in_code(path.read_text(encoding="utf-8"))
    }
    assert readers == LEL_WHITELIST, (
        f"the LEL read must stay confined to {sorted(LEL_WHITELIST)}; found {sorted(readers)}. "
        f"Confining it is what lets the static census state its whitelist precisely instead "
        f"of by judgement."
    )


def test_the_census_would_genuinely_catch_an_lel_read_that_was_added():
    """The VACUITY half of the static census (§N.7 item 4). A census that could not fail is
    not a detector. This runs the same predicate over a synthetic file that DOES read the LEL
    and asserts it is flagged."""
    fake_read = "def stage4_field(conn):\n    cur.execute('SELECT * FROM life_events')\n"
    assert [ln for ln, _ in lel_references_in_code(fake_read)] == [2], (
        "the census predicate must actually flag a real LEL read, even when the table name "
        "is inside a quoted SQL string"
    )

    fake_attr = "def stage4_field(store):\n    return store.life_events\n"
    assert [ln for ln, _ in lel_references_in_code(fake_attr)] == [2]

    # …and it must NOT flag prose that merely explains the boundary, or the census gets
    # silenced by whitelisting and stops being a guard.
    prose = '"""Stage 4 must never read life_events (see §8.3)."""\nX = 1\n'
    assert lel_references_in_code(prose) == []
    comment = "# life_events is off-limits on this path\nX = 1\n"
    assert lel_references_in_code(comment) == []


def test_stage_8_specifically_is_inside_the_hash_boundary_and_lel_free():
    """Stage 8 is Lane E's own file on the stage 0–8 side of the boundary (design §2's
    diagram puts the FIELD HASH BOUNDARY between stage 8 and stage 9). Called out separately
    from the package census because it is the one file this lane WRITES on that side, and a
    lane is likeliest to break the rule in its own file."""
    src = (SIDECAR / "services" / "ka_kshetra" / "stage8_spec.py").read_text(encoding="utf-8")
    assert lel_references_in_code(src) == []
    # …and it does not reach the LEL indirectly either: stage 8 opens no connection at all.
    for forbidden in ("psycopg", "cursor(", "execute("):
        assert forbidden not in src, f"stage8_spec.py must not reference {forbidden!r}"


# ── §2 — THE DYNAMIC HALF (honest skip until Lane C's tables land) ────────────────────

FIELD_TABLES = (
    "kala_field",
    "kala_field_windows",
    "kala_field_kinematics",
    "kala_field_primitives",
)


def _field_row_digest(conn, chart_id: str) -> str:
    """The §7.4-shaped digest over stage 0–8 rows: excludes `id / computed_at / created_at /
    released_at`, and excludes `kala_insights` rows with `lel_derived = TRUE` (§6.4's
    carve-out — those are Lane E's biographical join and are DELIBERATELY outside the hash)."""
    parts: list[str] = []
    for table in FIELD_TABLES:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass(%s) IS NOT NULL AS present", (table,))
            row = cur.fetchone()
            if not (row["present"] if isinstance(row, dict) else row[0]):
                continue
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_name = %s
                   AND column_name NOT IN ('id','computed_at','created_at','released_at')
                 ORDER BY ordinal_position
                """,
                (table,),
            )
            cols = [(r["column_name"] if isinstance(r, dict) else r[0]) for r in cur.fetchall()]
            if not cols:
                continue
            col_list = ", ".join(f'"{c}"' for c in cols)
            cur.execute(
                f"SELECT {col_list} FROM {table} WHERE chart_id = %s ORDER BY {col_list}",
                (chart_id,),
            )
            for r in cur.fetchall():
                parts.append(f"{table}:{r!r}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


@pytest.mark.integration
def test_circularity_guard_field_hash_invariant_under_lel_mutation():
    """CG-1's EMPIRICAL half, against the real W2 field tables.

    Runs inside ONE never-committed transaction and rolls back in a `finally`, mirroring the
    FROZEN writer contract's own "ctx.db_conn is NEVER committed by the writer" rule.

    HONEST SKIP, not a silent pass: at the time this lane was written, `ka_kshetra`'s
    migrations (474–481) were Lane C's and had not landed, so the field tables may not exist.
    The test says so and skips. §1 and §3 remain fully live in every environment, so the Guard
    is never left with no detector at all.
    """
    try:
        import psycopg
        import psycopg.rows
    except ImportError:
        pytest.skip("psycopg not installed in this environment")

    dsn = "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis"
    try:
        conn = psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, connect_timeout=5)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")

    chart_id = "482012f1-710e-4a25-994a-93821f5871aa"
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('kala_field') IS NOT NULL AS present")
            if not cur.fetchone()["present"]:
                pytest.skip(
                    "kala_field is not deployed yet (Lane C's migrations 474-481) — the "
                    "empirical half of the W2 Circularity Guard cannot run against a field "
                    "that does not exist. §1 (static census) and §3 (vacuity) still ran."
                )
            cur.execute("SELECT count(*) AS n FROM kala_field WHERE chart_id = %s", (chart_id,))
            if cur.fetchone()["n"] == 0:
                pytest.skip("kala_field holds no rows for the canonical chart — nothing to prove")

        h0 = _field_row_digest(conn, chart_id)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO life_events
                    (chart_id, event_id, event_date, event_type, description, domain,
                     outcome_observed, source_citation, recorded_at, category,
                     source_section, build_id, chart_state, provenance)
                VALUES (%s, %s, '1900-01-01', 'test', %s, 'test/circularity_guard_w2', TRUE,
                        'CIRCULARITY_GUARD_W2_TEST', now(), 'test', '§CG_W2', %s,
                        '{}'::jsonb, '{}'::jsonb)
                """,
                (
                    chart_id,
                    "circularity-guard-w2-synthetic",
                    "CIRCULARITY GUARD W2 synthetic row — never committed, rolled back.",
                    "circularity-guard-w2-test",
                ),
            )
            cur.execute(
                "SELECT count(*) AS n FROM life_events WHERE chart_id = %s AND event_id = %s",
                (chart_id, "circularity-guard-w2-synthetic"),
            )
            assert cur.fetchone()["n"] == 1, (
                "the synthetic LEL row is not visible in this transaction — the invariance "
                "check below would be vacuous rather than a proof"
            )

        h1 = _field_row_digest(conn, chart_id)
        assert h1 == h0, (
            "CIRCULARITY GUARD VIOLATION (CG-1): the stage 0–8 field row digest changed after "
            "an LEL mutation. The field must be a pure function of (chart, corpus_pin, "
            "config_pin, weights_version, cohort_version)."
        )
    finally:
        conn.rollback()
        conn.close()


# ── §3 — THE VACUITY HALF: stage 9 genuinely MOVES when the LEL moves ─────────────────

def _stage9_digest(events) -> str:
    """§8.3's `S` — sha256 of the fitted weight vector ‖ skill scores ‖ gof states.

    Computed through the real fitting stack, with no DB, so this half of the Guard runs in
    every environment — including the one where §2 must honestly skip.
    """
    basis = FieldBasis(
        event_class="career_change",
        covariate_ids=("x1_contact_moon_ref",),
        segments=(
            SegmentBasis(0.0, 5_000.0, math.log(1e-3), x_start=(0.0,), x_end=(0.0,)),
            SegmentBasis(5_000.0, 6_000.0, math.log(1e-3), x_start=(1.0,), x_end=(1.0,)),
            SegmentBasis(6_000.0, 36_525.0, math.log(1e-3), x_start=(0.0,), x_end=(0.0,)),
        ),
    )
    result = fit_event_class(
        basis=basis,
        events=events,
        prior=ParameterVector((), (0.0,), ()),
        horizon_end=36_525.0,
    )
    payload = {
        "theta": list(result.theta_shipped.as_flat()),
        "fit_loglik": result.fit_loglik,
        "pooled_oos": result.pooled_oos_loglik,
        "n_train": result.n_train,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()


def test_stage_nine_output_CHANGES_when_the_lel_changes():
    """§8.3's `ASSERT S₁ != S₀`, and the reason it is not optional.

    Without this assertion the Guard's `H₁ == H₀` passes even if stage 9 is DEAD CODE — the
    field would be invariant under an LEL mutation for the trivial reason that NOTHING reads
    the LEL, including the thing that is supposed to. That is a green signal with no detector
    behind it (§N.8), and it is exactly the failure mode this half exists to close.
    """
    base = [
        ScoredEvent(t=5_100.0 + 60.0 * i, event_class="career_change", event_id=f"e{i}")
        for i in range(10)
    ]
    s0 = _stage9_digest(base)
    s1 = _stage9_digest(base + [ScoredEvent(t=5_500.0, event_class="career_change", event_id="new")])
    assert s1 != s0, (
        "stage 9's output did NOT move when the LEL moved — the calibration plane is dead "
        "code, and the Circularity Guard's H₁ == H₀ would be passing vacuously."
    )


def test_stage_nine_output_is_STABLE_when_the_lel_does_not_change():
    """The complement: stage 9 must be deterministic, or `S₁ != S₀` would fire on noise and
    the vacuity half would be a coin flip rather than a detector."""
    base = [
        ScoredEvent(t=5_100.0 + 60.0 * i, event_class="career_change", event_id=f"e{i}")
        for i in range(10)
    ]
    assert _stage9_digest(base) == _stage9_digest(base)


def test_a_biographical_echo_insight_is_marked_lel_derived_and_excluded_from_the_hash():
    """§6.4's carve-out, which is what lets BOTH things be true at once: the LEL-derived
    insight is SERVED, and the field never moved.

    Asserted on the writer's own SQL — every `kala_insights` row Lane E writes carries
    `lel_derived = TRUE`, and the §7.4 hash excludes exactly those rows.
    """
    src = (SIDECAR / "services" / "mi_bhara" / "db.py").read_text(encoding="utf-8")
    start = src.index("def upsert_biographical_echo_insights")
    body = src[start:]
    assert "'biographical_echo'" in body
    assert "TRUE" in body and "lel_derived" in body, (
        "biographical-join rows must be written with lel_derived = TRUE, or the field hash "
        "would cover them and an LEL append would move the field (§6.4, §7.4)"
    )
    assert "field_snapshot_id" in body and "NULL" in body, (
        "a lel_derived insight carries a NULL field_snapshot_id — it belongs to no field "
        "snapshot, which is the schema-level statement that it is outside the hash"
    )
