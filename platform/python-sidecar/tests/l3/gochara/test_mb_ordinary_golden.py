"""An ordinary (markerless) P06 build preserves its accepted final-rule observations.

(I) INTERPRETATION: keep main's J-4p historical captures and their regression
unchanged, and use the accepted P06 capture (adc6b81ea) for P06 final rules.
This is the branch's existing settlement-amended copy: its snapshot note and
inventory/verify transcripts already include the accepted J-4p/J4P-B1 reads.
No capture is regenerated from the merged implementation.
The only SQL adaptation reverses B4's removed positive-bounds predicate when
comparing the accepted transcript; B5's replacement guard remains checked exactly.
All outcomes, counts, SQL order and non-implementation inputs remain pinned.

Main's historical baseline rationale follows:

The historical measuring-build golden, `fixtures/mb_ordinary_golden_main.json`
at 75eeda4c9, remains unchanged. It predates J-4p's governed reads and settled
build identity. Both comparisons already fail on the unmodified pre-B4 head.
(I) INTERPRETATION I6: use the pre-B4 J-4p head as the valid-data baseline.
Main's J-4p golden, `fixtures/mb_ordinary_golden_j4p.json`, was captured from
unmodified production sources at 2d75833d3963a61544deaa4c36cc8322cb2cdcb5.
Its provenance records the source hashes and the only SQL adaptation for B4:
remove the governed CTE's positive-bounds pre-filter. All other ordered SQL,
parameter counts, outcomes, row counts and manifest components remain pinned.

It holds, for a markerless run driven through the writer's REAL substeps on the real migration chain (the a55 template), with the real runner's config keys
(`chart_id`, `birth_params`) and an explicit rehearsal horizon:
  * every substep kind (rules, convention, body, manifest, snapshot, inventory, coverage, record, window, verify) and a dry run: its observable outcome (rows inserted
    and notes, or the refusal's type and message), the SQL statements it issued through the connection (whitespace-normalised text and parameter count, kept as a count
    per distinct statement shape plus the sha256 of the ordered sequence), and the row count of every ka_gochara_* / kala_gochara_* table after it;
  * the candidate manifest's input vector, every component.
For the P06 capture, the evaluation, geometry and window implementation identities
differ from the capture because the merged tree carries main's later source changes
(J4C-A/J4C-B, J-2a, the P1 testimony-contact fix); all three are pinned below as literals
re-derived from the merged tree's real bytes.
(I) INTERPRETATION: main made the final rules an explicit opt-in (`gochara_v5_final_rules`, rule_registry.rule_profile), so the
capture is driven with that flag True: the accepted P06 capture is, by definition, the final-rule build. The default (legacy) profile's
isolation is main's own claim, held by test_a53_gochara_v5_writer.py / test_nd_h_builder_tiers.py, not by this golden.
(I) INTERPRETATION: main's J4C-A (#3596) graha-mapping source updates are part of the
merged tree whose digests are pinned below, so no separate J4C pin is applied to this capture.
P06b adds exactly one manifest catalogue probe (LAYER_SELECT) and the near-miss verifier module to the geometry identity. Exactly one state-guard SELECT is checked
per non-dry-run substep and excluded from both SQL summaries. B5 adds exactly
one invalid-period guard SELECT to inventory:marriage; its complete shape and
parameter count are checked separately, preserving the stored baseline.
Texts are normalised only for values that differ between two runs of the SAME tree (per-world ids and the digests derived from them, in the notes): hex runs of 12+
characters (or a truncated id before an ellipsis) and UUIDs. Two captures on main agree exactly after that."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from .conftest import EPHE_PATH
from .test_a53_inventory import CHART_ID
from .test_a55_replace_chain import SHORT, _World, template as _a55_template

J4P_GOLDEN = Path(__file__).resolve().parent / "fixtures" / "mb_ordinary_golden_j4p.json"
GOLDEN = J4P_GOLDEN.with_name("mb_ordinary_golden_p06.json")
GOLDEN_COMMIT = "adc6b81ea"
# The immutable capture recorded the dasha build then settled (L1_SETTLED v1, ca17639b); the snapshot notes name it as
# "build <uuid first four groups>-<hex>", and the final group is normalised away by `_norm`. A settlement move
# (dasha_settlement.json) changes only this identity, so the comparison re-points it at the governed record instead of
# re-capturing the golden or pinning a second literal.
GOLDEN_SETTLED_BUILD_PREFIX = "ca17639b-f3cf-42c7-9866-"
# J-2a-P1L (SR-J2A-P1L-NOW, B.3): the snapshot now ledgers every pinned daśā row the P1 builder CONSULTS for a record's
# period_running_at (all rows of an anchor (lord, level), wherever they lie), not only the rows overlapping the horizon. The a55
# template chart holds 6 pinned rows (test_a53_inventory.DASHA); the horizon [2025-01-01, 2025-01-20) overlaps 4 of them
# (Saturn MD, Venus AD, Mars PD, Rahu PD) — the golden's "4 daśā rows" — and the marriage P1 anchors (Sun AD, Jupiter PD) consult the
# other 2 (rows 3 and 6, wholly after the horizon): 4 + 2 = 6. The immutable fixture is not re-captured; only this one count moves.
GOLDEN_SNAPSHOT_DASHA_ROWS = "10 L1 facts, 4 daśā rows"
P1L_SNAPSHOT_DASHA_ROWS = "10 L1 facts, 6 daśā rows"


@pytest.fixture(scope="module")
def template():
    """The a55 template (real migrations + sky-event substrate), seeded with the FINAL-rule registry: the capture below is the final-rule build, so its
    rule-registry rows (8 paths, the 1.2.0 factors) must be present in the template exactly as in the accepted P06 capture. The template's own seed runs
    outside any writer substep, so the explicit profile is what selects them."""
    from services.gochara_kernel import rule_registry
    with rule_registry.rule_profile(final_rules=True):
        yield from _a55_template.__wrapped__()


# the REAL runner's birth parameters shape (birth_params._to_birth_params): main ignores them, an ordinary HEAD build must too
BIRTH_PARAMS = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5, "place_name": "Bhubaneswar",
                "subject_label": "native"}
CLASS = "marriage"
GUARD_SELECT = "SELECT state FROM public.asset_throughput WHERE chart_id = %s AND asset_id = %s"
# F-CHANNEL (SR-W34-PREP-RULINGS 1): `run_substep` resolves the run's century config (_resolve_run_config) after its configuration checks and before the state guard,
# which reads build_runs.plan_manifest once more, through the same digest-verifying `_plan_manifest`. One extra read-only SELECT per non-dry-run substep, checked
# separately (exact text, one parameter, exactly one more than the golden's own manifest reads) and excluded from the statement summary like the state guard.
MANIFEST_READ_SELECT = "SELECT plan_manifest, plan_manifest_digest FROM public.build_runs WHERE id = %s"
LAYER_SELECT = ("SELECT to_regclass('public.ka_gochara_near_miss') IS NOT NULL AND "
                "to_regclass('public.ka_gochara_near_miss_search') IS NOT NULL AND "
                "to_regclass('public.ka_gochara_near_miss_object') IS NOT NULL")
# J-2a-P1L: the snapshot substep reads the applied schema ONCE through p1_minting_closed_reason (RecordStore.p1_anchor_columns_available) to
# decide whether the P1 anchor rows are consulted (and so ledgered). Like the state guard it is checked separately — its exact text, one
# parameter, exactly once — and, in the snapshot substep only (the golden's snapshot never issued it; coverage already did), excluded from
# the statement summary before it is compared with the golden.
P1_GATE_SELECT = ("SELECT count(*) FROM pg_attribute WHERE attrelid = 'public.ka_gochara_relationship_record'::regclass"
                  " AND attname = ANY(%s) AND NOT attisdropped AND attnum > 0")
# #3516 CI repair: the snapshot substep asks the applied schema whether a G12 copy exists (InventoryStore.snapshot_copy_available) one extra time — before the
# P1L ledger decision, because a copy holds horizon-overlapping rows only. Like P1_GATE_SELECT it is checked separately (exact text, no parameter, exactly
# three times in the snapshot substep: the golden already carries two, inside the insert and after it) and one occurrence is excluded from the summary
# before the comparison.
COPY_PROBE_SELECT = ("SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'"
                     " AND column_name IN ('consumed_fact_rows', 'consumed_dasha_rows', 'l1_facts_metadata_digest', 'dasha_metadata_digest')")
PERIOD_GUARD_SELECT = " ".join("""
    WITH governed_chart_dashas AS (
        SELECT * FROM public.chart_dashas
        WHERE chart_id = %s AND ayanamsha_id = %s AND build_id = %s
          AND system_id = ANY(%s) AND level_n BETWEEN 1 AND 4
          AND (verification_pass_status = %s
               OR (system_id = %s AND level_n = %s AND verification_pass_status = ANY(%s))
               OR (system_id = %s AND level_n = %s AND verification_pass_status = ANY(%s))))
    SELECT dasha_row_id, start_iso, end_iso FROM governed_chart_dashas
    WHERE start_iso IS NULL OR end_iso IS NULL OR end_iso <= start_iso LIMIT 1
