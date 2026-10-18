#!/usr/bin/env bash
# Slot databases v2.0 — status: built by KV3-B-LOCALDB, pending its independent review (relaunch plan v2.7 §3, §4a.2,
# §5 Slot DBs; KU-02). Production is never written by this script; the seed is a READ-ONLY dump.
#   local_db.sh slots                      the configured slots, one per line: b1..bN then v1..vM (N, M = the integers 1–8
#                                          in $KY_RUN/KY_WORKERS and $KY_RUN/KY_VERIFIERS); unknown → exit 1, no output
#   local_db.sh up --session S             start, or reuse after validating it, the container ky-pg (pgvector/pgvector:pg16,
#                                          labels campaign=kalayantra + ky.session=S, 127.0.0.1:${KY_PG_PORT:-55433}, PGDATA
#                                          bind-mounted from R/db/S/pgdata). Anything else called ky-pg is reported and left
#                                          alone — no stop, rm or rename — exit 2. With no container, a hand-over record
#                                          whose storage still exists is kept: storage on record as another session's (or
#                                          an unreadable record) refuses, exit 2; storage on record as S's is removed and
#                                          seen gone before the record goes, else exit 1
#   local_db.sh db <slot> --session S      create ky_<slot> (seed + the project's migration runner) or RE-VALIDATE it; the
#                                          answer is READY (every condition observed in THIS invocation, receipt written) or
#                                          FAILED — never just 'exists'. Another session's database: exit 2, nothing changed
#   local_db.sh reset <slot> --session S   drop and recreate ky_<slot>; S's own databases only
#   local_db.sh check <slot>               read-only: exit 0 only if the receipt says READY and container id, mount, the
#                                          three seed hashes and the database's session mark, observed now, equal it;
#                                          otherwise `ky_<slot> STALE: <reason>`, exit 1
#   local_db.sh close --session S          KU-02 clean-up; prints `close session=S dropped=<n> container=<c>`. Exit 0 with
#                                          c = absent (no container: S's receipts and S's storage — R/db/S unless it is on
#                                          record as handed over, and any storage on record as handed to S — removed and seen
#                                          gone) | incompatible (untouched) | removed (S's databases and receipts gone,
#                                          no other session's database left: container and its storage directory gone too)
#                                          | handed_over (another session's database remains: container and storage pass to
#                                          it, on record in $KY_RUN/local_db/container.json). With a container present,
#                                          removed and handed_over also mean R/db/S, when the container does not mount it
#                                          and it is not on record as another session's, and storage on record as S's,
#                                          removed and seen gone; a record of another session's storage that still
#                                          exists is never overwritten (handover_unrecorded). Exit 1 with c =
#                                          unmarked_database (a foreign database: nothing removed) | unobservable |
#                                          databases_remain | receipts_remain | not_removed | storage_remains |
#                                          record_remains | handover_unrecorded
#   local_db.sh down                       stop the container; never a clean-up — close is still owed
#   local_db.sh seed                       READ-ONLY schema dump of production + the applied-migrations ledger + the asset
#                                          registry rows → $KY_RUN/schema/. An OPERATOR or EXECUTOR action (executor kind
#                                          `local_schema_seed`, run as a lone copy of this file): it reads the production
#                                          connection settings, so it refuses inside a job (KY_LANE, KY_ITEM or JOB_SCRATCH)
# Exit: 0 ok or READY · 1 FAILED or not verified · 2 refused, nothing changed · 64 usage.
# S matches ^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$ and holds no `..`; anything else is exit 2 before any docker, psql or
# filesystem call. R = realpath($KY_SCRATCH).
# Environment: KY_RUN (default $KY_ROOT/run) · KY_SCRATCH (required: absolute, existing) · KY_SOURCE_REPO (the checkout
# whose platform/ holds the migration runner) · KY_PG_PORT. Test overrides, absolute paths: KY_DOCKER, KY_PSQL, KY_PG_DUMP,
# KY_NPX (recorded in the receipt's `tools`) and KY_PGENV (seed's settings file; refused against the live run directory).
# Logs: $KY_SCRATCH/db/_*. Plan §3: no connection string or password is printed or exported; they reach only this
# script's own psql and runner children, and there is no `url` command.
# INTERPRETATION (KU-02 "a bind mount inside R"): the layout `up` creates — the PGDATA mount is a bind whose resolved
# source lies below a direct child of R/db, and no other mount is a volume or leaves R.
# Changelog: v2.0 (2026-10-12, KV3-B-LOCALDB) session-bound slots, bind-mounted storage, bound receipts, check, close,
#   registry-mandatory seed, no url command; lanes and KY_REPO retired. v1.1 lane databases (charter §7).
#   v2.0 review round 1 (2026-10-12, B-01): close without a container removes S's receipts and storage and observes
#   their absence before it exits 0.
#   v2.0 review round 2 (2026-10-12, B-01, B-02): close with a container present also removes S's storage outside the
#   container's store and observes its absence; up no longer discards a hand-over record while the storage it names
#   exists (refused for another session's, removed and seen gone for S's own).
#   KV3-PREFLIGHT-VARIANTS: up waits at most ten one-second intervals for an observed compatible container's
#   removal and its matching hand-over cleanup, then retries creation once; foreign containers never qualify.
set -uo pipefail
export LC_ALL=C
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; KY_RUN="${KY_RUN:-$KY_ROOT/run}"
SRC="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"
CONT=ky-pg; IMAGE=pgvector/pgvector:pg16; PGDATA_DIR=/var/lib/postgresql/data; PORT="${KY_PG_PORT:-55433}"; PW=postgres
FLOOR_TABLES=400; FLOOR_KALA=70; FLOOR_LEDGER=900          # today's count floors
LIVE_RUN=/Users/Dev/kalayantra/run
REAL_PGENV=/Users/Dev/.config/pravaha/pgenv.sh
SESSION_RE='^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$'
DOCKER="${KY_DOCKER:-docker}"; PSQL="${KY_PSQL:-psql}"; PG_DUMP="${KY_PG_DUMP:-pg_dump}"; NPX="${KY_NPX:-npx}"
TAB="$(printf '\t')"; NL='
'
PY=""; for c in /opt/homebrew/bin/python3 /usr/bin/python3; do if [ -x "$c" ]; then PY="$c"; break; fi; done
[ -n "$PY" ] || PY="$(command -v python3 2>/dev/null || true)"
S=""; R=""; ENV_WHY=""; DBS=""; OWN=""; OTHERS=""; UNMARKED=""; SEED_TMP=""

