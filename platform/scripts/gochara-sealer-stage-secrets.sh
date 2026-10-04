#!/usr/bin/env bash
# Act 2b, STEP 1 — run by the steward on the machine that holds the owner's `gh` identity (runbook §2 / act 2b). One executable UNIT with explicit
# exit codes: it generates the sealer's password and writes it TWICE from one variable — (a) the full DSN as the `gochara-seal` environment secret
# GOCHARA_SEALER_DB_URL (the only lasting copy; GitHub secret names cannot contain hyphens and `gh secret set` reads STDIN when --body is omitted), and
# (b) the password alone as the TEMPORARY secret GOCHARA_SEALER_PASSWORD_STAGING in the cutover environment, which the reviewed one-shot workflow's
# `sealer-password` stage reads. (Codex R12-5: the earlier inline wrapper ended in an `echo` and so returned SUCCESS after a failed write.)
#
# EXIT CODES (the CALLER must stop on any non-zero status and must not proceed to step 2):
#   0   both secrets written
#   11  password generation / length check failed            (nothing written)
#   12  the `gochara-seal` secret (a) write failed            (nothing lasting; (a) removal attempted if it may exist)
#   13  the staging secret (b) write failed                   ((a) removed; (b) removal attempted)
#   14  a write failed AND the rollback could not be completed ((a) or (b) may still exist — list the environments' secrets and delete by hand before retrying)
#   2   bad input
# The password is never printed, never in argv, never in a file; it is cleaned up on EVERY exit path.
set -Eeuo pipefail
set +x
umask 077

DSN_TAIL="${DSN_TAIL:?DSN_TAIL (the NON-SECRET @host/db?params tail of the sealer DSN) is required}"
GH_BIN="${GH_BIN:-gh}"
OPENSSL_BIN="${OPENSSL_BIN:-openssl}"
GH_REPO="${GH_REPO:-Marsys-Technologies/Madhav}"
SEAL_ENV="${SEAL_ENV:-gochara-seal}"
STAGING_ENV="${STAGING_ENV:-data-plane-production-cutover}"
SECRET_A=GOCHARA_SEALER_DB_URL
SECRET_B=GOCHARA_SEALER_PASSWORD_STAGING

printf '%s' "$DSN_TAIL" | grep -Eq '^@[A-Za-z0-9._/:%=&?-]+$' || { echo "REFUSED: DSN_TAIL is not a plain @host/db?params string" >&2; exit 2; }
case "${DSN_TAIL#@}" in *@*) echo "REFUSED: DSN_TAIL must not contain a second @ (no credentials)" >&2; exit 2;; esac
# F-R13-7(d): the sealer connects from the GitHub runner through the Cloud SQL Auth Proxy on loopback (gochara-seal-approved.yml), NOT through the Cloud Run /cloudsql socket the
# builder/verifier jobs use — a socket-form tail would be staged and then fail to connect at the first seal.
printf '%s' "$DSN_TAIL" | grep -Eq '^@127\.0\.0\.1:[0-9]{2,5}/[A-Za-z0-9_-]+(\?[A-Za-z0-9._=&-]*)?$' || { echo "REFUSED: the sealer DSN tail must be the runner's loopback proxy form @127.0.0.1:<port>/<db>[?params] (not the Cloud Run /cloudsql socket form)" >&2; exit 2; }

PW=""; DSN=""
attempted_a=0; attempted_b=0
cleanup() {
  local rc=$?
  unset PW DSN
  if [ "$rc" -ne 0 ]; then
    local incomplete=0
    if [ "$attempted_a" = 1 ]; then
      if "$GH_BIN" secret delete "$SECRET_A" --env "$SEAL_ENV" --repo "$GH_REPO" >/dev/null 2>&1; then echo "rolled back: deleted $SECRET_A from $SEAL_ENV" >&2
      else echo "ROLLBACK INCOMPLETE: $SECRET_A may still exist in $SEAL_ENV — check 'gh secret list --env $SEAL_ENV' and delete it by hand" >&2; incomplete=1; fi
    fi
    if [ "$attempted_b" = 1 ]; then
      if "$GH_BIN" secret delete "$SECRET_B" --env "$STAGING_ENV" --repo "$GH_REPO" >/dev/null 2>&1; then echo "rolled back: deleted $SECRET_B from $STAGING_ENV" >&2
      else echo "ROLLBACK INCOMPLETE: $SECRET_B may still exist in $STAGING_ENV — check 'gh secret list --env $STAGING_ENV' and delete it by hand" >&2; incomplete=1; fi
    fi
    [ "$incomplete" = 0 ] || rc=14
    echo "ACT 2b STEP 1 FAILED (exit $rc): do NOT proceed to step 2." >&2
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT HUP

PW="$("$OPENSSL_BIN" rand -hex 48)" || { echo "FAILED: password generation" >&2; exit 11; }
[ "${#PW}" -eq 96 ] || { echo "FAILED: password length" >&2; exit 11; }
DSN="postgresql://gochara_sealer:${PW}${DSN_TAIL}"

attempted_a=1
printf '%s' "$DSN" | "$GH_BIN" secret set "$SECRET_A" --env "$SEAL_ENV" --repo "$GH_REPO" >/dev/null || { echo "FAILED: $SEAL_ENV secret write" >&2; exit 12; }
attempted_b=1
printf '%s' "$PW" | "$GH_BIN" secret set "$SECRET_B" --env "$STAGING_ENV" --repo "$GH_REPO" >/dev/null || { echo "FAILED: staging secret write — rolling back (a)" >&2; exit 13; }

echo "written: $SECRET_A (env $SEAL_ENV) and the TEMPORARY $SECRET_B (env $STAGING_ENV). NEXT: dispatch the one-shot workflow stage sealer-password; then delete $SECRET_B and VERIFY it is absent."