""".split())


FACTOR_READ_GOLDEN = ("SELECT operand_selector, null_state, function, direction FROM public.ka_gochara_factor"
                      " WHERE factor_id = %s AND rule_version = %s")
# OD-1 D2 (rule_registry.RuleRegistryStore, the persisted-membership read): the one per-factor read also returns `category_mapping`, so an authored
# value table (the P1 Form B rows) is read back as persisted and checked against the declaration. Same statement, same parameters, one more column.
FACTOR_READ_HEAD = ("SELECT operand_selector, null_state, function, direction, category_mapping FROM public.ka_gochara_factor"
                    " WHERE factor_id = %s AND rule_version = %s")


GRAIN_READ_GOLDEN_TAIL = "c.t_exact, c.convention_id FROM public.ka_gochara_relationship_record r"
GRAIN_READ_HEAD_TAIL = "c.t_exact, c.convention_id, NULL::text FROM public.ka_gochara_relationship_record r"


class _Rec:
    """A recording view of the connection: every `execute` is noted (whitespace-normalised SQL, parameter count) and delegated unchanged; everything else passes through."""

    def __init__(self, conn):
        self._c, self.statements = conn, []

    def execute(self, sql, params=None, *a, **k):
        self.statements.append([" ".join(str(sql).split()), 0 if params is None else len(params)])
        return self._c.execute(sql, *((params,) if params is not None else ()), *a, **k)

    def __getattr__(self, name):
        return getattr(self._c, name)


_HEX = re.compile(r"\b[0-9a-f]{12,}\b|\b[0-9a-f]{8,}(?=\u2026)")          # a long hex run, or a truncated id ("candidate manifest 11d2af0c\u2026")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def _norm(text):
    return None if text is None else _UUID.sub("<uuid>", _HEX.sub("<hex>", str(text)))


def _summarise(statements) -> dict:
    """A compact, order-sensitive summary of the statements: how many, how often each distinct shape ran, and the sha256 of the ordered sequence."""
    shapes: dict = {}
    for sql, n in statements:
        shapes[f"{n}|{sql}"] = shapes.get(f"{n}|{sql}", 0) + 1
    seq = hashlib.sha256("\n".join(f"{n}|{sql}" for sql, n in statements).encode("utf-8")).hexdigest()
    return {"count": len(statements), "shapes": dict(sorted(shapes.items())), "sequence_sha256": seq}


def _counts(conn):
    names = [r[0] for r in conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND (table_name LIKE 'ka\\_gochara\\_%' "
        "OR table_name LIKE 'kala\\_gochara\\_%') ORDER BY 1").fetchall()]
    return {t: conn.execute(f'SELECT count(*) FROM public."{t}"').fetchone()[0] for t in names}


def _keys():
    wp = [p for p in ("P2", "P3") if p in writer_mod.WINDOW_PATHS]
    return ([writer_mod.RULES_SUBSTEP, writer_mod.CONVENTION_SUBSTEP, f"{writer_mod.BODY_SUBSTEP_PREFIX}{writer_mod.SUBSTRATE_BODIES[0]}", writer_mod.MANIFEST_SUBSTEP,
             writer_mod.SNAPSHOT_SUBSTEP, f"{writer_mod.INVENTORY_SUBSTEP_PREFIX}{CLASS}", f"{writer_mod.COVERAGE_SUBSTEP_PREFIX}{CLASS}"]
            + [f"{writer_mod.RECORD_SUBSTEP_PREFIX}{CLASS}:{p}" for p in ("P2", "P3")] + [f"{writer_mod.WINDOW_SUBSTEP_PREFIX}{CLASS}:{p}" for p in wp]
            + [f"{writer_mod.VERIFY_SUBSTEP_PREFIX}{CLASS}"])


def capture(template_db, raw: dict | None = None) -> dict:
    """Drive the markerless run's substeps through the real writer on a clone of the template; return the observable record. Identical code runs on main and on HEAD.
    `raw`, when given, receives each substep's unsummarised statement list (HEAD's comparison removes the state guard's statement before summarising)."""
    w = _World(template_db)
    try:
        # The immutable main capture used this session zone. PostgreSQL renders
        # timestamptz refusals and convention JSON in the session zone.
        w.conn.execute("SET TIME ZONE 'Asia/Kolkata'")
        # the orchestrator's `asset_throughput` row of a healthy run (`building`); main never reads it, HEAD's state guard does
        w.conn.execute("CREATE TABLE public.asset_throughput (chart_id uuid, asset_id text, state text, last_built_at timestamptz, rows_written integer, last_error text)")
        w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s::uuid, %s, 'building', now(), 0, NULL)", (CHART_ID, writer_mod.ASSET_ID))
        rec = _Rec(w.conn)
        out = {"golden_commit": GOLDEN_COMMIT, "horizon": [x.isoformat() for x in SHORT], "substeps": []}

        def run(key, dry_run=False):
            rec.statements.clear()
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-golden", db_conn=rec, dry_run=dry_run,
                              config={"chart_id": CHART_ID, "birth_params": BIRTH_PARAMS, "horizon": SHORT, "ephe_path": EPHE_PATH,
                                    "gochara_v5_final_rules": True, "result_policy": "all_null_candidate/1"})   # OD-1: a final-rules run names its policy (the capture IS the all-NULL build). (I) INTERPRETATION: main made the final rules opt-in; the accepted P06 capture IS the final-rule build
            try:
                with w.conn.transaction():
                    res = writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=key, label=key))
                outcome = {"rows_inserted": res.rows_inserted, "notes": _norm(res.notes)}
            except Exception as exc:  # noqa: BLE001 - a refusal is an observable outcome too
                outcome = {"error": type(exc).__name__, "message": _norm(exc)}
            label = key + (" [dry_run]" if dry_run else "")
            if raw is not None:
                raw[label] = [list(s) for s in rec.statements]
            out["substeps"].append({"key": label, "outcome": outcome, "statements": _summarise(rec.statements), "counts": _counts(w.conn)})
        run(writer_mod.RULES_SUBSTEP, dry_run=True)
        for key in _keys():
            run(key)
            if key == writer_mod.MANIFEST_SUBSTEP:
                row = w.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                                     (CHART_ID, writer_mod.GENERATION)).fetchone()
                out["manifest_vector"] = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        return out
    finally:
        w.close()