note() { printf '%s\n' "$*" >&2; }
refuse() { note "refused: $*"; exit 2; }
usage() { note "usage: local_db.sh slots | up --session S | db <slot> --session S | reset <slot> --session S | check <slot> | close --session S | down | seed"; exit 64; }
valid_session() { [[ "$1" =~ $SESSION_RE ]] || return 1; case "$1" in *..*) return 1;; esac; return 0; }
valid_slot() { case "$1" in [bv][1-8]) return 0;; esac; return 1; }
lines() { printf '%s' "$1" | wc -l | tr -d ' '; }
tool_path() { command -v "$1" 2>/dev/null || true; }

# Every judgement on data — what a container is, what a receipt says, which restore errors are today's — is this helper.
py() { "$PY" -B -I /dev/fd/3 "$@" 3<<'KYPY'
import collections, hashlib, json, os, re, sys

SESSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
# The restore of the read-only dump produces EXACTLY nine statement errors — the pre-existing public schema (1) and the
# two types of the planner tables the dump could not include (6 + 2). An exact multiset: anything else is another fixture.
EXPECTED = collections.Counter({'ERROR: schema "public" already exists': 1,
                                'ERROR: type "public.planner_managed_prashna_jobs" does not exist': 6,
                                'ERROR: type "public.planner_inquiry_lifecycles" does not exist': 2})


def clean(v):
    return "" if v is None else re.sub(r"[\x00-\x1f\x7f]", "?", str(v))


def out(*vals):
    sys.stdout.write("".join(clean(v) + "\n" for v in vals))


def atomic(path, obj):
    tmp = "%s.tmp.%d" % (path, os.getpid())
    try:
        with open(tmp, "w") as f:
            json.dump(obj, f)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load(path):
    with open(path) as f:
        return json.load(f)


def below(path, root):
    """path lies strictly below root (both resolved)."""
    rel = os.path.relpath(path, root)
    return rel != "." and not rel.startswith(".." + os.sep) and rel != ".."


def judge(root, port, image, pgdata):
    """stdin: `docker inspect` of the container. Lines: compatible|incompatible, why, id, running, session label,
    resolved PGDATA mount source, the direct child of <root>/db holding it, removal-in-progress."""
    c = json.load(sys.stdin)
    if isinstance(c, list) and len(c) == 1:
        c = c[0]
    if not isinstance(c, dict) or not isinstance(c.get("Id"), str) or not c["Id"]:
        sys.exit(1)
    cfg, why, src, store = c.get("Config") or {}, [], "", ""
    labels = cfg.get("Labels") or {}
    if cfg.get("Image") != image:
        why.append("image is %s" % cfg.get("Image"))
    if labels.get("campaign") != "kalayantra":
        why.append("no campaign=kalayantra label")
    ports = (c.get("HostConfig") or {}).get("PortBindings") or {}
    got = [(b.get("HostIp"), str(b.get("HostPort"))) for b in (ports.get("5432/tcp") or []) if isinstance(b, dict)]
    if set(ports) != {"5432/tcp"} or got != [("127.0.0.1", str(port))]:
        why.append("not published as 127.0.0.1:%s:5432 alone" % port)
    mounts = [m for m in (c.get("Mounts") or []) if isinstance(m, dict)]
    base = os.path.join(root, "db")
    for m in mounts:
        raw = m.get("Source") or ""
        real = os.path.realpath(raw) if os.path.isabs(raw) else ""
        if m.get("Type") != "bind":
            why.append("anonymous or named volume at %s" % m.get("Destination"))
        elif not real or not below(real, root):
            why.append("bind mount from outside the session scratch root at %s" % m.get("Destination"))
        elif m.get("Destination") == pgdata:
            parts = os.path.relpath(real, base).split(os.sep)
            if below(real, base) and len(parts) >= 2:
                src, store = real, os.path.join(base, parts[0])
            else:
                why.append("PGDATA bind mount is not below a session directory of the scratch root's db/")
    if len([m for m in mounts if m.get("Destination") == pgdata]) != 1:
        why.append("no single mount at %s" % pgdata)
    if why:
        src = store = ""
    running = (c.get("State") or {}).get("Running") is True
    state = c.get("State") or {}
    removing = state.get("Status") == "removing"
    out("incompatible" if why else "compatible", "; ".join(why), c["Id"], "true" if running else "false",
        labels.get("ky.session"), src, store, "true" if removing else "false")


def sha(*paths):
    """One line per file, all or nothing."""
    found = []
    for path in paths:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        found.append(h.hexdigest())
    out(*found)


def receipt(path, slot, database, result, reason, session, name, cid, image, port, mount, h1, h2, h3, runner_rc,
            tables, kala, ledger, unexpected, t_docker, t_psql, t_pg_dump, t_npx, ts):
    num = lambda s: int(s) if re.fullmatch(r"-?\d+", s) else None   # unknown is null, never 0
    txt = lambda s: s or None
    atomic(path, {"schema": "ky.slot_db/1", "slot": slot, "database": database, "result": result, "reason": reason,
                  "session_id": txt(session),
                  "container": {"name": name, "id": txt(cid), "image": image, "port": num(port)},
                  "mount_source": txt(mount),
                  "seed": {"schema_sha256": txt(h1), "ledger_sha256": txt(h2), "registry_sha256": txt(h3)},
                  "runner_rc": num(runner_rc), "tables": num(tables), "kala_tables": num(kala), "ledger": num(ledger),
                  "unexpected_restore_errors": num(unexpected),
                  "tools": {"docker": txt(t_docker), "psql": txt(t_psql), "pg_dump": txt(t_pg_dump), "npx": txt(t_npx)},
                  "ts": ts})


def receipt_read(path):
    r = load(path)
    if not isinstance(r, dict) or r.get("schema") != "ky.slot_db/1":
        sys.exit(1)
    cont, seed = r.get("container"), r.get("seed")
    cont, seed = (cont if isinstance(cont, dict) else {}), (seed if isinstance(seed, dict) else {})
    vals = [r.get("result"), r.get("session_id"), cont.get("id"), r.get("mount_source"), seed.get("schema_sha256"),
            seed.get("ledger_sha256"), seed.get("registry_sha256"), r.get("slot"), r.get("database")]
    out(*[v if isinstance(v, str) else "" for v in vals])


def receipts_of(directory, session):
    found = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return found
    for name in names:
        path = os.path.join(directory, name)
        if not name.endswith(".json") or not os.path.isfile(path):
            continue
        try:
            r = load(path)
        except (OSError, ValueError):
            continue
        if isinstance(r, dict) and r.get("schema") == "ky.slot_db/1" and r.get("session_id") == session:
            found.append(path)
    return found


def forget(directory, session):
    """Remove the session's slot receipts; print how many are still there afterwards."""
    for path in receipts_of(directory, session):
        try:
            os.unlink(path)
        except OSError:
            pass
    out(len(receipts_of(directory, session)))


def unlink(*paths):
    for path in paths:
        try:
            os.unlink(path)
        except OSError:
            pass


def record_owner(path, storage):
    r = load(path)
    if (not isinstance(r, dict) or set(r) != {"owner", "storage", "from"} or r["storage"] != storage
            or not isinstance(r["owner"], str) or not SESSION.match(r["owner"]) or ".." in r["owner"]):
        sys.exit(1)
    out(r["owner"])


def record_held(path, session):
    """The storage a hand-over record leaves to this session; nothing when the record names another owner."""
    r = load(path)
    if (not isinstance(r, dict) or set(r) != {"owner", "storage", "from"} or r["owner"] != session
            or not isinstance(r["storage"], str) or not os.path.isabs(r["storage"])):
        sys.exit(1)
    out(r["storage"])


def record_read(path):
    """Owner and storage of a well-formed hand-over record, whatever storage it names."""
    r = load(path)
    if (not isinstance(r, dict) or set(r) != {"owner", "storage", "from"} or not isinstance(r["owner"], str)
            or not SESSION.match(r["owner"]) or ".." in r["owner"] or not isinstance(r["storage"], str)
            or not os.path.isabs(r["storage"])):
        sys.exit(1)
    out(r["owner"], r["storage"])


def record_write(path, owner, storage, source):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    atomic(path, {"owner": owner, "storage": storage, "from": source})


def restore_errors(path):
    """How far the restore log is from today's expected error multiset (0 = exactly it)."""
    with open(path, errors="replace") as f:
        found = (re.search(r"\b(ERROR|FATAL|PANIC):\s*(.*)$", line) for line in f.read().splitlines())
    actual = collections.Counter("%s: %s" % (m.group(1), " ".join(m.group(2).split())) for m in found if m)
    out(sum(((actual - EXPECTED) + (EXPECTED - actual)).values()))


def scrub(path, secret):
    with open(path, errors="replace") as f:
        text = f.read()
    if secret in text:
        with open(path, "w") as f:
            f.write(text.replace(secret, "<local connection>"))


def realpath(path):
    out(os.path.realpath(path))


COMMANDS = {"judge": judge, "sha": sha, "receipt": receipt, "receipt-read": receipt_read, "forget": forget,
            "unlink": unlink, "record-owner": record_owner, "record-held": record_held, "record-read": record_read,
            "record-write": record_write,
            "restore-errors": restore_errors, "scrub": scrub, "realpath": realpath}
try:
    COMMANDS[sys.argv[1]](*sys.argv[2:])
except (OSError, ValueError, KeyError, TypeError, IndexError):
    sys.exit(1)
KYPY
}

