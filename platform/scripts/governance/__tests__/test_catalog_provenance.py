"""test_catalog_provenance.py — Nikaṣa wave 1, Lane B B-4 proof-it-can-fail gate.

Four cases, named in NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §4 B-4:

  1. a unit with a resolvable range → derived producer
  2. an unresolvable range → no_detector with reason
  3. a shared table → all producers flagged
  4. the naive-regex noise words never appear as producers

Each test is written against a small, self-contained fixture tree (no live DB, no
snapshot.json dependency) so it can run in CI and so each one is a real
mutation-check: reverting the corresponding behavior in catalog_provenance.py makes
that test fail. See the inline comment on each test for the specific mutation it
catches.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import catalog_provenance as cp  # noqa: E402


def _asset(asset_id: str, table: str | None, layer: str = "ganita", nkp: str | None = None) -> cp.AssetRow:
    return cp.AssetRow(
        asset_id=asset_id,
        layer=layer,
        is_active=True,
        dead_flag=False,
        target_table=table,
        natural_key_partition=nkp,
        depends_on=(),
        asset_kind="data",
    )


# ── Case 1: a unit with a resolvable range → derived producer ───────────────


def test_resolvable_range_yields_derived_producer(tmp_path):
    """Mutation this catches: if `resolve_segment_text` silently returned None for a
    valid in-bounds range (e.g. an off-by-one on the inclusive line bounds), this
    would report NO_DETECTOR for a genuinely resolvable unit — the opposite of B-1's
    job. Asserts the exact disposition tag too (never 'reviewed_output' for a
    machine derivation — CLAUDE.md §N.7 honest-tiers)."""
    f = tmp_path / "handler.ts"
    f.write_text(
        "\n".join(
            [
                "const notSql = 'this is prose about today and the weather'  // line 1",
                "const sql = `SELECT * FROM real_table WHERE chart_id = $1`   // line 2",
                "const other = 1                                              // line 3",
            ]
        )
        + "\n"
    )
    req = {"kind": "source_query", "source_ref": f"{f.name}:2-2"}
    known_tables = {"real_table"}
    table_to_assets = {"real_table": [_asset("ga_real", "real_table")]}

    producers, reason = cp.derive_from_source_query(
        "scu.test.resolvable", req, known_tables, table_to_assets, tmp_path
    )

    assert reason is None
    assert len(producers) == 1
    assert producers[0].asset_id == "ga_real"
    assert producers[0].table == "real_table"
    assert producers[0].disposition == "derived_from_source_query"


# ── Case 2: an unresolvable range → no_detector with reason ──────────────────


def test_unresolvable_range_yields_no_detector_with_reason(tmp_path):
    """Mutation this catches (C-2/C-4): if an out-of-bounds or missing-file
    source_ref were treated as 'resolved to empty text' rather than 'unresolved',
    the SCU would silently get producers=[] with NO reason — exactly the
    guessed/blank outcome B-1 forbids ('a unit nothing resolves is NO_DETECTOR —
    never guessed'). Per the gate review finding 2/4 (B_REVIEW.md: 'a mutation
    this test claims to catch — deleting the out-of-bounds guard — actually
    leaves it green'), this test now asserts the EXACT, distinct reason class for
    each of three genuinely different causes, not just a 'starts with
    NO_DETECTOR' string match a mutation could still satisfy."""
    f = tmp_path / "handler.ts"
    f.write_text("const sql = `SELECT 1`\n")  # 1 line only

    # Case 2a: range 50-60 is out-of-bounds for this 1-line file. This is the
    # exact mutation the review named: deleting the bounds check in
    # `resolve_segment_text` used to leave this test green (it would return ""
    # instead of None, which still yields producers=[] with SOME reason — just
    # the WRONG one). Asserting the exact class + that the file's actual current
    # line count and the declared range both appear in the message is what makes
    # that specific mutation fail here.
    req_oob = {"kind": "source_query", "source_ref": f"{f.name}:50-60"}
    producers, reason = cp.derive_from_source_query(
        "scu.test.oob", req_oob, {"real_table"}, {}, tmp_path
    )
    assert producers == []
    assert reason is not None and reason.startswith("NO_DETECTOR")
    assert cp.classify_no_detector_reason(reason) == "source_ref_out_of_range"
    assert "1 lines" in reason
    assert "50-60" in reason

    # Case 2b: a source_ref that doesn't even match <file>:<a>-<b> (e.g. a bare
    # filename or a '#anchor' citation) is a DIFFERENT failure — the segment
    # never had a shape to check bounds on at all. Must classify differently
    # from case 2a, proving "segment unresolved" (bad shape) and "resolved,
    # no relation" are not conflated.
    req_bad_shape = {"kind": "source_query", "source_ref": f"{f.name}#someAnchor"}
    producers2, reason2 = cp.derive_from_source_query(
        "scu.test.badshape", req_bad_shape, {"real_table"}, {}, tmp_path
    )
    assert producers2 == []
    assert reason2 is not None and reason2.startswith("NO_DETECTOR")
    assert cp.classify_no_detector_reason(reason2) == "source_ref_unresolvable_shape"

    # Case 2c: a fully in-bounds, real range that genuinely contains no relation
    # name at all — "resolved, no relation" — must classify as a THIRD, distinct
    # class from both of the above (not "out of range", not "unresolvable shape").
    f2 = tmp_path / "handler2.ts"
    f2.write_text("const notSql = 'no table mentioned here at all'\n")
    req_no_relation = {"kind": "source_query", "source_ref": f"{f2.name}:1-1"}
    producers3, reason3 = cp.derive_from_source_query(
        "scu.test.norelation", req_no_relation, {"real_table"}, {}, tmp_path
    )
    assert producers3 == []
    assert reason3 is not None and reason3.startswith("NO_DETECTOR")
    assert cp.classify_no_detector_reason(reason3) == "no_relation_in_range"

    assert len({
        cp.classify_no_detector_reason(reason),
        cp.classify_no_detector_reason(reason2),
        cp.classify_no_detector_reason(reason3),
    }) == 3


# ── Case 3: a shared table → all producers flagged ───────────────────────────


def test_shared_table_flags_every_producer(tmp_path):
    """Mutation this catches: if `narrow_producers_by_partition` defaulted an
    ambiguous shared table to picking just the first candidate (or to shared=False),
    a caller could misread a multi-producer table as having one sole owner — the
    exact 'sole producer' test D5 rev. 2.1 explicitly rules out ('there is no
    sole-producer test... two full producers of one unit is a §9 consolidation
    opportunity, never a necessity failure')."""
    f = tmp_path / "handler.ts"
    f.write_text("const sql = `SELECT * FROM shared_table WHERE chart_id = $1`\n")
    req = {"kind": "source_query", "source_ref": f"{f.name}:1-1"}
    known_tables = {"shared_table"}
    # Two producers, and neither's natural_key_partition is parseable/pins-matching,
    # so B-1's rule ("otherwise keep all, flagged") must keep both.
    table_to_assets = {
        "shared_table": [
            _asset("owner_a", "shared_table", nkp="shared_table.free_prose, no clean pin"),
            _asset("owner_b", "shared_table", nkp=None),
        ]
    }

    producers, reason = cp.derive_from_source_query(
        "scu.test.shared", req, known_tables, table_to_assets, tmp_path
    )

    assert reason is None
    assert {p.asset_id for p in producers} == {"owner_a", "owner_b"}
    assert all(p.shared is True for p in producers)


def test_natural_key_partition_pin_narrows_to_one_owner(tmp_path):
    """Companion to the shared-table case: when the query pins a fact_category the
    natural_key_partition machinery CAN resolve unambiguously, the result narrows to
    that one owner (shared=False) rather than over-flagging everything — proving
    the shared/narrow branches are both real, not one always winning."""
    f = tmp_path / "handler.ts"
    f.write_text(
        "const sql = `SELECT * FROM chart_facts WHERE fact_category = ANY(ARRAY['ayurdaya']::text[])`\n"
    )
    req = {"kind": "source_query", "source_ref": f"{f.name}:1-1"}
    known_tables = {"chart_facts"}
    table_to_assets = {
        "chart_facts": [
            _asset("ga_ayurdaya", "chart_facts", nkp="chart_facts.fact_category = ayurdaya"),
            _asset("ga_positions", "chart_facts", nkp="chart_facts.fact_category IN (graha_position)"),
        ]
    }

    producers, reason = cp.derive_from_source_query(
        "scu.test.narrow", req, known_tables, table_to_assets, tmp_path
    )
    assert reason is None
    assert len(producers) == 1
    assert producers[0].asset_id == "ga_ayurdaya"
    assert producers[0].shared is False


# ── Case 4: naive-regex noise words never appear as producers ───────────────


def test_noise_words_never_appear_as_producers(tmp_path):
    """Mutation this catches: a naive `FROM (\\w+)` regex with no known-tables filter
    would emit 'today'/'the'/'unnest' as producers for prose and set-returning
    function calls that sit near FROM/JOIN. This is the exact defect class the
    wave1 prompt names by name (§4 B-1: 'a naive regex yields today, the, unnest —
    filter, never trust'). Asserts BOTH that the noise words are absent from the
    output AND that the real table is still found (so this isn't passing by
    accident because nothing resolved at all)."""
    f = tmp_path / "handler.ts"
    f.write_text(
        "\n".join(
            [
                "// Filter by ayanamsha_id (omit for all 5) or method. Default: today.",
                "const desc = 'Max rows for the current page.'",
                "const sql = `",
                "  SELECT * FROM unnest($1::text[]) AS x",
                "  UNION ALL",
                "  SELECT * FROM real_table WHERE chart_id = $2",
                "`",
            ]
        )
        + "\n"
    )
    req = {"kind": "source_query", "source_ref": f"{f.name}:1-7"}
    # known_tables intentionally omits 'today', 'the', 'unnest' — exactly as they
    # would be absent from asset_registry.target_table ∪ information_schema.tables
    # in production (they are not real relations). Deliberately give 'unnest' and
    # 'today' registered asset "owners" too (decoy_unnest/decoy_today) so that if the
    # known_tables filter were bypassed, this test would actually catch it via a
    # producer surfacing — not pass only because no owner happened to exist.
    known_tables = {"real_table"}
    table_to_assets = {
        "real_table": [_asset("ga_real", "real_table")],
        "unnest": [_asset("decoy_unnest", "unnest")],
        "today": [_asset("decoy_today", "today")],
    }

    producers, reason = cp.derive_from_source_query(
        "scu.test.noise", req, known_tables, table_to_assets, tmp_path
    )

    assert reason is None
    producer_names = {p.asset_id for p in producers}
    producer_tables = {p.table for p in producers}
    assert producer_names == {"ga_real"}
    assert "today" not in producer_tables
    assert "the" not in producer_tables
    assert "unnest" not in producer_tables


def test_find_relation_candidates_can_produce_noise_without_the_filter():
    """Documents WHY the filter step exists: the raw regex, unfiltered, DOES emit
    'unnest' and 'today' as candidates from realistic text — proving the noise
    reaches `filter_known_relations` and is removed there, not that it was never
    generated in the first place."""
    literal = "FROM unnest($1::text[]) AS x -- description says omit for today"
    candidates = cp.find_relation_candidates([literal])
    assert "unnest" in candidates
    filtered = cp.filter_known_relations(candidates, {"real_table"})
    assert "unnest" not in filtered
    assert filtered == []


# ── B-4 completeness gate itself ─────────────────────────────────────────────


def test_check_completeness_fails_on_a_scu_with_neither_producer_nor_reason():
    """Mutation this catches: `check_completeness` returning [] unconditionally (a
    cannot-fail gate, CLAUDE.md §N.8) would let a truly-unaccounted SCU through
    silently."""
    provenance = {
        "scu.ok.has_producer": cp.ScuProvenance(
            scu_id="scu.ok.has_producer",
            producers=[cp.Producer("ga_x", "x", "handler.ts:1-1", "derived_from_source_query")],
        ),
        "scu.ok.has_reason": cp.ScuProvenance(
            scu_id="scu.ok.has_reason", no_detector="NO_DETECTOR — no source_query requirement"
        ),
        "scu.bad.neither": cp.ScuProvenance(scu_id="scu.bad.neither"),
    }
    failures = cp.check_completeness(provenance)
    assert failures == ["scu.bad.neither"]


# ── B-3 reader scan must not re-scan its own output ─────────────────────────


def test_reader_scan_excludes_its_own_provenance_output_dir(tmp_path, monkeypatch):
    """Mutation this catches: without excluding PROVENANCE_DIR, a second consecutive
    scan finds its own prior report (which lists 'build_dependencies' on every hit
    line) and the hit count runaway-inflates on every run — observed exactly this
    (67 -> 144 hits) before the exclusion was added. Simulates the real shape: a repo
    tree with one genuine source hit plus a previously-generated report sitting under
    the provenance output dir that itself repeats the term many times."""
    repo = tmp_path
    src_dir = repo / "platform" / "python-sidecar" / "pipeline"
    src_dir.mkdir(parents=True)
    (src_dir / "dispatcher.py").write_text(
        "cur.execute('SELECT asset_id, depends_on FROM build_dependencies')\n"
    )

    prov_dir = repo / "00_ARCHITECTURE" / "briefs" / "nirmana" / "nikasha_test" / "provenance"
    prov_dir.mkdir(parents=True)
    stale_report = prov_dir / "BUILD_DEPENDENCIES_READER_SCAN.md"
    stale_report.write_text("\n".join(f"- L{i}: `build_dependencies`" for i in range(50)))

    monkeypatch.setattr(cp, "PROVENANCE_DIR", prov_dir)
    hits = cp.scan_build_dependencies_readers(repo_root=repo)

    files_hit = {rel for rel, _lineno, _text in hits}
    assert files_hit == {"platform/python-sidecar/pipeline/dispatcher.py"}
    assert len(hits) == 1


def test_reader_scan_excludes_its_own_wave1_report_and_review(tmp_path, monkeypatch):
    """C-5(iv): without excluding WAVE1_DIR, the reader-scan count silently
    drifts every time this lane's own B_REPORT.md / B_REVIEW.md gains or loses a
    line mentioning 'build_dependencies' while describing the scan itself
    (observed: 80 -> 81 the moment B_REPORT.md was extended — B_REVIEW.md 'Also
    noted, blocking nothing'). A genuine source hit outside wave1/ must still be
    found; the wave1/ narrative must contribute none. Mutation this catches:
    removing the WAVE1_DIR exclusion makes the 20 prose lines below reappear as
    hits."""
    repo = tmp_path
    src_dir = repo / "platform" / "python-sidecar" / "pipeline"
    src_dir.mkdir(parents=True)
    (src_dir / "dispatcher.py").write_text(
        "cur.execute('SELECT asset_id, depends_on FROM build_dependencies')\n"
    )
    wave1_dir = repo / "00_ARCHITECTURE" / "briefs" / "nirmana" / "nikasha_test" / "wave1"
    wave1_dir.mkdir(parents=True)
    (wave1_dir / "B_REPORT.md").write_text(
        "\n".join(f"mentions build_dependencies on line {i}" for i in range(20))
    )

    monkeypatch.setattr(cp, "WAVE1_DIR", wave1_dir)
    hits = cp.scan_build_dependencies_readers(repo_root=repo)

    files_hit = {rel for rel, _lineno, _text in hits}
    assert files_hit == {"platform/python-sidecar/pipeline/dispatcher.py"}
    assert len(hits) == 1


def test_check_completeness_passes_when_every_scu_is_accounted_for():
    provenance = {
        "scu.a": cp.ScuProvenance(
            scu_id="scu.a",
            producers=[cp.Producer("ga_x", "x", "handler.ts:1-1", "derived_from_source_query")],
        ),
        "scu.b": cp.ScuProvenance(scu_id="scu.b", no_detector="NO_DETECTOR — no source_query requirement"),
    }
    assert cp.check_completeness(provenance) == []


# ── C-1: the catch-all NO_DETECTOR fallback must not exist ──────────────────
#
# NIKASHA_WAVE1_LANE_B_REVIEW.md finding 1: `derive_all` used to always assign a
# no_detector reason via a catch-all (`"; ".join(...) or "NO_DETECTOR — no
# source_query requirement"`), so the checklist's own constructed case — an SCU
# with no reviewed and no derived producer — always read as a classified reason,
# never as a --check FAILURE. These tests drive `derive_all` (not a hand-built
# ScuProvenance) so the mutation is the actual removed line, not a fixture.


def test_producer_output_requirement_with_no_claims_gets_an_exact_reason_not_a_catchall():
    """Corrected per B_REVIEW2 R5: this SCU's `producer_output` requirement
    ALWAYS carries its own per-requirement reason (the
    `producer_output_unclaimed` branch fires unconditionally once no matching
    claim exists), so restoring the removed catch-all does NOT redden this
    test — the `or` in `"; ".join(...) or "..."` never fires here because
    `per_requirement_reasons` is never empty for this fixture. (An earlier
    version of this docstring wrongly claimed the catch-all mutation reddens
    it; it does not — see `test_derive_all_leaves_a_genuinely_unclassified_scu
    _without_a_fabricated_reason`'s history in C-1/C-5 for the case that
    actually depended on the catch-all, and
    `test_validate_derived_artifact_fails_on_a_stale_hand_edited_entry` /
    `test_classify_no_detector_reason_is_a_closed_set` for what actually
    guards a restored catch-all at HEAD: its text classifies as
    `"unclassified"`, which `--check` rejects via the closed reason-class set,
    not via this test.) What THIS test actually catches: deleting the
    `producer_output_unclaimed` reason-append itself (see the mutation run in
    B_REPORT.md) — that reddens it directly, since the reason would then
    revert to `None`/no reason at all."""
    snapshot = {
        "scus": [
            {
                "scu_id": "scu.test.orphan_producer_output",
                "availability_contracts": [
                    {"requirements": [{"kind": "producer_output", "asset_id": "ga_nonexistent_claim"}]}
                ],
                "producer_output_claims": [],
            }
        ]
    }
    result = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    sp = result["scu.test.orphan_producer_output"]
    assert sp.producers == []
    assert sp.no_detector is not None and sp.no_detector.startswith("NO_DETECTOR")
    assert cp.classify_no_detector_reason(sp.no_detector) == "producer_output_unclaimed"


def test_producer_output_claim_with_non_reviewed_disposition_is_carried_through():
    """C-5(iii): the gate review's own constructed case (§2 item 4, first orphan) —
    an SCU whose only requirement is `producer_output` and whose only matching
    claim carries a disposition OTHER than `reviewed_output` (here,
    `route_evidence_only` for `ka_kalasutra`/`scu.kala.temporal_activation`, the
    D5 ruling's 15th named asset). This claim must be carried through as a real
    producer under ITS OWN disposition — never silently dropped (that was the
    genuinely-unclassified gap the C-1 commit could only prove via
    `check_completeness`, not close), and never relabeled as `reviewed_output`
    (CLAUDE.md §N.7 honest tiers — nothing has independently reviewed this claim).
    Mutation this catches: reverting to carrying only `reviewed_output` claims
    through regresses this SCU back to producers=[] and a failing --check."""
    snapshot = {
        "scus": [
            {
                "scu_id": "scu.test.orphan_route_evidence_only",
                "availability_contracts": [
                    {"requirements": [{"kind": "producer_output", "asset_id": "ka_kalasutra"}]}
                ],
                "producer_output_claims": [
                    {
                        "asset_id": "ka_kalasutra",
                        "disposition": "route_evidence_only",
                        "evidence": "handler reads kala_activation",
                    }
                ],
            }
        ]
    }
    result = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    sp = result["scu.test.orphan_route_evidence_only"]
    assert len(sp.producers) == 1
    p = sp.producers[0]
    assert p.asset_id == "ka_kalasutra"
    assert p.disposition == "route_evidence_only"
    assert p.source_ref == "handler reads kala_activation"
    assert cp.check_completeness(result) == []


def test_classify_no_detector_reason_is_a_closed_set():
    """Any message this script doesn't specifically produce classifies as
    'unclassified', which is deliberately NOT a member of
    `NO_DETECTOR_REASON_CLASSES` — proving the set is actually closed, not
    open-ended by accident."""
    assert cp.classify_no_detector_reason("something a future bug might invent") == "unclassified"
    assert "unclassified" not in cp.NO_DETECTOR_REASON_CLASSES
    assert cp.classify_no_detector_reason(None) == "unclassified"


def test_validate_derived_artifact_fails_on_a_stale_hand_edited_entry():
    """C-1: `--check` validates the COMMITTED artifact itself, not a fresh
    re-derivation. A hand-edited/stale entry — a `derived_from_source_query`
    producer whose `source_ref` was edited into an unresolvable shape, or a
    `no_detector` string that classifies as 'unclassified' — must fail even though
    nothing about today's DB or snapshot would ever produce it via a fresh
    `--derive`. Mutation this catches: `validate_derived_artifact` accepting any
    non-empty `producers` list, or any non-empty `no_detector` string, without
    checking shape/closed-set membership."""
    payload = {
        "scus": {
            "scu.ok": {
                "producers": [
                    {
                        "asset_id": "ga_x",
                        "table": "x",
                        "source_ref": "handler.ts:1-1",
                        "disposition": "derived_from_source_query",
                        "shared": False,
                    }
                ],
            },
            "scu.stale_bad_source_ref": {
                "producers": [
                    {
                        "asset_id": "ga_y",
                        "table": "y",
                        "source_ref": "handler.ts#hand-edited-anchor",
                        "disposition": "derived_from_source_query",
                        "shared": False,
                    }
                ],
            },
            "scu.stale_unclassified_reason": {
                "producers": [],
                "no_detector": "NO_DETECTOR — a reason nobody's classifier has ever produced",
            },
            "scu.ok_no_detector": {
                "producers": [],
                "no_detector": "NO_DETECTOR — no_contract: no availability_contracts requirement and no reviewed_output claim",
            },
        }
    }
    # scu.ok's derived_from_source_query producer must be bound to a matching
    # snapshot source_query requirement (B2) to count as legitimate; everything
    # else in this fixture is deliberately unbacked/malformed with no snapshot
    # counterpart at all.
    snapshot = {
        "scus": [
            {
                "scu_id": "scu.ok",
                "availability_contracts": [
                    {"requirements": [{"kind": "source_query", "source_ref": "handler.ts:1-1"}]}
                ],
            },
        ]
    }
    failures = cp.validate_derived_artifact(payload, snapshot)
    failed_scu_ids = {f.split(":", 1)[0] for f in failures}
    assert failed_scu_ids == {"scu.stale_bad_source_ref", "scu.stale_unclassified_reason"}


# ── C-3: false producers from the one-hop helper / non-handler segments ─────
#
# NIKASHA_WAVE1_LANE_B_REVIEW.md finding 3: four derived producers were wrong.
# (a) the one-hop follower matched a *definition* line as a call. (b) a migration
# file's own unrelated SQL was taken as evidence of the SCU's query. (c) a
# writer's own INPUT read was taken as evidence of the SCU's query. Each test
# below reproduces the real shape of one cause and proves it is now excluded.


def test_one_hop_follower_skips_a_definition_header_not_a_call(tmp_path):
    """C-3(a): the real regression — a declared range's LAST line was itself the
    header of an unrelated function defined in the same file
    (`_idempotency.py:54-78`'s `def replace_prior_chart_dashas(`). The follower
    treated that header as a CALL and ingested the unrelated function's entire
    body, falsely producing a `chart_dashas`/`ga_dashas` producer for
    `get_ayurdaya`/`get_sensitive_degrees`, neither of which queries chart_dashas
    anywhere in their own declared range. Mutation this catches: removing the
    def/function-header guard in `one_hop_helper_texts` makes `ga_decoy`
    reappear as a producer."""
    f = tmp_path / "handler.py"
    f.write_text(
        "\n".join(
            [
                "def range_owner(conn, rows):",  # line 1
                "    return len(rows)",  # line 2
                "",  # line 3
                "def unrelated_function(conn, rows):",  # line 4 — LAST line of the declared range
                "    sql = \"DELETE FROM decoy_table WHERE chart_id = %s\"",  # line 5 — NOT in range
                "    return sql",  # line 6
            ]
        )
        + "\n"
    )
    req = {"kind": "source_query", "source_ref": f"{f.name}:1-4"}
    known_tables = {"decoy_table"}
    table_to_assets = {"decoy_table": [_asset("ga_decoy", "decoy_table")]}

    producers, reason = cp.derive_from_source_query(
        "scu.test.def_header", req, known_tables, table_to_assets, tmp_path
    )
    assert producers == []
    assert reason is not None and reason.startswith("NO_DETECTOR")


def test_migration_segment_is_never_a_producer_source(tmp_path):
    """C-3(b): a migration file's SQL is not evidence of what the SCU's OWN query
    reads. Real regression: `bg_dignity_reference` was picked up from migration
    606's unrelated integrity-check SQL when the actual handler read a different,
    unregistered table (`bg_graha_naisargika_friendship`). A migration-path
    segment must never contribute a relation candidate, even when it is the ONLY
    segment that resolves to real text alongside the handler."""
    handler = tmp_path / "query_graha_naisargika_friendship.ts"
    handler.write_text("const sql = `SELECT graha FROM unregistered_table WHERE x = $1`\n")
    migrations_dir = tmp_path / "supabase" / "migrations"
    migrations_dir.mkdir(parents=True)
    migration = migrations_dir / "606_integrity_contracts.sql"
    migration.write_text("SELECT 1 FROM real_table WHERE exists_check = true;\n")

    req = {
        "kind": "source_query",
        "source_ref": f"{handler.name}:1-1 | supabase/migrations/{migration.name}:1-1",
    }
    known_tables = {"real_table", "unregistered_table"}
    # 'real_table' has a registry owner; 'unregistered_table' (the handler's
    # actual read) does not — the honest 29-class outcome, matching the real bug.
    table_to_assets = {"real_table": [_asset("bg_decoy", "real_table")]}

    producers, reason = cp.derive_from_source_query(
        "scu.test.migration_segment", req, known_tables, table_to_assets, tmp_path
    )
    assert producers == []
    assert reason is not None
    assert "bg_decoy" not in reason
    assert cp.classify_no_detector_reason(reason) == "relation_unowned_by_registry"


def test_writer_segment_input_read_is_never_a_producer_source(tmp_path):
    """C-3(c): a writer's OWN input read (reading its upstream input table to
    build its output) is not the SCU's read. Real regression:
    `bg_texts`/`bg_text_index` were picked up from `bg_compendium_index`'s
    WRITER reading `classical_text_chunks` as ITS OWN input — the handler only
    ever reads `brahma_compendium_index`."""
    handler = tmp_path / "query_compendium_index.ts"
    handler.write_text("const sql = `SELECT * FROM brahma_compendium_index WHERE x = $1`\n")
    writers_dir = tmp_path / "pipeline" / "orchestrator" / "writers"
    writers_dir.mkdir(parents=True)
    writer = writers_dir / "bg_compendium_index.py"
    writer.write_text("cur.execute('SELECT chunk_id FROM classical_text_chunks')\n")

    req = {
        "kind": "source_query",
        "source_ref": f"{handler.name}:1-1 | pipeline/orchestrator/writers/{writer.name}:1-1",
    }
    known_tables = {"brahma_compendium_index", "classical_text_chunks"}
    table_to_assets = {
        "brahma_compendium_index": [_asset("bg_compendium_index", "brahma_compendium_index")],
        "classical_text_chunks": [
            _asset("bg_texts", "classical_text_chunks"),
            _asset("bg_text_index", "classical_text_chunks"),
        ],
    }

    producers, reason = cp.derive_from_source_query(
        "scu.test.writer_segment", req, known_tables, table_to_assets, tmp_path
    )
    assert reason is None
    assert {p.asset_id for p in producers} == {"bg_compendium_index"}


# ── C-4: full/partial/none recount, bounds-checked ───────────────────────────


def test_compute_segment_resolution_counts_distinguishes_full_partial_none(tmp_path):
    """C-4: the recount must distinguish a fully-resolved SCU (every declared
    piece in-bounds), a partially-resolved one (some pieces in-bounds, one
    stale/OOB), and a fully-unresolved one (no numeric-range piece at all) — and
    must name the exact stale piece, including the file's CURRENT line count,
    for the partial case. Mutation this catches: if the bounds check inside
    `resolve_segment_text` were removed, the partial SCU below would misreport
    as 'full' (its stale piece would 'resolve' to a truncated slice instead of
    failing)."""
    full_file = tmp_path / "full.ts"
    full_file.write_text("const sql = `SELECT 1`\n")
    partial_good_file = tmp_path / "partial_good.ts"
    partial_good_file.write_text("const sql = `SELECT 1`\n")
    partial_bad_file = tmp_path / "partial_bad.ts"
    partial_bad_file.write_text("const sql = `SELECT 1`\n")  # 1 line; ref below is 50-60 (OOB)

    snapshot = {
        "scus": [
            {
                "scu_id": "scu.test.full",
                "availability_contracts": [
                    {"requirements": [{"kind": "source_query", "source_ref": f"{full_file.name}:1-1"}]}
                ],
            },
            {
                "scu_id": "scu.test.partial",
                "availability_contracts": [
                    {
                        "requirements": [
                            {
                                "kind": "source_query",
                                "source_ref": f"{partial_good_file.name}:1-1 | {partial_bad_file.name}:50-60",
                            }
                        ]
                    }
                ],
            },
            {
                "scu_id": "scu.test.none_shape",
                "availability_contracts": [
                    {"requirements": [{"kind": "source_query", "source_ref": f"{full_file.name}#anchor"}]}
                ],
            },
        ]
    }
    full, partial, none, stale = cp.compute_segment_resolution_counts(snapshot, repo_root=tmp_path)
    assert (full, partial, none) == (1, 1, 1)
    assert len(stale) == 1
    assert "scu.test.partial" in stale[0]
    assert "1 lines" in stale[0]
    assert "50-60" in stale[0]


def test_out_of_range_handler_segment_wins_priority_over_a_still_resolving_migration_segment(tmp_path):
    """R2 (B_REVIEW2 finding 2): the production shape behind ALL 7 real
    `source_ref_out_of_range` outcomes (`get_ashtakavarga`, `get_aspects`,
    `get_avasthas`, `get_dignity`, `get_eclipse_flags`, `get_panchanga`,
    `get_structural`) — an out-of-bounds HANDLER segment sitting alongside a
    migration segment (commonly `204_chart_facts.sql:...`) that still resolves.
    Because migration-kind segments are excluded from producing relation
    candidates (C-3(b)), `resolved_any` is True (the migration segment
    resolved) but `known` ends up empty — this is a DIFFERENT code path from
    the 'nothing resolved at all' case (`test_unresolvable_range_yields_no_
    detector_with_reason`'s case 2a, where `resolved_any` is False because the
    ONLY segment is the OOB one). The priority branch (the `if oob_reasons:`
    check reached after `if not known:`) must still report
    `source_ref_out_of_range` here, not the generic 'resolved, no relation'
    message. Mutation this catches: commenting out that branch (`if
    oob_reasons:` -> `if False:`) leaves this test red, and reverts all 7
    production outcomes back to `no_relation_in_range` (recorded separately
    against production in B_REPORT.md)."""
    handler = tmp_path / "get_something.ts"
    handler.write_text("const sql = `SELECT 1`\n")  # 1 line only; declared range below is OOB

    migrations_dir = tmp_path / "supabase" / "migrations"
    migrations_dir.mkdir(parents=True)
    migration = migrations_dir / "204_chart_facts.sql"
    migration.write_text("CREATE TABLE chart_facts (id int);\n")

    req = {
        "kind": "source_query",
        "source_ref": f"{handler.name}:50-60 | supabase/migrations/{migration.name}:1-1",
    }
    known_tables = {"chart_facts"}
    table_to_assets = {"chart_facts": [_asset("ga_real", "chart_facts")]}

    producers, reason = cp.derive_from_source_query(
        "scu.test.oob_plus_migration", req, known_tables, table_to_assets, tmp_path
    )
    assert producers == []
    assert reason is not None
    assert cp.classify_no_detector_reason(reason) == "source_ref_out_of_range"
    assert "1 lines" in reason
    assert "50-60" in reason


# ── C-6: table_unregistered distinct from no_unit_names_it ──────────────────


def test_still_outside_asset_with_a_same_domain_unowned_table_reads_table_unregistered():
    """C-6: `bg_prashna_rules` and `ga_prashna` DO produce units — they only read
    as outside because a catalog unit queries a table their writer likely owns
    under a same-domain name (`bg_prashna_lagna_methods`, `ga_prashna_lagna`)
    that `asset_registry.target_table` never records. That must classify as
    `table_unregistered`, distinct from the generic `no_unit_names_it` — an
    asset with no same-domain unowned table at all still gets the generic
    reason. Mutation this catches: removing the table_unregistered branch makes
    both assets misreport as the generic, more pessimistic `no_unit_names_it`."""

    def _row(asset_id, layer, target_table, depends_on=()):
        return cp.AssetRow(
            asset_id=asset_id,
            layer=layer,
            is_active=True,
            dead_flag=False,
            target_table=target_table,
            natural_key_partition=None,
            depends_on=depends_on,
            asset_kind="data",
        )

    assets = {
        "bg_prashna_rules": _row("bg_prashna_rules", "brahmagyan", None),
        "bg_cohort": _row("bg_cohort", "brahmagyan", None),  # no same-domain unowned table
        "ga_real": _row("ga_real", "ganita", "real_table"),
    }
    provenance = {
        "scu.catalog.query_prashna_lagna_methods": cp.ScuProvenance(
            scu_id="scu.catalog.query_prashna_lagna_methods",
            no_detector=(
                "NO_DETECTOR — relation_unowned_by_registry: relation name(s) "
                "['bg_prashna_lagna_methods'] matched no row in "
                "asset_registry.target_table ('handler.ts:1-1')"
            ),
        ),
        "scu.catalog.get_real": cp.ScuProvenance(
            scu_id="scu.catalog.get_real",
            producers=[cp.Producer("ga_real", "real_table", "handler.ts:1-1", "derived_from_source_query")],
        ),
    }
    closure = cp.compute_closure_report(assets, provenance)
    reasons = {
        row["asset_id"]: row["reason"]
        for rows in closure["still_outside_by_layer"].values()
        for row in rows
    }
    assert reasons["bg_prashna_rules"].startswith("table_unregistered (bg_prashna_lagna_methods)")
    assert reasons["bg_cohort"].startswith("no_unit_names_it")
    assert closure["still_outside_reason_class_counts"] == {"table_unregistered": 1, "no_unit_names_it": 1}


# ── R1 (B_REVIEW2 finding 1): --check must compare the artifact against the ──
# catalog's own SCU id set, not just validate whatever entries happen to be
# present. `{"scus": {}}` and an artifact missing one real SCU both used to
# print PASS and exit 0.


def test_validate_scu_coverage_detects_missing_and_extra_scus():
    """Direct, mutation-isolated test of the pure coverage function. Mutation
    this catches: `validate_scu_coverage` returning [] unconditionally, or only
    checking one direction (missing OR extra, not both)."""
    snapshot = {"scus": [{"scu_id": "scu.a"}, {"scu_id": "scu.b"}]}
    payload = {"scus": {"scu.a": {}, "scu.c": {}}}
    failures = cp.validate_scu_coverage(payload, snapshot)
    assert any("scu.b" in f and "missing" in f for f in failures)
    assert any("scu.c" in f and "not in the catalog" in f for f in failures)
    assert len(failures) == 2


def _full_valid_artifact_matching_catalog() -> dict:
    """Build a synthetic-but-catalog-complete artifact: every REAL catalog SCU
    id (read from the actual snapshot file, via `cp.load_snapshot()`) gets a
    trivially valid `no_detector` entry, so the only thing under test in the
    three `main(["--check"])` tests below is SCU COVERAGE, never entry
    validity."""
    snapshot = cp.load_snapshot()
    scus = {
        scu["scu_id"]: {
            "producers": [],
            "no_detector": "NO_DETECTOR — no_contract: no availability_contracts requirement and no reviewed_output claim",
        }
        for scu in snapshot["scus"]
    }
    return {"scus": scus}


def test_check_fails_on_an_empty_artifact_through_the_real_entry_point(tmp_path, monkeypatch, capsys):
    """R1, probe D2: `{"scus": {}}` printed 'PASS: all 0 SCUs' and exited 0
    before this correction. Drives the REAL `main(["--check"])` entry point
    (not the pure function in isolation) end to end. Mutation this catches:
    removing the `validate_scu_coverage` call from main()'s --check branch
    makes this pass (exit 0) again."""
    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps({"scus": {}}))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert "FAIL" in out


