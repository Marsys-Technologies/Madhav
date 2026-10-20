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
merged tree whose digests are pinned below, so no separate J4C pin is applied to this capture. Exactly one state-guard SELECT is checked
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
                                    "gochara_v5_final_rules": True})   # (I) INTERPRETATION: main made the final rules opt-in; the accepted P06 capture IS the final-rule build
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
    kinds = {s["key"].split(":")[0].split(" ")[0] for s in want["substeps"]}
    assert kinds >= {"rules", "convention", "body", "manifest", "snapshot", "inventory", "coverage", "record", "window", "verify"}, kinds
    for g, m in zip(got["substeps"], want["substeps"]):
        key = m["key"]
        assert g["outcome"] == m["outcome"], f"{key}: the observable outcome differs from the accepted P06 baseline"
        assert g["counts"] == m["counts"], f"{key}: the table row counts differ from the accepted P06 baseline"
        guard = [s for s in raw[key] if s == [GUARD_SELECT, 2]]
        period_guard = [s for s in raw[key] if s == [PERIOD_GUARD_SELECT, 11]]
        assert len(period_guard) == (1 if key == "inventory:marriage" else 0), f"{key}: expected the B5 period guard exactly once before the inventory projection"
        rest = [s for s in raw[key] if s not in ([GUARD_SELECT, 2], [PERIOD_GUARD_SELECT, 11])]
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
        assert _summarise(rest) == m["statements"], f"{key}: statements other than the explicitly counted guards differ from the accepted P06 baseline"


def test_the_ordinary_manifest_vector_equals_mains_in_every_component_except_the_implementation_identity(head):
    """Preserve P06 inputs with main's evaluation/geometry implementation updates.

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
    # Evaluation re-pinned again for the snapshot-substep fix (#3516 CI repair): the J-2a-P1L out-of-horizon anchor ledger is kept for a LEGACY snapshot
    # only, because a G12 copy (1305) holds horizon-overlapping rows alone. Re-derived the same way; no golden component is re-captured.
    # Evaluation re-pinned for SR-W3-SHAPE 3 (gochara_v5_defer_in_build_verify): the writer and input_vector sources changed, the ordinary
    # (flag-absent) run's every other component, outcome, row count and SQL shape is unchanged. Re-derived the same way (main's bytes give 6c86c3fb…).
    assert got["implementation"]["evaluation"] == "9f6c462e41ee255517dc9619e469ef8a77eab1acfccf40cabef03c6a18835bcf"
    # J-4c: the geometry stage moved ONLY by the Swiss-polished in-orb span edges in record_store._in_orb_span_around_root (06825a43... -> the digest below, re-derived the same
    # way on the merged tree; evaluation and window are unchanged by J-4c). No golden component is re-captured: this capture's SQL shapes, counts and outcomes do not depend on the span edges' last arcsec.
    assert got["implementation"]["geometry"] == "e7634d7faf7df43521f5236d79a94c8a31192e62d78dc8eaa939160eaca0a6f7"
    assert got["implementation"]["window"] == "78b4d0a1cc63047045710a873f76b87f90de4493c4960bb08fd97ef1ad13aea3"