env_check() {   # env_check [scratch]: ENV_WHY says why the environment cannot be used (empty = usable); sets R. Reads only.
  local v; ENV_WHY=""
  case "$KY_RUN" in /*) ;; *) ENV_WHY="KY_RUN is not an absolute path"; return;; esac
  for v in "${KY_DOCKER:-}" "${KY_PSQL:-}" "${KY_PG_DUMP:-}" "${KY_NPX:-}" "${KY_PGENV:-}"; do
    case "$v" in ""|/*) ;; *) ENV_WHY="a KY_DOCKER, KY_PSQL, KY_PG_DUMP, KY_NPX or KY_PGENV override is not an absolute path"; return;; esac
  done
  case "$PORT" in ""|*[!0-9]*|??????*) ENV_WHY="KY_PG_PORT is not a port"; return;; esac
  if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then ENV_WHY="KY_PG_PORT is not a port"; return; fi
  [ -n "$PY" ] || { ENV_WHY="python3 was not found"; return; }
  [ "${1:-}" = scratch ] || return 0
  case "${KY_SCRATCH:-}" in /*) ;; *) ENV_WHY="KY_SCRATCH is unset or not an absolute path"; return;; esac
  [ -d "$KY_SCRATCH" ] || { ENV_WHY="KY_SCRATCH is not an existing directory"; return; }
  R="$(cd "$KY_SCRATCH" 2>/dev/null && pwd -P)" || { R=""; ENV_WHY="KY_SCRATCH cannot be resolved"; return; }
  case "$R" in *,*|*\"*|*"$NL"*) ENV_WHY="the KY_SCRATCH realpath holds a comma, quote or newline"; return;; esac
}

pool() { local v; [ -f "$1" ] && [ -r "$1" ] || return 1; v="$(cat "$1" 2>/dev/null)" || return 1; case "$v" in [1-8]) printf '%s' "$v";; *) return 1;; esac; }
slot_list() {   # all or nothing: both pool files are read before a line is printed
  local n m i; case "$KY_RUN" in /*) ;; *) return 1;; esac
  n="$(pool "$KY_RUN/KY_WORKERS")" || return 1; m="$(pool "$KY_RUN/KY_VERIFIERS")" || return 1
  i=1; while [ "$i" -le "$n" ]; do echo "b$i"; i=$((i + 1)); done
  i=1; while [ "$i" -le "$m" ]; do echo "v$i"; i=$((i + 1)); done
}
slot_configured() { local l; l="$(slot_list 2>/dev/null)" || return 1; case "$NL$l$NL" in *"$NL$1$NL"*) return 0;; esac; return 1; }

# psql against the loopback server. The password is this throwaway container's own and goes to this child alone.
pg() { PGPASSWORD="$PW" "$PSQL" -X -h 127.0.0.1 -p "$PORT" -U postgres "$@" </dev/null; }
wait_server() { local i; for i in $(seq 1 30); do pg -d postgres -At -c 'select 1' >/dev/null 2>&1 && return 0; sleep 1; done; return 1; }

observe() {   # what docker says about ky-pg now: C_STATE = absent | present | unobservable, and, when present, its judgement
  local ids json out
  C_STATE=unobservable; C_OK=""; C_WHY=""; C_ID=""; C_RUNNING=""; C_LABEL=""; C_MOUNT=""; C_STORE=""; C_REMOVING=""
  ids="$("$DOCKER" ps -a --no-trunc --filter "name=^/${CONT}\$" --format '{{.ID}}' 2>/dev/null </dev/null)" || return 0
  if [ -z "$ids" ]; then
    C_STATE=absent
    # Only a proven removal or a name-conflict path asks for the optional lookup:
    # Docker may omit a removing container from ps while still reserving its name.
    [ -n "${1:-}" ] || return 0
    ids="$1"
  fi
  case "$ids" in *"$NL"*) return 0;; esac
  json="$("$DOCKER" inspect --type container --format '{{json .}}' "$ids" 2>/dev/null </dev/null)" || return 0
  out="$(printf '%s' "$json" | py judge "$R" "$PORT" "$IMAGE" "$PGDATA_DIR")" || return 0
  { IFS= read -r C_OK; IFS= read -r C_WHY; IFS= read -r C_ID; IFS= read -r C_RUNNING; IFS= read -r C_LABEL
    IFS= read -r C_MOUNT; IFS= read -r C_STORE; IFS= read -r C_REMOVING; } <<EOF
$out
EOF
  [ -n "$C_ID" ] && C_STATE=present
  return 0
}
report_incompatible() { note "$CONT INCOMPATIBLE: $C_WHY — preserved and reported: no stop, rm or rename"; }

LIST_SQL="select d.datname, coalesce(pg_catalog.shobj_description(d.oid, 'pg_database'), '') from pg_catalog.pg_database d where not d.datistemplate and d.datname <> 'postgres' order by 1"
list_dbs() { DBS="$(pg -d postgres -At -F "$TAB" -c "$LIST_SQL" 2>/dev/null)" || { DBS=""; return 1; }; }
mark_session() { local s="${1#ky.session=}"; [ "$s" != "$1" ] && valid_session "$s" && printf '%s' "$s"; }
db_mark() {   # db_mark <database>: its comment as last listed; 1 when the database is not there
  local name mark
  while IFS="$TAB" read -r name mark; do if [ "$name" = "$1" ]; then printf '%s' "$mark"; return 0; fi; done <<EOF
$DBS
EOF
  return 1
}
sort_dbs() {   # the last listing, seen from S: OWN (databases), OTHERS (sessions), UNMARKED (databases); newline-ended
  local name mark t; OWN=""; OTHERS=""; UNMARKED=""
  while IFS="$TAB" read -r name mark; do
    [ -n "$name" ] || continue
    if t="$(mark_session "$mark")"; then if [ "$t" = "$S" ]; then OWN="$OWN$name$NL"; else OTHERS="$OTHERS$t$NL"; fi
    else UNMARKED="$UNMARKED$name$NL"; fi
  done <<EOF
$DBS
EOF
  [ -z "$OTHERS" ] || OTHERS="$(printf '%s' "$OTHERS" | sort -u)$NL"
}

present_path() { [ -e "$1" ] || [ -L "$1" ]; }
read_record() {   # REC_OWNER REC_STORAGE from a well-formed hand-over record; 1 when there is none to read
  local out; REC_OWNER=""; REC_STORAGE=""
  out="$(py record-read "$1" 2>/dev/null)" || return 1
  { IFS= read -r REC_OWNER; IFS= read -r REC_STORAGE; } <<EOF
$out
EOF
  return 0
}

wait_previous_removal() {
  local id0="$C_ID" store="$C_STORE" rec="$KY_RUN/local_db/container.json" owner="" i=0
  [ "$C_OK" = compatible ] && [ "$C_REMOVING" = true ] || return 1
  if read_record "$rec" && [ "$REC_STORAGE" = "$store" ]; then owner="$REC_OWNER"; fi
  # (I) INTERPRETATION: ten one-second intervals are a bounded teardown grace, only after Docker
  # proves this exact compatible container is being removed. No foreign storage is deleted.
  while :; do
    if [ "$C_STATE" = unobservable ]; then note "docker cannot be observed during removal"; return 1; fi
    if [ "$C_STATE" = present ]; then
      if [ "$C_OK" != compatible ]; then report_incompatible; return 2; fi
      [ "$C_ID" = "$id0" ] && [ "$C_REMOVING" = true ] || { note "the container changed during removal"; return 1; }
    elif [ -z "$owner" ] || ! present_path "$rec"; then
      return 0
    else
      read_record "$rec" && [ "$REC_STORAGE" = "$store" ] && [ "$REC_OWNER" = "$owner" ] \
        || { note "refused: the hand-over record changed during removal; nothing changed"; return 2; }
      ! present_path "$store" && return 0
    fi
    [ "$i" -lt 10 ] || { note "$CONT removal or its hand-over cleanup did not finish after ten one-second waits"; return 1; }
    sleep 1; i=$((i + 1)); observe "$id0"
  done
}

ensure_up() {   # 0 = a compatible ky-pg is running and its server answers; 1 = not observed; 2 = refused, nothing changed
  local want="$R/db/$S/pgdata" rec="$KY_RUN/local_db/container.json" held="" p err
  observe
  if [ "$C_STATE" = unobservable ]; then note "docker cannot be observed"; return 1; fi
  if [ "$C_STATE" = absent ]; then
    # a hand-over record outlives its container while the storage it names exists: that storage is its owner's to remove
    if present_path "$rec"; then
      read_record "$rec" || { note "refused: the hand-over record $rec cannot be read — whose storage it names cannot be known; nothing changed"; return 2; }
      if present_path "$REC_STORAGE"; then
        [ "$REC_OWNER" = "$S" ] || { note "refused: $REC_STORAGE is on record as session $REC_OWNER's storage (handed over from a container that is gone); close --session $REC_OWNER removes it; nothing changed"; return 2; }
        held="$REC_STORAGE"
      fi
    fi
    for p in "$R/db" "$R/db/$S" "$want"; do
      if [ -L "$p" ] || { [ -e "$p" ] && [ ! -d "$p" ]; }; then note "refused: $p is not a plain directory under the scratch root"; return 2; fi
    done
    if [ -n "$held" ]; then
      remove_storage "$held"
      ! present_path "$held" || { note "the storage $held on record as this session's could not be removed"; return 1; }
    fi
    py unlink "$rec"                                      # its container is gone and so is the storage it names
    ! present_path "$rec" || { note "the hand-over record $rec could not be removed"; return 1; }
    mkdir -p "$want" || return 1
    if ! err="$("$DOCKER" run -d --name "$CONT" --label campaign=kalayantra --label "ky.session=$S" -e "POSTGRES_PASSWORD=$PW" \
           -p "127.0.0.1:$PORT:5432" --mount "type=bind,source=$want,target=$PGDATA_DIR" "$IMAGE" 2>&1 >/dev/null </dev/null)"; then
      case "$err" in *'container name '*"$CONT"*'already in use'*)
        observe "$CONT"
        if [ "$C_STATE" = present ] && [ "$C_OK" != compatible ]; then report_incompatible; return 2; fi
        if [ "${1:-0}" = 0 ] && [ "$C_STATE" = present ] && [ "$C_OK" = compatible ] && [ "$C_REMOVING" = true ]; then
          wait_previous_removal || return $?
          ensure_up 1; return $?
        fi ;;
      esac
      note "docker run failed: $(printf '%s' "$err" | head -1)"; return 1
    fi
    observe
    if [ "$C_STATE" != present ] || [ "$C_OK" != compatible ] || [ "$C_MOUNT" != "$want" ] || [ "$C_LABEL" != "$S" ]; then
      note "the container just started is not the one asked for${C_WHY:+: $C_WHY}"; return 1; fi
  else
    if [ "$C_OK" != compatible ]; then report_incompatible; return 2; fi
    if [ "$C_REMOVING" = true ]; then
      [ "${1:-0}" = 0 ] || { note "$CONT is still being removed after the bounded wait"; return 1; }
      wait_previous_removal || return $?
      ensure_up 1; return $?
    fi
    if [ "$C_RUNNING" != true ]; then "$DOCKER" start "$C_ID" >/dev/null 2>&1 </dev/null || { note "the container could not be started"; return 1; }; fi
  fi
  wait_server || { note "the database server did not answer"; return 1; }
}

cmd_up() {
  local rc; ensure_up; rc=$?; [ "$rc" -eq 0 ] || return "$rc"
  echo "$CONT up: id=$(printf '%s' "$C_ID" | cut -c1-12) session=$C_LABEL mount=$C_MOUNT port=$PORT"
}

write_receipt() {   # write_receipt <slot> <READY|FAILED> <reason>
  mkdir -p "$KY_RUN/local_db" 2>/dev/null || return 1
  py receipt "$KY_RUN/local_db/$1.json" "$1" "ky_$1" "$2" "$3" "$S" "$CONT" "$C_ID" "$IMAGE" "$PORT" "$C_MOUNT" "$H1" "$H2" "$H3" \
     "$RUNNER_RC" "$TABLES" "$KALA" "$LEDGER" "$UNEXP" "$(tool_path "$DOCKER")" "$(tool_path "$PSQL")" "$(tool_path "$PG_DUMP")" \
     "$(tool_path "$NPX")" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
failed() {   # failed <slot> <reason>: the slot is S's to speak for — a FAILED receipt, the line, exit 1
  write_receipt "$1" FAILED "$2" || note "the receipt could not be written"
  echo "ky_$1 FAILED: $2 (receipt $KY_RUN/local_db/$1.json)"; exit 1
}
seed_hashes() {   # H1 H2 H3 = sha256 of the three seed files as they are now; all empty when one cannot be read
  local out; H1=""; H2=""; H3=""
  out="$(py sha "$1/prod_schema.sql" "$1/migrations_applied_data.sql" "$1/asset_registry_data.sql" 2>/dev/null)" || return 1
  { IFS= read -r H1; IFS= read -r H2; IFS= read -r H3; } <<EOF
$out
EOF
  [ -n "$H1" ] && [ -n "$H2" ] && [ -n "$H3" ]
}
read_receipt() {   # RC_* from a ky.slot_db/1 receipt; 1 when there is none to read
  local out; RC_RESULT=""; RC_SESSION=""; RC_CID=""; RC_MOUNT=""; RC_H1=""; RC_H2=""; RC_H3=""; RC_SLOT=""; RC_DB=""
  out="$(py receipt-read "$1" 2>/dev/null)" || return 1
  { IFS= read -r RC_RESULT; IFS= read -r RC_SESSION; IFS= read -r RC_CID; IFS= read -r RC_MOUNT; IFS= read -r RC_H1
    IFS= read -r RC_H2; IFS= read -r RC_H3; IFS= read -r RC_SLOT; IFS= read -r RC_DB; } <<EOF
$out
EOF
  return 0
}
count() { local v; v="$(pg -d "$1" -At -c "$2" 2>/dev/null)" || return 0; case "$v" in ""|*[!0-9]*) ;; *) printf '%s' "$v";; esac; }

# MIGRATE_APPLY_PROTECTED=1: slot databases are loopback superuser rehearsal DBs, so the runner also applies the Kāla
# protected-window files (platform/scripts/kala_protected_migrations.txt) that production applies only via kala_schema_migration=true.
cmd_db() {   # cmd_db <slot> <db|reset>
  local slot="$1" how="$2" db="ky_$1" rcpt="$KY_RUN/local_db/$1.json" D="$KY_RUN/schema" rlog="$R/db/_ky_$1.restore.log"
  local runlog="$R/db/_ky_$1.runner.log" url="postgresql://postgres:$PW@127.0.0.1:$PORT/ky_$1" rc mark owner f state=absent id0 mount0 why=""
  RUNNER_RC=""; TABLES=""; KALA=""; LEDGER=""; UNEXP=""; H1=""; H2=""; H3=""
  ensure_up; rc=$?
  [ "$rc" -ne 2 ] || exit 2
  [ "$rc" -eq 0 ] || { echo "ky_$slot FAILED: the container or its server could not be observed"; exit 1; }
  list_dbs || { echo "ky_$slot FAILED: the server did not list its databases"; exit 1; }
  if mark="$(db_mark "$db")"; then
    owner="$(mark_session "$mark")" || refuse "$db exists without a valid session mark: whose it is cannot be known; nothing changed"
    [ "$owner" = "$S" ] || refuse "$db belongs to session $owner; nothing changed"
    state=own
  fi
  for f in prod_schema.sql migrations_applied_data.sql asset_registry_data.sql; do
    [ -s "$D/$f" ] || failed "$slot" "seed file $f is missing or empty under $D (an operator or executor prerequisite: seed)"
  done
  seed_hashes "$D" || failed "$slot" "a seed file could not be read"
  mkdir -p "$R/db" || failed "$slot" "the log directory $R/db could not be made"
  if [ "$state" = own ] && [ "$how" = db ]; then   # an existing database is trusted only on its own bound receipt
    read_receipt "$rcpt" && [ "$RC_RESULT" = READY ] && [ "$RC_SLOT" = "$slot" ] && [ "$RC_DB" = "$db" ] && [ "$RC_SESSION" = "$S" ] \
      && [ "$RC_CID" = "$C_ID" ] && [ "$RC_MOUNT" = "$C_MOUNT" ] && [ "$RC_H1" = "$H1" ] && [ "$RC_H2" = "$H2" ] && [ "$RC_H3" = "$H3" ] \
      || failed "$slot" "restore provenance missing or changed (no proven receipt of this session, container and seed) — run: local_db.sh reset $slot --session $S"
  else
    py unlink "$rcpt"                                # a restore in progress has no receipt; only a proven one writes it
    [ ! -e "$rcpt" ] || { echo "ky_$slot FAILED: the old receipt could not be removed"; exit 1; }
    if [ "$state" = own ]; then
      pg -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"$db\" WITH (FORCE);" >/dev/null 2>&1
      list_dbs && ! db_mark "$db" >/dev/null || failed "$slot" "the old database could not be dropped"
    fi
    pg -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$db\";" >/dev/null 2>&1 || failed "$slot" "the database could not be created"
    if ! pg -d postgres -v ON_ERROR_STOP=1 -c "COMMENT ON DATABASE \"$db\" IS 'ky.session=$S';" >/dev/null 2>&1; then
      pg -d postgres -c "DROP DATABASE IF EXISTS \"$db\" WITH (FORCE);" >/dev/null 2>&1   # created here, a moment ago: ours to take back
      failed "$slot" "the database could not be marked with its session"
    fi
    pg -d "$db" -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS vector;' -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto;' -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;' \
       -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' -c 'CREATE EXTENSION IF NOT EXISTS btree_gist;' >/dev/null 2>&1 || failed "$slot" "an extension could not be created"
    set --
    for f in role_sidecar role_jobs data_plane_builder role_orchestrator role_mcp_reader role_portal_reader role_pipeline_reader verifier_principal gochara_sealer role_web_serve role_ledger_write amjis_app anon authenticated service_role; do
      set -- "$@" -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$f') THEN CREATE ROLE $f NOLOGIN; END IF; END \$\$;"
    done
    pg -d "$db" "$@" >/dev/null 2>&1 || true
    # psql exits 0 on statement errors (they are judged exactly, below) and non-zero on a connection or process failure (fatal here)
    : > "$rlog" || failed "$slot" "the restore log $rlog could not be written"
    for f in prod_schema.sql migrations_applied_data.sql asset_registry_data.sql; do
      pg -d "$db" -q -f "$D/$f" >> "$rlog" 2>&1 || failed "$slot" "the restore of $f did not complete (log $rlog)"
    done
  fi
  id0="$C_ID"; mount0="$C_MOUNT"
  ( cd "$SRC/platform" && DATABASE_URL="$url" MIGRATE_APPLY_PROTECTED=1 "$NPX" tsx scripts/migrate.ts ) > "$runlog" 2>&1 </dev/null; RUNNER_RC=$?
  py scrub "$runlog" "$url"
  TABLES="$(count "$db" "select count(*) from pg_tables where schemaname='public'")"
  KALA="$(count "$db" "select count(*) from pg_tables where schemaname='public' and (tablename like 'kala_%' or tablename like 'ka_gochara%')")"
  LEDGER="$(count "$db" 'select count(*) from _migrations_applied')"
  UNEXP="$(py restore-errors "$rlog" 2>/dev/null)" || UNEXP=""
  [ "$RUNNER_RC" -eq 0 ] || why="$why; the migration runner exited $RUNNER_RC (log $runlog)"
  [ -n "$TABLES" ] && [ "$TABLES" -ge "$FLOOR_TABLES" ] || why="$why; tables=${TABLES:-unknown}, floor $FLOOR_TABLES"
  [ -n "$KALA" ] && [ "$KALA" -ge "$FLOOR_KALA" ] || why="$why; kala_tables=${KALA:-unknown}, floor $FLOOR_KALA"
  [ -n "$LEDGER" ] && [ "$LEDGER" -ge "$FLOOR_LEDGER" ] || why="$why; ledger=${LEDGER:-unknown}, floor $FLOOR_LEDGER"
  [ "$UNEXP" = 0 ] || why="$why; restore errors are not today's expected set (${UNEXP:-unknown} off, log $rlog)"
  observe                                            # the mount and the session mark, seen again after the work
  [ "$C_STATE" = present ] && [ "$C_OK" = compatible ] && [ "$C_RUNNING" = true ] && [ "$C_ID" = "$id0" ] && [ "$C_MOUNT" = "$mount0" ] \
    || why="$why; the container or its mount is no longer the one this started on"
  list_dbs && [ "$(db_mark "$db")" = "ky.session=$S" ] || why="$why; the database's session mark could not be verified"
  [ -z "$why" ] || failed "$slot" "${why#; }"
  write_receipt "$slot" READY "every condition observed in this invocation" || { echo "ky_$slot FAILED: the receipt could not be written"; exit 1; }
  echo "ky_$slot READY: tables=$TABLES kala_tables=$KALA ledger=$LEDGER unexpected_restore_errors=$UNEXP runner_rc=$RUNNER_RC (receipt $rcpt)"
}

cmd_check() {   # read-only: no start, no write
  local slot="$1" db="ky_$1" rcpt="$KY_RUN/local_db/$1.json" D="$KY_RUN/schema" mark H1 H2 H3
  stale() { echo "ky_$slot STALE: $1"; exit 1; }
  env_check scratch; [ -z "$ENV_WHY" ] || stale "$ENV_WHY"
  slot_configured "$slot" || stale "the slot is not configured (KY_WORKERS, KY_VERIFIERS)"
  read_receipt "$rcpt" || stale "no readable ky.slot_db/1 receipt at $rcpt"
  [ "$RC_RESULT" = READY ] || stale "the receipt does not record a proven database"
  [ "$RC_SLOT" = "$slot" ] && [ "$RC_DB" = "$db" ] || stale "the receipt is another slot's"
  valid_session "$RC_SESSION" || stale "the receipt names no valid session"
  observe
  [ "$C_STATE" != unobservable ] || stale "docker cannot be observed"
  [ "$C_STATE" = present ] || stale "the container is absent"
  [ "$C_OK" = compatible ] || stale "the container is not a slot container: $C_WHY"
  [ "$C_RUNNING" = true ] || stale "the container is not running"
  [ "$C_ID" = "$RC_CID" ] || stale "the container is not the one in the receipt"
  [ "$C_MOUNT" = "$RC_MOUNT" ] || stale "the mount source is not the one in the receipt"
  seed_hashes "$D" || stale "a seed file cannot be read"
  [ "$H1" = "$RC_H1" ] || stale "the schema seed is not the one in the receipt"
  [ "$H2" = "$RC_H2" ] || stale "the ledger seed is not the one in the receipt"
  [ "$H3" = "$RC_H3" ] || stale "the registry seed is not the one in the receipt"
  list_dbs || stale "the server did not list its databases"
  mark="$(db_mark "$db")" || stale "database $db is absent"
  [ "$mark" = "ky.session=$RC_SESSION" ] || stale "the database's session mark is not the receipt's"
  echo "ky_$slot READY: receipt, container, mount, seed hashes and session mark observed equal now (session $RC_SESSION)"
}

remove_storage() {   # the resolved direct child of R/db that held the bind mount, and nothing else
  local s="$1"
  [ -n "$R" ] && [ -n "$s" ] && [ "${s%/*}" = "$R/db" ] || return 1
  case "${s##*/}" in ""|.|..) return 1;; esac
  [ ! -L "$s" ] || return 1
  [ -e "$s" ] || return 0
  rm -rf -- "$s"
}

