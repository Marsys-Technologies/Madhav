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
    """(problem, source, sliced): problem is None when the input vector PROVES a test slice, by the WRITER'S OWN validation; source says HOW
    (or, for a refusal, what was tried); sliced is the writer's validated slice (None on a refusal).

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
        return "the manifest carries no input vector", None, None
    if vector.get("stored_scope") != module.TEST_SLICE_SCOPE:
        return f"stored_scope is {vector.get('stored_scope')!r}, not {module.TEST_SLICE_SCOPE!r}", None, None
    comp = vector.get("test_slice")                   # the component key the writer stamps (ka_gochara_v5, the input-vector stamp check)
    if not isinstance(comp, dict):
        return "no 'test_slice' component", None, None
    sliced, source, notes = None, None, []
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
            sliced, source = candidate, f"proved against the ORIGINAL marker of run {run_id} (digest {candidate.digest[:12]})"
            break
        notes.append(f"run {run_id}: its marker digest {candidate.digest[:12]} is not the stamp's")
    if sliced is None:
        if run_manifests:
            return ("an owned run row survives, so its ORIGINAL marker preimage must prove the stamp, and it does not "
                    f"(reconstruction is not allowed while a run survives): {'; '.join(notes)}"), None, None
        if require_run:
            return "no owned run row survives to prove this stamp against its original marker (a run-proven stamp is required)", None, None
        marker = {"schema": comp.get("schema"), "run": comp.get("run"), "horizon": comp.get("horizon"), "classes": comp.get("classes")}
        preimage = "no owned run row survives"
        try:
            reconstructed = module._validate_test_slice(marker)
        except module.TestSliceRefusal as exc:
            return (f"the stamp's marker fails the writer's own validation ({exc}); the original marker preimage could not prove it "
                    f"({preimage}), so the reconstruction from the normalised component was used and failed"), None, None
        except Exception as exc:  # noqa: BLE001 — any other failure to validate is a refusal, never an acceptance
            return f"the stamp's marker could not be validated ({type(exc).__name__}); preimage: {preimage}", None, None
        if comp != module._slice_component(reconstructed):
            return ("the stamp is not the writer's component for its marker (the marker digest or a normalised field differs from what "
                    f"the writer's own _slice_component produces); the original marker preimage could not prove it ({preimage}), so "
                    "the reconstruction from the normalised component was used and failed"), None, None
        sliced, source = reconstructed, f"proved by RECONSTRUCTION from the normalised component (original marker preimage unavailable: {preimage})"
    return None, source, sliced


def stamp_problem(vector, horizon, run_manifests=()):
    """(problem, source): `prove_stamp`, plus the manifest's horizon must be the stamp's horizon."""
    problem, source, sliced = prove_stamp(vector, run_manifests)
    if problem:
        return problem, None
    if horizon is None or not (same_instant(getattr(horizon, "lower", None), sliced.horizon[0])
                               and same_instant(getattr(horizon, "upper", None), sliced.horizon[1])):
        return "the manifest's horizon is not the stamp's horizon", None
    return None, source


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


def referencing_rows(cur, parent: str, parent_pk: str, ids: list[str], skip_tables) -> list[str]:
    """Every foreign key INTO `public.<parent>` from the catalog, with the complete child and parent column lists, minus the tables the
    calling script deletes itself. A SUPPORTED key is a single child column referencing the parent's primary-key column (`parent_pk`):
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
        if table.strip('"') in skip_tables:
            continue
        child, target = list(ref["child_cols"]), list(ref["parent_cols"])
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


def generation_ownership(cur, owned: list[str], *, remedy: str, unproven: str, notes: list[str] | None = None, lock: bool = False):
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
    problem, stamp_source = stamp_problem(manifest["input_generation_vector"], manifest["horizon"], run_manifests)
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
        problem2, source2, earlier = prove_stamp(snapshot.get("snapshot_vector"), run_manifests, require_run=True)
        if problem2:
            raise Refused(
                f"the stored input snapshot of chart {CHART_ID} '5.0' carries a DIFFERENT input vector from the stamped "
                "manifest: a later slice stamped the manifest and its snapshot substep has not yet replaced the older output "
                f"(an interrupted replacement), and the older stamp is not proved by an owned test run ({problem2}) — the output "
                f"is not provably this test's. {remedy}")
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