def test_check_fails_when_the_artifact_is_missing_a_catalog_scu_through_the_real_entry_point(
    tmp_path, monkeypatch, capsys
):
    """R1, probe D: an artifact missing one real catalog SCU (e.g. the
    equivalent of deleting `get_dignity`) printed 'PASS: all 181 SCUs' and
    exited 0 before this correction. The missing SCU must be named in the
    output. Mutation this catches: removing the coverage check."""
    payload = _full_valid_artifact_matching_catalog()
    removed_id = sorted(payload["scus"])[0]
    del payload["scus"][removed_id]

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert removed_id in out


def test_check_fails_when_the_artifact_carries_an_unknown_scu_through_the_real_entry_point(
    tmp_path, monkeypatch, capsys
):
    """R1: an artifact carrying an SCU id no longer in the catalog (a stale
    entry left over from before a snapshot/registry change — exactly the case
    the pre-R1 docstrings claimed was already handled) must fail, naming it.
    Mutation this catches: removing the coverage check."""
    payload = _full_valid_artifact_matching_catalog()
    payload["scus"]["scu.test.not_in_catalog"] = {
        "producers": [],
        "no_detector": "NO_DETECTOR — no_contract: no availability_contracts requirement and no reviewed_output claim",
    }

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert "scu.test.not_in_catalog" in out