close_absent() {   # close_absent <record>: no container — what is left of S is its receipts and its storage: removed, then looked for again
  local rec="$1" own="$R/db/$S" held t left
  left="$(py forget "$KY_RUN/local_db" "$S")" || left=""
  held="$(py record-held "$rec" "$S" 2>/dev/null)" || held=""    # storage a hand-over left to S
  t="$(py record-owner "$rec" "$own" 2>/dev/null)" || t="$S"     # R/db/S on record as handed to another session is no longer S's
  [ "$t" != "$S" ] || remove_storage "$own"
  [ -z "$held" ] || remove_storage "$held"
  [ "$left" = 0 ] || { said 0 receipts_remain; return 1; }
  if [ "$t" = "$S" ] && { [ -e "$own" ] || [ -L "$own" ]; }; then said 0 storage_remains; return 1; fi
  if [ -n "$held" ]; then
    if [ -e "$held" ] || [ -L "$held" ]; then said 0 storage_remains; return 1; fi
    py unlink "$rec"
    [ ! -e "$rec" ] || { said 0 record_remains; return 1; }
  fi
  said 0 absent; return 0
}

settle_outside() {   # settle_outside <store>: with a container present, what S holds outside its store — R/db/S unless it is on
  # record as another session's, and storage on record as S's — removed and seen gone; a record whose storage is gone is
  # discarded. Prints what remains (storage_remains | record_remains) and returns 1, else nothing.
  local store="$1" rec="$KY_RUN/local_db/container.json" own="$R/db/$S" ro="" rs=""
  if read_record "$rec" && [ "$REC_STORAGE" != "$store" ]; then ro="$REC_OWNER"; rs="$REC_STORAGE"; fi
  if [ -n "$rs" ]; then                                 # the record of a container that is gone
    [ "$ro" != "$S" ] || remove_storage "$rs"
    if [ "$ro" = "$S" ] && present_path "$rs"; then echo storage_remains; return 1; fi
    if ! present_path "$rs"; then py unlink "$rec"; ! present_path "$rec" || { echo record_remains; return 1; }; fi
  fi
  if [ "$own" != "$store" ] && { [ "$rs" != "$own" ] || [ "$ro" = "$S" ]; }; then
    remove_storage "$own"
    ! present_path "$own" || { echo storage_remains; return 1; }
  fi
  return 0
}

