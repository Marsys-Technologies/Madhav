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
    """Mutation this catches: if an out-of-bounds or missing-file source_ref were
    treated as 'resolved to empty text' rather than 'unresolved', the SCU would
    silently get producers=[] with NO reason — exactly the guessed/blank outcome
    B-1 forbids ('a unit nothing resolves is NO_DETECTOR — never guessed')."""
    f = tmp_path / "handler.ts"
    f.write_text("const sql = `SELECT 1`\n")  # 1 line only

    # Range 50-60 is out of bounds for a 1-line file.
    req_oob = {"kind": "source_query", "source_ref": f"{f.name}:50-60"}
    producers, reason = cp.derive_from_source_query(
        "scu.test.oob", req_oob, {"real_table"}, {}, tmp_path
    )
    assert producers == []
    assert reason is not None
    assert reason.startswith("NO_DETECTOR")

    # A source_ref that doesn't even match <file>:<a>-<b> (e.g. a bare filename or
    # a '#anchor' citation) must also fail honestly, not silently pass through.
    req_bad_shape = {"kind": "source_query", "source_ref": f"{f.name}#someAnchor"}
    producers2, reason2 = cp.derive_from_source_query(
        "scu.test.badshape", req_bad_shape, {"real_table"}, {}, tmp_path
    )
    assert producers2 == []
    assert reason2 is not None
    assert reason2.startswith("NO_DETECTOR")


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
