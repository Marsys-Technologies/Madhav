"""The committed-substep LEDGER of the ka_gochara_v5 century build (SR-RESUME-NOW; OWNER-RESUMABLE-REQUIRED-20261025; migration 1410).

THE PROBLEM. The orchestrator is FROZEN and never feeds `completed_keys`, so a failed century build restarted from zero. The writer itself
therefore plans only what is not yet done (the ka_sangam pattern), and that needs a durable answer to: which substeps committed, under which
program, and what did each leave behind.

THE LEDGER. One row per committed substep (`public.ka_gochara_build_ledger`), written by the writer INSIDE the substep's own savepoint /
transaction — the orchestrator commits after the substep, so the substep's data and its ledger row become durable together or not at all. A
killed run therefore never leaves a half-recorded substep. Nothing here commits, rolls back or closes the connection (frozen contract, N.2).

A ROW BINDS the substep to its PROGRAM (implementation digest of the governed modules, writer source digest, plan digest, horizon, manifest +
input-vector digest) and records WHAT IT LEFT BEHIND (`scope`: rows and a content digest per owned table, write-time columns excluded).

A RESUME (`check_binding` -> `check_manifest` -> the writer's live-input check -> `verify_chain`) skips a recorded substep only when
  * the recorded substeps are a PREFIX of the full plan (the orchestrator runs it in order and stops at the first failure);
  * every row names the program that is running now (writer, implementation, plan, horizon) and the manifest that still stands, unchanged;
  * every recorded scope re-measures equal (a changed, deleted or added row is a tamper);
  * no chain rows exist for a substep that is NOT recorded (no orphan) and no verification row exists yet.
Anything else raises `ResumeRefused` BY NAME and writes nothing: a program fix means teardown + a fresh build, never a silent rebuild.

THE EXPLICIT BINDING (SR-RESUME-EXPLICIT-BINDING). A ledger alone never authorises a skip. The writer resumes ONLY when the run's staged plan_manifest carries
`gochara_v5_century_resume` (RESUME_BINDING_KEY; staged by the executor's century_resume binding from its accepted ledger readback): the run being resumed, the program
identity (implementation, writer and plan digests + horizon) and the ordered substeps already ledgered. A run WITHOUT it that finds ledger rows written by another run
refuses `fresh_run_found_ledger` (never resumes, never deletes); a run WITH it whose identity or substep list disagrees with the ledger refuses by name. Rows this very
run wrote are its own (the orchestrator re-plans after the last substep to confirm nothing remains) and are never "found".

HONEST LIMITS (named, not hidden): a global substep (rules, convention, body:*) owns no chart x generation rows, so its scope is NULL and its resume
trust is the binding + atomicity; near-miss rows and contacts a record grain wrote are covered through the records that reference them (a contact
no ledgered record references is not attributable to a substep), and the independent verification job re-derives both.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone

TABLE = "ka_gochara_build_ledger"
SCOPE_SCHEMA = "gochara_build_ledger_scope/1"
EXECUTION_ENV = "CLOUD_RUN_EXECUTION"
#: the plan_manifest key the executor's century_resume binding stages (platform/scripts/v5_small_test_shared.py RESUME_BINDING_KEY / resume_binding) and the writer's ONLY resume signal
RESUME_BINDING_KEY = "gochara_v5_century_resume"
RESUME_BINDING_SCHEMA = "gochara_v5_century_resume/1"
_BINDING_FIELDS = frozenset({"schema", "resumes_run_id", "program", "ledger_substeps"})
_PROGRAM_FIELDS = frozenset({"implementation_digest", "writer_digest", "plan_digest", "horizon"})
_HEX64 = re.compile(r"[0-9a-f]{64}")

#: write-time / run-identity columns: never part of a content digest (two correct builds differ in exactly these)
VOLATILE_COLUMNS = ("created_at", "computed_at", "finalized_at", "build_id", "manifest_id", "published_at", "superseded_at")

_EMPTY = hashlib.sha256(b"").hexdigest()


class ResumeRefused(RuntimeError):
    """A resume that cannot be proved safe, refused BY NAME. `code` is the stable reason; `keys` the substep keys (or tables) concerned. Nothing was written."""

    def __init__(self, code: str, detail: str, keys=()):
        super().__init__(f"{code}: {detail}")
        self.code, self.keys = code, tuple(keys)


@dataclasses.dataclass(frozen=True)
class Binding:
    """What the program running NOW is: the identity every ledger row must equal."""
    implementation_digest: str
    writer_digest: str
    plan_digest: str
    horizon: tuple                       # (lo, hi) aware datetimes


@dataclasses.dataclass(frozen=True)
class Entry:
    substep_key: str
    ordinal: int
    manifest_id: str | None
    vector_sha256: str | None
    implementation_digest: str
    writer_digest: str
    plan_digest: str
    horizon: tuple
    build_run_id: str
    execution_id: str | None
    rows_written: int
    scope: dict | None
    scope_digest: str | None


def _tuple(row):
    return tuple(row.values()) if isinstance(row, dict) else tuple(row)


def _all(conn, sql, params=()):
    return [_tuple(r) for r in conn.execute(sql, params).fetchall()]


def _one(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return None if row is None else _tuple(row)


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def vector_sha256(vector) -> str:
    """The digest of the manifest's stored input vector (a dict from jsonb): the canonical JSON, the same rule the vector module uses."""
    return sha256_text(canonical(vector))


