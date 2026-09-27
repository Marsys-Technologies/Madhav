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

import pathlib
import sys

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
    """Mutation this catches: restoring the catch-all
    (`... or "NO_DETECTOR — no source_query requirement"`) makes this SCU's reason
    revert to that generic string, which does not classify as
    'producer_output_unclaimed' — this assertion would then fail."""
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


def test_derive_all_leaves_a_genuinely_unclassified_scu_without_a_fabricated_reason():
    """The gate review's own constructed case (§2 item 4, first orphan): an SCU whose
    only requirement is `producer_output` and whose only matching claim carries a
    disposition OTHER than `reviewed_output` (e.g. `route_evidence_only`) is neither
    picked up by the reviewed-claims pass NOR given a reason by the producer_output
    branch (a claim DOES exist, so 'unclaimed' does not fire either) — as of this
    commit (before C-5 carries non-reviewed dispositions through), this SCU must
    come out of `derive_all` with `no_detector=None`, not a fabricated catch-all
    string. That is precisely what makes `check_completeness` /
    `validate_derived_artifact` able to read this as a real FAILURE instead of a
    silently-passing green reason (CLAUDE.md §N.8). Mutation this catches: restoring
    the catch-all gives this SCU a generic reason and this assertion fails."""
    snapshot = {
        "scus": [
            {
                "scu_id": "scu.test.orphan_route_evidence_only",
                "availability_contracts": [
                    {"requirements": [{"kind": "producer_output", "asset_id": "ka_kalasutra"}]}
                ],
                "producer_output_claims": [
                    {"asset_id": "ka_kalasutra", "disposition": "route_evidence_only", "evidence": "handler reads kala_activation"}
                ],
            }
        ]
    }
    result = cp.derive_all(snapshot, assets={}, known_tables=set(), table_to_assets={})
    sp = result["scu.test.orphan_route_evidence_only"]
    assert sp.producers == []
    assert sp.no_detector is None
    failures = cp.check_completeness(result)
    assert failures == ["scu.test.orphan_route_evidence_only"]


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
                "no_detector": "NO_DETECTOR — no availability_contracts requirement and no reviewed_output claim",
            },
        }
    }
    failures = cp.validate_derived_artifact(payload)
    assert set(failures) == {"scu.stale_bad_source_ref", "scu.stale_unclassified_reason"}


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
