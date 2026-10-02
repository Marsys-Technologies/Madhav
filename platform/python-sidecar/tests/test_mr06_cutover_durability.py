"""
tests/test_mr06_cutover_durability.py — MR-06 gate: cutover irreversible-by-accident.

GAP (PARISHKARA MR-06):
  asset_registry_seed.ts and migration 542's ON-CONFLICT upserts still reflect
  the PRE-cutover state. If the seed runs again after a deployment reset, it would:
    - Un-retire ka_gochara_sweep (restore catalog_status='CURRENT', is_active=true)
    - Resurrect ka_gochara_v2_materialize as a live asset
    - Overwrite ka_gochara's identity with the old service-asset stale data

  Additionally: generation='3.0' protection for kala_gochara_windows rows was
  promised in plan W6.4 but NEVER authored — no trigger exists in migration 566
  to prevent unauthorized DELETE of gen-3.0 rows.

REMEDIATION (what MR-06 implements):
  1. asset_registry_seed.ts updated to post-cutover truth:
     - ka_gochara_sweep: catalog_status='RETIRED', is_active=false
     - ka_gochara_v2_materialize: removed from seed
     - ka_gochara: catalog_status='CURRENT', is_active=true, storage_type='postgres_table',
       target_table='kala_gochara_windows_v2', generation='2.0' count_sql
       (MIGRATION 1230 REVERT of the WP10 1091 re-pin, 2026-10-02, steward ruling
           reversal 2026-10-02 — the registered writer writers/ka_gochara.py writes
           kala_gochara_windows_v2 at generation '2.0', so the registry row catalogs
           that surface; the 1091 '4.0' pin returns with the writer switch at D-FLIP.
           See the succession note below)
  2. The ON-CONFLICT UPDATE clause in asset_registry_seed.ts guards against
     resurrecting a RETIRED asset: it does NOT overwrite catalog_status when
     the existing row is already RETIRED.
  3. Migration 566 adds a BEFORE DELETE trigger on kala_gochara_windows that
     refuses DELETE of generation='3.0' rows unless the protected_generation_bypass
     privilege is held (checked via a build_protected_assets guard).

WHAT THESE TESTS VERIFY (all offline/static, no DB required):
  1. Seed ka_gochara_sweep entry declares catalog_status='RETIRED' and is_active=false.
  2. Seed does NOT contain an asset_id='ka_gochara_v2_materialize' entry.
  3. Seed ka_gochara entry is post-cutover: storage_type='postgres_table',
     target_table='kala_gochara_windows_v2', count_sql references
     generation='2.0' against that same table, and satisfies integrity
     conjunct (j) — target_table IS the relation count_sql reads (migration
     1230, the 2026-10-02 revert of the WP10 1091 re-pin, steward ruling
     reversal 2026-10-02: the registered writer writes
     kala_gochara_windows_v2 at generation '2.0'; the 1091 pin returns with
     the writer switch at D-FLIP).
  4. The ON-CONFLICT UPDATE clause in asset_registry_seed.ts does NOT overwrite
     catalog_status unconditionally — it guards RETIRED rows.
  5. Migration 566 exists and contains a BEFORE DELETE trigger body that raises
     on generation='3.0' rows for protected charts.
  6. Mutation test: removing the CONFLICT guard text from the seed's update clause
     makes the guard-test fail (proves the guard test is not trivially passing).

PARIṢKĀRA MR-40 correction (2026-08-11): test 3 originally asserted
target_table='kala_gochara_windows_v2' — correct for W6.4's own cutover
moment, but silently orphaned by a LATER, separate architecture change: the
writer's own W5.4 UTK-R1 ADJUDICATOR repoint moved PRODUCTION authority to
kala_gochara_windows generation='3.0' (kala_gochara_windows_v2 became a
calibration/staging copy only, generation='g3_utkarsha'). This test locking
in the pre-repoint value is exactly how MR-40's cockpit bug went
undetected: the seed's count_sql/target_table were correct once, then wrong
after a change nobody re-checked this test against. Updated to the
post-repoint truth; see MR-40 in MASTER_REMEDIATION_REGISTER_v2_0.md for
the full incident and PARISHKARA_LEDGER.md's "MR-24 FINAL RE-RUN" entry for
live evidence (89/85 real rows, cockpit read 0 pre-fix).

KĀLA B1 CORRECTION (2026-09-22, pre-elevation Phase 1.1) — SUPERSEDES the
MR-40 repoint above: the writer has since been rewritten under a NATIVE
RULING recorded verbatim in writers/ka_gochara.py's module docstring ("this
writer's only DELETE/SELECT/INSERT target is kala_gochara_windows_v2 --
there is no code path, error branch, or override that ever names
kala_gochara_windows"). kala_gochara_windows generation='3.0' belongs to
ka_gochara_v3_century_materialize, a separate asset. W0 census #4
(MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md) settles the same
identity: ka_gochara → kala_gochara_windows_v2 + kala_gochara_v2_build_state.

MIGRATION 1230 REVERT (2026-10-02, steward ruling reversal 2026-10-02) —
SUPERSEDES the WP10 re-pin as the SEED identity: the registered writer
(writers/ka_gochara.py) still writes kala_gochara_windows_v2 at generation
'2.0', so the registry row must point there (CLAUDE.md N.4/N.8). 1230 restores
target_table / count_sql / integrity_check_sql / clear_tables from
kala_gochara_cutover_step05_snapshot (the pre-1091 row), and the seed literal
follows it. The 1091 '4.0' pin is re-applied TOGETHER WITH the writer switch
at D-FLIP (native-only), not before. Test 3 pins the 1230 identity with the
same conjunct-(j) equality and a negative assertion that the superseded 1091
'4.0'/kala_gochara_windows pair can never pass.
"""
from __future__ import annotations