def plan_digest(*, asset_id: str, keys, final_rules, defer_in_build_verify, result_policy, horizon) -> str:
    """The identity of the PLAN and the staged config this run executes. `keys` is the FULL ordered plan (never the shortened resume plan)."""
    return sha256_text(canonical({
        "schema": SCOPE_SCHEMA, "asset": asset_id, "plan": list(keys), "final_rules": final_rules,
        "defer_in_build_verify": defer_in_build_verify, "result_policy": result_policy,
        "horizon": [horizon[0].isoformat(), horizon[1].isoformat()]}))


#: the seal brief's PINNED_SETTINGS, restated here and tied to it by a test: the writer must not import the sealing side (seal_brief is outside the run's module cluster)
PINNED_SETTINGS = (("TimeZone", "UTC"), ("DateStyle", "ISO, YMD"), ("IntervalStyle", "iso_8601"), ("extra_float_digits", "1"))


@contextmanager
def pinned_session(conn):
    """Pin the settings that change how timestamps, ranges and floats render as text, for a content digest that cannot depend on the session that
    computes it (PINNED_SETTINGS). Transaction-local; the caller's values are restored. Inside the orchestrator's transaction it opens and
    ends nothing (a failure inside rolls back to the caller's savepoint, which reverts the local settings by itself). On an AUTOCOMMIT connection (a test, the
    sealer) every statement is its own transaction and a transaction-local setting would vanish at once, so there — and only there, where there is no outer
    transaction to disturb — the block runs in its own."""
    own = getattr(conn, "autocommit", False) is True and hasattr(conn, "transaction")
    with (conn.transaction() if own else nullcontext()):
        prev = {k: _one(conn, "SELECT current_setting(%s)", (k,))[0] for k, _ in PINNED_SETTINGS}
        for k, v in PINNED_SETTINGS:
            conn.execute("SELECT set_config(%s, %s, true)", (k, v))
        yield
        for k, v in prev.items():
            conn.execute("SELECT set_config(%s, %s, true)", (k, v))


# ── scope: what a substep owns ──────────────────────────────────────────────────────────────────────────────────────────────────────────

_RECORDS_OF_GRAIN = ("SELECT record_id FROM public.ka_gochara_relationship_record"
                     " WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s")


def _probes(key: str, chart_id: str, generation: str):
    """The (name, table, WHERE, params) probes of the rows substep `key` owns, or None for a GLOBAL idempotent substep (rules, convention, body:*)."""
    cg = (chart_id, generation)
    where = "chart_id = %s AND generation = %s"
    if key == "manifest":
        return [("kala_gochara_publication", "kala_gochara_publication", where, cg)]
    if key == "snapshot":
        return [("ka_gochara_search_input_snapshot", "ka_gochara_search_input_snapshot", where, cg)]
    kind, _, rest = key.partition(":")
    if kind == "inventory":
        w = where + " AND event_class = %s"
        return [(t, t, w, cg + (rest,)) for t in ("ka_gochara_search_inventory", "ka_gochara_search_path_pin",
                                                  "ka_gochara_search_obligation", "ka_gochara_search_interval")]
    if kind == "coverage":
        return [("kala_gochara_coverage", "kala_gochara_coverage", where + " AND partition_kind = 'event_class' AND partition_key = %s", cg + (rest,))]
    if kind in ("record", "window"):
        event_class, _, path_id = rest.partition(":")
        grain = cg + (event_class, path_id)
        w = where + " AND event_class = %s AND path_id = %s"
        if kind == "record":
            sub = f" AND record_id IN ({_RECORDS_OF_GRAIN})"
            return [("ka_gochara_relationship_record", "ka_gochara_relationship_record", w, grain),
                    ("ka_gochara_record_prerequisite", "ka_gochara_record_prerequisite", where + sub, cg + grain),
                    ("ka_gochara_contact (referenced by the grain's records)", "ka_gochara_contact",
                     where + " AND contact_id IN (SELECT contact_id FROM public.ka_gochara_relationship_record"
                             " WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s)", cg + grain)]
        return [("ka_gochara_eval_window", "ka_gochara_eval_window", w, grain),
                ("ka_gochara_eval_window_record", "ka_gochara_eval_window_record", w, grain)]
    if kind == "verify":
        return []                                   # the in-build verify persists nothing (R9-6.1): a recorded, EMPTY scope
    return None