cmd_close() {
  local n=0 before left id0 store owner back why t="" db q='"' rec="$KY_RUN/local_db/container.json"
  said() { echo "close session=$S dropped=$1 container=$2"; }
  observe
  if [ "$C_STATE" = unobservable ]; then note "docker cannot be observed"; said 0 unobservable; return 1; fi
  if [ "$C_STATE" = absent ]; then close_absent "$rec"; return $?; fi
  if [ "$C_OK" != compatible ]; then report_incompatible; said 0 incompatible; return 0; fi
  id0="$C_ID"; store="$C_STORE"
  [ "$C_RUNNING" = true ] || "$DOCKER" start "$C_ID" >/dev/null 2>&1 </dev/null     # a stopped server cannot say whose databases it holds
  if ! wait_server || ! list_dbs; then note "the database server did not answer"; said 0 unobservable; return 1; fi
  sort_dbs
  if [ -n "$UNMARKED" ]; then
    note "foreign database(s) without a session mark — nothing removed, nothing handed over: $(printf '%s' "$UNMARKED" | tr '\n' ' ')"
    said 0 unmarked_database; return 1
  fi
  before="$(lines "$OWN")"
  while IFS= read -r db; do
    [ -n "$db" ] || continue
    pg -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $q${db//$q/$q$q}$q WITH (FORCE);" >/dev/null 2>&1
  done <<EOF
$OWN
EOF
  if ! list_dbs; then said 0 unobservable; return 1; fi
  sort_dbs; left="$(lines "$OWN")"; n=$((before - left))
  [ "$left" -eq 0 ] || { said "$n" databases_remain; return 1; }
  [ "$(py forget "$KY_RUN/local_db" "$S")" = 0 ] || { said "$n" receipts_remain; return 1; }
  if [ -z "$OTHERS" ]; then                           # no other session's database remains: the container and its storage go
    "$DOCKER" stop "$id0" >/dev/null 2>&1 </dev/null; "$DOCKER" rm "$id0" >/dev/null 2>&1 </dev/null
    observe
    [ "$C_STATE" = absent ] || { said "$n" not_removed; return 1; }
    remove_storage "$store"
    if [ -e "$store" ] || [ -L "$store" ] || [ -z "$store" ]; then said "$n" storage_remains; return 1; fi
    why="$(settle_outside "$store")" || { said "$n" "$why"; return 1; }
    # a record still naming storage that exists is another session's obligation and stays; any other record goes
    if ! { read_record "$rec" && [ "$REC_OWNER" != "$S" ] && present_path "$REC_STORAGE"; }; then
      py unlink "$rec"
      [ ! -e "$rec" ] || { said "$n" record_remains; return 1; }
    fi
    said "$n" removed; return 0
  fi
  why="$(settle_outside "$store")" || { said "$n" "$why"; return 1; }
  if read_record "$rec" && [ "$REC_STORAGE" != "$store" ]; then   # never overwrite another session's record of storage still there
    note "$rec records $REC_STORAGE as session $REC_OWNER's storage: the hand-over cannot be recorded until $REC_OWNER closes"
    said "$n" handover_unrecorded; return 1
  fi
  # both pass to a remaining session: the present owner if it is one of them, else the first
  owner="$(py record-owner "$rec" "$store" 2>/dev/null)" || owner="$C_LABEL"
  case "$NL$OTHERS" in *"$NL$owner$NL"*) t="$owner";; *) t="$(printf '%s' "$OTHERS" | head -1)";; esac
  py record-write "$rec" "$t" "$store" "$S" 2>/dev/null
  observe; back="$(py record-owner "$rec" "$store" 2>/dev/null)" || back=""
  if [ "$C_STATE" = present ] && [ "$C_OK" = compatible ] && [ "$C_ID" = "$id0" ] && [ -n "$t" ] && [ "$back" = "$t" ]; then said "$n" handed_over; return 0; fi
  said "$n" handover_unrecorded; return 1
}