# ── R6: CLOSURE_REPORT.md must state the closure computation itself ─────────


def test_write_closure_report_md_states_the_closure_computation(tmp_path):
    """R6 (B_REVIEW2, C-6 'not landed' half): `CLOSURE_REPORT.md` previously
    stated only the population query — never the closure computation itself
    (seed sets, edges, the recursive `depends_on` traversal or its SQL
    equivalent). Mutation this catches: removing the 'How this closure is
    computed' section from `write_closure_report_md` reddens this test."""
    closure = {
        "population_active_count": 1,
        "before": {"named_producers": 0, "necessary_count": 0},
        "after": {"named_producers": 0, "necessary_count": 0},
        "still_outside_by_layer": {},
        "still_outside_reason_class_counts": {},
    }
    out_path = tmp_path / "CLOSURE_REPORT.md"
    cp.write_closure_report_md(closure, out_path=out_path)
    text = out_path.read_text()
    assert "How this closure is computed" in text
    assert "depends_on" in text
    assert "RECURSIVE" in text


def test_closure_traversal_prose_reads_computed_numbers_not_a_literal(tmp_path):
    """N (B_REVIEW4 N3): the traversal paragraph used to hardcode "the same
    111/127 and the same 16 still-outside assets". With a closure whose numbers
    are NOT 111/127/16 the paragraph must state the computed ones. Mutation
    this catches: restoring the literal."""
    closure = {
        "population_active_count": 9,
        "before": {"named_producers": 2, "necessary_count": 3},
        "after": {"named_producers": 4, "necessary_count": 5},
        "still_outside_by_layer": {
            "ganita": [{"asset_id": "ga_x", "reason_class": "no_unit_names_it", "reason": "r"}],
            "kala": [
                {"asset_id": "ka_y", "reason_class": "no_unit_names_it", "reason": "r"},
                {"asset_id": "ka_z", "reason_class": "table_unregistered", "reason": "r"},
            ],
        },
        "still_outside_reason_class_counts": {"no_unit_names_it": 2, "table_unregistered": 1},
    }
    out_path = tmp_path / "CLOSURE_REPORT.md"
    cp.write_closure_report_md(closure, out_path=out_path)
    traversal = [ln for ln in out_path.read_text().splitlines() if ln.startswith("**Traversal**")]
    assert len(traversal) == 1
    assert "**5/9**" in traversal[0]
    assert "**3**" in traversal[0]
    assert "111" not in traversal[0] and "127" not in traversal[0]