def table_digest(conn, table: str, where: str, params=(), exclude=VOLATILE_COLUMNS) -> tuple[int, str]:
    """(row count, content digest) of `public.<table>` rows matching `where`: md5 of each row's canonical jsonb text minus the volatile columns, hex-sorted,
    sha256 over the concatenation. Pure read. Callers hold `pinned_session`."""
    n, digest = _one(
        conn,
        "SELECT count(*)::bigint, COALESCE(encode(sha256(convert_to(COALESCE(string_agg(h, '' ORDER BY h), ''), 'UTF8')), 'hex'), %s)"
        f" FROM (SELECT md5((to_jsonb(t) - %s::text[])::text) AS h FROM public.{table} t WHERE {where}) s",
        (_EMPTY, list(exclude)) + tuple(params))
    return int(n), digest


def measure_scope(conn, chart_id: str, generation: str, key: str):
    """(scope dict, scope digest) of what substep `key` owns now, or (None, None) for a global idempotent substep."""
    probes = _probes(key, chart_id, generation)
    if probes is None:
        return None, None
    tables = {}
    with pinned_session(conn):
        for name, table, where, params in probes:
            n, digest = table_digest(conn, table, where, params)
            tables[name] = {"rows": n, "digest": digest}
    scope = {"schema": SCOPE_SCHEMA, "tables": tables}
    return scope, sha256_text(canonical(scope))


# ── the ledger rows ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _horizon_text(horizon) -> str:
    return f"[{horizon[0].isoformat()},{horizon[1].isoformat()})"


def execution_id() -> str | None:
    return os.environ.get(EXECUTION_ENV) or None


def load(conn, chart_id: str, generation: str) -> list[Entry]:
    """The ledger of (chart, generation) in plan order; [] when it has no rows. A schema without the table is `build_ledger_absent` — a century run
    that cannot record its progress is refused, never run unrecoverable."""
    if not _present(conn, TABLE):
        raise ResumeRefused("build_ledger_absent", f"public.{TABLE} does not exist — apply migration 1410 before a century build")
    rows = _all(conn,
                "SELECT substep_key, ordinal, manifest_id::text, vector_sha256, implementation_digest, writer_digest, plan_digest,"
                " lower(horizon), upper(horizon), build_run_id, execution_id, rows_written, scope::text, scope_digest"
                " FROM public.ka_gochara_build_ledger WHERE chart_id = %s::uuid AND generation = %s ORDER BY ordinal", (chart_id, generation))
    return [Entry(k, int(o), m, v, i, w, p, (lo, hi), b, e, int(n), json.loads(s) if s else None, d)
            for (k, o, m, v, i, w, p, lo, hi, b, e, n, s, d) in rows]


