"""
v5_small_test_shared.py — the ONE copy of what the dispatch (C37) and the teardown (C38) of the ka_gochara_v5 SMALL TEST both rely on.

Codex (PR 3097 review, ruling 2): the dispatch must establish eligibility and ownership with the SAME proof the teardown uses, so the proof
lives here, imported by both scripts; neither carries a second copy.

  * `stamp_problem` / `generation_ownership` — is the existing generation '5.0' output PROVEN to be a small-test slice's?
      The manifest's stamp is validated by the WRITER'S OWN functions (`ka_gochara_v5._validate_test_slice`, `_slice_component`,
      imported — no second implementation of the marker rules), against the ORIGINAL marker preimage of an owned run when a run row
      survives, else by reconstruction from the normalised component (and the refusal says which); the manifest's horizon must be the
      stamp's; the stored input snapshot must carry the stamped manifest's vector and every inventory header its identity.
  * `end_state_problems` — the Nirmana monitor's N-137 predicate for the v5 asset (`definitions.ts`,
      NIRMANA_STAGED_INERT_CANDIDATE_RULES + runtimeEvidenceSql): catalog_status not RETIRED, nothing depends on the asset, and no
      receipt or build_run_assets row of the asset on ANY chart from a run that is not a 'gochara-v5-small-test' run (a NULL run link
      counts as non-test).

Every function takes a dict-row cursor and reads only; none writes, locks or commits.
"""
from __future__ import annotations

import os
import sys

ASSET_ID = "ka_gochara_v5"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"
GENERATION = "5.0"
# The century (final, ordinary candidate) build's own run trigger: a century run carries NO slice marker, so it is never mistaken for
# a small-test or measuring run (and the small-test/measuring teardown, which is bound to TRIGGERED_BY and the stamp, never selects it).
CENTURY_TRIGGERED_BY = "gochara-v5-century"
CENTURY_ITEM = "J-4e"

# (table, extra WHERE) — the generation's OUTPUT. The order is the teardown's deletion order (the kernel's own: RecordStore.
# delete_generation_chain, InventoryStore.delete_generation_inventory; a test runs the REAL helpers against a recording connection).
CHAIN_TABLES = (
    ("ka_gochara_eval_window", ""),                 # window membership cascades with it
    ("ka_gochara_relationship_record", ""),         # prerequisites cascade with it
    ("ka_gochara_contact", ""),                     # ALL of the generation's contacts (orphans and shared ones too)
    ("kala_gochara_coverage", " AND partition_kind = 'event_class'"),   # last: records / windows reference it
)
INVENTORY_TABLES = (
    ("ka_gochara_search_interval", ""),
    ("ka_gochara_search_obligation", ""),
    ("ka_gochara_search_path_pin", ""),
    ("ka_gochara_search_inventory", ""),            # its verification rows cascade
    ("ka_gochara_search_input_snapshot", ""),
)
OUTPUT_TABLES = CHAIN_TABLES + INVENTORY_TABLES     # what "generation output exists" means (the manifest is judged on its own)
# Migration 1308's chart x generation near-miss tables (NearMissStore.delete_generation deletes exactly these two, by chart_id AND generation).
# Neither references the other and nothing references them, so their order is free. They are the teardown's to delete and the absence proof's
# to count, but they are NOT in OUTPUT_TABLES: the dispatch's "generation output exists" test is unchanged. ka_gochara_near_miss_object is GLOBAL
# and insert-only (its trigger refuses DELETE; other charts and generations share an object): it is deliberately in none of these lists, so no
# teardown deletes it and no absence proof counts it. The scoped backup (backup_v5_small_test_scope.json) records it instead.
NEAR_MISS_TABLES = (
    ("ka_gochara_near_miss", ""),
    ("ka_gochara_near_miss_search", ""),
)
ABSENCE_TABLES = OUTPUT_TABLES + NEAR_MISS_TABLES   # the generation-scoped tables the absence census must count (the manifest and the cascade children are added where it is built)


class Refused(RuntimeError):
    """A named refusal: nothing was changed. The message holds ids and counts only, never connection text."""


def writer():
    """The sidecar writer module: its slice validator is the SINGLE implementation of what a valid stamp is."""
    sidecar = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python-sidecar"))
    if sidecar not in sys.path:
        sys.path.insert(0, sidecar)
    try:
        import pipeline.orchestrator.writers.ka_gochara_v5 as module
    except Exception as exc:  # an environment without the sidecar deps cannot validate: refuse, never skip
        raise Refused(
            f"cannot import the ka_gochara_v5 writer to validate the slice stamp ({type(exc).__name__}); run this from an "
            "environment with the sidecar dependencies — the stamp is never accepted unvalidated") from None
    return module


def count(cur, sql: str, params: tuple = ()) -> int:
    cur.execute(sql, params)
    return int(cur.fetchone()["n"])


def table_exists(cur, table: str) -> bool:
    cur.execute("SELECT to_regclass(%s) AS r", (f"public.{table}",))
    return cur.fetchone()["r"] is not None


def same_instant(a, b) -> bool:
    try:
        return a == b
    except TypeError:
        return False


def refuse_if_frozen(cur) -> None:
    """Refuse, by name, when generation '5.0' of the pinned chart is PUBLISHED (immutable), SEALED (permanent publication history) or the
    SERVING generation. Both scripts make this check, inside their transaction and under the chart lock. Reads only."""
    cur.execute(
        """SELECT manifest_id FROM kala_gochara_publication
           WHERE chart_id = %s AND generation = %s AND status = 'published'""",
        (CHART_ID, GENERATION),
    )
    published = cur.fetchone()
    if published:
        raise Refused(
            f"kala_gochara_publication has a PUBLISHED '5.0' manifest {published['manifest_id']} for chart {CHART_ID} "
            "— a published generation is immutable")

    cur.execute(
        """SELECT manifest_id FROM ka_gochara_generation_seal
           WHERE chart_id = %s AND generation = %s""",
        (CHART_ID, GENERATION),
    )
    seal = cur.fetchone()
    if seal:
        raise Refused(
            f"ka_gochara_generation_seal records '5.0' (manifest {seal['manifest_id']}) for chart {CHART_ID} — a sealed "
            "generation is permanent publication history")

    cur.execute("SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = %s", (CHART_ID,))
    authority = cur.fetchone()
    if authority and authority["authoritative_generation"] == GENERATION:
        raise Refused(
            f"kala_gochara_authority names '5.0' as the authoritative_generation for chart {CHART_ID} — a serving "
            "generation is never touched")


def prove_stamp(vector, run_manifests=(), *, require_run: bool = False):
    """(problem, source, sliced, matched): problem is None when the input vector PROVES a test slice, by the WRITER'S OWN validation; source says HOW
    (or, for a refusal, what was tried); sliced is the writer's validated slice (None on a refusal); `matched` is the list of EVERY surviving owned run id whose original marker proves the
    stamp (empty for a reconstruction or a refusal): the caller of an interrupted replacement needs two DISTINCT runs.

    The writer hashes the ORIGINAL marker (`_validate_test_slice` digest) but stores the NORMALISED component (`_slice_component`: scored
    class order, UTC timestamps). The proof is:
      1. the original marker preimage: an owned run's `plan_manifest` (immutable by migration 595), its digest checked with the runner's
         canonicalisation (`writer._manifest_digest`), its marker validated by the writer, its digest equal to the stamp's
         `marker_digest` and its normalised form equal to the stored component. This accepts a marker the writer accepted whatever form it
         was written in (Z timestamps, another class order);
      2. ONLY when NO owned run row survives (all pruned): the reconstruction — the marker rebuilt from the normalised component and
         validated, its component equal to the stored one (digest recomputed). The refusal says that this fallback was used.
    While ANY owned run row survives its original-preimage proof MUST succeed: a surviving run with a wrong digest, a missing marker or a
    different marker is refused, never rescued by reconstruction (Codex round 4, T4). `require_run` demands a run-proven stamp even
    when no run survives (used for the snapshot's stamp in an interrupted replacement)."""
    module = writer()
    if not isinstance(vector, dict):
        return "the manifest carries no input vector", None, None, []
    if vector.get("stored_scope") != module.TEST_SLICE_SCOPE:
        return f"stored_scope is {vector.get('stored_scope')!r}, not {module.TEST_SLICE_SCOPE!r}", None, None, []
    comp = vector.get("test_slice")                   # the component key the writer stamps (ka_gochara_v5, the input-vector stamp check)
    if not isinstance(comp, dict):
        return "no 'test_slice' component", None, None, []
    sliced, source, notes, matched = None, None, [], []
    for run_id, manifest, manifest_digest in run_manifests:
        if not isinstance(manifest, dict) or module.TEST_SLICE_KEY not in manifest:
            notes.append(f"run {run_id} carries no slice marker")
            continue
        if module._manifest_digest(manifest) != manifest_digest:
            notes.append(f"run {run_id}: its plan_manifest does not match its plan_manifest_digest")
            continue
        try:
            candidate = module._validate_test_slice(manifest[module.TEST_SLICE_KEY])
        except module.TestSliceRefusal as exc:
            notes.append(f"run {run_id}: its marker fails the writer's own validation ({exc})")
            continue
        if candidate.digest == comp.get("marker_digest") and module._slice_component(candidate) == comp:
            matched.append(run_id)                    # EVERY run whose original marker proves the stamp, not just the first
            if sliced is None:
                sliced, source = candidate, f"proved against the ORIGINAL marker of run {run_id} (digest {candidate.digest[:12]})"
            continue
        notes.append(f"run {run_id}: its marker digest {candidate.digest[:12]} is not the stamp's")
    if sliced is None:
        if run_manifests:
            return ("an owned run row survives, so its ORIGINAL marker preimage must prove the stamp, and it does not "
                    f"(reconstruction is not allowed while a run survives): {'; '.join(notes)}"), None, None, []
        if require_run:
            return "no owned run row survives to prove this stamp against its original marker (a run-proven stamp is required)", None, None, []
        marker = {"schema": comp.get("schema"), "run": comp.get("run"), "horizon": comp.get("horizon"), "classes": comp.get("classes")}
        preimage = "no owned run row survives"
        try:
            reconstructed = module._validate_test_slice(marker)
        except module.TestSliceRefusal as exc:
            return (f"the stamp's marker fails the writer's own validation ({exc}); the original marker preimage could not prove it "
                    f"({preimage}), so the reconstruction from the normalised component was used and failed"), None, None, []
        except Exception as exc:  # noqa: BLE001 — any other failure to validate is a refusal, never an acceptance
            return f"the stamp's marker could not be validated ({type(exc).__name__}); preimage: {preimage}", None, None, []
        if comp != module._slice_component(reconstructed):
            return ("the stamp is not the writer's component for its marker (the marker digest or a normalised field differs from what "
                    f"the writer's own _slice_component produces); the original marker preimage could not prove it ({preimage}), so "
                    "the reconstruction from the normalised component was used and failed"), None, None, []
        sliced, source = reconstructed, f"proved by RECONSTRUCTION from the normalised component (original marker preimage unavailable: {preimage})"
    return None, source, sliced, matched