cmd_down() {
  observe
  if [ "$C_STATE" = unobservable ]; then note "docker cannot be observed"; return 1; fi
  if [ "$C_STATE" = absent ]; then echo "$CONT absent"; return 0; fi
  if [ "$C_OK" != compatible ]; then report_incompatible; return 2; fi
  "$DOCKER" stop "$C_ID" >/dev/null 2>&1 </dev/null
  observe
  [ "$C_STATE" = present ] && [ "$C_RUNNING" = false ] || { note "the container was not seen stopped"; return 1; }
  echo "stopped (container, databases and storage kept; close --session is still owed)"
}

cmd_seed() {
  local pgenv="${KY_PGENV:-$REAL_PGENV}" D="$KY_RUN/schema" W rc f x
  [ -f "$pgenv" ] || { echo "seed FAILED: the settings file is missing"; return 1; }
  mkdir -p "$D" "$R/db" && W="$(mktemp -d "$D/.seed.XXXXXX")" || { echo "seed FAILED: $D or $R/db cannot be written"; return 1; }
  SEED_TMP="$W"; trap '[ -z "$SEED_TMP" ] || rm -rf -- "$SEED_TMP"' EXIT      # an interrupted seed leaves no half-written dump behind
  # the settings live in this subshell only, and reach nothing but its pg_dump children
  ( set +u; . "$pgenv" >/dev/null 2>&1 || exit 2
    EXCL=(); ok=0
    for i in $(seq 1 40); do args=(); for t in "${EXCL[@]}"; do args+=(-T "$t"); done
      if "$PG_DUMP" --schema-only --no-owner --no-privileges --no-comments -n public "${args[@]}" -f "$W/prod_schema.sql" 2>"$R/db/_seed.pg_dump.err"; then ok=1; break; fi
      t="$(grep -oE 'permission denied for (table|sequence|view|materialized view) [a-zA-Z0-9_]+' "$R/db/_seed.pg_dump.err" | head -1 | awk '{print $NF}')"
      [ -n "$t" ] || exit 3; EXCL+=("public.$t"); done
    [ "$ok" = 1 ] || exit 3
    : > "$W/excluded_tables.txt"; for t in "${EXCL[@]}"; do printf '%s\n' "$t" >> "$W/excluded_tables.txt"; done
    "$PG_DUMP" --data-only --no-owner --no-privileges -t public._migrations_applied -f "$W/migrations_applied_data.sql" 2>"$R/db/_seed.pg_dump_applied.err" || exit 4
    # the asset registry rows (reference config, no secrets): migrations that guard on a registry row (integrity_check_sql,
    # writer registration) fail on a structure-only seed otherwise (K2-1b 1339, 2026-10-09; 1320/1333/1335 before it)
    "$PG_DUMP" --data-only --no-owner --no-privileges -t public.asset_registry -f "$W/asset_registry_data.sql" 2>"$R/db/_seed.pg_dump_registry.err" || exit 5
  ) </dev/null; rc=$?
  case "$rc" in 0) ;; 2) f="the settings file could not be applied";; 3) f="the schema dump failed (log $R/db/_seed.pg_dump.err)";;
    4) f="the ledger dump failed (log $R/db/_seed.pg_dump_applied.err)";; *) f="the registry dump failed (log $R/db/_seed.pg_dump_registry.err)";; esac
  if [ "$rc" -eq 0 ]; then f=""; for x in prod_schema.sql migrations_applied_data.sql asset_registry_data.sql; do [ -s "$W/$x" ] || f="the dump $x is missing or empty"; done; fi
  if [ -n "$f" ]; then rm -rf -- "$W"; echo "seed FAILED: $f; the files under $D are unchanged"; return 1; fi
  for f in prod_schema.sql migrations_applied_data.sql asset_registry_data.sql excluded_tables.txt; do
    mv -f "$W/$f" "$D/$f" || { rm -rf -- "$W"; echo "seed FAILED: $D/$f could not be replaced"; return 1; }
  done
  rm -rf -- "$W"; date -u +%Y-%m-%dT%H:%M:%SZ > "$D/SEEDED_AT"
  seed_hashes "$D" || { echo "seed FAILED: the files written under $D cannot be read back"; return 1; }
  echo "seed ready: tables=$(grep -c 'CREATE TABLE' "$D/prod_schema.sql") excluded=$(wc -l < "$D/excluded_tables.txt" | tr -d ' ') ($D/excluded_tables.txt)" \
       "schema_sha256=$H1 ledger_sha256=$H2 registry_sha256=$H3"
}