def record(conn, chart_id: str, generation: str, *, key: str, ordinal: int, binding: Binding, manifest_id, vec_sha, build_run_id,
           rows_written: int, scope, scope_digest) -> None:
    """Upsert this substep's row in the CALLER's transaction (never committed here). An upsert, not an insert: the substep's natural key replaces."""
    conn.execute(
        "INSERT INTO public.ka_gochara_build_ledger (chart_id, generation, substep_key, ordinal, manifest_id, vector_sha256, implementation_digest, writer_digest,"
        " plan_digest, horizon, build_run_id, execution_id, rows_written, scope, scope_digest)"
        " VALUES (%s::uuid, %s, %s, %s, %s::uuid, %s, %s, %s, %s, %s::tstzrange, %s, %s, %s, %s::jsonb, %s)"
        " ON CONFLICT (chart_id, generation, substep_key) DO UPDATE SET ordinal = EXCLUDED.ordinal, manifest_id = EXCLUDED.manifest_id,"
        " vector_sha256 = EXCLUDED.vector_sha256, implementation_digest = EXCLUDED.implementation_digest, writer_digest = EXCLUDED.writer_digest,"
        " plan_digest = EXCLUDED.plan_digest, horizon = EXCLUDED.horizon, build_run_id = EXCLUDED.build_run_id,"
        " execution_id = EXCLUDED.execution_id, rows_written = EXCLUDED.rows_written, scope = EXCLUDED.scope,"
        " scope_digest = EXCLUDED.scope_digest, committed_at = now()",
        (chart_id, generation, key, int(ordinal), manifest_id, vec_sha, binding.implementation_digest, binding.writer_digest,
         binding.plan_digest, _horizon_text(binding.horizon), str(build_run_id), execution_id(), int(rows_written),
         canonical(scope) if scope is not None else None, scope_digest))


def manifest_identity(conn, chart_id: str, generation: str):
    """(manifest_id, status, vector_sha256, horizon_basis) of the generation's manifest — the pin read back from the STORED vector — or None."""
    row = _one(conn, "SELECT manifest_id::text, status, input_generation_vector::text FROM public.kala_gochara_publication"
                     " WHERE chart_id = %s AND generation = %s", (chart_id, generation))
    if row is None:
        return None
    vector = json.loads(row[2])
    return row[0], row[1], vector_sha256(vector), vector.get("horizon_basis")


# ── the resume checks ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def check_binding(entries: list[Entry], binding: Binding, full_keys: list[str]) -> None:
    """The cheap, ledger-only checks, in the order they name a cause: prefix, writer, implementation, horizon, plan."""
    plan = list(full_keys)
    stray = [e.substep_key for e in entries if e.substep_key not in plan]
    if stray:
        raise ResumeRefused("resume_ledger_key_not_in_plan", f"ledgered substep(s) {stray} are not in this run's plan — the plan changed", stray)
    keys = [e.substep_key for e in entries]
    if keys != plan[:len(keys)]:
        missing = [k for k in plan[:plan.index(keys[-1]) + 1] if k not in keys]
        gap = missing or [next(k for k, p in zip(keys, plan) if k != p)]
        raise ResumeRefused("resume_ledger_not_a_prefix",
                            f"the recorded substeps are not the first {len(keys)} of the plan (missing or out of order: {gap}): the orchestrator runs the plan in "
                            "order and stops at the first failure, so a gap means the ledger was altered", gap)
    for field, code in (("writer_digest", "resume_program_changed"), ("implementation_digest", "resume_program_changed")):
        bad = sorted({getattr(e, field) for e in entries if getattr(e, field) != getattr(binding, field)})
        if bad:
            first = next(e for e in entries if getattr(e, field) != getattr(binding, field))
            raise ResumeRefused(code, f"{field}: the substeps were built by a different program (recorded {bad}, running now {getattr(binding, field)}; first at "
                                f"{first.substep_key!r}) — a program fix means teardown + a fresh build, never a resume",
                                [e.substep_key for e in entries if getattr(e, field) != getattr(binding, field)])
    bad = [e for e in entries if tuple(e.horizon) != tuple(binding.horizon)]
    if bad:
        raise ResumeRefused("resume_horizon_changed", f"recorded horizon {_horizon_text(bad[0].horizon)} != this run's {_horizon_text(binding.horizon)} "
                            f"(first at {bad[0].substep_key!r}) — a different horizon is a new build", [e.substep_key for e in bad])
    bad = [e for e in entries if e.plan_digest != binding.plan_digest]
    if bad:
        raise ResumeRefused("resume_plan_changed", f"plan_digest recorded {bad[0].plan_digest} != this run's {binding.plan_digest}: the plan or the staged config "
                            f"(rules profile, verify deferral, result policy) differs (first at {bad[0].substep_key!r})", [e.substep_key for e in bad])


# ── the explicit resume binding ───────────────────────────────────────────────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class ResumeBinding:
    """The validated `plan_manifest[RESUME_BINDING_KEY]`: what the executor admitted this run to continue."""
    resumes_run_id: str
    implementation_digest: str
    writer_digest: str
    plan_digest: str
    horizon: tuple                       # (lo, hi) aware UTC datetimes
    ledger_substeps: tuple               # ordered substep keys the accepted readback measured


