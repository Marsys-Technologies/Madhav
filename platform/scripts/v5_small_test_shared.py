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


def end_state_problems(cur) -> list[str]:
    """The Nirmana N-137 end state for the v5 asset (definitions.ts, NIRMANA_STAGED_INERT_CANDIDATE_RULES and runtimeEvidenceSql):
    catalog_status not RETIRED, nothing depends on the asset, and NO receipt or build_run_assets row of the asset on ANY chart
    from a run that is not a 'gochara-v5-small-test' run (a receipt whose run is gone reads as non-test). Returned as named
    problems; empty means the monitor would still exclude the asset as an unsealed test candidate."""
    problems: list[str] = []
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
           GROUP BY r.chart_id""", (ASSET_ID, TRIGGERED_BY))
    receipts = cur.fetchall()
    if receipts:
        problems.append("receipts of the asset from a non-test run (or with no run link) exist on chart(s) "
                        f"{[(str(r['chart_id']), int(r['n'])) for r in receipts]}")
    cur.execute(
        """SELECT b0.chart_id, count(*) AS n FROM build_run_assets a LEFT JOIN build_runs b0 ON b0.id = a.run_id
           WHERE a.asset_id = %s
             AND NOT EXISTS (SELECT 1 FROM build_runs b WHERE b.id = a.run_id AND b.triggered_by = %s)
           GROUP BY b0.chart_id""", (ASSET_ID, TRIGGERED_BY))
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
    if measuring and req.get('item_id') != 'J-3d':
        raise Refused('measuring teardown belongs to J-3d')
    scope = req.get('measuring_scope' if measuring else 'smalltest_scope')
    if not isinstance(scope, dict):
        raise Refused('identified staged small-test scope required')
    if scope.get('empty') is True:
        if req.get('kind') != 'smalltest_teardown_dryrun' or scope != {'empty': True}:
            raise Refused('empty scope is for the initial teardown rehearsal only')
        return scope
    r, a = accepted_receipt(root, scope.get('dispatch_receipt'), scope.get('dispatch_acceptance'), 'measuring_dispatch' if measuring else 'smalltest_dispatch')
    launch = r.get('launch') or {}
    try:
        valid_uuid = str(uuid.UUID(str(scope.get('run_id')))) == scope.get('run_id')
    except ValueError:
        valid_uuid = False
    if (not valid_uuid or r.get('item_id') not in (('J-3c',) if measuring else ('J-2a', 'J-2c')) or r.get('status') != 'COMPLETED'
            or launch.get('status') != 'LAUNCHED' or launch.get('run_id') != scope.get('run_id')
            or launch.get('chart_id') != CHART_ID or launch.get('asset_id') != ASSET_ID
            or scope.get('chart_id') != CHART_ID or scope.get('generation') != GENERATION
            or scope.get('asset_id') != ASSET_ID or launch.get('plan_manifest_digest') != scope.get('plan_manifest_digest')
            or not re.fullmatch(r'[0-9a-f]{64}', str(scope.get('plan_manifest_digest', '')))
            or not re.fullmatch(r'brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*', str(launch.get('execution_name', '')))
            or not ((scope.get('manifest_id') is None and scope.get('input_vector_sha256') is None)
                    or (scope.get('manifest_id') and re.fullmatch(r'[0-9a-f]{64}', str(scope.get('input_vector_sha256', '')))))):
        raise Refused('scope differs from the accepted staged launch/manifest identity')
    if measuring and (launch.get('schema') != 'ky.measuring_launch/1'
            or not re.fullmatch(r'[0-9a-f]{64}', str(scope.get('input_vector_sha256', '')))
            or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', str(scope.get('manifest_id', '')))):
        raise Refused('measuring scope requires its actual launch, candidate manifest and input vector')
    return scope


def dryrun_evidence(req, root, scope, rowset_sha256=None):
    measuring = req.get('kind') == 'measuring_teardown'
    r = completed_receipt(root, req.get('dryrun_receipt'), 'measuring_teardown_dryrun' if measuring else 'smalltest_teardown_dryrun')
    p = r.get('teardown') or {}
    if (r.get('reviewed_commit') != req.get('reviewed_commit') or r.get('status') != 'COMPLETED' or p.get('schema') != ('ky.measuring_teardown/1' if measuring else 'ky.smalltest_teardown/1')
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
            if ((old.get('kind') in ('smalltest_teardown', 'measuring_teardown') and (old.get('teardown') or {}).get('status') == 'COMMITTED_AWAITING_ABSENCE')
                    or (old.get('kind') in ('smalltest_dispatch', 'measuring_dispatch') and old.get('status') == 'COMPLETED' and old.get('launch'))):
                raise Refused('prior teardown requires its own independent absence')
    else:
        proof = committed.get('teardown') or {}
        if (committed.get('kind') not in ('smalltest_teardown', 'measuring_teardown')
                or proof.get('schema') != ('ky.measuring_teardown/1' if committed.get('kind') == 'measuring_teardown' else 'ky.smalltest_teardown/1')
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
                if (old.get('kind') in ('smalltest_dispatch', 'measuring_dispatch') and old.get('status') == 'COMPLETED'
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
# loads this module alone, from the reviewed commit; a test ties the pin to the file. The window is how long a scoped
# backup stays a valid pre-test record: outside it the dispatch requires a fresh backup + restore proof.
SCOPED_BACKUP_SCOPE_SHA256 = "1daf69d6e31279592947aa25e2b4f9a5c1c8137d6663ba039c27e7331ac7335a"
SCOPED_BACKUP_VALIDITY_S = 4 * 3600


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


def scoped_backup_problem(req, root, now=None):
    """A `smalltest_dispatch` MUST name its backup (`backup_label` + the restore proof's `backup_restore_sha256`), and
    that proof must be taken no more than SCOPED_BACKUP_VALIDITY_S ago (SR-J2A-BACKUP-SCOPE condition 4). A scoped proof
    (schema /2) must be a verified proof of the pinned scope; a full proof (schema /1) is accepted only with the same
    window, measured from its capture receipt's `ts`. Raises Refused.

    (I) INTERPRETATION J2A-S2 (replaces the earlier opt-in reading): no label, no restore-proof digest, or a /1 proof
    without a readable timestamp is refused, never silently allowed. (I) INTERPRETATION J2A-S4: the /1 capture has no
    snapshot instant, so its window starts at the capture receipt's `ts`, written after the dump; alternative: refuse
    every /1 proof."""
    label = req.get('backup_label')
    if label is None or req.get('backup_restore_sha256') is None:
        raise Refused('a dispatch must name its backup_label and backup_restore_sha256; run a fresh backup and restore proof')
    import re
    from datetime import datetime, timedelta, timezone
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
    if proof.get('scope_sha256') != SCOPED_BACKUP_SCOPE_SHA256:
        raise Refused('scoped backup covers a scope other than the reviewed one')
    capture = read_evidence(root, folder, {'name': 'capture.json', 'sha256': proof.get('capture_sha256')})
    scope = capture.get('scope') or {}
    window = capture.get('validity') or {}
    try:
        start = datetime.fromisoformat(window['not_before'])
        end = datetime.fromisoformat(window['not_after'])
        taken = datetime.fromisoformat(proof['ts'])
        if (start.tzinfo is None or end.tzinfo is None or taken.tzinfo is None
                or end - start != timedelta(seconds=SCOPED_BACKUP_VALIDITY_S) or window.get('seconds') != SCOPED_BACKUP_VALIDITY_S):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise Refused('scoped backup validity window missing or malformed') from None
    if (capture.get('schema') != 'ky.smalltest_backup/2' or capture.get('label') != label
            or scope.get('sha256') != SCOPED_BACKUP_SCOPE_SHA256 or capture.get('archive_sha256') != proof.get('archive_sha256')
            or proof.get('validity') != window):
        raise Refused('scoped backup restore proof does not match its capture')
    instant = now or datetime.now(timezone.utc)
    if not start <= taken <= instant <= end:
        raise Refused('scoped backup is outside its validity window; a fresh backup and restore proof are required')


def smalltest_request_problem(req, root):
    """Pure file evidence admission; used from the reviewed source by executor."""
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
                scoped_backup_problem(req, root)
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
    run_where = f"id = {run}" if run else f"chart_id = {chart} AND triggered_by = '{TRIGGERED_BY}'"
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
    queries['owned_test_runs'] = f"SELECT count(*) FROM build_runs WHERE chart_id = {chart} AND triggered_by = '{TRIGGERED_BY}'"
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