def test_capture_the_markerless_run(template):
    """Writes the capture to $MB_GOLDEN_OUT (how the golden was generated, on main); without it, only checks the capture is repeatable."""
    got = capture(template)
    dest = os.environ.get("MB_GOLDEN_OUT")
    if dest:
        Path(dest).write_text(json.dumps(got, indent=1, sort_keys=True), encoding="utf-8")
    assert got["substeps"] and "manifest_vector" in got


# ── the comparison (merged P06 against the accepted final-rule golden) ───────────────────────────────────────────────────────────────────────

def _load(path=GOLDEN):
    assert path.exists(), f"the pinned golden is missing: {path}"
    golden = json.loads(path.read_text(encoding="utf-8"))
    assert golden["golden_commit"] == (GOLDEN_COMMIT if path == GOLDEN else "2d75833d3963a61544deaa4c36cc8322cb2cdcb5")
    if path == GOLDEN:
        return golden
    assert golden["provenance"]["sql_adaptations"] == {
        "state_guard_selects_removed": 12,
        "b4_cte_positive_bounds_predicates_removed": 1,
    }
    return golden


def _follow_settlement(golden: dict) -> dict:
    """The golden with its one settled-build identity re-pointed at the governed settlement record.

    Only the dasha build named in the snapshot notes moves; the golden must carry that identity exactly once (so the
    re-pointing is never silent or vacuous) and every other field stays strictly compared.
    """
    from services.gochara_kernel import dasha_read

    run_id = dasha_read.load_dasha_settlement(CHART_ID)["run_id"]
    settled_prefix = run_id.rsplit("-", 1)[0] + "-"
    text = json.dumps(golden, sort_keys=True)
    assert text.count(GOLDEN_SETTLED_BUILD_PREFIX) == 1, "the golden names its settled dasha build exactly once"
    return json.loads(text.replace(GOLDEN_SETTLED_BUILD_PREFIX, settled_prefix))