def stamp_proof(vector, horizon, run_manifests=(), *, require_run=False):
    """(problem, source, matched): `prove_stamp`, plus the manifest's horizon must be the stamp's horizon."""
    problem, source, sliced, matched = prove_stamp(vector, run_manifests, require_run=require_run)
    if problem:
        return problem, None, []
    if horizon is None or not (same_instant(getattr(horizon, "lower", None), sliced.horizon[0])
                               and same_instant(getattr(horizon, "upper", None), sliced.horizon[1])):
        return "the manifest's horizon is not the stamp's horizon", None, []
    return None, source, matched


def stamp_problem(vector, horizon, run_manifests=()):
    """(problem, source): `stamp_proof` without the matched run ids."""
    problem, source, _matched = stamp_proof(vector, horizon, run_manifests)
    return problem, source


def stamped_classes(vector) -> list[str]:
    return list((vector.get("test_slice") or {}).get("classes") or [])


def generation_rows(cur) -> int:
    total = 0
    for table, extra in OUTPUT_TABLES:
        total += count(cur, f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s{extra}", (CHART_ID, GENERATION))
    return total


#: Every foreign key INTO a parent table, with the COMPLETE child and parent column lists (Codex round 4 T2). `scripts/v5_small_test_incoming_fks_readback.sql`
#: runs the same text, read-only, for the steward before the dry run (a test pins the two are the same).
INCOMING_FK_SQL = (
    "SELECT c.conname, c.conrelid::regclass::text AS tbl, c.confdeltype AS action, "
    "ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(attnum, ord) "
    "JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum ORDER BY k.ord) AS child_cols, "
    "ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(attnum, ord) "
    "JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = k.attnum ORDER BY k.ord) AS parent_cols "
    "FROM pg_constraint c WHERE c.contype = 'f' AND c.confrelid = %s::regclass ORDER BY c.conname"
)
_ACTIONS = {"n": "SET NULL", "c": "CASCADE", "a": "NO ACTION", "r": "RESTRICT", "d": "SET DEFAULT"}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def referencing_rows(cur, parent: str, parent_pk: str, ids: list[str], understood=()) -> list[str]:
    """Every foreign key INTO `public.<parent>` from the catalog, with the complete child and parent column lists, minus the tables the
    calling script deletes itself. `understood` is a set of whole RELATIONSHIPS `(table, child columns, parent columns, delete action)` the
    caller has analysed and whose referencing rows its deletion scope covers (Codex round 5 (3): exempt the relationship, never the table —
    any OTHER foreign key from the same table goes through the shape check and the refusal). A SUPPORTED key is a single child column referencing the parent's primary-key column (`parent_pk`):
    the rows that reference `ids` come back as named problems (table, column, delete action, count). ANY OTHER SHAPE (a composite key, or a
    key that targets a different column) is REFUSED BY NAME: this code cannot prove deleting the parent row safe for it, and a silent
    skip would let the delete cascade into or null an audit row (Codex round 4 T2). The catalog is the list, so a reference added by a
    later migration is found without anyone remembering to add it here."""
    if not ids:
        return []
    cur.execute(INCOMING_FK_SQL, (f"public.{parent}",))
    found, unsupported = [], []
    for ref in cur.fetchall():
        table = ref["tbl"][len("public."):] if ref["tbl"].startswith("public.") else ref["tbl"]
        child, target = list(ref["child_cols"]), list(ref["parent_cols"])
        if (table.strip('"'), tuple(child), tuple(target), ref["action"]) in understood:
            continue
        if len(child) != 1 or target != [parent_pk]:
            unsupported.append(f"{ref['conname']} on {table}({', '.join(child)}) -> {parent}({', '.join(target)})")
            continue
        n = count(cur, f"SELECT count(*) AS n FROM {ref['tbl']} WHERE {_quote(child[0])} = ANY(%s::uuid[])", (ids,))
        if n:
            found.append(f"{table}.{child[0]} ({n} row(s), ON DELETE {_ACTIONS.get(ref['action'], ref['action'])})")
    if unsupported:
        raise Refused(
            f"incoming foreign key(s) into {parent} have a shape this script does not support (a composite key, or one that targets a "
            f"column other than {parent_pk}): {unsupported} — it cannot prove deleting the row safe for them; resolve by hand "
            "(run scripts/v5_small_test_incoming_fks_readback.sql to see every incoming key)")
    return found


def generation_exists(cur):
    """(output_rows, manifest_row_or_None): does ANY generation '5.0' output, snapshot, inventory or manifest exist for the chart?"""
    rows = generation_rows(cur)
    cur.execute("SELECT manifest_id, status FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GENERATION))
    return rows, cur.fetchone()


def generation_ownership(cur, owned: list[str], *, remedy: str, unproven: str, notes: list[str] | None = None, lock: bool = False, require_run=False):
    """Is the existing generation '5.0' output (the chain, the inventory, the snapshot) of this chart PROVEN to be a small-test slice's?
    Returns `(manifest_row_or_None, output_rows)`; raises `Refused` by name when output or a manifest exists and is not proven. `owned` is
    the ids of the small-test runs (their original markers are the preimage of the stamps); `remedy` is the sentence that tells the
    operator what to do when the output is the test's but interrupted in a way that cannot be proved, `unproven` the sentence for output
    that is not provably a small test's at all; `notes` (a list) receives how each stamp was proved. `lock=True` takes the manifest row
    `FOR UPDATE` (the teardown holds it through its delete, so no new reference can appear; needs UPDATE on at least one column).

    INTERRUPTED REPLACEMENT (steward D3): a later slice committed its manifest and died before its snapshot substep replaced the older
    output, so the stored snapshot carries ANOTHER vector than the manifest. That state is removable only when BOTH stamps are
    proved by owned test runs' original markers: the current manifest's (as always) and the SNAPSHOT's own stamp (its marker digest recorded
    in the snapshot vector, proved by another owned run). The older output is then provably an earlier test slice's (the writer replaces
    the whole chain at the snapshot substep, so a chain under snapshot S1 is S1's), and the inventory headers are checked against the
    SNAPSHOT's stamp. Anything not provable stays refused. Reads only (apart from the optional row lock)."""
    notes = notes if notes is not None else []
    rows = generation_rows(cur)
    cur.execute("SELECT manifest_id, status, input_generation_vector, horizon FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s"
                + (" FOR UPDATE" if lock else ""), (CHART_ID, GENERATION))
    manifest = cur.fetchone()
    if not (rows or manifest):
        return None, 0
    if manifest is None:
        raise Refused(
            f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} with NO manifest — nothing proves they are the "
            "small test's; they are left as they are")
    run_manifests = []
    if owned:
        cur.execute("SELECT id, plan_manifest, plan_manifest_digest FROM build_runs WHERE id = ANY(%s::uuid[]) ORDER BY created_at DESC",
                    (owned,))
        run_manifests = [(str(r["id"]), r["plan_manifest"], r["plan_manifest_digest"]) for r in cur.fetchall()]
    problem, stamp_source, manifest_runs = stamp_proof(manifest["input_generation_vector"], manifest["horizon"], run_manifests, require_run=require_run)
    if stamp_source:
        notes.append(stamp_source)
    if manifest["status"] != "candidate" or problem:
        raise Refused(
            f"the '5.0' manifest of chart {CHART_ID} is not PROVEN to be a test slice ("
            f"{'status ' + repr(manifest['status']) if manifest['status'] != 'candidate' else problem}) — a historical "
            f"'{TRIGGERED_BY}' run never authorises acting on an unproven candidate; {rows} output row(s) are left as they are. {unproven}")
    classes = stamped_classes(manifest["input_generation_vector"])
    cur.execute(
        """SELECT (s.input_generation_vector = p.input_generation_vector) AS same_vector, s.input_digest,
                  s.input_generation_vector AS snapshot_vector
           FROM ka_gochara_search_input_snapshot s
           JOIN kala_gochara_publication p ON p.chart_id = s.chart_id AND p.generation = s.generation
           WHERE s.chart_id = %s AND s.generation = %s""", (CHART_ID, GENERATION))
    snapshot = cur.fetchone()
    if snapshot is None:
        if rows:
            raise Refused(
                f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} but no input snapshot binds them to the "
                f"stamped manifest — their origin is unproven; {remedy}")
        return manifest, rows
    check_classes = list(classes)
    if snapshot["same_vector"] is True:
        cur.execute(
            """SELECT count(*) AS n FROM ka_gochara_search_inventory i
               JOIN ka_gochara_search_input_snapshot s ON s.chart_id = i.chart_id AND s.generation = i.generation
               JOIN kala_gochara_publication p ON p.chart_id = i.chart_id AND p.generation = i.generation
               WHERE i.chart_id = %s AND i.generation = %s
                 AND (i.input_digest <> s.input_digest OR i.horizon <> p.horizon OR NOT (i.event_class = ANY(%s::text[])))""",
            (CHART_ID, GENERATION, classes))
    else:
        problem2, source2, earlier, snapshot_runs = prove_stamp(snapshot.get("snapshot_vector"), run_manifests, require_run=True)
        if problem2:
            raise Refused(
                f"the stored input snapshot of chart {CHART_ID} '5.0' carries a DIFFERENT input vector from the stamped "
                "manifest: a later slice stamped the manifest and its snapshot substep has not yet replaced the older output "
                f"(an interrupted replacement), and the older stamp is not proved by an owned test run ({problem2}) — the output "
                f"is not provably this test's. {remedy}")
        # Codex round 5 (D3): the two stamps must be proved by DISTINCT surviving owned runs. One run cannot be both the later slice that
        # stamped the manifest and the earlier slice that built the snapshot (identical markers over a different vector component would
        # otherwise satisfy both proofs from the same run).
        if not manifest_runs or not any(a != b for a in manifest_runs for b in snapshot_runs):
            raise Refused(
                f"the stored input snapshot of chart {CHART_ID} '5.0' carries a DIFFERENT input vector from the stamped manifest, but the "
                f"two stamps are not proved by two DISTINCT surviving owned runs (manifest: {manifest_runs or 'no run'}, snapshot: "
                f"{snapshot_runs}) — one run cannot be both slices; the output is not provably this test's. {remedy}")
        notes.append(f"interrupted replacement: the stored snapshot is an EARLIER test slice's, {source2}; the current manifest "
                     "stamped by a later slice never replaced it")
        cur.execute(
            """SELECT count(*) AS n FROM ka_gochara_search_inventory i
               JOIN ka_gochara_search_input_snapshot s ON s.chart_id = i.chart_id AND s.generation = i.generation
               WHERE i.chart_id = %s AND i.generation = %s
                 AND (i.input_digest <> s.input_digest
                      OR i.horizon <> tstzrange(%s::timestamptz, %s::timestamptz) OR NOT (i.event_class = ANY(%s::text[])))""",
            (CHART_ID, GENERATION, earlier.horizon[0], earlier.horizon[1], list(earlier.classes)))
        check_classes = list(earlier.classes)
    bad = int(cur.fetchone()["n"])
    if bad:
        raise Refused(
            f"{bad} inventory header(s) of chart {CHART_ID} '5.0' do not carry the stamped identity (input "
            f"digest, horizon, or a class outside the stamp) — the output is not provably this test's; {remedy}")
    # TB1 (Stream B): the CHAIN is tied to the stamped classes too, not only the inventory headers: every window, record and event_class
    # coverage partition must be of a stamped class (the snapshot's stamp when the snapshot is an earlier slice's)
    cur.execute(
        """SELECT (SELECT count(*) FROM ka_gochara_eval_window WHERE chart_id = %s AND generation = %s
                      AND NOT (event_class = ANY(%s::text[]))) AS windows,
                  (SELECT count(*) FROM ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s
                      AND NOT (event_class = ANY(%s::text[]))) AS records,
                  (SELECT count(*) FROM kala_gochara_coverage WHERE chart_id = %s AND generation = %s
                      AND partition_kind = 'event_class' AND NOT (partition_key = ANY(%s::text[]))) AS coverage""",
        (CHART_ID, GENERATION, check_classes) * 3)
    outside = cur.fetchone()
    if any(int(outside[k]) for k in ("windows", "records", "coverage")):
        raise Refused(
            f"chain row(s) of chart {CHART_ID} '5.0' belong to a class outside the stamp {check_classes}: "
            f"{ {k: int(outside[k]) for k in ('windows', 'records', 'coverage') if int(outside[k])} } — the output is not provably "
            f"this test's; {remedy}")
    return manifest, rows