import os
import re

# ── paths ────────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.dirname(_HERE)
_PLATFORM = os.path.dirname(_SIDECAR)
_REPO_ROOT = os.path.dirname(_PLATFORM)

_SEED = os.path.join(_PLATFORM, "scripts", "seed", "asset_registry_seed.ts")
_MIGRATION_566 = os.path.join(
    _PLATFORM, "supabase", "migrations", "566_parishkara_mr06_gen3_protection.sql"
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_asset_block(src: str, asset_id: str) -> str:
    """Return the text of the seed object whose asset_id matches.

    Scans for the pattern `asset_id: '<asset_id>'` and returns everything from
    the preceding `{` to the matching `}` (first closing brace on its own line
    after the asset_id line). This is intentionally simple — the seed file is
    consistently formatted so this heuristic is sufficient.
    """
    pattern = rf"asset_id:\s*['\"]({re.escape(asset_id)})['\"]"
    m = re.search(pattern, src)
    if m is None:
        return ""
    # Walk back to find the opening brace of this object.
    start = src.rfind("{", 0, m.start())
    if start == -1:
        return ""
    # Walk forward to find the matching closing brace (depth-aware).
    depth = 0
    pos = start
    while pos < len(src):
        ch = src[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start : pos + 1]
        pos += 1
    return src[start:]


def _asset_exists_in_seed(src: str, asset_id: str) -> bool:
    """Return True if the seed ASSETS array contains an entry for asset_id."""
    return bool(re.search(rf"asset_id:\s*['\"{asset_id}'\"]", src)) or \
           bool(re.search(rf"asset_id:\s*'{re.escape(asset_id)}'", src)) or \
           bool(re.search(rf'asset_id:\s*"{re.escape(asset_id)}"', src))


# ── Test 1: ka_gochara_sweep seed entry is RETIRED ───────────────────────────

def test_seed_ka_gochara_sweep_is_retired():
    """ka_gochara_sweep seed entry must declare catalog_status='RETIRED' and is_active=false.

    The W6.4 cutover (migration 563, PR #1192) SET ka_gochara_sweep to
    catalog_status='RETIRED', is_active=false in the DB. If the seed still carries
    catalog_status='CURRENT' and is_active=true, a re-seed would un-retire it —
    the exact resurrection hazard MR-06 closes.
    """
    src = _read(_SEED)
    block = _extract_asset_block(src, "ka_gochara_sweep")
    assert block, "ka_gochara_sweep entry not found in asset_registry_seed.ts"

    # Must declare RETIRED status
    assert re.search(r"catalog_status\s*:\s*['\"]RETIRED['\"]", block), (
        "ka_gochara_sweep seed entry must have catalog_status: 'RETIRED' "
        f"(found block: {block[:300]!r})"
    )
    # Must declare is_active=false
    assert re.search(r"is_active\s*:\s*false", block), (
        "ka_gochara_sweep seed entry must have is_active: false "
        f"(found block: {block[:300]!r})"
    )


# ── Test 2: ka_gochara_v2_materialize absent from seed ───────────────────────

def test_seed_ka_gochara_v2_materialize_absent():
    """ka_gochara_v2_materialize must NOT appear in the seed ASSETS array.

    Post-cutover, ka_gochara_v2_materialize was renamed to ka_gochara (migration
    563). The old asset_id no longer exists in the DB. If the seed still contains
    it, a re-seed's ON-CONFLICT INSERT would resurrect a ghost asset row.

    Note: the asset_id string may still appear in COMMENTS explaining the rename
    history. This test strips line-comment text before checking for the live
    asset_id declaration, so a comment mention does not cause a false failure.
    """
    src = _read(_SEED)
    # Strip TypeScript line comments (// ...) to avoid false matches inside comments.
    src_no_comments = re.sub(r"//[^\n]*", "", src)
    block = _extract_asset_block(src_no_comments, "ka_gochara_v2_materialize")
    assert not block, (
        "ka_gochara_v2_materialize must NOT appear as an active seed entry "
        "(it was renamed to ka_gochara at W6.4 cutover — remove the seed row). "
        f"Found block: {block[:300]!r}"
    )


# ── Test 3: ka_gochara seed entry is post-cutover materializer ───────────────

def test_seed_ka_gochara_is_post_cutover_materializer():
    """ka_gochara seed entry must reflect the migration-1230 reverted registry identity.

    Post-cutover (W6.4, migration 563) AND post-1230-REVERT (migration 1230,
    2026-10-02, steward ruling reversal 2026-10-02: the registered ka_gochara
    writer — writers/ka_gochara.py — writes kala_gochara_windows_v2 at
    generation '2.0' (TABLE / GENERATION_V2), so the registry row must point
    there; CLAUDE.md N.4: count_sql must count what the writer writes). The
    registry row catalogs the asset's writer surface:
      - storage_type: 'postgres_table' (was 'service')
      - target_table: 'kala_gochara_windows_v2' — the relation the registered
        writer writes (1230 reverted 1091's '4.0'/kala_gochara_windows re-pin;
        the 1091 pin returns with the writer switch at D-FLIP, native-only).
      - count_sql references generation='2.0' AGAINST kala_gochara_windows_v2 —
        the exact text migration 1230 writes.
      - integrity conjunct (j): target_table IS the relation count_sql reads —
        a pair where the two differ can never pass this test.
      - scope: 'per_chart' (was 'global')
      - catalog_status: 'CURRENT'
      - is_active: true

    The old service-asset entry (storage_type='service', scope='global') was
    deleted by migration 563 and replaced with the renamed materializer.

    Succession of this pin: '3.0'/kala_gochara_windows (MR-40, W5.4 UTK-R1
    repoint) → '2.0'/kala_gochara_windows_v2 (Kāla B1, 2026-09-22 — the WRITER
    MODULE's native-ruled identity, still true of ka_gochara.py and pinned by
    gochara_seed_target_table_parity.test.ts) → '4.0'/kala_gochara_windows
    (WP10 1091 — superseded) → '2.0'/kala_gochara_windows_v2 (migration 1230,
    the revert this test pins, per the steward ruling reversal of 2026-10-02).
    Re-pointed, not weakened: the conjunct-(j) equality assertion is the
    inverted-form descendant of the never-touch-the-protected-corpus guard —
    it fails for exactly the pair that guard forbade.
    """
    src = _read(_SEED)
    block = _extract_asset_block(src, "ka_gochara")
    assert block, "ka_gochara entry not found in asset_registry_seed.ts"

    # Must be postgres_table, not service
    assert re.search(r"storage_type\s*:\s*['\"]postgres_table['\"]", block), (
        "ka_gochara seed entry must have storage_type: 'postgres_table' post-cutover "
        f"(found block: {block[:400]!r})"
    )
    # Must carry the 1230 registry identity: kala_gochara_windows_v2 — the
    # surface the registered writer (writers/ka_gochara.py TABLE) writes.
    assert re.search(r"target_table\s*:\s*['\"]kala_gochara_windows_v2['\"]", block), (
        "ka_gochara seed entry must have target_table: 'kala_gochara_windows_v2' "
        "(migration 1230 revert of the 1091 re-pin, steward ruling reversal 2026-10-02 — "
        "the registered writer writes kala_gochara_windows_v2 at generation '2.0'; "
        "the 1091 '4.0' pin returns with the writer switch at D-FLIP) "
        f"(found block: {block[:400]!r})"
    )
    # count_sql must reference generation='2.0' (the registered writer's
    # GENERATION_V2 — the exact text migration 1230 writes)
    assert re.search(r"count_sql\s*:.*generation.*2\.0", block, re.DOTALL), (
        "ka_gochara seed count_sql must reference generation='2.0' "
        f"(registered writer's generation, migration 1230) (found block: {block[:400]!r})"
    )
    # count_sql must query kala_gochara_windows_v2 (the writer's relation).
    assert re.search(r"count_sql\s*:\s*[\"'].*FROM kala_gochara_windows_v2\s", block), (
        "ka_gochara seed count_sql must SELECT FROM kala_gochara_windows_v2 "
        f"(migration 1230 revert) (found block: {block[:400]!r})"
    )
    # Integrity conjunct (j), negative form: a row whose target_table differs
    # from the relation its count_sql reads can never pass. Derived from the
    # block itself — never restated — and the superseded 1091 '4.0' pair is shown
    # to violate it (that mismatch is exactly what 1230 closed).
    tt = re.search(r"target_table\s*:\s*['\"]([a-z0-9_]+)['\"]", block)
    cs = re.search(r"count_sql\s*:\s*[\"']([^\"']+)[\"']", block)
    assert tt and cs, "ka_gochara seed entry must declare both target_table and count_sql"
    cs_rel = re.search(r"FROM\s+([a-z0-9_]+)", cs.group(1), re.IGNORECASE)
    assert cs_rel, f"ka_gochara seed count_sql must name a FROM relation (found: {cs.group(1)!r})"
    assert tt.group(1) == cs_rel.group(1), (
        "conjunct (j) violation: ka_gochara target_table "
        f"({tt.group(1)!r}) != count_sql relation ({cs_rel.group(1)!r}) — "
        "the mismatch migration 1230 exists to close can never pass"
    )
    # Explicit negative control: the superseded 1091 '4.0' pair MUST NOT satisfy
    # the invariant (proves the equality above is able to fail — §N.8).
    superseded_rel = re.search(
        r"FROM\s+([a-z0-9_]+)",
        "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'",
    ).group(1)
    assert superseded_rel == "kala_gochara_windows"
    assert superseded_rel != tt.group(1), (
        "negative control broken: the superseded 1091 '4.0' count_sql relation must "
        "differ from the current target_table — that pair would violate conjunct (j) "
        "under the 1230 identity"
    )
    # Must be per_chart scope
    assert re.search(r"scope\s*:\s*['\"]per_chart['\"]", block), (
        "ka_gochara seed entry must have scope: 'per_chart' post-cutover "
        f"(found block: {block[:400]!r})"
    )
    # Must be CURRENT and active
    assert re.search(r"catalog_status\s*:\s*['\"]CURRENT['\"]", block), (
        "ka_gochara seed entry must have catalog_status: 'CURRENT' "
        f"(found block: {block[:400]!r})"
    )
    assert re.search(r"is_active\s*:\s*true", block), (
        "ka_gochara seed entry must have is_active: true "
        f"(found block: {block[:400]!r})"
    )


# ── Test 4: ON-CONFLICT guard protects RETIRED rows ──────────────────────────

def test_seed_on_conflict_does_not_overwrite_retired_status():
    """The ON-CONFLICT UPDATE clause must not unconditionally overwrite catalog_status.

    The bare `catalog_status = EXCLUDED.catalog_status` in the ON-CONFLICT clause
    would overwrite a DB row's 'RETIRED' status with whatever the seed says — even
    if the seed itself says 'CURRENT'. The guard must add a WHERE condition or
    CASE expression that refuses to promote a RETIRED row back to active.

    Specifically, the update must include a guard of the form:
      catalog_status = CASE WHEN asset_registry.catalog_status = 'RETIRED'
                            THEN asset_registry.catalog_status
                            ELSE EXCLUDED.catalog_status END
    or equivalent logic that preserves RETIRED status on conflict.
    """
    src = _read(_SEED)
    # The ON-CONFLICT clause is in the runSeed() function body.
    # We look for the RETIRED-preservation guard pattern.
    assert re.search(
        r"RETIRED.*THEN.*asset_registry\.catalog_status|"
        r"catalog_status.*=.*CASE.*WHEN.*RETIRED|"
        r"WHEN.*asset_registry\.catalog_status\s*=\s*'RETIRED'",
        src,
        re.DOTALL | re.IGNORECASE,
    ), (
        "asset_registry_seed.ts ON-CONFLICT UPDATE clause must guard RETIRED rows: "
        "catalog_status must not be overwritten when the existing DB row is RETIRED. "
        "Expected a CASE WHEN catalog_status='RETIRED' THEN ... pattern in the SQL."
    )


# ── Test 5: Migration 566 exists and contains gen-3.0 protection trigger ─────

def test_migration_566_gen3_protection_trigger_exists():
    """Migration 566 must exist and define a BEFORE DELETE trigger on kala_gochara_windows.

    The trigger must:
      - Fire BEFORE DELETE on kala_gochara_windows
      - Check OLD.generation = '3.0'
      - RAISE EXCEPTION when the deleting session lacks the bypass

    This migration was promised in plan W6.4 but never authored. MR-06 authors it.
    """
    assert os.path.exists(_MIGRATION_566), (
        f"Migration 566 not found at {_MIGRATION_566}. "
        "MR-06 must author 566_parishkara_mr06_gen3_protection.sql"
    )
    src = _read(_MIGRATION_566)

    # Must have a BEFORE DELETE trigger on kala_gochara_windows
    assert re.search(
        r"BEFORE\s+DELETE.*ON\s+kala_gochara_windows|"
        r"CREATE\s+(OR\s+REPLACE\s+)?TRIGGER.*BEFORE\s+DELETE",
        src,
        re.IGNORECASE | re.DOTALL,
    ), (
        "Migration 566 must define a BEFORE DELETE trigger on kala_gochara_windows. "
        f"(migration content excerpt: {src[:500]!r})"
    )

    # Must check generation = '3.0'
    assert re.search(r"generation\s*=\s*['\"]3\.0['\"]|OLD\.generation", src, re.IGNORECASE), (
        "Migration 566 trigger function must reference OLD.generation or generation='3.0'. "
        f"(migration content excerpt: {src[:500]!r})"
    )

    # Must RAISE EXCEPTION (the protection mechanism)
    assert re.search(r"RAISE\s+EXCEPTION", src, re.IGNORECASE), (
        "Migration 566 trigger function must RAISE EXCEPTION to refuse protected DELETEs. "
        f"(migration content excerpt: {src[:500]!r})"
    )

    # Must have a DOWN path (commented DROP TRIGGER + DROP FUNCTION)
    assert re.search(r"DROP\s+TRIGGER", src, re.IGNORECASE), (
        "Migration 566 must include a DOWN path with DROP TRIGGER (in a comment block). "
        f"(migration content excerpt: {src[:500]!r})"
    )


# ── Test 6: Mutation test — guard test is not trivially passing ───────────────

def test_mutation_removing_retired_guard_fails_detection():
    """Mutation test: the guard-detection regex must reject a seed with no RETIRED guard.

    This verifies that test_seed_on_conflict_does_not_overwrite_retired_status is
    not trivially passing on any seed text. If we mutate the seed by removing the
    RETIRED-preservation pattern and re-run the detection regex, it must NOT match —
    proving the test has real discriminating power.

    This is a static mutation: we construct a known-bad string and assert the
    detection pattern rejects it, without touching any real file.
    """
    # A seed snippet that has the OLD (bare, unguarded) ON-CONFLICT clause
    mutated_seed_fragment = """
      ) ON CONFLICT (asset_id) DO UPDATE SET
        layer = EXCLUDED.layer,
        sort_order = EXCLUDED.sort_order,
        catalog_status = EXCLUDED.catalog_status,
        is_active = EXCLUDED.is_active
    """
    # The guard regex from test 4 must NOT match this (it lacks the RETIRED guard)
    guard_present = bool(re.search(
        r"RETIRED.*THEN.*asset_registry\.catalog_status|"
        r"catalog_status.*=.*CASE.*WHEN.*RETIRED|"
        r"WHEN.*asset_registry\.catalog_status\s*=\s*'RETIRED'",
        mutated_seed_fragment,
        re.DOTALL | re.IGNORECASE,
    ))
    assert not guard_present, (
        "Mutation test failed: the guard-detection regex matched a seed fragment "
        "that deliberately lacks the RETIRED guard. The regex is too permissive and "
        "would pass even on an unguarded seed."
    )
