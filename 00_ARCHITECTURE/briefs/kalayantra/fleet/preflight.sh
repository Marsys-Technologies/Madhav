#!/usr/bin/env bash
# KĀLA-YANTRA preflight v3.0 — changelog: v1.1 (per-lane topology and file-existence checks) replaced by v3.0.
# (plan v2.7 §5 "Preflight v3", §14 B-1/B-2; KU-01 `preflight-v3`; rulings P16, P17).
#   preflight.sh bootstrap   repairs campaign-local dependencies (venv, node modules, ephemeris pins); no smoke, no receipt
#   preflight.sh launch      repairs nothing; removes run/LAUNCH_RECEIPT.json first, then checks, in order: secrets, claude, smoke,
#                            dependencies, tracker, audit, slots; on success only, writes the receipt atomically (the model's B-3
#                            detector reads "mode": "launch"). It is the precondition of INSTALL_RECEIPT.json (B-2).
# One line per check: `ok <name>` or `FAIL <name>: <reason>`. Exit 0 every check ok; 1 a check failed or is unknown; 64 usage.
# A check whose command cannot run, times out, or whose answer cannot be read is FAIL, never ok (root CLAUDE.md §N.8/§N.7.6).
# Smoke is the binary's version check plus the KV-06 launchd qualification check of every installed launch
# configuration; preflight starts no model job. It never writes the audit reconciliation record or its review (ruling P17).
# KV3-PREFLIGHT-VARIANTS: installer step 9 variant names, qualification identity and evidence checks; no new import.
# `ky audit` is read from its standard output only (FAIL lines and the count line). Environment: KY_ROOT, KY_RUN (default $KY_ROOT/run), KY_FLEET (default $KY_ROOT/fleet_live), KY_SCRATCH (for local_db.sh),
# KY_SOURCE_REPO, CLAUDE_BIN, PRAVAHA_URL, SE_EPHE_PATH; tests only: KY_CURL (absolute path), KY_PREFLIGHT_TIMEOUT (seconds).
set -uo pipefail

PY=/opt/homebrew/bin/python3
MIN_CLAUDE=2.1.296
usage() { echo "usage: preflight.sh launch|bootstrap" >&2; exit 64; }
[ $# -eq 1 ] || usage
MODE="$1"
case "$MODE" in launch|bootstrap) ;; *) usage ;; esac

KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_RUN="${KY_RUN:-$KY_ROOT/run}"
KY_FLEET="${KY_FLEET:-$KY_ROOT/fleet_live}"
CAMP="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"
EPHE="${SE_EPHE_PATH:-$KY_ROOT/ephe}"
CLAUDE_BIN="${CLAUDE_BIN:-/Users/Dev/.local/bin/claude}"
PRAVAHA_URL="${PRAVAHA_URL:-http://127.0.0.1:8767}"
for p in "$KY_ROOT" "$KY_RUN" "$KY_FLEET" "$CAMP" "$EPHE"; do
  case "$p" in /*) ;; *) echo "preflight.sh: every path setting must be absolute: $p" >&2; exit 64 ;; esac
done
case "${KY_PREFLIGHT_TIMEOUT:-1}" in ''|*[!0-9]*) echo "preflight.sh: KY_PREFLIGHT_TIMEOUT must be whole seconds" >&2; exit 64 ;; esac
export KY_ROOT KY_RUN KY_FLEET
export KY_SOURCE_REPO="$CAMP"
RECEIPT="$KY_RUN/LAUNCH_RECEIPT.json"
PF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
PINS="$CAMP/platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py"
LOCAL_DB="$KY_FLEET/local_db.sh"

FAILED=0; CHECKS=(); WORK=""; SLOT_SESSION=""; CLOSE_OWED=0; CLOSE_RC=0

# launch first removes the receipt: nothing below may leave an earlier one standing
if [ "$MODE" = launch ]; then
  rm -f "$RECEIPT"
  if [ -e "$RECEIPT" ] || [ -L "$RECEIPT" ]; then echo "FAIL receipt: $RECEIPT cannot be removed"; exit 1; fi
fi

# Everything that needs real parsing lives in one helper: JSON, hashes, versions, bounded child processes.
read -r -d '' PYSRC <<'PYEOF'
import glob, hashlib, json, os, re, sys, time

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SLOT = re.compile(r"^[bv][0-9]+$")
PIN_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1")
SEED = {"schema_sha256": "prod_schema.sql", "ledger_sha256": "migrations_applied_data.sql",
        "registry_sha256": "asset_registry_data.sql"}


def bad(msg):
    print(msg)
    sys.exit(1)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def load_json(path):
    try:
        with open(path, "rb") as f:
            return json.loads(f.read())
    except (OSError, ValueError):
        return None


def dump(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)


def text(path):
    try:
        with open(path, errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def cmd_sha256(path):
    print(sha256_file(path))


def cmd_claude_facts(binpath, version_out, facts_out):
    m = re.search(r"(?<![0-9.])(\d+)\.(\d+)\.(\d+)(?![0-9])", text(version_out))
    if not m:
        bad("no version number in the --version output")
    if tuple(int(x) for x in m.groups()) < (2, 1, 296):
        bad("version %s is below 2.1.296" % m.group(0))
    dump(facts_out, {"path": binpath, "version": m.group(0), "sha256": sha256_file(binpath)})


QUALIFICATION_JOB_ENV = {
    role: {"KY_STREAM": stream, "KY_LANE": lane, "KY_CONTROLLER_ID": "CTL-qualification"}
    for role, stream, lane in (
        ("build", "K", "b1"), ("rework", "K", "b1"), ("verify", "V", "v1"),
        ("artifact", "V", "v1"), ("pre-accept", "V", "v1"), ("post-readback", "V", "v1"),
        ("ruling", "N", "b1"), ("request-prep", "N", "b1"), ("model", "S", "b1"),
        ("plan", "S", "b1"), ("surrogate", "steward", "b1"))
}
# (I) INTERPRETATION: use install.sh step 9's representative b1/v1 qualification
# identity; this check never claims an item. TESTS retains kyqualify's caller/default policy.


def qualification_tag(cfg, doc):
    """Same naming rule as install.sh step 9; tests compare every installed template."""
    name = os.path.basename(cfg)
    if not name.startswith("LAUNCH_CONFIG."):
        return doc["role"]
    match = re.fullmatch(r"LAUNCH_CONFIG\.([a-z][a-z0-9-]*)(\.chart)?(\.tests)?(\.codex)?\.json", name)
    if (not match or match[1] != doc["role"]
            or bool(match[4]) != (doc.get("engine", "claude") == "codex")
            or doc.get("engine", "claude") not in ("claude", "codex")):
        raise ValueError("launch template name disagrees with role/engine: " + cfg)
    return doc["role"] + ("-chart" if match[2] else "") + ("-tests" if match[3] else "")


def cmd_smoke_plan(fleet, run, plan_out):
    """RUN<TAB>config<TAB>receipt<TAB>role<TAB>stream<TAB>lane, or ERR<TAB>message."""
    configs = sorted(glob.glob(os.path.join(fleet, "templates", "LAUNCH_CONFIG.*.json")))
    if not configs:
        print("ERR\tno launch configuration under %s/templates" % fleet)
    entries = []
    for cfg in configs:
        d = load_json(cfg)
        base = os.path.basename(cfg)
        if not isinstance(d, dict) or not all(isinstance(d.get(k), str) and NAME.match(d.get(k, "")) for k in ("role", "model")):
            print("ERR\t%s has no usable role and model" % base)
            continue
        try:
            tag = qualification_tag(cfg, d)
        except ValueError as ex:
            print("ERR\t%s" % ex)
            continue
        identity = QUALIFICATION_JOB_ENV.get(d["role"], {})
        if not identity and any(n in d.get("env_names", []) for n in ("KY_STREAM", "KY_LANE", "KY_CONTROLLER_ID")):
            print("ERR\tno conventional qualification identity for role " + d["role"])
            continue
        receipt = os.path.join(run, "QUALIFICATIONS", "%s-%s.json" % (tag, d["model"]))
        if not os.path.isfile(receipt):
            print("ERR\t%s: no qualification receipt %s" % (d["role"], receipt))
            continue
        entries.append({"role": d["role"], "model": d["model"], "config": cfg, "receipt": receipt,
                        "config_sha256": sha256_file(cfg), "receipt_sha256": sha256_file(receipt)})
        print("RUN\t%s\t%s\t%s\t%s\t%s" % (cfg, receipt, d["role"], identity.get("KY_STREAM", "-"), identity.get("KY_LANE", "-")))
    dump(plan_out, entries)


def cmd_ephe_pin(pins, name):
    m = re.search(r'"%s"\s*:\s*"([0-9a-f]{64})"' % re.escape(name), text(pins))
    if not m:
        bad("no pin for %s in %s" % (name, pins))
    print(m.group(1))


def cmd_ephe_bad(pins, ephe):
    """Print `name<TAB>missing|mismatch` per unusable file; exit 1 with a reason when the pins cannot be read."""
    body = text(pins)
    if not body:
        bad("cannot read %s" % pins)
    for name in PIN_FILES:
        m = re.search(r'"%s"\s*:\s*"([0-9a-f]{64})"' % re.escape(name), body)
        if not m:
            bad("no pin for %s in %s" % (name, pins))
        path = os.path.join(ephe, name)
        if not os.path.isfile(path):
            print("%s\tmissing" % name)
        elif sha256_file(path) != m.group(1):
            print("%s\tmismatch" % name)


def cmd_health(path):
    d = load_json(path)
    if not isinstance(d, dict):
        bad("health answer is not a JSON object")
    if d.get("ok") is not True:
        bad("health does not say ok: true")
    if d.get("model_error"):
        bad("health reports a model_error")


def cmd_audit_parse(stdout_file, facts_out):
    findings, counts, odd = [], [], []
    for line in text(stdout_file).splitlines():
        if line.startswith("FAIL "):
            m = re.match(r"^FAIL (\S+) (\S+?):(?: |$)", line)
            if m:
                findings.append({"code": m.group(1), "ref": m.group(2)})
            else:
                odd.append(line[:80])
        m = re.match(r"^AUDIT FAIL: (\d+) findings?$", line)
        if m:
            counts.append(int(m.group(1)))
    if odd:
        bad("unparseable finding line: %s" % odd[0])
    if len(counts) != 1:
        bad("expected one 'AUDIT FAIL: <n> findings' line, found %d" % len(counts))
    if counts[0] != len(findings):
        bad("the count line says %d findings, %d lines parsed" % (counts[0], len(findings)))
    if not findings:
        bad("exit 1 with no finding lines is unknown")
    dump(facts_out, {"exit": 1, "findings": findings})


def cmd_audit_reconcile(facts_file, recon, review, facts_out):
    facts = load_json(facts_file)
    try:
        with open(recon, "rb") as f:
            raw = f.read()
    except OSError:
        bad("%d findings and no reconciliation record %s" % (len(facts["findings"]), recon))
    rec = None
    try:
        rec = json.loads(raw)
    except ValueError:
        pass
    if not isinstance(rec, dict) or rec.get("schema") != "ky.audit_reconciliation/1" or not isinstance(rec.get("entries"), list):
        bad("reconciliation record is not a ky.audit_reconciliation/1 object with entries")
    pairs, problems = [], []
    for i, e in enumerate(rec["entries"]):
        if not isinstance(e, dict) or not all(isinstance(e.get(k), str) and e[k].strip() for k in ("code", "ref", "disposition", "authority")):
            problems.append("entry %d lacks code, ref, disposition or authority" % i)
            continue
        pairs.append((e["code"], e["ref"]))
    if len(set(pairs)) != len(pairs):
        problems.append("duplicate entries")
    found = {(f["code"], f["ref"]) for f in facts["findings"]}
    for code, ref in sorted(found - set(pairs)):
        problems.append("finding %s %s has no entry" % (code, ref))
    for code, ref in sorted(set(pairs) - found):
        problems.append("entry %s %s has no finding" % (code, ref))
    if problems:
        bad("; ".join(problems))
    digest = sha256_bytes(raw)
    try:
        with open(review, "rb") as f:
            rraw = f.read()
    except OSError:
        bad("record %s is not accepted: no review %s" % (digest[:12], review))
    rev = None
    try:
        rev = json.loads(rraw)
    except ValueError:
        pass
    if not isinstance(rev, dict):
        bad("review is not a JSON object")
    if rev.get("verdict") != "ACCEPTED":
        bad("review verdict is not ACCEPTED")
    if rev.get("inputs") != digest:
        bad("review does not accept the record's current digest %s" % digest)
    r, a = rev.get("reviewer_session_id"), rev.get("author_session_id")
    if not (isinstance(r, str) and r.strip() and isinstance(a, str) and a.strip()):
        bad("review names no reviewer_session_id and author_session_id")
    if r == a:
        bad("reviewer_session_id equals author_session_id: not independent")
    dump(facts_out, {"exit": 1, "findings": facts["findings"], "reconciliation_sha256": digest,
                     "review_sha256": sha256_bytes(rraw)})


def cmd_slots_parse(stdout_file, facts_out):
    slots = text(stdout_file).splitlines()
    if not slots or not all(SLOT.match(s) for s in slots):
        bad("slots output is empty or holds a line that is not b<N>/v<N>")
    if not any(s[0] == "b" for s in slots) or not any(s[0] == "v" for s in slots):
        bad("slots must list at least one b and one v slot")
    dump(facts_out, slots)
    print(slots[0])


def cmd_slot_proof(receipt, slot, session, schema_dir, facts_out):
    r = load_json(receipt)
    if not isinstance(r, dict):
        bad("no readable slot receipt %s" % receipt)
    if r.get("result") != "READY":
        bad("slot receipt result is %r, not READY" % (r.get("result"),))
    if r.get("session_id") != session or r.get("slot") != slot:
        bad("slot receipt is not READY for this slot and session")
    seed = r.get("seed")
    want = {}
    for key, fname in SEED.items():
        p = os.path.join(schema_dir, fname)
        if not os.path.isfile(p) or os.path.getsize(p) == 0:
            bad("seed file %s is missing or empty" % p)
        want[key] = sha256_file(p)
    if not isinstance(seed, dict) or {k: seed.get(k) for k in SEED} != want:
        bad("slot receipt seed hashes differ from the files in %s" % schema_dir)
    dump(facts_out, {"slot": slot, "session": session, "seed": want})


def cmd_receipt(out, work, camp, script):
    def need(name):
        d = load_json(os.path.join(work, name))
        if d is None:
            bad("missing facts %s" % name)
        return d

    claude, plan, audit, slots, proof = need("claude.json"), need("plan.json"), need("audit.json"), need("slots.json"), need("proof.json")
    if not os.path.exists(os.path.join(work, "slot_closed")):
        bad("the slot proof was never closed")
    quals = []
    for q in plan:
        for key, path in (("config_sha256", q["config"]), ("receipt_sha256", q["receipt"])):
            if not os.path.isfile(path) or sha256_file(path) != q[key]:
                bad("%s changed while preflight ran" % path)
        quals.append({k: q[k] for k in ("role", "model", "receipt_sha256", "config_sha256")})
    if not os.path.isfile(claude["path"]) or sha256_file(claude["path"]) != claude["sha256"]:
        bad("%s changed while preflight ran" % claude["path"])
    for key, path in (("reconciliation_sha256", os.environ["KY_RUN"] + "/AUDIT_RECONCILIATION.json"),
                      ("review_sha256", os.environ["KY_RUN"] + "/AUDIT_RECONCILIATION.review.json")):
        if audit.get(key) and sha256_file(path) != audit[key]:
            bad("%s changed while preflight ran" % path)
    proof["closed"] = True
    model = os.path.join(camp, "00_ARCHITECTURE/control/kalayantra/plan_model.json")
    rec = {"schema": "ky.launch_receipt/3", "mode": "launch", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "checks": text(os.path.join(work, "checks.txt")).split(), "slots": slots, "slot_proof": proof,
           "claude": claude, "qualifications": quals,
           "audit": {"exit": audit["exit"], "findings": audit["findings"],
                     "reconciliation_sha256": audit.get("reconciliation_sha256"), "review_sha256": audit.get("review_sha256")},
           "campaign_head": text(os.path.join(work, "head.txt")).strip(),
           "model_sha256": sha256_file(model) if os.path.isfile(model) else None, "preflight_sha256": sha256_file(script)}
    tmp = os.path.join(os.path.dirname(out), ".LAUNCH_RECEIPT.json.%d.tmp" % os.getpid())
    try:
        with open(tmp, "w") as f:
            json.dump(rec, f, indent=1)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, out)
    except OSError as ex:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        bad("cannot write %s: %s" % (out, ex))


if __name__ == "__main__":
    rc = globals()["cmd_" + sys.argv[1].replace("-", "_")](*sys.argv[2:])
    sys.exit(rc if isinstance(rc, int) else 0)
PYEOF

py() { "$PY" -I -B -S -c "$PYSRC" "$@"; }
# bounded <secs> <stdout-file> <stderr-file> cmd... : stdin closed, own process group, group killed on timeout or TERM.
# Exit: the command's, 124 timed out, 127 could not run. (perl: starts in milliseconds; python costs ~0.15 s a call here.)
read -r -d '' BOUNDED_PL <<'PLEOF'
my ($t, $o, $e, @c) = @ARGV;
my $p = fork();
defined $p or exit 127;
if (!$p) {
  setpgrp(0, 0);
  open(STDIN, "<", "/dev/null"); open(STDOUT, ">", $o) or exit 127; open(STDERR, ">", $e) or exit 127;
  { exec { $c[0] } @c; }
  print STDERR "cannot run $c[0]: $!\n"; exit 127;
}
$SIG{ALRM} = sub { kill 9, -$p; waitpid($p, 0); exit 124 };
$SIG{TERM} = sub { kill 9, -$p; waitpid($p, 0); exit 143 };
$SIG{INT}  = sub { kill 9, -$p; waitpid($p, 0); exit 130 };
alarm($t);
waitpid($p, 0);
exit(($? & 127) ? 128 + ($? & 127) : $? >> 8);
PLEOF
bounded() { local secs="${KY_PREFLIGHT_TIMEOUT:-$1}"; shift; /usr/bin/perl -e "$BOUNDED_PL" "$secs" "$@"; }
ok()   { echo "ok $1"; CHECKS+=("ok:$1"); }
fail() { echo "FAIL $1: $(printf '%s' "$2" | LC_ALL=C tr -c '[:print:]' ' ' | cut -c1-500)"; FAILED=1; }
note() { echo "  $1"; }

run_close() {   # one attempt to close the proof session's databases; never repeated
  CLOSE_OWED=0
  bounded 300 "$WORK/close.out" "$WORK/close.err" bash "$LOCAL_DB" close --session "$SLOT_SESSION"; CLOSE_RC=$?
}
on_exit() {
  local rc=$?
  if [ "$CLOSE_OWED" = 1 ] && [ -n "$SLOT_SESSION" ] && [ -n "$WORK" ]; then run_close; fi
  [ -n "$WORK" ] && rm -rf "$WORK"
  exit $rc
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

TBASE=""
for d in "${TMPDIR:-}" "${KY_SCRATCH:-}"; do
  case "$d" in /*) if [ -d "$d" ]; then TBASE="$d"; break; fi ;; esac
done
[ -n "$TBASE" ] || { echo "FAIL tmpdir: neither TMPDIR nor KY_SCRATCH is an existing absolute directory"; exit 1; }
WORK="$(mktemp -d "$TBASE/ky-preflight.XXXXXX")" || { WORK=""; echo "FAIL tmpdir: cannot create a temporary directory under $TBASE"; exit 1; }

curl_bin() { echo "${KY_CURL:-/usr/bin/curl}"; }

# ── 1 secrets ────────────────────────────────────────────────────────────────────────────────────────────────────
check_secrets() {
  local names="" v
  while IFS= read -r v; do
    case "$v" in DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY) names="$names $v"; unset "$v" ;; esac
  done < <(compgen -v)
  if [ -z "$names" ]; then ok secrets; else fail secrets "credential variable names set (values never read):$names"; fi
}

# ── 2 claude ─────────────────────────────────────────────────────────────────────────────────────────────────────
check_claude() {
  local rc reason
  case "$CLAUDE_BIN" in /*) ;; *) fail claude "CLAUDE_BIN is not an absolute path"; return ;; esac
  if [ ! -f "$CLAUDE_BIN" ] || [ ! -x "$CLAUDE_BIN" ]; then fail claude "$CLAUDE_BIN is not an executable file"; return; fi
  bounded 30 "$WORK/claude.out" "$WORK/claude.err" "$CLAUDE_BIN" --version; rc=$?
  [ $rc -eq 0 ] || { fail claude "'$CLAUDE_BIN --version' exit $rc"; return; }
  reason="$(py claude-facts "$CLAUDE_BIN" "$WORK/claude.out" "$WORK/claude.json")" || { fail claude "$reason (need >= $MIN_CLAUDE)"; return; }
  ok claude
}

# ── 3 smoke (installed launch configurations) ────────────────────────────────────────────────────────────────────
check_smoke() {
  local probs="" kind a b role stream lane rc
  if [ ! -f "$KY_FLEET/kyqualify.py" ]; then fail smoke "$KY_FLEET/kyqualify.py is missing"; return; fi
  while IFS=$'\t' read -r kind a b role stream lane; do
    case "$kind" in
      ERR) probs="$probs; $a" ;;
      RUN) if [ "$lane" = - ]; then
             bounded 300 "$WORK/qual.out" "$WORK/qual.err" "$PY" -I -B "$KY_FLEET/kyqualify.py" check "$b" --config "$a" --require-context launchd --verify-evidence
           else
             bounded 300 "$WORK/qual.out" "$WORK/qual.err" env KY_STREAM="$stream" KY_LANE="$lane" KY_CONTROLLER_ID=CTL-qualification \
               "$PY" -I -B "$KY_FLEET/kyqualify.py" check "$b" --config "$a" --require-context launchd --verify-evidence
           fi; rc=$?
           [ $rc -eq 0 ] || probs="$probs; $role: kyqualify check exit $rc" ;;
    esac
  done < <(py smoke-plan "$KY_FLEET" "$KY_RUN" "$WORK/plan.json")
  [ -f "$WORK/plan.json" ] || probs="$probs; the launch-configuration plan could not be built"
  if [ -n "$probs" ]; then fail smoke "${probs#; }"; else ok smoke; fi
}

# ── 4 dependencies (bootstrap repairs first; launch repairs nothing) ─────────────────────────────────────────────
check_dependencies() {
  local probs="" rc reason n
  bounded 30 "$WORK/git.out" "$WORK/git.err" git -C "$CAMP" rev-parse --is-inside-work-tree HEAD; rc=$?
  if [ $rc -ne 0 ] || [ "$(sed -n 1p "$WORK/git.out")" != true ]; then
    probs="$probs; $CAMP is not a git work tree"
  else
    sed -n 2p "$WORK/git.out" > "$WORK/head.txt"
    grep -qE '^[0-9a-f]{40}$' "$WORK/head.txt" || probs="$probs; cannot read the campaign head"
  fi
  if [ ! -x "$KY_ROOT/venv/bin/python" ]; then
    probs="$probs; no $KY_ROOT/venv/bin/python"
  else
    bounded 60 "$WORK/venv.out" "$WORK/venv.err" "$KY_ROOT/venv/bin/python" -c 'import pytest, psycopg, swisseph'; rc=$?
    [ $rc -eq 0 ] || probs="$probs; venv import of pytest, psycopg, swisseph exit $rc"
  fi
  for n in platform platform-mcp; do
    [ -d "$CAMP/$n/node_modules" ] || probs="$probs; no $CAMP/$n/node_modules"
  done
  if reason="$(py ephe-bad "$PINS" "$EPHE")"; then
    [ -z "$reason" ] || probs="$probs; ephemeris: $(printf '%s\n' "$reason" | tr '\t' ' ' | paste -sd, -)"
  else probs="$probs; $reason"; fi
  if [ -n "$probs" ]; then fail dependencies "${probs#; }"; else ok dependencies; fi
}

repair() {   # bootstrap only; every failure is reported and the dependencies check then judges the result
  local n name want tmp
  if [ ! -d "$CAMP" ]; then note "repair skipped: $CAMP does not exist"; return; fi
  if [ ! -x "$KY_ROOT/venv/bin/python" ]; then
    note "repair: creating $KY_ROOT/venv"
    if bounded 600 "$WORK/r.out" "$WORK/r.err" "$PY" -m venv "$KY_ROOT/venv"; then
      for n in requirements.txt requirements-ci.txt; do
        bounded 1800 "$WORK/r.out" "$WORK/r.err" "$KY_ROOT/venv/bin/python" -m pip install --disable-pip-version-check -q \
          -r "$CAMP/platform/python-sidecar/$n" || note "repair: pip install -r $n failed"
      done
    else note "repair: venv creation failed"; fi
  fi
  for n in platform platform-mcp; do
    [ -d "$CAMP/$n/node_modules" ] && continue
    note "repair: npm ci in $CAMP/$n"
    bounded 1800 "$WORK/r.out" "$WORK/r.err" bash -c 'cd "$1" && exec npm ci' _ "$CAMP/$n" || note "repair: npm ci in $n failed"
  done
  mkdir -p "$EPHE" 2>/dev/null
  while IFS=$'\t' read -r name _; do
    [ -n "$name" ] || continue
    want="$(py ephe-pin "$PINS" "$name")" || continue
    tmp="$EPHE/.$name.tmp.$$"
    note "repair: fetching $name"
    if bounded 600 "$WORK/r.out" "$WORK/r.err" "$(curl_bin)" -fsSL -o "$tmp" "https://storage.googleapis.com/madhav-ephemeris/se1/$name" \
       && [ "$(py sha256 "$tmp" 2>/dev/null)" = "$want" ]; then mv -f "$tmp" "$EPHE/$name"
    else rm -f "$tmp"; note "repair: $name did not download to the pinned hash"; fi
  done < <(py ephe-bad "$PINS" "$EPHE")
}

# ── 5 tracker ────────────────────────────────────────────────────────────────────────────────────────────────────
check_tracker() {
  local curl rc reason
  curl="$(curl_bin)"
  case "$curl" in /*) ;; *) fail tracker "KY_CURL is not an absolute path"; return ;; esac
  if [ ! -x "$curl" ]; then fail tracker "$curl is not executable"; return; fi
  bounded 15 "$WORK/health.json" "$WORK/health.err" "$curl" -fsS -m 5 "${PRAVAHA_URL%/}/api/health"; rc=$?
  [ $rc -eq 0 ] || { fail tracker "GET ${PRAVAHA_URL%/}/api/health exit $rc"; return; }
  reason="$(py health "$WORK/health.json")" || { fail tracker "$reason"; return; }
  ok tracker
}

# ── 6 audit (KU-01, rulings P17) ─────────────────────────────────────────────────────────────────────────────────
check_audit() {
  local ky="$KY_ROOT/bin/ky" rc reason
  if [ ! -f "$ky" ] || [ ! -x "$ky" ]; then fail audit "$ky is not an executable file"; return; fi
  bounded 300 "$WORK/audit.out" "$WORK/audit.err" env KY_STREAM=S "$ky" audit --since kickoff; rc=$?
  case $rc in
    0) printf '{"exit": 0, "findings": [], "reconciliation_sha256": null, "review_sha256": null}' > "$WORK/audit.json"; ok audit ;;
    1) grep '^FAIL ' "$WORK/audit.out" | LC_ALL=C tr -c '[:print:]\n' ' ' | sed 's/^/  audit finding: /'
       reason="$(py audit-parse "$WORK/audit.out" "$WORK/audit-found.json")" || { fail audit "ky audit exit 1: $reason"; return; }
       reason="$(py audit-reconcile "$WORK/audit-found.json" "$KY_RUN/AUDIT_RECONCILIATION.json" \
                 "$KY_RUN/AUDIT_RECONCILIATION.review.json" "$WORK/audit.json")" || { fail audit "$reason"; return; }
       ok audit ;;
    *) fail audit "ky audit exit $rc: unavailable" ;;
  esac
}

# ── 7 slots (ruling P16: provisionability, proven on a disposable slot in a session of its own) ──────────────────
slot_step() {   # slot_step <name> <secs> args... ; runs local_db.sh and records the first failing step
  local name="$1" secs="$2" rc; shift 2
  bounded "$secs" "$WORK/step.out" "$WORK/step.err" bash "$LOCAL_DB" "$@"; rc=$?
  [ $rc -eq 0 ] || SLOT_PROBLEM="${SLOT_PROBLEM:-'$name' exit $rc}"
  return $rc
}
check_slots() {
  local rc first reason
  SLOT_PROBLEM=""
  if [ ! -f "$LOCAL_DB" ]; then fail slots "$LOCAL_DB is missing"; return; fi
  bounded 60 "$WORK/slots.out" "$WORK/slots.err" bash "$LOCAL_DB" slots; rc=$?
  [ $rc -eq 0 ] || { fail slots "'slots' exit $rc"; return; }
  first="$(py slots-parse "$WORK/slots.out" "$WORK/slots.json")" || { fail slots "$first"; return; }
  SLOT_SESSION="PREFLIGHT-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  if ! [[ "$SLOT_SESSION" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$ ]]; then fail slots "session name $SLOT_SESSION breaks the LOCALDB grammar"; return; fi
  CLOSE_OWED=1
  if slot_step up 600 up --session "$SLOT_SESSION" \
     && slot_step db 1800 db "$first" --session "$SLOT_SESSION" \
     && slot_step check 120 check "$first"; then
    reason="$(py slot-proof "$KY_RUN/local_db/$first.json" "$first" "$SLOT_SESSION" "$KY_RUN/schema" "$WORK/proof.json")" \
      || SLOT_PROBLEM="slot receipt: $reason"
  fi
  run_close
  if [ "$CLOSE_RC" -ne 0 ]; then SLOT_PROBLEM="${SLOT_PROBLEM:+$SLOT_PROBLEM; }'close' exit $CLOSE_RC (removal not proven)"
  elif [ -e "$KY_RUN/local_db/$first.json" ] || [ -L "$KY_RUN/local_db/$first.json" ]; then
    SLOT_PROBLEM="${SLOT_PROBLEM:+$SLOT_PROBLEM; }slot receipt survives 'close' (removal not proven)"
  else : > "$WORK/slot_closed"; fi
  if [ -n "$SLOT_PROBLEM" ]; then fail slots "$SLOT_PROBLEM"; else ok slots; fi
}

if [ "$MODE" = bootstrap ]; then
  repair
  check_dependencies
else
  check_secrets
  check_claude
  check_smoke
  check_dependencies
  check_tracker
  check_audit
  check_slots
  if [ $FAILED -eq 0 ]; then
    printf '%s\n' "${CHECKS[@]}" > "$WORK/checks.txt"
    reason="$(py receipt "$RECEIPT" "$WORK" "$CAMP" "$PF")" || { fail receipt "$reason"; rm -f "$RECEIPT"; }
  fi
fi
exit $FAILED