def end_state_problems(cur, triggers: tuple = (TRIGGERED_BY,)) -> list[str]:
    """The Nirmana N-137 end state for the v5 asset (definitions.ts, NIRMANA_STAGED_INERT_CANDIDATE_RULES and runtimeEvidenceSql):
    catalog_status not RETIRED, nothing depends on the asset, and NO receipt or build_run_assets row of the asset on ANY chart
    from a run that is not a 'gochara-v5-small-test' run (a receipt whose run is gone reads as non-test). Returned as named
    problems; empty means the monitor would still exclude the asset as an unsealed test candidate."""
    problems: list[str] = []
    # The default (one trigger) is the monitor's predicate, byte for byte; the century teardown passes its own trigger as well.
    trigger_sql, trigger_arg = (("b.triggered_by = %s", triggers[0]) if len(triggers) == 1
                                else ("b.triggered_by = ANY(%s::text[])", list(triggers)))
    cur.execute("SELECT catalog_status FROM asset_registry WHERE asset_id = %s", (ASSET_ID,))
    row = cur.fetchone()
    if row is None:
        problems.append(f"asset_registry row for {ASSET_ID} is missing")
    elif row["catalog_status"] == "RETIRED":
        problems.append("the registry row's catalog_status is RETIRED (rule N-137 requires it not to be)")
    cur.execute("SELECT asset_id FROM asset_registry WHERE %s = ANY(depends_on)", (ASSET_ID,))
    dependents = [r["asset_id"] for r in cur.fetchall()]
    if dependents:
        problems.append(f"asset(s) {dependents} list {ASSET_ID} in depends_on (rule N-137: nothing may depend on it)")
    cur.execute(
        """SELECT r.chart_id, count(*) AS n FROM asset_provenance_receipts r
           WHERE r.asset_id = %s
             AND NOT EXISTS (SELECT 1 FROM build_runs b WHERE b.id = r.build_id AND b.triggered_by = %s)
           GROUP BY r.chart_id""".replace("b.triggered_by = %s", trigger_sql), (ASSET_ID, trigger_arg))
    receipts = cur.fetchall()
    if receipts:
        problems.append("receipts of the asset from a non-test run (or with no run link) exist on chart(s) "
                        f"{[(str(r['chart_id']), int(r['n'])) for r in receipts]}")
    cur.execute(
        """SELECT b0.chart_id, count(*) AS n FROM build_run_assets a LEFT JOIN build_runs b0 ON b0.id = a.run_id
           WHERE a.asset_id = %s
             AND NOT EXISTS (SELECT 1 FROM build_runs b WHERE b.id = a.run_id AND b.triggered_by = %s)
           GROUP BY b0.chart_id""".replace("b.triggered_by = %s", trigger_sql), (ASSET_ID, trigger_arg))
    run_assets = cur.fetchall()
    if run_assets:
        problems.append("build_run_assets rows of the asset from a non-test run exist on chart(s) "
                        f"{[(str(r['chart_id']), int(r['n'])) for r in run_assets]}")
    return problems


# Wave 4 deletion authority is a verifier-bound request, never a trigger tag.
# (I) INTERPRETATION: receipt references are byte hashes under the executor's
# evidence directories; unreferenced checklist booleans grant no row authority.
def evidence_digest(value):
    import hashlib
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()



def lane_rehearsal_request():
    """Only the initial empty LOCAL teardown rehearsal; never execute authority.

    Production's operation_request/acceptance path is unchanged. Called before
    connecting, only from teardown(dry_run=True). No service, implicit libpq
    defaults, host override or populated scope may enter this exception.
    """
    import json
    import re
    try: req = json.loads(os.environ.get('KY_OPERATION_REQUEST', '{}'))
    except (TypeError, ValueError): return None
    if not isinstance(req, dict) or 'lane_target' not in req: return None
    target = req.get('lane_target')
    if (req.get('kind') != 'smalltest_teardown_dryrun' or req.get('dry_run') is not True
            or req.get('smalltest_scope') != {'empty': True} or req.get('chart_id') != CHART_ID
            or not isinstance(target, dict) or set(target) != {'host', 'port', 'database'}
            or target.get('host') not in ('127.0.0.1', 'localhost', '::1')
            or type(target.get('port')) is not int or target['port'] != 55433
            or not isinstance(target.get('database'), str)
            or re.fullmatch(r'ky_[a-z][a-z0-9_]{0,54}', target['database']) is None):
        raise Refused('local lane exception requires dry-run kind and an empty scope on ky_<lane>')
    from psycopg.conninfo import conninfo_to_dict
    try: settings = conninfo_to_dict(os.environ.get('DATABASE_URL', ''))
    except Exception: raise Refused('lane rehearsal connection settings invalid') from None
    expected = dict(host=target['host'], hostaddr='::1' if target['host'] == '::1' else '127.0.0.1',
                    port='55433', dbname=target['database'], user='postgres', password='',
                    passfile=os.devnull, options='', sslmode='disable', connect_timeout='10')
    if settings != expected or any(key.startswith('PG') and key != 'PGPASSFILE' for key in os.environ):
        raise Refused('lane rehearsal connection must be explicit and match the local target')
    return req


def operation_request():
    import json
    try:
        req = json.loads(os.environ['KY_OPERATION_REQUEST'])
    except (KeyError, TypeError, ValueError):
        raise Refused('executor-bound small-test request required') from None
    if not isinstance(req, dict):
        raise Refused('executor-bound small-test request required')
    if not str(req.get('kind', '')).endswith('_dryrun'):    # A8 §3.8: a dry run is read-only with a credential; no V acceptance exists
        acceptance(req, evidence_root())                    # A8 §3.9: a writing kind carries exactly one V acceptance, bound to the request
    return req


def evidence_root():
    from pathlib import Path
    try:
        return Path(os.environ['KY_ROOT']) / 'run/ops'
    except KeyError:
        raise Refused('executor evidence root required') from None


def request_hash(req):
    """executor.request_digest, byte for byte (A8 §3.9): without `acceptance_receipt`, `expires_at` and any `*_expires_at` field."""
    return evidence_digest({k: v for k, v in req.items() if k not in ('acceptance_receipt', 'expires_at') and not k.endswith('_expires_at')})


def read_evidence(root, folder, ref):
    import hashlib
    import json
    import re
    from pathlib import Path
    if not isinstance(ref, dict) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.json', str(ref.get('name', ''))):
        raise Refused('named evidence reference required')
    path = root / folder / ref['name']
    try:
        if path.resolve().parent != (root / folder).resolve():
            raise Refused('evidence reference escapes its directory')
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != ref.get('sha256'):
            raise Refused('evidence byte digest mismatch')
        result = json.loads(body)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except (OSError, ValueError, TypeError):
        raise Refused('referenced evidence unreadable') from None


def independent_acceptance(a):
    """A verifier lane's (v1..v4) acceptance, or the executor's own MECHANICAL pre-acceptance (OWNER-MINIMAL-PROTECTION-NOW): schema
    ky.mechanical_acceptance/1, phase pre, and every check recorded true. executor.mechanical_pre_acceptance writes it only for a request that equals a
    verified pack fill with a completed dry run and a live lease; deletions and serving changes never get one."""
    if a.get('by') in ('v1', 'v2', 'v3', 'v4'):
        return True
    checks = a.get('checks')
    return (a.get('by') == 'executor-mechanical' and a.get('schema') == 'ky.mechanical_acceptance/1' and a.get('phase') == 'pre'
            and isinstance(checks, dict) and bool(checks) and all(v is True for v in checks.values()))


def acceptance(req, root):
    import json
    from pathlib import Path
    try:
        # a mechanically accepted request names no acceptance_receipt: its record is acceptance/<operation_id>.json (and only a pack-fill request may omit one)
        path = Path(req['acceptance_receipt']) if req.get('acceptance_receipt') or not req.get('pack_fill') else root / 'acceptance' / (str(req['operation_id']) + '.json')
        if path.resolve().parent != (root / 'acceptance').resolve():
            raise Refused('request acceptance outside executor directory')
        a = json.loads(path.read_text())
        if (a.get('result') != 'ACCEPTED' or not independent_acceptance(a)
                or a.get('operation_id') != req.get('operation_id')
                or not req.get('reviewed_commit') or a.get('reviewed_commit') != req['reviewed_commit']
                or a.get('request_sha256') != request_hash(req) or req.get('chart_id') != CHART_ID):
            raise Refused('request is not bound to independent verifier acceptance')
        return a
    except (OSError, KeyError, ValueError, TypeError):
        raise Refused('request acceptance unreadable') from None


def accepted_receipt(root, receipt_ref, acceptance_ref, kind):
    r = read_evidence(root, 'receipts', receipt_ref)
    a = read_evidence(root, 'acceptance', acceptance_ref)
    if (r.get('kind') != kind or r.get('status') not in ('COMPLETED', 'AWAITING_ABSENCE') or r.get('exit_code') != 0
            or not r.get('request_sha256') or not r.get('reviewed_commit')
            or a.get('result') != 'ACCEPTED' or not independent_acceptance(a)
            or a.get('operation_id') != r.get('operation_id')
            or a.get('request_sha256') != r['request_sha256'] or a.get('reviewed_commit') != r['reviewed_commit']):
        raise Refused('operation receipt is not independently accepted for this request')
    return r, a


def completed_receipt(root, receipt_ref, kind):
    """The executor receipt of a `*_dryrun` kind (A8 §3.8): COMPLETED, exit 0, bound to a request and a reviewed commit.

    A dry run is read-only with a credential, so no V lane accepts it; its receipt is the whole evidence."""
    r = read_evidence(root, 'receipts', receipt_ref)
    if (r.get('kind') != kind or r.get('status') != 'COMPLETED' or r.get('exit_code') != 0
            or not r.get('request_sha256') or not r.get('reviewed_commit')):
        raise Refused('dry-run operation receipt is not a completed receipt for this kind')
    return r