def _follow_p1_ledger(golden: dict) -> dict:
    """The golden with its one snapshot daśā-row count moved to the J-2a-P1L ledger (see P1L_SNAPSHOT_DASHA_ROWS).

    The golden must carry the old count exactly once (the adaptation is never silent or vacuous); everything else stays strictly compared.
    """
    text = json.dumps(golden, sort_keys=True, ensure_ascii=False)
    assert text.count(GOLDEN_SNAPSHOT_DASHA_ROWS) == 1, "the golden names its snapshot daśā-row count exactly once"
    return json.loads(text.replace(GOLDEN_SNAPSHOT_DASHA_ROWS, P1L_SNAPSHOT_DASHA_ROWS))


# SR-OD1 I1 (OD-1 D2 / P1a): two READ shapes of the window and rule-registry stages gained one selected column each. The accepted P06 capture predates both, so its two
# shapes are compared through this adaptation and nothing else is relaxed: each pair below is (the golden's fragment, the head's fragment); every statement is otherwise
# byte-compared, in order, with the same parameter counts, and the head must issue the new fragment EXACTLY as often as the golden issued the old one (never silently or vacuously).
#   * RuleRegistryStore.persisted_factors reads the authored `category_mapping` back (rule_registry.py), so the persisted Form B value table is checked against the declaration.
#   * WindowStore.read_grain selects the P1 period-anchor column, `NULL::text` for every path except a P1 grain with P1 operand sources bound (window_store.py).
OD1_READ_ADAPTATIONS = (
    (" direction FROM public.ka_gochara_factor WHERE factor_id = %s",
     " direction, category_mapping FROM public.ka_gochara_factor WHERE factor_id = %s"),
    ("c.t_exact, c.convention_id FROM public.ka_gochara_relationship_record r JOIN",
     "c.t_exact, c.convention_id, NULL::text FROM public.ka_gochara_relationship_record r JOIN"),
)


def _follow_od1_reads(rest: list, golden_shapes: dict, key: str, seen: list) -> list:
    """`rest` with the head's OD-1 read shapes mapped back to the golden's, after proving the golden carried each old shape exactly as often as the head issues the new one."""
    for i, (old, new) in enumerate(OD1_READ_ADAPTATIONS):
        golden_n = sum(n for shape, n in golden_shapes.items() if old in shape.split("|", 1)[1])
        head_n = sum(1 for sql, _ in rest if new in sql)
        assert head_n == golden_n, f"{key}: the head issues the OD-1 read shape {i} {head_n} times, the golden's old shape {golden_n}"
        assert not any(old in sql for sql, _ in rest), f"{key}: the old read shape {i} must not survive at the head"
        rest = [[sql.replace(new, old), n] if new in sql else [sql, n] for sql, n in rest]
        seen[i] += golden_n
    return rest


def test_b4_baseline_preserves_final_main_settlement_amendments():
    """Keep final J-4p's outcomes and transcript alongside B4's baseline.

    B4 deliberately removes one positive-bounds SQL predicate; B5's additional
    guard is counted separately below. No other main SQL shape may change.
    """
    main = json.loads(GOLDEN.with_name("mb_ordinary_golden_main.json").read_text())
    b4 = _load(J4P_GOLDEN)
    assert [s["key"] for s in b4["substeps"]] == [s["key"] for s in main["substeps"]]
    for got, want in zip(b4["substeps"], main["substeps"]):
        assert got["outcome"] == want["outcome"], want["key"]
        assert got["counts"] == want["counts"], want["key"]
        if want["key"] == "inventory:marriage":
            shapes = want["statements"]["shapes"]
            assert sum(n for sql, n in shapes.items()
                       if "AND start_iso < end_iso AND" in sql) == 1
            assert got["statements"]["shapes"] == {
                sql.replace("AND start_iso < end_iso AND", "AND"): n
                for sql, n in shapes.items()
            }
            assert got["statements"]["count"] == want["statements"]["count"]
        else:
            assert got["statements"] == want["statements"], want["key"]
    assert b4["manifest_vector"]["implementation"]["window"] == (
        "beaa23107518458b89bb8fe498a8b3682ffe67fb08951196a69c7b18db123aa4")
    # The two immutable captures used different local Swiss library builds;
    # their corpus, version and numerical probe must still agree exactly.
    for key, value in main["manifest_vector"].items():
        if key == "implementation":
            continue
        if key == "ephemeris":
            value = {k: v for k, v in value.items() if k != "library_sha256"}
            actual = {k: v for k, v in b4["manifest_vector"][key].items()
                      if k != "library_sha256"}
        else:
            actual = b4["manifest_vector"][key]
        assert actual == value, key