# ── R7 (B_REVIEW3): --check must not accept a fabricated exemption-tier ──────
# producer that never traces to anything the catalog itself declares. Before
# this correction, ANY non-empty source_ref string was enough for
# reviewed_output / route_evidence_only / derived_from_service_probe.


def _load_real_committed_artifact() -> dict:
    with open(cp.DERIVED_OUTPUT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_check_fails_when_all_no_detector_scus_get_a_fake_route_evidence_only_producer(
    tmp_path, monkeypatch, capsys
):
    """R7, probe G2 (the gate review's own attack): replace every NO_DETECTOR SCU
    in a copy of the REAL committed artifact with a fabricated
    `{"asset_id": "zz_fake", "disposition": "route_evidence_only",
    "source_ref": "x"}` producer. Before this correction this read as 182/182
    covered and PASSED (exit 0). Mutation this catches: removing the
    snapshot-backing cross-check in `validate_derived_artifact` makes this pass
    again."""
    payload = _load_real_committed_artifact()
    faked = []
    for scu_id, entry in payload["scus"].items():
        if entry.get("no_detector"):
            entry["producers"] = [
                {"asset_id": "zz_fake", "disposition": "route_evidence_only", "source_ref": "x"}
            ]
            entry["no_detector"] = None
            faked.append(scu_id)
    assert len(faked) == 75  # the exact count the gate review's own attack used

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    for scu_id in faked:
        assert scu_id in out


def test_check_fails_when_get_dignity_is_given_a_fake_reviewed_output_producer(
    tmp_path, monkeypatch, capsys
):
    """R7, probe G1: `get_dignity` has no `reviewed_output` claim in the snapshot
    at all. Giving it a fabricated `{"asset_id": "zz_fake", "disposition":
    "reviewed_output", "source_ref": "x"}` producer used to pass. Mutation this
    catches: removing the snapshot-backing check."""
    payload = _load_real_committed_artifact()
    target = "scu.catalog.get_dignity"
    assert target in payload["scus"]
    payload["scus"][target]["producers"] = [
        {"asset_id": "zz_fake", "disposition": "reviewed_output", "source_ref": "x"}
    ]
    payload["scus"][target]["no_detector"] = None

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_check_fails_on_a_service_probe_producer_for_an_unprobed_asset(
    tmp_path, monkeypatch, capsys
):
    """R7: a `derived_from_service_probe` producer must name an asset the SCU's
    OWN `kind: service_probe` requirement actually probes — not just any
    asset_id that happens to sound plausible."""
    payload = _load_real_committed_artifact()
    target = None
    for scu_id, entry in payload["scus"].items():
        if any(p.get("disposition") == "derived_from_service_probe" for p in entry.get("producers", [])):
            target = scu_id
            break
    assert target is not None, "expected >=1 derived_from_service_probe producer in the committed artifact"
    payload["scus"][target]["producers"] = [
        {
            "asset_id": "zz_fake_probe",
            "disposition": "derived_from_service_probe",
            "source_ref": "service_probe:fake",
            "table": None,
        }
    ]
    payload["scus"][target]["no_detector"] = None

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_check_passes_on_the_real_committed_artifact_unmodified(capsys):
    """R7 (d): the real, unmodified committed artifact must still PASS after the
    snapshot-backing correction lands."""
    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "PASS" in out


def test_all_committed_exemption_producers_are_snapshot_backed():
    """R7 (d): confirms the exact count the gate review found — 24 exemption-tier
    producers (reviewed_output + route_evidence_only + derived_from_service_probe)
    in the real committed artifact, ALL backed by the snapshot (0 unbacked).
    This is precisely what makes the unmodified artifact pass."""
    payload = _load_real_committed_artifact()
    snapshot = cp.load_snapshot()
    claim_keys = cp.snapshot_producer_output_claim_keys(snapshot)
    probe_assets = cp.snapshot_service_probe_asset_ids(snapshot)

    exemption_count = 0
    unbacked = []
    for scu_id, entry in payload["scus"].items():
        for p in entry.get("producers", []):
            disp = p.get("disposition")
            if disp in ("reviewed_output", "route_evidence_only"):
                exemption_count += 1
                if (p.get("asset_id"), disp) not in claim_keys.get(scu_id, set()):
                    unbacked.append((scu_id, p.get("asset_id"), disp))
            elif disp == "derived_from_service_probe":
                exemption_count += 1
                if p.get("asset_id") not in probe_assets.get(scu_id, set()):
                    unbacked.append((scu_id, p.get("asset_id"), disp))
    assert unbacked == []
    assert exemption_count == 24


# ── B_REVIEW4: three siblings of the R7 defect, plus a test-gap and a ────────
# classifier fix.


def test_check_fails_when_temporal_activation_is_reduced_to_only_its_route_evidence_producer(
    tmp_path, monkeypatch, capsys
):
    """B1 (B_REVIEW4): an SCU whose ONLY producer is `route_evidence_only`
    passed --check before this correction, even though D5 rev. 2.1's own
    wording is "names the asset(s) that PRODUCE or part-produce it" — route
    evidence is carried (never dropped) but is not production, so it must
    never count as coverage on its own. This is an EXECUTOR APPLICATION of
    that wording, not yet a recorded native ruling — flagged for confirmation
    at the R85 fold (see B_REPORT.md). Mutation this catches: letting
    route_evidence_only count toward coverage (i.e. reverting
    `scu_has_covering_producer`'s exclusion / the disposition check in
    `validate_derived_artifact`) makes this pass again."""
    payload = _load_real_committed_artifact()
    target = "scu.kala.temporal_activation"
    assert target in payload["scus"]
    reo_producers = [
        p for p in payload["scus"][target]["producers"] if p.get("disposition") == "route_evidence_only"
    ]
    assert len(reo_producers) == 1, "expected exactly one route_evidence_only producer on this SCU"
    payload["scus"][target]["producers"] = reo_producers
    payload["scus"][target]["no_detector"] = None

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_derive_all_gives_a_route_evidence_only_producer_an_explicit_no_detector_reason():
    """B1: at DERIVATION time (not just --check time), an SCU whose only
    producer ends up being a carried `route_evidence_only` claim must get the
    new `route_evidence_only_not_a_producer` no_detector reason — never
    silently read as 'covered' just because producers[] is non-empty."""
    snapshot = {
        "scus": [
            {
                "scu_id": "scu.test.reo_only",
                "availability_contracts": [
                    {"requirements": [{"kind": "producer_output", "asset_id": "ka_kalasutra"}]}
                ],
                "producer_output_claims": [
                    {
                        "asset_id": "ka_kalasutra",
                        "disposition": "route_evidence_only",
                        "evidence": "handler reads kala_activation",
                    }
                ],
            }
        ]
    }
    result = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    sp = result["scu.test.reo_only"]
    assert len(sp.producers) == 1  # the claim is still carried, never dropped
    assert sp.producers[0].disposition == "route_evidence_only"
    assert sp.no_detector is not None
    assert cp.classify_no_detector_reason(sp.no_detector) == "route_evidence_only_not_a_producer"
    assert not cp.scu_has_covering_producer(sp.producers)


def _reo_only_snapshot() -> dict:
    """Two synthetic SCUs whose only claim is `route_evidence_only`: one with no
    other requirement, one that ALSO carries a `kind: derived` requirement (so
    derive_all has a second reason to join — the route-evidence one must still
    be the class token)."""
    claim = {
        "asset_id": "ka_kalasutra",
        "disposition": "route_evidence_only",
        "evidence": "handler reads kala_activation",
    }
    return {
        "scus": [
            {
                "scu_id": "scu.test.reo_only",
                "availability_contracts": [
                    {"requirements": [{"kind": "producer_output", "asset_id": "ka_kalasutra"}]}
                ],
                "producer_output_claims": [dict(claim)],
            },
            {
                "scu_id": "scu.test.reo_plus_derived",
                "availability_contracts": [
                    {
                        "requirements": [
                            {"kind": "producer_output", "asset_id": "ka_kalasutra"},
                            {"kind": "derived", "source_ref": "x.ts#y"},
                        ]
                    }
                ],
                "producer_output_claims": [dict(claim)],
            },
        ]
    }


def test_honest_route_evidence_only_scu_round_trips_through_the_real_check(tmp_path, monkeypatch, capsys):
    """B1 (review-4 corrections): the honest state for an SCU whose only producer
    is route evidence is `NO_DETECTOR — route_evidence_only_not_a_producer`, and
    `--check` must ACCEPT that state — derivation and gate must agree. Before
    this correction `derive_all` wrote the reason but `validate_derived_artifact`
    rejected it, because its F2 guard treated the snapshot's route-evidence claim
    as proof a producer belonged there (route evidence is not production). Also
    pins that the route-evidence reason is the class token even when another
    reason is joined to it. Mutation this catches: restoring the guard to fire on
    ANY snapshot claim (including route_evidence_only) reddens this test."""
    snapshot = _reo_only_snapshot()
    prov = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    for scu_id in ("scu.test.reo_only", "scu.test.reo_plus_derived"):
        assert cp.classify_no_detector_reason(prov[scu_id].no_detector) == "route_evidence_only_not_a_producer"
    payload = {"scus": {k: v.to_json() for k, v in prov.items()}}

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)
    monkeypatch.setattr(cp, "load_snapshot", lambda *a, **k: snapshot)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code == 0, out
    assert "PASS" in out