def staged_scope(req, root):
    import re
    import uuid
    measuring = req.get('kind') in ('measuring_teardown', 'measuring_teardown_dryrun')
    century = req.get('kind') in ('century_teardown', 'century_teardown_dryrun')
    if measuring and req.get('item_id') != 'J-3d':
        raise Refused('measuring teardown belongs to J-3d')
    if century and req.get('item_id') != CENTURY_ITEM:
        raise Refused('century teardown belongs to ' + CENTURY_ITEM)
    scope = req.get('century_scope' if century else 'measuring_scope' if measuring else 'smalltest_scope')
    if not isinstance(scope, dict):
        raise Refused('identified staged small-test scope required')
    if scope.get('empty') is True:
        if req.get('kind') != 'smalltest_teardown_dryrun' or scope != {'empty': True}:
            raise Refused('empty scope is for the initial teardown rehearsal only')
        return scope
    r, a = accepted_receipt(root, scope.get('dispatch_receipt'), scope.get('dispatch_acceptance'),
                            'century_dispatch' if century else 'measuring_dispatch' if measuring else 'smalltest_dispatch')
    launch = r.get('launch') or {}
    try:
        valid_uuid = str(uuid.UUID(str(scope.get('run_id')))) == scope.get('run_id')
    except ValueError:
        valid_uuid = False
    if (not valid_uuid or r.get('item_id') not in ((CENTURY_ITEM,) if century else ('J-3c',) if measuring else ('J-2a', 'J-2c')) or r.get('status') != 'COMPLETED'
            or launch.get('status') != 'LAUNCHED' or launch.get('run_id') != scope.get('run_id')
            or launch.get('chart_id') != CHART_ID or launch.get('asset_id') != ASSET_ID
            or scope.get('chart_id') != CHART_ID or scope.get('generation') != GENERATION
            or scope.get('asset_id') != ASSET_ID or launch.get('plan_manifest_digest') != scope.get('plan_manifest_digest')
            or not re.fullmatch(r'[0-9a-f]{64}', str(scope.get('plan_manifest_digest', '')))
            or not re.fullmatch(r'brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*', str(launch.get('execution_name', '')))
            or not ((scope.get('manifest_id') is None and scope.get('input_vector_sha256') is None)
                    or (scope.get('manifest_id') and re.fullmatch(r'[0-9a-f]{64}', str(scope.get('input_vector_sha256', '')))))):
        raise Refused('scope differs from the accepted staged launch/manifest identity')
    if (measuring or century) and (launch.get('schema') != ('ky.century_launch/1' if century else 'ky.measuring_launch/1')
            or not re.fullmatch(r'[0-9a-f]{64}', str(scope.get('input_vector_sha256', '')))
            or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', str(scope.get('manifest_id', '')))):
        raise Refused(('century' if century else 'measuring') + ' scope requires its actual launch, candidate manifest and input vector')
    resumed_runs_problem(scope, root, century)
    return scope


RESUMED_RUN_KEYS = ('run_id', 'plan_manifest_digest', 'resume_receipt', 'resume_acceptance')


def resumed_runs_problem(scope, root, century):
    """SR-RESUME-NOW teardown scope: a century build that was RESUMED left one more build_runs row per resume (each a new run over the same generation '5.0' chain),
    and the century teardown deletes exactly the runs its scope names. `scope['resumed_runs']` (optional; century only) names them, each bound to the accepted
    `century_resume` launch receipt that started it (same run id, same plan manifest digest, an actual execution of the century job). Without it a resumed
    build's extra runs refuse the teardown by name (`only the identified staged run ... may be deleted`) and the chart could never be cleared for a fresh dispatch.
    Raises Refused; returns None. A scope that carries no `resumed_runs` is judged exactly as before."""
    import re
    import uuid
    if 'resumed_runs' not in scope:
        return None
    if not century:
        raise Refused('resumed_runs belong to the century teardown scope only')
    entries = scope['resumed_runs']
    if not isinstance(entries, list) or not entries:
        raise Refused('resumed_runs must be a non-empty list of the resumed runs')
    seen = {scope.get('run_id')}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != set(RESUMED_RUN_KEYS):
            raise Refused('a resumed run names exactly ' + ', '.join(RESUMED_RUN_KEYS))
        try:
            canonical = str(uuid.UUID(str(entry['run_id']))) == entry['run_id']
        except ValueError:
            canonical = False
        if not canonical or entry['run_id'] in seen:
            raise Refused('a resumed run id must be a canonical UUID, distinct from every other run of the scope')
        seen.add(entry['run_id'])
        r, _ = accepted_receipt(root, entry['resume_receipt'], entry['resume_acceptance'], 'century_resume')
        launch = r.get('launch') or {}
        if (r.get('status') != 'COMPLETED' or r.get('item_id') != CENTURY_ITEM or launch.get('status') != 'LAUNCHED'
                or launch.get('schema') != 'ky.century_launch/1' or launch.get('run_id') != entry['run_id']
                or launch.get('chart_id') != CHART_ID or launch.get('asset_id') != ASSET_ID
                or not re.fullmatch(r'[0-9a-f]{64}', str(entry['plan_manifest_digest']))
                or launch.get('plan_manifest_digest') != entry['plan_manifest_digest']
                or not re.fullmatch(r'brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*', str(launch.get('execution_name', '')))):
            raise Refused('a resumed run differs from the accepted century_resume launch that started it')


def dryrun_evidence(req, root, scope, rowset_sha256=None):
    family = 'century' if req.get('kind') == 'century_teardown' else 'measuring' if req.get('kind') == 'measuring_teardown' else 'smalltest'
    r = completed_receipt(root, req.get('dryrun_receipt'), family + '_teardown_dryrun')
    p = r.get('teardown') or {}
    if (r.get('reviewed_commit') != req.get('reviewed_commit') or r.get('status') != 'COMPLETED' or p.get('schema') != f'ky.{family}_teardown/1'
            or p.get('status') != 'ROLLED_BACK' or p.get('rollback_confirmed') is not True
            or p.get('scope') != scope or p.get('scope_sha256') != evidence_digest(scope)
            or p.get('request_sha256') != r.get('request_sha256') or p.get('operation_id') != r.get('operation_id')
            or not p.get('rowset_sha256') or (rowset_sha256 is not None and p['rowset_sha256'] != rowset_sha256)):
        raise Refused('successful rollback-confirmed dry run for the same scope and row set required')
    from datetime import datetime
    try:
        if datetime.fromisoformat(r['ts']) >= datetime.fromisoformat(acceptance(req, root)['ts']):
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise Refused('successful dry-run receipt must precede this accepted teardown request') from None
    return p


# Every launch / committed-teardown kind a lifecycle can contain: an absence proof is only ever bound to the LATEST of them.
DISPATCH_KINDS = ('smalltest_dispatch', 'measuring_dispatch', 'century_dispatch', 'century_resume')   # SR-RESUME-NOW: a resume's launch is a launch of the lifecycle, so a later dispatch needs its own teardown and absence after it too
TEARDOWN_KINDS = ('smalltest_teardown', 'measuring_teardown', 'century_teardown')


def absence_evidence(req, root, *, teardown_receipt=None):
    """Separate verifier-accepted readback, bound to the committed teardown.

    The first dispatch instead consumes a baseline readback with run_id=null.
    Readback output is JSON emitted by SELECT; the executor retains full bytes.
    """
    r, a = accepted_receipt(root, req.get('absence_receipt'), req.get('absence_acceptance'), 'readback_sql')
    p = a.get('absence') or {}
    import hashlib
    if r.get('status') != 'COMPLETED' or not r.get('output_file'):
        raise Refused('independent absence readback output required')
    from pathlib import Path
    path = Path(r['output_file'])
    try:
        if path.resolve().parent != (root / 'receipts').resolve():
            raise Refused('absence output escapes evidence directory')
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != r.get('output_sha256'):
            raise Refused('absence output digest mismatch')
    except OSError:
        raise Refused('absence readback output unreadable') from None
    import csv
    import io
    import json
    try:
        records = list(csv.DictReader(io.StringIO(body.decode()), delimiter="\t"))
        measured = json.loads(records[0]["absence_proof"]) if len(records) == 1 else None
    except (ValueError, KeyError, UnicodeError):
        raise Refused("readback must emit one JSON absence_proof column") from None
    if measured != {k: v for k, v in p.items() if k != "output_sha256"}:
        raise Refused("accepted absence differs from the measured readback output")
    # Acceptance binds the measured readback output, the exact deleted scope,
    # and commit receipt. It is never inferred from exit zero or N-137 alone.
    if (p.get('schema') != 'ky.smalltest_independent_absence/1' or p.get('chart_id') != CHART_ID
            or p.get('generation') != GENERATION or p.get('registry_inert') is not True or p.get('output_sha256') != r['output_sha256']
            or not isinstance(p.get('counts'), dict) or not p['counts']
            or any(type(n) is not int or n != 0 for n in p['counts'].values())):
        raise Refused('measured, scope-bound independent absence required')
    required = {t for t, _ in ABSENCE_TABLES} | {'kala_gochara_publication', 'build_runs', 'build_run_assets',
                'asset_provenance_receipts', 'asset_freshness', 'asset_throughput',
                'ka_gochara_eval_window_record', 'ka_gochara_record_prerequisite',
                'ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification', 'owned_test_runs'}
    if not required <= p['counts'].keys():
        raise Refused('independent absence census is incomplete')
    if teardown_receipt is not None:
        committed = teardown_receipt
    elif req.get('prior_teardown_receipt'):
        committed = read_evidence(root, 'receipts', req['prior_teardown_receipt'])
    else:
        committed = None
    if committed is None:
        if p.get('run_id') is not None or p.get('baseline') is not True:
            raise Refused('first dispatch requires an explicit empty baseline readback')
        # Baseline cannot be replayed over an earlier committed teardown.
        import json
        for path in (root / 'receipts').glob('*.json'):
            try:
                old = json.loads(path.read_text())
            except (OSError, ValueError):
                raise Refused('prior operation evidence unreadable') from None
            if ((old.get('kind') in TEARDOWN_KINDS and (old.get('teardown') or {}).get('status') == 'COMMITTED_AWAITING_ABSENCE')
                    or (old.get('kind') in DISPATCH_KINDS and old.get('status') == 'COMPLETED' and old.get('launch'))):
                raise Refused('prior teardown requires its own independent absence')
    else:
        proof = committed.get('teardown') or {}
        if (committed.get('kind') not in TEARDOWN_KINDS
                or proof.get('schema') != 'ky.' + str(committed.get('kind')) + '/1'
                or committed.get('exit_code') != 0
                or committed.get('status') not in ('AWAITING_ABSENCE', 'COMPLETED')
                or proof.get('status') != 'COMMITTED_AWAITING_ABSENCE'
                or p.get('run_id') != (proof.get('scope') or {}).get('run_id')
                or p.get('scope_sha256') != proof.get('scope_sha256')
                or p.get('rowset_sha256') != proof.get('rowset_sha256')
                or p.get('teardown_request_sha256') != committed.get('request_sha256')
                or p.get('teardown_operation_id') != committed.get('operation_id')
                or p.get('teardown_receipt_sha256') != evidence_digest(committed)
                or r.get('operation_id') == committed.get('operation_id')):
            raise Refused('independent absence is not bound to this committed teardown')
        # A later completed launch cannot be bypassed using an older run's
        # valid absence proof. Bind dispatch admission to the latest lifecycle.
        import json
        from datetime import datetime
        for path in (root / 'receipts').glob('*.json'):
            try:
                old = json.loads(path.read_text())
                if (old.get('kind') in DISPATCH_KINDS and old.get('status') == 'COMPLETED'
                        and old.get('launch') and datetime.fromisoformat(old['ts']) > datetime.fromisoformat(committed['ts'])):
                    raise Refused('a later staged launch requires its own teardown and independent absence')
            except (OSError, ValueError, KeyError, TypeError):
                raise Refused('prior launch evidence unreadable') from None
        try:
            if datetime.fromisoformat(r['ts']) <= datetime.fromisoformat(committed['ts']):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise Refused('independent readback must follow the committed teardown') from None
    return p


# J-2a SCOPED backup (backup_v5_small_test_job.py --scope small_test; spec fleet/J2A_SCOPED_BACKUP_v1_0.md).
# The digest is the reviewed scope file's (backup_v5_small_test_scope.json) and is pinned HERE because the executor
# loads this module alone, from the reviewed commit; a test ties the pin to the file.
# SR-BACKUP-VALIDITY-A8 (A8 §3): a scoped backup stays a valid pre-test record exactly while the content digest of its
# scoped relations is unchanged: the digest recorded at capture equals a fresh read-only measurement of the same
# relations, and its restore proof is verified. There is no clock. SCOPED_BACKUP_VALIDITY_S is now the window of the
# FULL-form (/1) proof only (full_backup_window_problem); an old scoped capture's `validity.not_after` stays readable
# and is never a gate.
SCOPED_BACKUP_SCOPE_SHA256 = "1daf69d6e31279592947aa25e2b4f9a5c1c8137d6663ba039c27e7331ac7335a"
# W3W4 pack verify E3: the other reviewed scopes (backup_v5_century_scope.json, backup_v5_verification_seal_scope.json; M-W56-6: backup_v5_w5w6_union_scope.json), pinned the same way and for the same reason.
# A dispatch names ITS scope (scoped_backup_problem(scope=...)); a proof of another scope never admits it (the digest covers the scope's name as well as its tables).
SCOPED_BACKUP_SCOPE_SHA256S = {"small_test": SCOPED_BACKUP_SCOPE_SHA256,
                               "century": "eab44eef1ceb06604cab21fbcc464334a9253af1f320ca322b797cf3ff32b020",
                               "verification_seal": "d20d37b36dad2c7707379415a3981dc434caf85bf952f2bb43546fe392fca7ad",
                               "w5w6_union": "28f093154c6044fbffed64ef718caac3456d8b829932f70dbc6c36c5a065f6da"}
SCOPED_BACKUP_VALIDITY_S = 4 * 3600
SCOPED_MEASUREMENT_METHOD = 'sql_sum_sha256_rowjson/1'


def scoped_content_digest(measurements):
    """THE scoped-content digest: SHA-256 over the canonical JSON of a scoped measurement (per-table row count and
    content hash, per-sequence state) and the method that produced it. The capture records it from its snapshot
    measurement, the dispatch check compares it to a fresh measurement of the same relations: one implementation, so
    the two can never be computed differently. Raises ValueError for anything that is not a measurement."""
    import hashlib
    import json
    if (not isinstance(measurements, dict) or set(measurements) != {'tables', 'sequences'}
            or not isinstance(measurements['tables'], dict) or not measurements['tables']
            or not isinstance(measurements['sequences'], dict)):
        raise ValueError('not a scoped measurement')
    body = json.dumps({'method': SCOPED_MEASUREMENT_METHOD, 'tables': measurements['tables'],
                       'sequences': measurements['sequences']}, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(body.encode()).hexdigest()


def full_backup_window_problem(proof, label, folder, root, now=None):
    """A full-form (/1) proof names its backup only with the same freshness bound as a scoped one."""
    from datetime import datetime, timedelta, timezone
    if (proof.get('status') != 'verified' or proof.get('label') != label or proof.get('restore_verified') is not True
            or proof.get('backup_taken') is not True or proof.get('target_removed') is not True):
        raise Refused('full backup restore proof is not a verified proof for this label')
    capture = read_evidence(root, folder, {'name': 'capture.json', 'sha256': proof.get('capture_sha256')})
    if (capture.get('schema') != 'ky.smalltest_backup/1' or capture.get('label') != label
            or capture.get('archive_sha256') != proof.get('archive_sha256')):
        raise Refused('full backup restore proof does not match its capture')
    try:
        start = datetime.fromisoformat(capture['ts'])
        taken = datetime.fromisoformat(proof['ts'])
        if start.tzinfo is None or taken.tzinfo is None:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise Refused('full backup has no timestamp inside a validity window') from None
    instant = now or datetime.now(timezone.utc)
    if not start <= taken <= instant <= start + timedelta(seconds=SCOPED_BACKUP_VALIDITY_S):
        raise Refused('backup is outside its validity window; a fresh backup and restore proof are required')


def scoped_backup_problem(req, root, now=None, measure=None, scope='small_test'):
    """A `smalltest_dispatch` (or, with `scope=`, a `century_dispatch`) MUST name its backup (`backup_label` + the restore proof's `backup_restore_sha256`), and
    that backup must still describe the database (SR-BACKUP-VALIDITY-A8): its restore proof is a verified proof of the
    pinned scope, bound to its capture, and the scoped-content digest recorded at capture equals the digest of a fresh
    measurement of the same relations. A scoped proof (schema /2) is checked that way; a full proof (schema /1) is
    accepted only with its 4 h window, measured from its capture receipt's `ts`. Raises Refused.

    `measure(tables, sequences) -> {'tables': ..., 'sequences': ...}` is a read-only measurement of those relations as
    the capture measured them (backup_v5_small_test_job.measure_scope_now). Without it (the executor's admission,
    which has no database) every recorded-evidence check still runs and the fresh comparison is left to the dispatch
    script, which re-runs this policy with a measure at `--execute`. A measure that fails refuses; it never admits.

    (I) INTERPRETATION J2A-S2: no label, no restore-proof digest, or a /1 proof without a readable timestamp is
    refused, never silently allowed. (I) INTERPRETATION J2A-S4: the /1 capture has no snapshot instant, so its window
    starts at the capture receipt's `ts`, written after the dump; alternative: refuse every /1 proof."""
    label = req.get('backup_label')
    if label is None or req.get('backup_restore_sha256') is None:
        raise Refused('a dispatch must name its backup_label and backup_restore_sha256; run a fresh backup and restore proof')
    import re
    from datetime import datetime, timezone
    if not isinstance(label, str) or not re.fullmatch(r'[a-z][a-z0-9_]{2,39}', label):
        raise Refused('backup label malformed')
    folder = 'backups/' + label
    proof = read_evidence(root, folder, {'name': 'restore.json', 'sha256': req.get('backup_restore_sha256')})
    if proof.get('schema') == 'ky.smalltest_restore/1':
        return full_backup_window_problem(proof, label, folder, root, now)
    if (proof.get('schema') != 'ky.smalltest_restore/2' or proof.get('status') != 'verified' or proof.get('label') != label
            or proof.get('scoped') is not True or proof.get('restore_verified') is not True
            or proof.get('backup_taken') is not True or proof.get('target_removed') is not True):
        raise Refused('scoped backup restore proof is not a verified proof for this label')
    expected_scope = SCOPED_BACKUP_SCOPE_SHA256S[scope]
    if proof.get('scope_sha256') != expected_scope:
        raise Refused('scoped backup covers a scope other than the reviewed one')
    capture = read_evidence(root, folder, {'name': 'capture.json', 'sha256': proof.get('capture_sha256')})
    captured_scope = capture.get('scope') or {}
    window = capture.get('validity') or {}
    try:
        start = datetime.fromisoformat(window['not_before'])
        taken = datetime.fromisoformat(proof['ts'])
        if start.tzinfo is None or taken.tzinfo is None:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise Refused('scoped backup capture instant missing or malformed') from None
    if (capture.get('schema') != 'ky.smalltest_backup/2' or capture.get('label') != label
            or captured_scope.get('sha256') != expected_scope or capture.get('archive_sha256') != proof.get('archive_sha256')
            or proof.get('validity') != window):
        raise Refused('scoped backup restore proof does not match its capture')
    instant = now or datetime.now(timezone.utc)
    if not start <= taken <= instant:
        raise Refused('scoped backup restore proof predates its capture or lies in the future')
    # the content the backup describes: recorded at capture, re-proven by the restore, compared with the database now
    try:
        recorded = scoped_content_digest(capture.get('measurements'))
        restored = scoped_content_digest(proof.get('measurements'))
    except ValueError:
        raise Refused('scoped backup records no scoped content measurements') from None
    if capture.get('measurement_method') != SCOPED_MEASUREMENT_METHOD:
        raise Refused('scoped backup measurement method differs')
    if 'scoped_content_digest' in capture and capture['scoped_content_digest'] != recorded:
        raise Refused('scoped backup digest differs from its recorded measurements')
    if restored != recorded:
        raise Refused('scoped backup restore proof measured content other than the capture recorded')
    if measure is not None:
        try:
            fresh = scoped_content_digest(measure(sorted(capture['measurements']['tables']),
                                                  sorted(capture['measurements']['sequences'])))
        except Exception:
            raise Refused('scoped content could not be measured now; the backup is not shown to be valid') from None
        if fresh != recorded:
            raise Refused('scoped content has changed since the backup was captured; a fresh backup and restore proof are required')


def smalltest_request_problem(req, root, measure=None):
    """File evidence admission; used from the reviewed source by executor (no `measure`: no database) and by the
    dispatch script at `--execute` (with `measure`, see scoped_backup_problem)."""
    try:
        kind = req.get('kind')
        if kind in ('smalltest_dispatch', 'smalltest_dispatch_dryrun'):
            args = req.get('args') or {}
            if args.get('run') not in ('all_classes_1y', 'one_class_full'):
                raise Refused('measuring phase is disabled for the small-test operation')
            if args.get('run') == 'all_classes_1y' and args.get('classes', 'all') != 'all':
                raise Refused('first small test requires all scored classes')
            if args.get('run') == 'one_class_full' and args.get('classes') != 'marriage':
                raise Refused('conditional small test is limited to marriage')
            if args.get('run') == 'all_classes_1y':
                from datetime import datetime, timedelta
                try:
                    start = datetime.fromisoformat(args['horizon-start'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(args['horizon-end'].replace('Z', '+00:00'))
                    if start.tzinfo is None or end.tzinfo is None or not timedelta(0) < end - start <= timedelta(days=366):
                        raise ValueError()
                except (KeyError, ValueError, TypeError):
                    raise Refused('annual small test requires timezone-qualified bounds of at most 366 days') from None
            if kind == 'smalltest_dispatch':
                absence_evidence(req, root)
                scoped_backup_problem(req, root, measure=measure)
        elif kind in ('smalltest_teardown', 'smalltest_teardown_dryrun'):
            scope = staged_scope(req, root)
            if kind == 'smalltest_teardown':
                dryrun_evidence(req, root, scope)
        return None
    except (Refused, KeyError, TypeError, ValueError) as exc:
        return str(exc) if isinstance(exc, Refused) else 'malformed small-test evidence'


def absence_readback_sql(committed=None):
    """One independent SELECT for readback_sql; no DB connection or mutation.

    The cockpit stages this returned text under run/ops/sql, submits readback_sql,
    then V accepts its measured absence_proof plus the output byte digest.
    """
    import json
    def literal(value):
        return "'" + json.dumps(value, sort_keys=True, separators=(',', ':')).replace("'", "''") + "'::jsonb"
    # Only constants built here enter SQL, with JSON and SQL quoting. UUID/SQL
    # injection through a receipt is impossible, even before receipt validation.
    scope = (committed.get('teardown') or {}).get('scope') if committed else None
    proof = dict(schema='ky.smalltest_independent_absence/1', chart_id=CHART_ID, generation=GENERATION,
                 run_id=scope['run_id'] if scope else None, baseline=not bool(committed))
    if committed:
        t = committed['teardown']
        proof.update(scope_sha256=t['scope_sha256'], rowset_sha256=t['rowset_sha256'],
                     teardown_request_sha256=committed['request_sha256'], teardown_operation_id=committed['operation_id'],
                     teardown_receipt_sha256=evidence_digest(committed))
    chart = "'" + CHART_ID + "'::uuid"
    gen = "'" + GENERATION + "'"
    asset = "'" + ASSET_ID + "'"
    run = "(" + literal(proof['run_id']) + " #>> '{}')::uuid" if scope else None
    # a century teardown's census counts the century trigger; every other lifecycle keeps the small-test one, byte for byte
    trigger = CENTURY_TRIGGERED_BY if committed and committed.get('kind') == 'century_teardown' else TRIGGERED_BY
    run_where = f"id = {run}" if run else f"chart_id = {chart} AND triggered_by = '{trigger}'"
    queries = {t: f"SELECT count(*) FROM {t} WHERE chart_id = {chart} AND generation = {gen}{extra}"
               for t, extra in ABSENCE_TABLES + (("kala_gochara_publication", ""),)}
    for t in ('ka_gochara_eval_window_record', 'ka_gochara_record_prerequisite',
              'ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification'):
        queries[t] = f"SELECT count(*) FROM {t} WHERE chart_id = {chart} AND generation = {gen}"
    for t in ('asset_provenance_receipts', 'asset_freshness', 'asset_throughput'):
        queries[t] = f"SELECT count(*) FROM {t} WHERE chart_id = {chart} AND asset_id = {asset}"
    queries['build_runs'] = f"SELECT count(*) FROM build_runs WHERE {run_where}"
    queries['build_run_assets'] = (f"SELECT count(*) FROM build_run_assets WHERE run_id = {run}" if run else
                                  f"SELECT count(*) FROM build_run_assets WHERE asset_id = {asset}")
    queries['owned_test_runs'] = f"SELECT count(*) FROM build_runs WHERE chart_id = {chart} AND triggered_by = '{trigger}'"
    counts = ', '.join("'" + table + "', (" + sql + ")" for table, sql in sorted(queries.items()))
    return ("SELECT (" + literal(proof) + " || jsonb_build_object('counts', jsonb_build_object(" + counts + "), "
            "'registry_inert', (SELECT is_active IS FALSE FROM asset_registry WHERE asset_id = " + asset + ")))::text AS absence_proof")


def measuring_request_problem(req, root):
    """Measuring-only file evidence admission, loaded from reviewed source."""
    try:
        kind = req.get('kind')
        if kind in ('measuring_dispatch', 'measuring_dispatch_dryrun'):
            if req.get('item_id') != 'J-3c':
                raise Refused('measuring dispatch belongs to J-3c')
            args = req.get('args') or {}
            if args != {'run': 'all_classes_full', 'classes': 'all'}:
                raise Refused('measuring request requires only all_classes_full and all classes')
            # Even a staging rollback may not bypass the previous lifecycle.
            absence_evidence(req, root)
            if kind == 'measuring_dispatch':
                measuring_dryrun_evidence(req, root)
        elif kind in ('measuring_teardown', 'measuring_teardown_dryrun'):
            scope = staged_scope(req, root)
            if kind == 'measuring_teardown':
                dryrun_evidence(req, root, scope)
        else:
            raise Refused('unknown measuring operation kind')
        return None
    except (Refused, KeyError, TypeError, ValueError) as exc:
        return str(exc) if isinstance(exc, Refused) else 'malformed measuring evidence'


def measuring_dryrun_evidence(req, root, manifest_digest=None):
    """A real completed staging rollback, same source/args/manifest, before launch (no V acceptance of a dry run, A8 §3.8)."""
    r = completed_receipt(root, req.get('dryrun_receipt'), 'measuring_dispatch_dryrun')
    p = r.get('staging') or {}
    if (r.get('status') != 'COMPLETED' or r.get('item_id') != 'J-3c' or r.get('reviewed_commit') != req.get('reviewed_commit')
            or p.get('schema') != 'ky.measuring_staging/1' or p.get('status') != 'ROLLED_BACK'
            or p.get('rollback_confirmed') is not True or p.get('args') != req.get('args')
            or p.get('operation_id') != r.get('operation_id') or p.get('request_sha256') != r.get('request_sha256')
            or p.get('plan_manifest_digest') != evidence_digest(p.get('plan_manifest'))
            or (manifest_digest is not None and p.get('plan_manifest_digest') != manifest_digest)):
        raise Refused('accepted measuring staging rollback for the same source, args and manifest required')
    from datetime import datetime
    try:
        if datetime.fromisoformat(r['ts']) >= datetime.fromisoformat(acceptance(req, root)['ts']):
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise Refused('measuring staging rollback must precede the accepted launch request') from None
    return p


# ───────────────────────────── the century (final, ordinary candidate) build ─────────────────────────────
# SR-PREBUILD-ALL: the century launch is the measuring launch minus the test slice. Same gates (accepted request, live lease, scoped backup,
# a rollback-confirmed staging dry run before the real staging, one durable launch claim, a previous lifecycle independently absent), but
# the staged run carries NO slice marker and its own trigger, so the candidate it builds is an ordinary, sealable one.
# F-CHANNEL (SR-W34-PREP-RULINGS 1): the century request also carries the three values the production orchestrator cannot (its writer config is chart_id and
# birth_params only): the final-rule profile, the verify-deferral switch and the D-G9 horizon. They ride in the request `args` — so the request digest the
# acceptance and the pack fill bind covers them — and are STAGED in plan_manifest[CENTURY_CONFIG_KEY], which plan_manifest_digest covers. All four are required:
# a century request that omitted one would stage a run the writer refuses at its first substep.
# OD-1 (SR-OD1-NUMERICAL): a fifth required value, `result_policy`, names the numeric-result policy the century build is bound under (the writer's century config /2 carries
# it; a final-rules run without it is refused by name). Executor-side admission holds its OWN literal of the two named policies (a test pins it equal to the writer's).
CENTURY_ARG_KEYS = ('classes', 'final_rules', 'defer_in_build_verify', 'horizon', 'result_policy')
CENTURY_RESULT_POLICIES = ('all_null_candidate/1', 'window_qualification/1')
CENTURY_CONFIG_KEY = 'gochara_v5_century_config'      # the writer's CENTURY_CONFIG_KEY (a test pins the two equal)
CENTURY_EXECUTION_ENV = 'PUBSUB_DISABLED=1'      # J-3 gate: Pub/Sub on would publish asset.substep and print nothing the log read could see


def parse_century_horizon(raw):
    """The two derived horizon bounds of a century request: 'start,end', each a tz-aware ISO timestamp, start before end — else Refused by name.
    Returns the pair of strings as given (the writer's `validate_century_config` canonicalises them to UTC and bounds them to the substrate domain)."""
    from datetime import datetime
    parts = raw.split(',') if isinstance(raw, str) else None
    if parts is None or len(parts) != 2:
        raise Refused("century horizon must be exactly two tz-aware ISO timestamps 'start,end'")
    try:
        start, end = (datetime.fromisoformat(part) for part in parts)
    except ValueError:
        raise Refused('century horizon bounds must be ISO 8601 timestamps') from None
    if start.tzinfo is None or end.tzinfo is None:
        raise Refused('century horizon bounds must carry a timezone; an unstated zone is never guessed')
    if not start < end:
        raise Refused('century horizon is empty or inverted')
    return parts[0], parts[1]


def century_args_problem(args):
    """The century request's exact argument contract (executor-side admission; the writer's own validator runs at the staging rollback that must precede
    the real launch). Raises Refused; returns None when `args` is exactly classes=all, final_rules and defer_in_build_verify as 'true'/'false', a horizon and one of the two named result policies."""
    if not isinstance(args, dict) or set(args) != set(CENTURY_ARG_KEYS):
        raise Refused('century request requires exactly ' + ', '.join(CENTURY_ARG_KEYS))
    if args['classes'] != 'all':
        raise Refused('century request requires only all classes')
    for key in ('final_rules', 'defer_in_build_verify'):
        if args[key] not in ('true', 'false'):
            raise Refused(f"century {key} must be the string 'true' or 'false'")
    if args['defer_in_build_verify'] == 'true' and args['final_rules'] != 'true':
        raise Refused('century defer_in_build_verify needs final_rules')
    if args['result_policy'] not in CENTURY_RESULT_POLICIES:
        raise Refused('century result_policy must be one of ' + ', '.join(CENTURY_RESULT_POLICIES))
    parse_century_horizon(args['horizon'])


def century_config_component(final_rules, defer_in_build_verify, horizon, result_policy):
    """The plan_manifest component for the four values, validated and canonicalised by the WRITER's own validator (the single implementation of what the
    writer will accept). Arguments are the request strings ('true'/'false', 'start,end')."""
    module = writer()
    bounds = parse_century_horizon(horizon)
    for name, value in (('final_rules', final_rules), ('defer_in_build_verify', defer_in_build_verify)):
        if value not in ('true', 'false'):
            raise Refused(f"century {name} must be the string 'true' or 'false'")
    try:
        return module.validate_century_config({'schema': module.CENTURY_CONFIG_SCHEMA, 'final_rules': final_rules == 'true',
                                               'defer_in_build_verify': defer_in_build_verify == 'true', 'horizon': list(bounds),
                                               'result_policy': result_policy})
    except Exception as exc:    # the writer's CenturyConfigRefusal or the horizon module's named domain refusals
        raise Refused(str(exc)) from None


def century_request_problem(req, root, measure=None):
    """Century-only file evidence admission, loaded from reviewed source (the executor loads this module alone, from the reviewed commit).
    `measure()` is the dispatch script's fresh read-only measurement of the reviewed century scope's relations (the executor's admission has none and
    passes nothing). SR-A12-BACKUP-REMOVAL removed the scoped-backup freshness check it used to feed (SR-BACKUP-VALIDITY-A8 §3.10) but NOT the exact-scope
    measurability: a scoped relation that cannot be found or read now still refuses (never admits) a `century_dispatch`."""
    try:
        kind = req.get('kind')
        if kind in ('century_dispatch', 'century_dispatch_dryrun'):
            if req.get('item_id') != CENTURY_ITEM:
                raise Refused('century dispatch belongs to ' + CENTURY_ITEM)
            century_args_problem(req.get('args') or {})
            # Even a staging rollback may not bypass the previous lifecycle: generation '5.0' must be independently absent.
            absence_evidence(req, root)
            if kind == 'century_dispatch':
                # SR-A12-BACKUP-REMOVAL: a century dispatch no longer names a scoped backup (no dump is taken): the scoped_backup_problem call that stood here
                # is gone and every other check of this branch (item, args, absence, completed staging dry run) stays. smalltest_dispatch keeps its own call.
                # The exact-scope measurability stays too (the ruling keeps dry run, exact scope and absence readback): a relation that cannot be measured now refuses.
                if measure is not None:
                    try:
                        measure()
                    except Refused:
                        raise       # the dispatch script's own named refusal (relation names only, SR-J4E-FIX)
                    except Exception:
                        raise Refused('scoped content could not be measured now; the century scope is not shown to be present') from None
                century_dryrun_evidence(req, root)
        elif kind in ('century_resume', 'century_resume_dryrun'):
            # SR-RESUME-NOW: the ONE kind (and its staging-rollback twin) whose absence gate admits a partly present chain, and only a ledger-attested one
            # (resume_evidence). A century_dispatch above still demands every count zero; nothing here is reachable from another kind.
            if req.get('item_id') != CENTURY_ITEM:
                raise Refused('century resume belongs to ' + CENTURY_ITEM)
            century_args_problem(req.get('args') or {})
            resume_evidence(req, root)
        elif kind in ('century_teardown', 'century_teardown_dryrun'):
            scope = staged_scope(req, root)
            if kind == 'century_teardown':
                dryrun_evidence(req, root, scope)
        else:
            raise Refused('unknown century operation kind')
        return None
    except (Refused, KeyError, TypeError, ValueError) as exc:
        return str(exc) if isinstance(exc, Refused) else 'malformed century evidence'


def century_dryrun_evidence(req, root, manifest_digest=None):
    """A real completed staging rollback, same source/args/manifest, before launch (no V acceptance of a dry run, A8 §3.8)."""
    r = completed_receipt(root, req.get('dryrun_receipt'), 'century_dispatch_dryrun')
    p = r.get('staging') or {}
    manifest = p.get('plan_manifest')
    if (r.get('status') != 'COMPLETED' or r.get('item_id') != CENTURY_ITEM or r.get('reviewed_commit') != req.get('reviewed_commit')
            or p.get('schema') != 'ky.century_staging/1' or p.get('status') != 'ROLLED_BACK'
            or p.get('rollback_confirmed') is not True or p.get('args') != req.get('args')
            or p.get('triggered_by') != CENTURY_TRIGGERED_BY or not isinstance(manifest, dict) or 'gochara_v5_test_slice' in manifest
            or p.get('operation_id') != r.get('operation_id') or p.get('request_sha256') != r.get('request_sha256')
            or p.get('plan_manifest_digest') != evidence_digest(manifest)
            or (manifest_digest is not None and p.get('plan_manifest_digest') != manifest_digest)):
        raise Refused('accepted century staging rollback for the same source, args and manifest required')
    from datetime import datetime
    try:
        if datetime.fromisoformat(r['ts']) >= datetime.fromisoformat(acceptance(req, root)['ts']):
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise Refused('century staging rollback must precede the accepted launch request') from None
    return p


# ───────────────────────────── the century resume (SR-RESUME-NOW, OWNER-RESUMABLE-REQUIRED-20261025) ─────────────────────────────
# A resume continues a killed or failed century build over the substeps its own ledger has COMMITTED, instead of tearing the chain down and rebuilding it. A
# century_dispatch demands generation '5.0' independently absent (absence_evidence, unchanged). A century_resume instead demands a ledger-attested partial chain:
# an accepted read-only readback (resume_readback_sql) of the ledger and of the generation's tables, bound to the run it resumes, whose
#   - ledger rows all carry ONE program identity, equal to the request's `program_identity` (manifest digest, writer source digest, runtime library digest, horizon);
#     the executor additionally ties its writer_digest to the century contract at the reviewed commit, so a resume on a different program refuses by name;
#   - every substep was committed by an execution of the resumed lineage (the cited launch receipt and the launches it itself resumed);
#   - per-table counts equal the sum of the ledger's `scope_counts`: a row no committed substep accounts for is an UNATTESTED row and refuses by name, as does a
#     ledger that accounts for more rows than are present (a deleted or torn-down row);
#   - verification tables hold nothing (a resume after the verifier started is refused) and the one manifest is still a candidate.
# The per-substep `scope_digest` is the WRITER's to recompute at plan time (it owns the natural keys); this gate cannot re-derive a row digest, so it binds the ledger's
# counts and identity and records the digests, never claiming to have checked them (§N.8).
# (I) INTERPRETATION: the ledger is the writer lane's migration-1410 table; the names below are this gate's reading of it (stated in the job result for the cockpit to
# reconcile). If the migration differs, ONE edit of these constants changes the readback and the gate together.
RESUME_LEDGER_TABLE = 'ka_gochara_build_ledger'
RESUME_LEDGER_COLUMNS = ('substep_key', 'ordinal', 'execution_id', 'manifest_digest', 'writer_digest', 'library_digest', 'horizon', 'rows_written', 'scope_digest', 'scope_counts')
RESUME_IDENTITY_FIELDS = ('manifest_digest', 'writer_digest', 'library_digest', 'horizon')
RESUME_CHAIN_TABLES = tuple(t for t, _ in ABSENCE_TABLES) + ('ka_gochara_eval_window_record', 'ka_gochara_record_prerequisite')
RESUME_NEVER_PRESENT = ('ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification')
RESUME_SCHEMA = 'ky.century_resume_readback/1'
RESUME_LINEAGE_MAX = 32      # the longest chain of resumes followed back to the original dispatch


def resume_readback_sql():
    """One independent SELECT for readback_sql (no connection, no mutation): the ledger of (chart, generation) and the generation's table counts, as ONE
    `resume_proof` JSON column the verifier accepts together with the output byte digest (the shape of absence_readback_sql). Constants only enter the SQL."""
    import json
    chart = "'" + CHART_ID + "'::uuid"
    gen = "'" + GENERATION + "'"
    base = "'" + json.dumps(dict(schema=RESUME_SCHEMA, chart_id=CHART_ID, generation=GENERATION), sort_keys=True, separators=(',', ':')) + "'::jsonb"
    columns = ', '.join("'" + c + "', l." + c for c in RESUME_LEDGER_COLUMNS)
    ledger = ("COALESCE((SELECT jsonb_agg(jsonb_build_object(" + columns + ") ORDER BY l.ordinal, l.substep_key) FROM " + RESUME_LEDGER_TABLE
              + " l WHERE l.chart_id = " + chart + " AND l.generation = " + gen + "), '[]'::jsonb)")
    extras = dict(ABSENCE_TABLES)
    queries = {t: f"SELECT count(*) FROM {t} WHERE chart_id = {chart} AND generation = {gen}{extras.get(t, '')}" for t in RESUME_CHAIN_TABLES + RESUME_NEVER_PRESENT}
    counts = ', '.join("'" + t + "', (" + sql + ")" for t, sql in sorted(queries.items()))
    manifest = ("(SELECT jsonb_build_object('count', count(*), 'status', min(status)) FROM kala_gochara_publication WHERE chart_id = " + chart
                + " AND generation = " + gen + ")")
    return ("SELECT (" + base + " || jsonb_build_object('ledger', " + ledger + ", 'census', jsonb_build_object(" + counts + "), 'manifest', " + manifest
            + "))::text AS resume_proof")


def _resume_horizon(value):
    """A horizon as a pair of UTC datetimes, from 'start,end' or a two-element list — else Refused by name."""
    from datetime import datetime, timezone
    parts = list(value) if isinstance(value, (list, tuple)) and len(value) == 2 else value.split(',') if isinstance(value, str) else None
    if parts is None or len(parts) != 2:
        raise Refused('a resume horizon must be two timestamps')
    try:
        pair = tuple(datetime.fromisoformat(str(part).replace('Z', '+00:00')) for part in parts)
    except ValueError:
        raise Refused('a resume horizon bound is not an ISO 8601 timestamp') from None
    if any(bound.tzinfo is None for bound in pair):
        raise Refused('a resume horizon bound carries no timezone')
    return tuple(bound.astimezone(timezone.utc) for bound in pair)


def resume_lineage(root, prior):
    """The executions of the lineage `prior` (a century_dispatch or century_resume launch receipt) belongs to: its own and, for a resume, those of the launches
    it itself resumed, back to the original century_dispatch. Each hop reads the archived request of the receipt and checks it is the request the receipt bound."""
    executions, seen = set(), set()
    for _ in range(RESUME_LINEAGE_MAX):
        name = prior.get('operation_id')
        launch = prior.get('launch') or {}
        if (prior.get('kind') not in ('century_dispatch', 'century_resume') or prior.get('status') != 'COMPLETED' or prior.get('exit_code') != 0
                or prior.get('item_id') != CENTURY_ITEM or not isinstance(name, str) or name in seen
                or launch.get('status') != 'LAUNCHED' or launch.get('schema') != 'ky.century_launch/1'
                or launch.get('chart_id') != CHART_ID or launch.get('asset_id') != ASSET_ID):
            raise Refused('resume lineage: every hop must be the COMPLETED launch receipt of a century dispatch or resume')
        seen.add(name)
        executions.add(launch.get('execution_name'))
        if prior['kind'] == 'century_dispatch':
            return executions
        import json
        try:
            archived = json.loads((root / 'done' / (name + '.json')).read_text())
        except (OSError, ValueError):
            raise Refused('resume lineage: the archived request of ' + str(name) + ' is unreadable') from None
        if not isinstance(archived, dict) or request_hash(archived) != prior.get('request_sha256'):
            raise Refused('resume lineage: the archived request of ' + str(name) + ' is not the request its receipt bound')
        prior = read_evidence(root, 'receipts', archived.get('resumes'))
    raise Refused('resume lineage is longer than ' + str(RESUME_LINEAGE_MAX))


def resume_program_problem(req, contract):
    """Raises Refused unless the request's program identity names the writer program the century contract declares (`image.writer_source_digest`): a resume
    continues only the program that wrote the ledger and that the deployed image carries. Pure: `contract` is the parsed fleet/century_contract.json of the
    reviewed tree (the executor ties the same two values at admission; the launcher and the staging rollback repeat it, so no entry point trusts the caller)."""
    identity = req.get('program_identity')
    declared = ((contract or {}).get('image') or {}).get('writer_source_digest') if isinstance(contract, dict) else None
    if not (isinstance(identity, dict) and isinstance(declared, str) and declared and identity.get('writer_digest') == declared):
        raise Refused('program_identity.writer_digest differs from the century contract writer_source_digest: a resume continues only the same program')


def resume_evidence(req, root):
    """The admission of a `century_resume` (see the section header). Raises Refused by name; returns the accepted readback proof."""
    import csv
    import hashlib
    import io
    import json
    import re
    from datetime import datetime
    from pathlib import Path
    prior = read_evidence(root, 'receipts', req.get('resumes'))
    if req['resumes']['name'] != str(prior.get('operation_id')) + '.json':
        raise Refused('resumes must cite a receipt by its own operation id')
    executions = resume_lineage(root, prior)
    if (prior.get('launch') or {}).get('run_id') != req.get('resume_run_id'):
        raise Refused('resume_run_id is not the run the cited launch receipt names')
    identity = req.get('program_identity')
    if not isinstance(identity, dict) or set(identity) != set(RESUME_IDENTITY_FIELDS):
        raise Refused('program_identity must name exactly ' + ', '.join(RESUME_IDENTITY_FIELDS))
    for field in RESUME_IDENTITY_FIELDS[:3]:
        if not (isinstance(identity[field], str) and re.fullmatch(r'[0-9a-f]{64}', identity[field])):
            raise Refused('program_identity.' + field + ' must be 64 lowercase hex')
    if _resume_horizon(identity['horizon']) != _resume_horizon((req.get('args') or {}).get('horizon')):
        raise Refused('program_identity.horizon differs from the request horizon')
    # the accepted readback, measured: its bytes are the executor's retained output, the acceptance repeats exactly what they say
    r, a = accepted_receipt(root, req.get('resume_receipt'), req.get('resume_acceptance'), 'readback_sql')
    p = a.get('resume_readback') or {}
    if r.get('status') != 'COMPLETED' or not r.get('output_file'):
        raise Refused('independent resume readback output required')
    path = Path(r['output_file'])
    try:
        if path.resolve().parent != (root / 'receipts').resolve():
            raise Refused('resume readback output escapes evidence directory')
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != r.get('output_sha256'):
            raise Refused('resume readback output digest mismatch')
    except OSError:
        raise Refused('resume readback output unreadable') from None
    try:
        records = list(csv.DictReader(io.StringIO(body.decode()), delimiter='\t'))
        measured = json.loads(records[0]['resume_proof']) if len(records) == 1 else None
    except (ValueError, KeyError, UnicodeError):
        raise Refused('readback must emit one JSON resume_proof column') from None
    if measured != {k: v for k, v in p.items() if k != 'output_sha256'} or p.get('output_sha256') != r['output_sha256']:
        raise Refused('accepted resume readback differs from the measured readback output')
    try:
        if datetime.fromisoformat(r['ts']) <= datetime.fromisoformat(prior['ts']):
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise Refused('the resume readback must follow the launch it resumes') from None
    if p.get('schema') != RESUME_SCHEMA or p.get('chart_id') != CHART_ID or p.get('generation') != GENERATION:
        raise Refused('measured resume readback of this chart and generation required')
    # the ledger: one program, committed inside the resumed lineage, accounting for the present rows exactly
    rows = p.get('ledger')
    if not isinstance(rows, list) or not rows:
        raise Refused('no committed-substep ledger for this chart and generation: there is nothing to resume')
    attested = {t: 0 for t in RESUME_CHAIN_TABLES}
    keys = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(RESUME_LEDGER_COLUMNS):
            raise Refused('ledger row does not carry exactly the columns ' + ', '.join(RESUME_LEDGER_COLUMNS))
        key = row['substep_key']
        if not isinstance(key, str) or not key or key in keys:
            raise Refused('ledger substep_key missing or duplicated')
        keys.add(key)
        for field in RESUME_IDENTITY_FIELDS:
            same = (_resume_horizon(row[field]) == _resume_horizon(identity[field])) if field == 'horizon' else row[field] == identity[field]
            if not same:
                raise Refused('program identity differs from the ledger (' + field + ' of substep ' + key + '): a resume continues only the same program')
        if row['execution_id'] not in executions:
            raise Refused('ledger substep ' + key + ' was committed by an execution outside the resumed lineage')
        if not (isinstance(row['scope_digest'], str) and re.fullmatch(r'[0-9a-f]{64}', row['scope_digest'])):
            raise Refused('ledger substep ' + key + ' carries no scope digest')
        counts = row['scope_counts']
        if (not isinstance(counts, dict) or not set(counts) <= set(RESUME_CHAIN_TABLES)
                or any(type(n) is not int or n < 0 for n in counts.values()) or type(row['rows_written']) is not int or row['rows_written'] != sum(counts.values())):
            raise Refused('ledger substep ' + key + ' has a malformed row count')
        for table, n in counts.items():
            attested[table] += n
    census = p.get('census')
    if not isinstance(census, dict) or not set(RESUME_CHAIN_TABLES + RESUME_NEVER_PRESENT) <= set(census) or any(type(n) is not int or n < 0 for n in census.values()):
        raise Refused('resume census is incomplete')
    for table in RESUME_NEVER_PRESENT:
        if census[table]:
            raise Refused('verification rows exist in ' + table + ': a resume after the verifier started is refused')
    for table in RESUME_CHAIN_TABLES:
        if census[table] > attested[table]:
            raise Refused('unattested rows in ' + table + ': ' + str(census[table]) + ' present, the ledger accounts for ' + str(attested[table]))
        if census[table] < attested[table]:
            raise Refused('the ledger accounts for more rows in ' + table + ' than are present: ' + str(attested[table]) + ' attested, ' + str(census[table]) + ' present')
    manifest = p.get('manifest')
    if not isinstance(manifest, dict) or manifest.get('count') != 1 or manifest.get('status') != 'candidate':
        raise Refused('exactly one candidate manifest is required to resume')
    return p


def century_generation_ownership(cur, owned: list[str], *, remedy: str, notes: list[str] | None = None, lock: bool = False):
    """Is the existing generation '5.0' output of this chart PROVEN to be an ORDINARY candidate built by an owned century run?
    (The counterpart of `generation_ownership`, whose proof is a test-slice STAMP: a century candidate has none.) Returns
    `(manifest_row_or_None, output_rows)`; raises `Refused` by name otherwise. `owned` is the ids of the century runs.

    The proof, all of it measured here: the manifest is a CANDIDATE (published / sealed / serving are refused earlier by
    `refuse_if_frozen`) whose input vector is the ordinary one — `stored_scope` the default and NO `test_slice` component (a stamped
    candidate belongs to the small-test / measuring teardown and is refused by name); every owned run is a century run whose staged
    manifest carries NO slice marker and whose digest is its own; the stored input snapshot carries the manifest's own vector; every
    search-inventory header carries the snapshot's input digest and the manifest's horizon; and every event_class coverage partition was
    written by an owned run. Reads only (apart from the optional manifest row lock)."""
    notes = notes if notes is not None else []
    module = writer()
    rows = generation_rows(cur)
    cur.execute("SELECT manifest_id, status, input_generation_vector, horizon FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s"
                + (" FOR UPDATE" if lock else ""), (CHART_ID, GENERATION))
    manifest = cur.fetchone()
    if not (rows or manifest):
        return None, 0
    if manifest is None:
        raise Refused(f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} with NO manifest — nothing proves they are the "
                      "century run's; they are left as they are")
    vector = manifest["input_generation_vector"]
    if manifest["status"] != "candidate":
        raise Refused(f"the '5.0' manifest of chart {CHART_ID} has status {manifest['status']!r}, not 'candidate' — a century teardown never "
                      f"touches anything else; {rows} output row(s) are left as they are")
    if (not isinstance(vector, dict) or vector.get("stored_scope") != module.gk_input_vector.STORED_SCOPE or "test_slice" in vector):
        raise Refused(f"the '5.0' manifest of chart {CHART_ID} is not an ordinary century candidate (stored_scope "
                      f"{vector.get('stored_scope') if isinstance(vector, dict) else None!r}, test_slice component "
                      f"{'present' if isinstance(vector, dict) and 'test_slice' in vector else 'absent'}) — a test-slice candidate is "
                      "torn down by the small-test / measuring teardown, never by this one")
    run_manifests = []
    if owned:
        cur.execute("SELECT id, plan_manifest, plan_manifest_digest FROM build_runs WHERE id = ANY(%s::uuid[]) AND triggered_by = %s",
                    (owned, CENTURY_TRIGGERED_BY))
        run_manifests = cur.fetchall()
    if not owned or len(run_manifests) != len(owned):
        raise Refused(f"the '5.0' candidate of chart {CHART_ID} is not tied to an owned '{CENTURY_TRIGGERED_BY}' run — a historical "
                      f"trigger tag never authorises acting on an unproven candidate; {rows} output row(s) are left as they are. {remedy}")
    for run in run_manifests:
        staged = run["plan_manifest"]
        if (not isinstance(staged, dict) or module.TEST_SLICE_KEY in staged or module._manifest_digest(staged) != run["plan_manifest_digest"]):
            raise Refused(f"century run {run['id']}: its staged manifest carries a slice marker, or does not match its own digest — "
                          f"it is not an ordinary century run; {remedy}")
    cur.execute(
        """SELECT (s.input_generation_vector = p.input_generation_vector) AS same_vector, s.input_digest
           FROM ka_gochara_search_input_snapshot s
           JOIN kala_gochara_publication p ON p.chart_id = s.chart_id AND p.generation = s.generation
           WHERE s.chart_id = %s AND s.generation = %s""", (CHART_ID, GENERATION))
    snapshot = cur.fetchone()
    if snapshot is None:
        if rows:
            raise Refused(f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} but no input snapshot binds them to the "
                          f"manifest — their origin is unproven; {remedy}")
        return manifest, rows
    if snapshot["same_vector"] is not True:
        raise Refused(f"the stored input snapshot of chart {CHART_ID} '5.0' carries ANOTHER input vector than the manifest — the output is "
                      f"not provably the century run's; {remedy}")
    cur.execute(
        """SELECT count(*) AS n FROM ka_gochara_search_inventory i
           JOIN ka_gochara_search_input_snapshot s ON s.chart_id = i.chart_id AND s.generation = i.generation
           JOIN kala_gochara_publication p ON p.chart_id = i.chart_id AND p.generation = i.generation
           WHERE i.chart_id = %s AND i.generation = %s AND (i.input_digest <> s.input_digest OR i.horizon <> p.horizon)""",
        (CHART_ID, GENERATION))
    bad = int(cur.fetchone()["n"])
    if bad:
        raise Refused(f"{bad} inventory header(s) of chart {CHART_ID} '5.0' do not carry the manifest's identity (input digest or horizon) "
                      f"— the output is not provably the century run's; {remedy}")
    cur.execute("SELECT count(*) AS n FROM kala_gochara_coverage WHERE chart_id = %s AND generation = %s AND partition_kind = 'event_class'"
                " AND (build_id IS NULL OR NOT (build_id = ANY(%s::text[])))", (CHART_ID, GENERATION, list(owned)))
    foreign = int(cur.fetchone()["n"])
    if foreign:
        raise Refused(f"{foreign} event_class coverage partition(s) of chart {CHART_ID} '5.0' were not written by the identified century "
                      f"run — the output is not provably its own; {remedy}")
    notes.append("proved as an ordinary century candidate: default stored_scope, no test_slice stamp, owned century run(s) with an unmarked "
                 "manifest, snapshot / inventory / coverage tied to it")
    return manifest, rows