def validate_resume_binding(raw) -> ResumeBinding:
    """The binding as a typed value, or `resume_binding_malformed` by name. Exact fields, 64-hex digests, an aware ISO horizon, a non-empty duplicate-free substep list."""
    def refuse(msg):
        raise ResumeRefused("resume_binding_malformed", f"{RESUME_BINDING_KEY}: {msg} — refused, never guessed")
    if not isinstance(raw, dict) or set(raw) != _BINDING_FIELDS:
        refuse(f"fields {sorted(raw) if isinstance(raw, dict) else type(raw).__name__} are not exactly {sorted(_BINDING_FIELDS)}")
    if raw["schema"] != RESUME_BINDING_SCHEMA:
        refuse(f"schema {raw['schema']!r} is not {RESUME_BINDING_SCHEMA!r}")
    try:
        run_id = str(uuid.UUID(str(raw["resumes_run_id"])))
    except ValueError:
        refuse(f"resumes_run_id {raw['resumes_run_id']!r} is not a UUID")
    program = raw["program"]
    if not isinstance(program, dict) or set(program) != _PROGRAM_FIELDS:
        refuse(f"program fields {sorted(program) if isinstance(program, dict) else type(program).__name__} are not exactly {sorted(_PROGRAM_FIELDS)}")
    for field in ("implementation_digest", "writer_digest", "plan_digest"):
        if not (isinstance(program[field], str) and _HEX64.fullmatch(program[field])):
            refuse(f"program.{field} is not a 64-hex digest")
    horizon = program["horizon"]
    if not isinstance(horizon, (list, tuple)) or len(horizon) != 2 or not all(isinstance(x, str) for x in horizon):
        refuse(f"program.horizon {horizon!r} is not a pair of ISO timestamps")
    try:
        points = tuple(datetime.fromisoformat(x) for x in horizon)
    except ValueError:
        refuse(f"program.horizon {horizon!r} is not parseable ISO 8601")
    if any(p.tzinfo is None for p in points):
        refuse(f"program.horizon {horizon!r} carries a naive timestamp")
    keys = raw["ledger_substeps"]
    if not isinstance(keys, (list, tuple)) or not keys or not all(isinstance(k, str) and k.strip() for k in keys) or len(set(keys)) != len(keys):
        refuse("ledger_substeps is not a non-empty list of distinct substep keys")
    return ResumeBinding(run_id, program["implementation_digest"], program["writer_digest"], program["plan_digest"],
                         tuple(p.astimezone(timezone.utc) for p in points), tuple(keys))


def foreign_entries(entries: list[Entry], build_run_id) -> list[Entry]:
    """The ledger rows another run wrote. The rows this run wrote itself are never 'found': the orchestrator re-plans after the last substep to confirm nothing remains."""
    return [e for e in entries if str(e.build_run_id) != str(build_run_id)]


def check_not_a_fresh_run_over_a_ledger(entries: list[Entry], build_run_id) -> None:
    """A run staged WITHOUT the explicit binding that finds rows another run ledgered refuses `fresh_run_found_ledger`: it never resumes (the ledger alone does not
    authorise a skip) and never deletes (a clean start is a teardown, the owner's operation)."""
    found = foreign_entries(entries, build_run_id)
    if found:
        runs = sorted({str(e.build_run_id) for e in found})
        raise ResumeRefused("fresh_run_found_ledger",
                            f"this run carries no {RESUME_BINDING_KEY} binding but {len(found)} substep(s) are already ledgered by run(s) {', '.join(runs)} "
                            f"(first {found[0].substep_key!r}): a resume is staged only through the century_resume operation; a fresh dispatch never resumes and never deletes — "
                            "tear the generation down first", [e.substep_key for e in found])