def test_check_fails_on_a_route_evidence_only_scu_carrying_no_reason(tmp_path, monkeypatch, capsys):
    """B1, isolated: the snapshot declares ONLY a route-evidence claim, the artifact
    carries exactly that (bound, present) producer and NO no_detector reason.
    Nothing else can fail this SCU — binding holds, presence holds — so the only
    thing that makes `--check` exit non-zero is that route evidence does not
    count as coverage. Mutation this catches: letting route_evidence_only count
    as coverage turns this into a PASS."""
    snapshot = _reo_only_snapshot()
    prov = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    payload = {"scus": {k: v.to_json() for k, v in prov.items()}}
    for entry in payload["scus"].values():
        assert [p["disposition"] for p in entry["producers"]] == ["route_evidence_only"]
        entry.pop("no_detector", None)

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)
    monkeypatch.setattr(cp, "load_snapshot", lambda *a, **k: snapshot)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert "scu.test.reo_only" in out and "scu.test.reo_plus_derived" in out


def test_check_fails_when_a_route_evidence_only_scu_is_relabelled_with_another_class(
    tmp_path, monkeypatch, capsys
):
    """B1, reverse direction: an SCU whose only producer is a bound route-evidence
    claim must carry the `route_evidence_only_not_a_producer` class — relabelling
    it `no_contract` (exact format, closed set) hides the one fact derive_all
    states first. Mutation this catches: dropping the reverse agreement check."""
    snapshot = _reo_only_snapshot()
    prov = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    payload = {"scus": {k: v.to_json() for k, v in prov.items()}}
    payload["scus"]["scu.test.reo_only"]["no_detector"] = "NO_DETECTOR — no_contract: relabelled"

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)
    monkeypatch.setattr(cp, "load_snapshot", lambda *a, **k: snapshot)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert "scu.test.reo_only" in out
    assert "scu.test.reo_plus_derived" not in out