cmd="${1:-}"; [ $# -eq 0 ] || shift
case "$cmd" in
  slots) [ $# -eq 0 ] || usage; listed="$(slot_list 2>/dev/null)" || exit 1; printf '%s\n' "$listed" ;;
  up|close)
    [ "${1:-}" = "--session" ] && [ $# -le 2 ] || usage
    S="${2-}"; valid_session "$S" || refuse "the session must match $SESSION_RE and hold no '..'"
    env_check scratch; [ -z "$ENV_WHY" ] || refuse "$ENV_WHY"
    "cmd_$cmd" ;;
  db|reset)
    [ $# -ge 2 ] && [ $# -le 3 ] && [ "$2" = "--session" ] || usage
    S="${3-}"; valid_session "$S" || refuse "the session must match $SESSION_RE and hold no '..'"
    valid_slot "$1" || refuse "the slot must be b1..b8 or v1..v8"
    env_check scratch; [ -z "$ENV_WHY" ] || refuse "$ENV_WHY"
    slot_configured "$1" || refuse "slot $1 is not configured (KY_WORKERS, KY_VERIFIERS under $KY_RUN)"
    cmd_db "$1" "$cmd" ;;
  check) [ $# -eq 1 ] || usage; valid_slot "$1" || refuse "the slot must be b1..b8 or v1..v8"; cmd_check "$1" ;;
  down) [ $# -eq 0 ] || usage; env_check scratch; [ -z "$ENV_WHY" ] || refuse "$ENV_WHY"; cmd_down ;;
  seed)
    [ $# -eq 0 ] || usage
    [ -z "${KY_LANE+x}${KY_ITEM+x}${JOB_SCRATCH+x}" ] || refuse "seed reads the production connection settings: it is the operator's or the executor's action, never a job's (KY_LANE, KY_ITEM or JOB_SCRATCH is set; request executor kind local_schema_seed)"
    env_check scratch; [ -z "$ENV_WHY" ] || refuse "$ENV_WHY"
    if [ -n "${KY_PGENV:-}" ] && [ "$(py realpath "$KY_RUN")" = "$(py realpath "$LIVE_RUN")" ]; then refuse "KY_PGENV is a test override: never against $LIVE_RUN"; fi
    cmd_seed ;;
  *) usage ;;
esac