def check_resume_binding(binding: ResumeBinding, entries: list[Entry], build_run_id) -> None:
    """The explicit binding agrees with the ledger it claims to continue: it is another run's resume (not this run's own), the identity it names is the identity of every
    row another run ledgered (implementation, writer, plan digests, horizon), and the ordered substeps it lists are exactly those rows. The running program is judged
    against the same rows next (`check_binding`), so the three — binding, ledger, program — are one identity."""
    if binding.resumes_run_id == str(build_run_id):
        raise ResumeRefused("resume_binding_self_reference", f"{RESUME_BINDING_KEY}.resumes_run_id is this run ({build_run_id}): a run cannot resume itself")
    found = foreign_entries(entries, build_run_id)
    for field in ("implementation_digest", "writer_digest", "plan_digest"):
        bad = [e for e in found if getattr(e, field) != getattr(binding, field)]
        if bad:
            raise ResumeRefused("resume_binding_program_mismatch",
                                f"{field}: the binding names {getattr(binding, field)} but the ledger holds {getattr(bad[0], field)} (first at {bad[0].substep_key!r}) — the binding "
                                "does not describe this ledger", [e.substep_key for e in bad])
    bad = [e for e in found if tuple(e.horizon) != tuple(binding.horizon)]
    if bad:
        raise ResumeRefused("resume_binding_program_mismatch", f"horizon: the binding names {_horizon_text(binding.horizon)} but the ledger holds {_horizon_text(bad[0].horizon)} "
                            f"(first at {bad[0].substep_key!r})", [e.substep_key for e in bad])
    held = [e.substep_key for e in found]
    if held != list(binding.ledger_substeps):
        extra = [k for k in held if k not in binding.ledger_substeps]
        lost = [k for k in binding.ledger_substeps if k not in held]
        raise ResumeRefused("resume_binding_substeps_mismatch",
                            f"the binding lists {len(binding.ledger_substeps)} ledgered substep(s) but the ledger holds {len(held)} from other runs "
                            f"(in the ledger only: {extra}; in the binding only: {lost}; or the order differs)", extra + lost)


def check_manifest(conn, chart_id: str, generation: str, entries: list[Entry], *, require_horizon_basis: bool = False) -> None:
    """V1: the candidate manifest the ledgered substeps were bound to still stands, unchanged. The vector digest covers the whole input vector, including the
    horizon_basis pin (FB-2): a resume that skips the manifest substep must find the pin it recorded. With `require_horizon_basis` (a run that could pin: it carries
    birth parameters) the pin is READ BACK from the stored manifest and must exist and describe the horizon the substeps were built over — a chain without a pin
    (built before the pin was written for century runs) is NON-RESUMABLE, refused by name, never re-pinned and never recomputed."""
    bound = [e for e in entries if e.manifest_id is not None]
    if not bound:
        raise ResumeRefused("resume_manifest_unrecorded", "the manifest substep is recorded without the manifest it bound", [e.substep_key for e in entries])
    now = manifest_identity(conn, chart_id, generation)
    if now is None:
        raise ResumeRefused("resume_manifest_missing", f"the ledger records the manifest substep but generation {generation} has no manifest", [bound[0].substep_key])
    manifest_id, status, vec, basis = now
    if status != "candidate":
        raise ResumeRefused("resume_manifest_not_candidate", f"the manifest is {status!r}, not 'candidate': a published or sealed generation is never resumed", [bound[0].substep_key])
    bad = [e.substep_key for e in bound if e.manifest_id != manifest_id or e.vector_sha256 != vec]
    if bad:
        raise ResumeRefused("resume_manifest_changed", f"the manifest (id {manifest_id}, vector {vec}) is not the one the substeps were bound to "
                            f"(recorded id {bound[0].manifest_id}, vector {bound[0].vector_sha256}) — including its horizon_basis pin", bad)
    if require_horizon_basis:
        if not isinstance(basis, dict) or basis.get("schema") != "horizon_basis/1":
            raise ResumeRefused("resume_horizon_basis_unpinned", "the stored manifest carries no horizon_basis pin: a chain built without one is non-resumable "
                                "(teardown + a fresh build); the pin is read back from the manifest, never recomputed or added to it", [bound[0].substep_key])
        recorded = [h.astimezone(timezone.utc).isoformat() for h in bound[0].horizon]
        if basis.get("horizon") != recorded:
            raise ResumeRefused("resume_horizon_basis_mismatch", f"the manifest's horizon_basis pin describes {basis.get('horizon')}, the substeps were built over {recorded}",
                                [bound[0].substep_key])


def _present(conn, table: str) -> bool:
    return _one(conn, "SELECT to_regclass(%s)", (f"public.{table}",))[0] is not None