def test_check_fails_on_a_route_evidence_reason_with_no_route_evidence_producer(tmp_path, monkeypatch, capsys):
    """B1: `route_evidence_only_not_a_producer` is a claim about the producers
    present, not free text. On an SCU with no route-evidence producer at all
    (`get_dignity`) it is false and must fail. Mutation this catches: dropping
    the class/producer agreement check lets the false reason pass."""
    payload = _load_real_committed_artifact()
    target = "scu.catalog.get_dignity"
    payload["scus"][target]["producers"] = []
    payload["scus"][target]["no_detector"] = "NO_DETECTOR — route_evidence_only_not_a_producer: fabricated"

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_check_fails_when_temporal_activation_is_cut_to_route_evidence_with_the_honest_reason(
    tmp_path, monkeypatch, capsys
):
    """B1: the review's reo-only cut (`scu.kala.temporal_activation` reduced to
    its single `route_evidence_only` producer), this time WITH the exact-format
    `route_evidence_only_not_a_producer` reason a forger would add. It must
    still fail: the snapshot declares two `reviewed_output` claims on this SCU,
    so the honest reason is false here. Mutation this catches: letting route
    evidence count as coverage makes the cut read covered and pass."""
    payload = _load_real_committed_artifact()
    target = "scu.kala.temporal_activation"
    entry = payload["scus"][target]
    entry["producers"] = [p for p in entry["producers"] if p.get("disposition") == "route_evidence_only"]
    assert len(entry["producers"]) == 1
    entry["no_detector"] = "NO_DETECTOR — route_evidence_only_not_a_producer: only route-evidence claim(s)"

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_check_fails_when_all_no_detector_scus_get_a_fake_source_query_producer(
    tmp_path, monkeypatch, capsys
):
    """B2 (B_REVIEW4): a fabricated `derived_from_source_query` producer
    (`table: no_such_table_xyz`, `source_ref: nope.ts:1-2` — shape-valid but
    uncatalogued) on all 75 NO_DETECTOR SCUs used to pass 182/182. Binding
    each producer's `source_ref` to a `kind: source_query` requirement's own
    `source_ref` on the SAME SCU (checkable from the snapshot alone, no DB)
    closes this. Table EXISTENCE remains a stated, DB-bound limit (E).
    Mutation this catches: removing the `source_ref in source_query_refs`
    binding check makes this pass again."""
    payload = _load_real_committed_artifact()
    faked = []
    for scu_id, entry in payload["scus"].items():
        if entry.get("no_detector"):
            entry["producers"] = [
                {
                    "asset_id": "zz_fake",
                    "table": "no_such_table_xyz",
                    "source_ref": "nope.ts:1-2",
                    "disposition": "derived_from_source_query",
                    "shared": False,
                }
            ]
            entry["no_detector"] = None
            faked.append(scu_id)
    assert len(faked) == 75

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    # B2 (review-4 corrections): each failure names BOTH the SCU and the unbound
    # producer (asset id + disposition), on one line — not just the SCU.
    lines = out.splitlines()
    for scu_id in faked:
        assert any(
            scu_id in ln and "'zz_fake'" in ln and "'derived_from_source_query'" in ln for ln in lines
        ), scu_id