@pytest.fixture(scope="module")
def head(template):
    raw: dict = {}
    return capture(template, raw), raw


def test_every_substep_kind_of_a_markerless_run_equals_mains_except_the_one_read_only_state_guard_select(head):
    got, raw = head
    want = _follow_p1_ledger(_follow_settlement(_load()))
    assert [s["key"] for s in got["substeps"]] == [s["key"] for s in want["substeps"]]
    adapted = [0] * len(OD1_READ_ADAPTATIONS)
    kinds = {s["key"].split(":")[0].split(" ")[0] for s in want["substeps"]}
    assert kinds >= {"rules", "convention", "body", "manifest", "snapshot", "inventory", "coverage", "record", "window", "verify"}, kinds
    for g, m in zip(got["substeps"], want["substeps"]):
        key = m["key"]
        assert g["outcome"] == m["outcome"], f"{key}: the observable outcome differs from the accepted P06 baseline"
        assert g["counts"] == m["counts"], f"{key}: the table row counts differ from the accepted P06 baseline"
        guard = [s for s in raw[key] if s == [GUARD_SELECT, 2]]
        layer = [s for s in raw[key] if s == [LAYER_SELECT, 0]]
        assert len(layer) == (1 if key == "manifest" else 0), (key, layer)
        period_guard = [s for s in raw[key] if s == [PERIOD_GUARD_SELECT, 11]]
        assert len(period_guard) == (1 if key == "inventory:marriage" else 0), f"{key}: expected the B5 period guard exactly once before the inventory projection"
        rest = [s for s in raw[key] if s not in ([GUARD_SELECT, 2], [PERIOD_GUARD_SELECT, 11], [LAYER_SELECT, 0])]
        golden_reads = m["statements"]["shapes"].get(f"1|{MANIFEST_READ_SELECT}", 0)
        if "[dry_run]" not in key:
            assert rest.count([MANIFEST_READ_SELECT, 1]) == golden_reads + 1, f"{key}: expected exactly one extra plan_manifest read (the century-config resolution)"
            rest.remove([MANIFEST_READ_SELECT, 1])         # the first one is the resolution's: it precedes the substep's own reads (the golden's sequence is order-sensitive)
        if key == writer_mod.SNAPSHOT_SUBSTEP:       # every other substep keeps its own P1 gate reads, compared with the golden unchanged
            assert rest.count([P1_GATE_SELECT, 1]) == 1, f"{key}: expected the new P1-minting schema read exactly once"
            rest.remove([P1_GATE_SELECT, 1])
            assert rest.count([COPY_PROBE_SELECT, 0]) == 3, f"{key}: expected the G12 copy probe exactly three times (before the ledger decision, inside the insert, and after it)"
            rest.remove([COPY_PROBE_SELECT, 0])
        assert len(guard) == (0 if "[dry_run]" in key else 1), f"{key}: expected exactly one state-guard SELECT per non-dry-run substep, saw {len(guard)}"
        if key == "inventory:marriage":
            old_shapes = m["statements"]["shapes"]
            old = [sql.split("|", 1)[1] for sql in old_shapes
                   if "AND start_iso < end_iso AND" in sql]
            assert len(old) == 1
            new = old[0].replace("AND start_iso < end_iso AND", "AND")
            assert rest.count([new, 13]) == 1
            rest = [[old[0], n] if sql == new else [sql, n] for sql, n in rest]
        # OD-1 D2: follow the golden's per-factor read to the head's one extra column. Never silent or vacuous: every occurrence the golden carries must be matched by
        # exactly as many head occurrences of the new text (and none of the old), and the rest of the sequence stays strictly compared.
        golden_factor_reads = m["statements"]["shapes"].get(f"2|{FACTOR_READ_GOLDEN}", 0)
        assert rest.count([FACTOR_READ_GOLDEN, 2]) == 0, f"{key}: the head still ran the pre-D2 factor read"
        assert rest.count([FACTOR_READ_HEAD, 2]) == golden_factor_reads, f"{key}: the factor read ran {rest.count([FACTOR_READ_HEAD, 2])}x, the golden {golden_factor_reads}x"
        rest = [[FACTOR_READ_GOLDEN, n] if sql == FACTOR_READ_HEAD else [sql, n] for sql, n in rest]
        # OD-1 I1 (window_store.WindowStore.read_grain): the grain read carries one more select column, the P1 period-anchor lord; for every non-P1 path it is the constant
        # `NULL::text`. Same follow-the-golden discipline: the golden's occurrences must be matched one for one by the head's new text, none of the old text may remain.
        golden_grain_reads = sum(v for shape, v in m["statements"]["shapes"].items() if GRAIN_READ_GOLDEN_TAIL in shape)
        assert not [s for s, _ in rest if GRAIN_READ_GOLDEN_TAIL in s], f"{key}: the head still ran the pre-I1 grain read"
        assert len([s for s, _ in rest if GRAIN_READ_HEAD_TAIL in s]) == golden_grain_reads, f"{key}: the grain read count differs from the golden's {golden_grain_reads}"
        rest = [[sql.replace(GRAIN_READ_HEAD_TAIL, GRAIN_READ_GOLDEN_TAIL), n] for sql, n in rest]
        if key.startswith("record:"):
            # J-4c F-LEANNESS (C5, test_a53_j4c_leanness_pipeline.py): the P1 anchor-column catalogue probe is read ONCE per store, no longer once per
            # record. The accepted capture ran it before every relationship-record INSERT; this build runs it once (before the first) plus the substep's
            # own single read. Assert exactly that, then put the probe back before each later INSERT so the full ordered sequence is still compared.
            insert = "INSERT INTO public.ka_gochara_relationship_record"
            assert rest.count([P1_GATE_SELECT, 1]) == 2, f"{key}: expected the anchor-column probe exactly twice (substep read + once per store)"
            expanded, minted = [], 0
            for sql, n in rest:
                if sql.startswith(insert):
                    minted += 1
                    if minted > 1:
                        expanded.append([P1_GATE_SELECT, 1])
                expanded.append([sql, n])
            rest = expanded
        rest = _follow_od1_reads(rest, m["statements"]["shapes"], key, adapted)
        assert _summarise(rest) == m["statements"], f"{key}: statements other than the explicitly counted guards and layer probe differ from the accepted P06 baseline"
    assert all(adapted), f"every OD-1 read adaptation must have been exercised by the run (never vacuous): {adapted}"