def verify_chain(conn, chart_id: str, generation: str, entries: list[Entry]) -> None:
    """V5/V7/V8: every recorded scope re-measures equal (a changed, deleted or added row names its substep); no chain row exists for a substep that is not
    recorded; no verification row exists yet. Pure reads."""
    tampered, detail = [], []
    for e in entries:
        if e.scope is None:
            continue
        scope, digest = measure_scope(conn, chart_id, generation, e.substep_key)
        if digest != e.scope_digest:
            tampered.append(e.substep_key)
            cur, was = (scope or {}).get("tables", {}), e.scope.get("tables", {})
            diff = sorted(t for t in set(cur) | set(was) if cur.get(t) != was.get(t))
            detail.append(f"{e.substep_key} ({', '.join(diff)})")
    if tampered:
        raise ResumeRefused("resume_chain_tampered",
                            "the stored rows of recorded substep(s) are no longer what they committed: " + "; ".join(detail) + " — refused, never rebuilt silently", tampered)
    done = {e.substep_key for e in entries}
    cg = (chart_id, generation)
    orphans = []
    for key_fmt, sql in (("inventory:{0}", "SELECT DISTINCT event_class FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s"),
                         ("coverage:{0}", "SELECT DISTINCT partition_key FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s AND partition_kind = 'event_class'"),
                         ("record:{0}:{1}", "SELECT DISTINCT event_class, path_id FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"),
                         ("window:{0}:{1}", "SELECT DISTINCT event_class, path_id FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s")):
        orphans += [k for k in (key_fmt.format(*r) for r in _all(conn, sql, cg)) if k not in done]
    if _one(conn, "SELECT count(*) FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s", cg)[0] and "snapshot" not in done:
        orphans.append("snapshot")
    if orphans:
        raise ResumeRefused("resume_orphan_rows", "chain rows exist for substep(s) the ledger does not record: " + ", ".join(sorted(orphans)), sorted(orphans))
    persisted = [t for t in ("ka_gochara_eval_window_verification", "ka_gochara_search_inventory_verification")
                 if _present(conn, t) and _one(conn, f"SELECT count(*) FROM public.{t} WHERE chart_id = %s AND generation = %s", cg)[0]]
    if persisted:
        raise ResumeRefused("resume_verification_rows_present", f"the verifier already persisted rows ({persisted}): a build after verification started is a new generation", persisted)


# ── the producer-execution list (the sealer's side) ───────────────────────────────────────────────────────────────────────────────────

def producer_executions(conn, chart_id: str, generation: str) -> list[dict]:
    """The ordered distinct producers of a generation's substeps: [{build_run_id, execution_id, substeps}] by first substep. [] = no ledger rows."""
    if not _present(conn, TABLE):
        return []                               # a schema without the ledger has no resumed generation (the sealer's read must not abort its transaction)
    rows = _all(conn, "SELECT build_run_id, execution_id, count(*), min(ordinal) FROM public.ka_gochara_build_ledger WHERE chart_id = %s::uuid AND generation = %s"
                      " GROUP BY build_run_id, execution_id ORDER BY min(ordinal)", (chart_id, generation))
    return [{"build_run_id": b, "execution_id": e, "substeps": int(n)} for b, e, n, _ in rows]


def resumed_generation_problem(conn, chart_id: str, generation: str) -> str | None:
    """None when the generation was produced by ONE execution (or has no ledger: legacy / slice / test builds); else the named reason the SEALER refuses it.
    The seal brief does not yet record the list of producer executions, so a generation several executions built has an unrecorded gap — refused, not hidden."""
    produced = producer_executions(conn, chart_id, generation)
    if len(produced) <= 1:
        return None
    return ("resumed_generation_not_sealable: generation " + generation + " was produced by " + str(len(produced)) + " executions ("
            + ", ".join(f"{p['build_run_id']}/{p['execution_id'] or 'no-execution-id'}: {p['substeps']} substeps" for p in produced)
            + ") and the seal does not yet record the list of producer executions — a resumed build is not sealed until it does")


__all__ = ["Binding", "Entry", "RESUME_BINDING_KEY", "RESUME_BINDING_SCHEMA", "ResumeBinding", "ResumeRefused", "TABLE", "canonical", "check_binding",
           "check_manifest", "check_not_a_fresh_run_over_a_ledger", "check_resume_binding", "foreign_entries", "load", "manifest_identity", "measure_scope",
           "pinned_session", "plan_digest", "producer_executions", "record", "resumed_generation_problem", "table_digest", "validate_resume_binding",
           "vector_sha256", "verify_chain"]