def test_all_committed_source_query_producers_are_snapshot_bound():
    """B2 (d): confirms the count the gate review found — all 294
    `derived_from_source_query` producers in the real committed artifact have
    a `source_ref` equal to a `kind: source_query` requirement's own
    `source_ref` on the SAME SCU in the snapshot. This is what makes the
    unmodified artifact still pass under the new B2 binding check."""
    payload = _load_real_committed_artifact()
    snapshot = cp.load_snapshot()
    refs_by_scu = cp.snapshot_source_query_refs(snapshot)

    bound_count = 0
    unbound = []
    for scu_id, entry in payload["scus"].items():
        for p in entry.get("producers", []):
            if p.get("disposition") == "derived_from_source_query":
                bound_count += 1
                if p.get("source_ref") not in refs_by_scu.get(scu_id, set()):
                    unbound.append((scu_id, p.get("asset_id")))
    assert unbound == []
    assert bound_count == 294


def test_check_fails_when_a_fake_producer_is_appended_beside_a_real_one(
    tmp_path, monkeypatch, capsys
):
    """B3 (B_REVIEW4): the check used to stop at the first VALID producer per
    SCU — a fabricated `{zz_fake, reviewed_output, "x"}` producer appended
    beside (or placed before) an already-covered SCU's real producers still
    passed. Every producer must now be validated. This is the artifact a
    follow-on lane will wire into `compiler.ts`, so a fabricated producer
    reaching it would be a real problem, not just a report-honesty one.
    Mutation this catches: restoring the first-valid-producer short-circuit
    (breaking out of the per-producer loop as soon as one is bound) makes
    this pass again."""
    payload = _load_real_committed_artifact()
    target = "scu.bodha.mechanism.network"
    assert target in payload["scus"]
    assert payload["scus"][target]["producers"], "expected this SCU to already have real producer(s)"
    payload["scus"][target]["producers"].append(
        {"asset_id": "zz_fake", "disposition": "reviewed_output", "source_ref": "x"}
    )

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_check_fails_when_a_fake_producer_is_placed_first_and_every_fake_is_named(
    tmp_path, monkeypatch, capsys
):
    """B3 (review-4 corrections), bypass3b + "every producer": a fabricated
    producer placed BEFORE an already-covered SCU's real producers, plus a
    second, differently-named fabricated producer appended to a SECOND covered
    SCU (a derived-tier one, `scu.catalog.get_divisionals`). Both SCUs must fail
    and both fake producers must be named — the check validates every producer
    of every SCU, of every tier, not the first valid one. Mutation this catches:
    restoring the first-valid-producer short-circuit (unbound producers ignored,
    loop stops at the first covering one)."""
    payload = _load_real_committed_artifact()
    first = "scu.bodha.mechanism.network"
    second = "scu.catalog.get_divisionals"
    assert payload["scus"][first]["producers"] and payload["scus"][second]["producers"]
    payload["scus"][first]["producers"].insert(
        0, {"asset_id": "zz_fake_first", "disposition": "reviewed_output", "source_ref": "x"}
    )
    payload["scus"][second]["producers"].append(
        {
            "asset_id": "zz_fake_sq",
            "table": "no_such_table_xyz",
            "source_ref": "nope.ts:1-2",
            "disposition": "derived_from_source_query",
        }
    )

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    lines = out.splitlines()
    assert any(first in ln and "'zz_fake_first'" in ln for ln in lines)
    assert any(second in ln and "'zz_fake_sq'" in ln for ln in lines)