def test_the_ordinary_manifest_vector_equals_mains_in_every_component_except_the_implementation_identity(head):
    """Preserve P06 inputs with main's evaluation/geometry implementation updates; P06b adds its near-miss verifier to the geometry identity.

    No `horizon_basis` or `test_slice` component may appear in an ordinary run.
    """
    got, want = head[0]["manifest_vector"], _load()["manifest_vector"]
    assert "horizon_basis" not in got and "test_slice" not in got

    same_host = got["ephemeris"]["platform"] == want["ephemeris"]["platform"]
    host_bound = () if same_host else ("platform", "library_sha256", "probe_digest")
    # the golden was generated on `want['ephemeris']['platform']`: the host library's own identity (its artifact hash, platform string and numerical probe digest) is a
    # property of the MACHINE, not of the repository's code, so on another host those three are not compared; every other component is, exactly

    def comparable(v):
        out = {k: x for k, x in v.items() if k != "implementation"}
        out["ephemeris"] = {k: x for k, x in v["ephemeris"].items() if k not in host_bound}
        return out
    assert comparable(got) == comparable(want), "non-implementation components equal the accepted P06 baseline (excluding another host's library identity)"
    assert set(got["implementation"]) == set(want["implementation"])
    differing = sorted(st for st in got["implementation"] if got["implementation"][st] != want["implementation"][st])
    assert differing == ["evaluation", "geometry", "window"], differing
    # ci-kalayantra-w4-p06 (#3516), merge of origin/main (J4C-A/J4C-B, J-2a, the P1 testimony-contact fix): every governed stage now carries main's
    # source changes on top of the accepted P06 capture. The three digests below are re-derived from this merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the function the manifest vector itself is built by); the golden
    # fixture is not re-captured and every other component, outcome, row count and SQL shape is still compared to it unchanged.
    # P06b (this PR) merged on top: its input-vector/verifier changes move the evaluation pin and its near_miss_verifier enters the geometry identity; the pins below are
    # re-derived the same way from the merged tree's real bytes (never relaxed).
    # Evaluation re-pinned again for the snapshot-substep fix (#3516 CI repair): the J-2a-P1L out-of-horizon anchor ledger is kept for a LEGACY snapshot
    # only, because a G12 copy (1305) holds horizon-overlapping rows alone. Re-derived the same way; no golden component is re-captured.
    # Evaluation re-pinned for SR-W3-SHAPE 3 (gochara_v5_defer_in_build_verify): the writer and input_vector sources changed, the ordinary
    # (flag-absent) run's every other component, outcome, row count and SQL shape is unchanged. Merged with P06b (this PR) and re-derived from the
    # merged tree's real bytes with input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (never relaxed).
    # Evaluation re-pinned for F-1305-INVENTED-SUPPORT (#3774): dasha_read and inventory_verifier changed (the snapshot path no longer invents support for a lord held
    # only outside the horizon). Re-derived the same way on the merge of this branch with main (main's bytes give 9f6c462e...); no golden component is re-captured.
    # Evaluation re-pinned again for F-CHANNEL (SR-W34-PREP-RULINGS 1, kalayantra/kind-batch): this branch also changes the ka_gochara_v5 writer's century-config overlay
    # (+101 lines), which sits in the evaluation stage. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (main alone gives 3d24331f...); geometry and window are unchanged by it.
    # Evaluation re-pinned for OD-1 (SR-OD1-NUMERICAL): the ka_gochara_v5 writer's century config now carries result_policy (schema /2) and refuses a final-rules run with no
    # explicit policy, and input_vector binds the qualification table. Re-derived from the merged tree's real bytes the same way (main alone gives f065569b...); no golden
    # component is re-captured (this fixture's run names result_policy all_null_candidate/1, the accepted all-NULL build).
    # Evaluation re-pinned for SR-OD1 W0 (kalayantra/od1-w0-interface, #3832): the ka_gochara_v5 writer's reason pass-through and input_vector (solver_check switch) changed. Re-derived
    # from the merged tree's real bytes with input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin e5fae125... is the pre-W0 merge); geometry
    # is asserted unchanged below and no golden component is re-captured.
    # Evaluation re-pinned ONCE for the SR-OD1 I1 union (S1/S2/P1a/P1b/P1c/C2 on one branch) and the D2 binding of the owner's Form B table: the writer (per-version P1 operands,
    # the verifier self-check), input_vector (p1_nature_operands / p1_operands / p1_valence / the P1 L0 consumption), rule_registry (the authored category_mapping read back and
    # persisted), inventory / inventory_verifier (P1 1.0.0 -> 1.3.0 supersession) and gochara_rules.registry (the P1@1.3.0 rows) changed. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin 906763ec... is the pre-union W0 merge); no golden component is re-captured.
    # Evaluation re-pinned ONCE for SR-OD1 R9c-A10-1 (G-8): input_vector.py itself is an evaluation module and gained the comment/list entry that puts window_solver and
    # window_solver_check into the window stage, so its bytes (hence this digest) moved; no evaluation behaviour changed. Re-derived with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin 26e70004... is the I1 union before this change); no golden component is re-captured.
    # Evaluation and window re-pinned ONCE more at the SR-OD1 merge-back (R1, R3, R5, R4, Q3C, D1 incl. V1, C1, implmods on one head): the evaluation stage moved by the
    # lanes' kernel/rules edits (R4/R5/Q3C p1_operands*, p1_valence, p1_inputs, rule_registry, V1 registry rows, inventory(+_verifier), D1/V1 input_vector) and by `vedha_source`
    # joining the window stage (implmods review, "Answer to check (2)"); geometry is asserted unchanged (a8cb08f0...). Re-derived with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) from the merged tree's real bytes; no golden component is re-captured.
    # Evaluation re-pinned for SR-OD1 R2 (SR-H2-1S): p1_operands and p1_nature_operands search the P1 state boundaries at the 1 s STATE floor and publish the state named limit.
    # Re-pinned ONCE more at the SR-OD1 merge-back wave 2 (R2 on the wave-1 head): the R2 edits and the wave-1 evaluation edits are on one tree; re-derived with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) from the merged tree's real bytes (the prior pin bc169218... is the wave-1 head); no golden component is re-captured.
    # Evaluation re-pinned at the SR-OD1 merge-back wave 2 (D3): D3 owner-confirmed vedha: rule_registry, inventory_verifier, vedha_source and the registry rows moved. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin ec5ef7a9... is the head before this merge); no golden component is re-captured.
    # Evaluation re-pinned for SR-OD1 S3 (the solver wired end to end): ka_gochara_v5 (the writer asks the solver, carries its named reasons) and input_vector (the solver and its
    # prover join the identity) changed. Re-derived the same way (the prior pin 26e70004... is the I1 union); geometry is asserted unchanged below and no golden component is re-captured.
    # Evaluation re-pinned at the SR-OD1 merge-back wave 2 (S3 on R2+D3+R8): S3 solver wiring (ka_gochara_v5, input_vector) joins the R2/D3 evaluation edits on one tree. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin b66b5847... is the head before this merge); no golden component is re-captured.
    # Evaluation re-pinned at the SR-OD1 merge-back wave 3a (R67, l0verify on the wave-2 head): input_vector (window_cert_check joins the window stage list) and input_vector_verifier (P1's L0
    # authorities get an independent digest) are evaluation-stage modules. Re-derived from the merged tree's real bytes with input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES)
    # (the prior pin 65ba9ca9... is the wave-2 head); geometry is unchanged; no golden component is re-captured.
    # Evaluation re-pinned at the SR-OD1 merge-back wave 3b (DASH, R8X): dasha_read (table_coverage_end / coverage_end), inventory_verifier (the table-end arm of the record-support statement),
    # record_verifier, ka_gochara_v5 (the table-end note) and input_vector (g6_plan joins the window stage list) are evaluation-stage modules. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin 3fe1142e... is the wave-3a head); no golden component is re-captured.
    assert got["implementation"]["evaluation"] == "1f37c1f09d854d2703aa301cc8a10553f465c2af68edc3728d83603c79a2bb7e"
    # J-4c (main, #3770): the geometry stage also moved by the Swiss-polished in-orb span edges in record_store._in_orb_span_around_root. With P06b's near_miss_verifier in the
    # geometry identity, the merged-tree digest below is re-derived the same way (main alone gives 4479243d...; evaluation and window are unchanged by J-4c itself; J-4c F-LEANNESS (d96b3bfb0) then moved record_store again, anchor-column probe once per store). No golden component is
    # re-captured: this capture's SQL shapes, counts and outcomes do not depend on the span edges' last arcsec.
    # Geometry re-pinned again for F-1305-INVENTED-SUPPORT (#3774): record_store's period-rows cache now carries the held-presence flag; the digest below is re-derived on the
    # merged tree (main's bytes give 0ecc897c...).
    # Geometry re-pinned for SR-OD1 R2 (SR-H2-1S): contact_reconstruct gains the STATE floor / STATE_NAMED_LIMIT and `_core`'s `min_excursion_seconds` keyword (default unchanged, so the
    # contact geometry's own behaviour and 60 s named limit are untouched). Re-derived the same way (the prior pin a8cb08f0... is the I1 union).
    # Geometry re-pinned at the SR-OD1 merge-back wave 3b (DASH, T13): record_store gains the table-end blank (a P1 support that reaches past the end of the stored daśā table stays the contact span with
    # `unknown`, reason dasha_table_ends_before_support). Re-derived from the merged tree's real bytes the same way (the prior pin 0186cc07... is the wave-3a head); the near-miss / contact geometry
    # is untouched and no golden component is re-captured: this capture's SQL shapes, counts and outcomes do not depend on the table-end arm. (Geometry has now moved once after R2: recorded for T20.)
    assert got["implementation"]["geometry"] == "3c129bd32603839412510625eb0431d07edb121fe8dfc15e1f788948d75c147c"
    # Window re-pinned for PR #3773 (F1): window_verifier derives karaka_agent (the omitted rank factor) as the sweep does. With P06b's window-stage changes the merged-tree
    # digest below is re-derived the same way (main alone gives 6c981eb8...; J-4c F-LEANNESS also changed window_store); evaluation and geometry are untouched by this change, and no golden component is re-captured.
    # Window re-pinned for the W3W4 strict-slice window-qualification fix: window_sweep.build_program no longer lists an OMITTED operand (karaka_agent, null_state omit)
    # as an unresolved reason, so the writer's `unresolved` equals the verifier's. Re-derived on the merge with main (which carries P06b) from the merged tree's real bytes
    # (main alone gives 41d28f76...); evaluation and geometry are untouched by this change and equal main's, and no golden component is re-captured.
    # Window re-pinned for OD-1 (SR-OD1-NUMERICAL): numerical_window_gate joins the window stage, and seal_brief / seal_flow / verification_job / seal_job changed. Re-derived the
    # same way from the merged tree's real bytes (main alone gives e0aea2fa...); no golden component is re-captured.
    # Window re-pinned for SR-OD1 W0 (#3832): window_sweep (per-factor boundaries, per-instant channel hook), window_verifier and window_store changed. Re-derived the same way from
    # the merged tree's real bytes (the prior pin 7dc92acc... is the pre-W0 merge); geometry is unchanged by W0 and no golden component is re-captured.
    # Window re-pinned ONCE for the SR-OD1 I1 union: vedha_verifier (C2), p1_operands_check (P1c) join the window stage and window_sweep / window_store /
    # window_verifier / verification_job changed (S1, S2, P1a-c, C2, D2). Geometry is UNCHANGED by the union (P1a's `RecordStore.fetch_stations` read moved to
    # `WindowStore._fetch_stations` precisely so that it stays a8cb08f0...). Re-derived the same way (the prior pin 873236f3... is the pre-union W0 merge).
    # Window re-pinned ONCE for SR-OD1 R9c-A10-1 (G-8): window_solver (S1) and window_solver_check (S2) join the window stage (they were in no stage list; nothing imports
    # them until the sweep calls the solver, so the import-closure test could not see them). Geometry is asserted unchanged above (a8cb08f0...). Re-derived the same way
    # (the prior pin fc0e7500... is the I1 union before this change); no golden component is re-captured.
    # Window re-pinned for SR-OD1 R2 (SR-H2-1S): p1_operands_check searches at the STATE floor. Re-derived the same way on the wave-2 merged tree (the prior pin e9e05bae... is the wave-1 head);
    # geometry is asserted unchanged by the merge (R2's own geometry pin 0186cc07... carries over); no golden component is re-captured.
    # Window re-pinned at the SR-OD1 merge-back wave 2 (D3): D3 vedha_source/vedha_verifier/input_vector stage moves with the same edits. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin 875d5eec... is the head before this merge); no golden component is re-captured.
    # Window re-pinned at the SR-OD1 merge-back wave 2 (R8): R8 sharded aggregate: verification_job / numerical_window_gate (window stage) changed; evaluation and geometry are unchanged. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin 51971966... is the head before this merge); no golden component is re-captured.
    # Window re-pinned for SR-OD1 S3: window_sweep (the builder calls window_solver), window_verifier (the prover re-derives and compares), window_store, window_solver_check,
    # numerical_window_gate and result_policy (table /2) changed. Re-derived the same way (the prior pin fc0e7500... is the I1 union); geometry is unchanged by S3.
    # Window re-pinned at the SR-OD1 merge-back wave 2 (S3 on R2+D3+R8): S3 window_sweep/window_verifier/window_store/numerical_window_gate on top of R8/D3/R2; geometry unchanged. Re-derived from the merged tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin 0c0ae8a9... is the head before this merge); no golden component is re-captured.
    # Window re-pinned at the SR-OD1 merge-back wave 3a (R67): window_cert_check joins the window stage; window_sweep (the production solver path stores the certificate), window_verifier (the
    # certificate check and the demotion path), window_solver (stored_certificate), window_solver_check and numerical_window_gate (demotions, the cap) changed. Re-derived from the merged tree's
    # real bytes with input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin bb608cda... is the wave-2 head); geometry is unchanged; no golden component is re-captured.
    # Window re-pinned at the SR-OD1 merge-back wave 3b (R8X on R67+S3+D3+R2+R8): g6_plan joins the window stage and numerical_window_gate / verification_job changed (aggregate T16 universe, T18 G-6
    # plan, B4 wall rule); geometry is unchanged. Re-derived from the merged tree's real bytes with input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin
    # ba0588e6... is the wave-3a head); R8X's own lane pin 0e4f173d... was derived without R67's window_cert_check and is superseded; no golden component is re-captured.
    # Window re-pinned for SR-OD1 R8X review S-1 (od1-g6-resolver): window_verifier gains `resolve_inputs` and the production `g6_resolver`, verification_job binds it per grain, g6_plan's
    # "who resolves" text changed. Evaluation and geometry are asserted unchanged above. Re-derived from the tree's real bytes with
    # input_vector_verifier.module_digests(input_vector.IMPLEMENTATION_MODULES) (the prior pin a7d18689... is the wave-3b head); no golden component is re-captured.
    assert got["implementation"]["window"] == "2e7a0b6a1bf77a03157b44fe7143fcc11dc71c6a4464f4efa1a6bf9d1d713eee"