def test_check_fails_when_a_real_claim_is_copied_onto_the_wrong_scu(tmp_path, monkeypatch, capsys):
    """T1 (B_REVIEW4 test gap): the per-SCU binding is correct today (bypass1/
    bypass2 in the gate's own probes), but nothing in this suite pinned it —
    a mutation that widened the lookup from per-SCU to global (a union of
    every SCU's claims/probes) left the whole suite green. Copies the REAL
    `(bo_yantra_mechanism, reviewed_output)` claim — genuinely declared on
    `scu.bodha.mechanism.network` — onto an unrelated NO_DETECTOR SCU and
    expects `--check` to still fail it. Mutation this catches: replacing the
    per-SCU `claim_keys_by_scu.get(scu_id, set())` lookup with a global union
    across all SCUs reddens this test."""
    payload = _load_real_committed_artifact()
    wrong_target = None
    for scu_id, entry in payload["scus"].items():
        if entry.get("no_detector") and scu_id != "scu.bodha.mechanism.network":
            wrong_target = scu_id
            break
    assert wrong_target is not None

    payload["scus"][wrong_target]["producers"] = [
        {
            "asset_id": "bo_yantra_mechanism",
            "disposition": "reviewed_output",
            "source_ref": "platform/migrations/1009_nirmana_l2_bo_yantra_mechanism_output_digest_spec.sql:114",
        }
    ]
    payload["scus"][wrong_target]["no_detector"] = None

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert wrong_target in out


def test_check_fails_when_a_real_service_probe_is_copied_onto_the_wrong_scu(tmp_path, monkeypatch, capsys):
    """T (review-4 corrections), probe half of the per-SCU pin: `ka_graha_sancara`
    is genuinely probed — but only by `scu.catalog.call_ephemeris_at_t`'s own
    service_probe requirement. Copied as a `derived_from_service_probe` producer
    onto NO_DETECTOR `scu.catalog.assess_career` it must fail. Mutation this
    catches: replacing the per-SCU `probe_assets_by_scu.get(scu_id, set())`
    lookup with a union across all SCUs."""
    payload = _load_real_committed_artifact()
    source = "scu.catalog.call_ephemeris_at_t"
    wrong_target = "scu.catalog.assess_career"
    real = [
        p
        for p in payload["scus"][source]["producers"]
        if p.get("disposition") == "derived_from_service_probe" and p.get("asset_id") == "ka_graha_sancara"
    ]
    assert len(real) == 1, "expected the real probe producer on its own SCU"
    assert payload["scus"][wrong_target].get("no_detector")
    payload["scus"][wrong_target]["producers"] = [dict(real[0])]
    payload["scus"][wrong_target]["no_detector"] = None

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert any(wrong_target in ln and "'ka_graha_sancara'" in ln for ln in out.splitlines())


def test_check_fails_on_a_no_detector_reason_containing_a_trigger_substring_but_no_exact_prefix(
    tmp_path, monkeypatch, capsys
):
    """F (B_REVIEW4): the OLD substring classifier let a bogus reason
    containing a known class's trigger text ANYWHERE pass —
    `'zzz kind: derived zzz'` classified as `derived_kind_no_source_query`.
    The new exact-match classifier requires the literal `"NO_DETECTOR — "`
    prefix followed immediately by a real class token and `": "` — a string
    that merely contains a trigger substring, with no such prefix, must be
    `"unclassified"` and fail. Mutation this catches: reverting
    `classify_no_detector_reason` to substring search makes this pass again."""
    payload = _load_real_committed_artifact()
    target = "scu.catalog.get_dignity"
    assert target in payload["scus"]
    payload["scus"][target]["producers"] = []
    payload["scus"][target]["no_detector"] = "zzz kind: derived zzz"

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


@pytest.mark.parametrize(
    "forged",
    [
        "NO_DETECTOR — zzz kind: derived zzz",
        "NO_DETECTOR — I made this up; no availability_contracts requirement exists lol",
        "NO_DETECTOR — xx source_ref_out_of_range xx: y",
        "NO_DETECTOR — resolved range(s) contain no relation name: y",
        "NO_DETECTOR — no_contractX: y",
        "NO_DETECTOR —  no_contract: leading space is not the class token",
        "NO_DETECTOR — no_contract",
    ],
)
def test_check_fails_on_a_prefixed_reason_whose_class_token_is_not_exact(forged, tmp_path, monkeypatch, capsys):
    """F (review-4 corrections): WITH the exact `NO_DETECTOR — ` prefix, a reason
    is valid only when the text before its FIRST ":" is exactly a closed-set
    class. Each forged string carries an old substring trigger (or a near-miss
    class name) somewhere else, which the substring classifier accepted.
    Mutation this catches: restoring substring matching (the pre-F classifier)."""
    payload = _load_real_committed_artifact()
    target = "scu.catalog.get_dignity"
    payload["scus"][target]["producers"] = []
    payload["scus"][target]["no_detector"] = forged

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out


def test_classify_splits_on_the_first_colon_and_exact_matches():
    """F: split on the FIRST ":" (not ": "), exact-match the class token."""
    assert cp.classify_no_detector_reason("NO_DETECTOR — no_contract:detail") == "no_contract"
    assert cp.classify_no_detector_reason("NO_DETECTOR — no_contract: a: b") == "no_contract"
    assert cp.classify_no_detector_reason("NO_DETECTOR — no_contract") == "unclassified"
    assert cp.classify_no_detector_reason("NO_DETECTOR — x: no_contract: y") == "unclassified"
    assert cp.classify_no_detector_reason("no_contract: y") == "unclassified"


def test_check_fails_when_a_reviewed_claim_is_demoted_beside_derived_producers(tmp_path, monkeypatch, capsys):
    """F (review-4 corrections): `scu.kala.temporal_activation` keeps its derived
    producers (so it still reads covered) but its two snapshot-declared
    `reviewed_output` claims are removed. The snapshot says those producers
    belong here, so this must fail, naming each missing one. Mutation this
    catches: dropping the declared-producer presence check."""
    payload = _load_real_committed_artifact()
    target = "scu.kala.temporal_activation"
    entry = payload["scus"][target]
    removed = sorted(p["asset_id"] for p in entry["producers"] if p.get("disposition") == "reviewed_output")
    assert removed == ["ka_bhavishya_lekha", "ka_yojaka"]
    entry["producers"] = [p for p in entry["producers"] if p.get("disposition") != "reviewed_output"]
    assert any(p.get("disposition") == "derived_from_source_query" for p in entry["producers"])

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    lines = out.splitlines()
    for asset_id in removed:
        assert any(target in ln and repr(asset_id) in ln and "missing" in ln for ln in lines), asset_id


def test_all_snapshot_declared_producers_are_present_in_the_committed_artifact():
    """F: the presence check is satisfiable — the real artifact carries all 15
    declared producer_output_claims pairs and all 9 service-probe pairs."""
    payload = _load_real_committed_artifact()
    snapshot = cp.load_snapshot()
    claim_keys = cp.snapshot_producer_output_claim_keys(snapshot)
    probe_assets = cp.snapshot_service_probe_asset_ids(snapshot)
    n_claims = sum(len(v) for v in claim_keys.values())
    n_probes = sum(len(v) for v in probe_assets.values())
    missing = []
    for scu_id, keys in claim_keys.items():
        present = {(p["asset_id"], p["disposition"]) for p in payload["scus"][scu_id]["producers"]}
        missing += [(scu_id, k) for k in keys - present]
    for scu_id, assets in probe_assets.items():
        present = {p["asset_id"] for p in payload["scus"][scu_id]["producers"]
                   if p["disposition"] == "derived_from_service_probe"}
        missing += [(scu_id, a) for a in assets - present]
    assert (n_claims, n_probes, missing) == (15, 9, [])


def test_check_fails_when_a_reviewed_scus_producers_are_erased_and_replaced_with_a_fake_reason(
    tmp_path, monkeypatch, capsys
):
    """F2 (B_REVIEW4): erasing a REVIEWED SCU's real producers and writing a
    fabricated but exact-format `no_contract` reason in their place must still
    fail — the snapshot's own `producer_output_claims` entry for this SCU is
    proof a producer belongs here, and no no_detector reason (however
    correctly formatted) can override that. Mutation this catches: dropping
    the "snapshot already proves a producer belongs here" guard (letting any
    exact-classified reason excuse a claimed SCU) makes this pass again."""
    payload = _load_real_committed_artifact()
    target = "scu.bodha.mechanism.network"  # has a real reviewed_output claim in the snapshot
    assert target in payload["scus"]
    assert payload["scus"][target]["producers"]
    payload["scus"][target]["producers"] = []
    payload["scus"][target]["no_detector"] = "NO_DETECTOR — no_contract: fabricated, this SCU has a real contract"

    artifact_path = tmp_path / "producer_provenance.derived.json"
    artifact_path.write_text(json.dumps(payload))
    monkeypatch.setattr(cp, "DERIVED_OUTPUT_PATH", artifact_path)

    exit_code = cp.main(["--check"])
    out = capsys.readouterr().out
    assert exit_code != 0
    assert target in out
