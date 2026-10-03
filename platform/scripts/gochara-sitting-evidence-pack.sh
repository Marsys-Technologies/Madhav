#!/usr/bin/env bash
# gochara-sitting-evidence-pack.sh — Pravāha C43: LOCAL, OFFLINE evidence pack for the steward.
#
#   usage: gochara-sitting-evidence-pack.sh --evidence-dir DIR [--note FILE ...] [--allow-missing PHASE ...]
#
# DIR holds the readback runner's phase folders (pre-window, pre-train, pre-dispatch,
# post-window), each with its MANIFEST.sha256. The pack:
#   1. verifies every phase MANIFEST sha256 against the files present and STOPs on any mismatch
#      or missing phase (unless --allow-missing PHASE is given — recorded in the index);
#   2. writes SITTING_EVIDENCE_INDEX.md listing per phase: check id, status, file, sha256, in
#      the order the runner emitted them (the MANIFEST order), plus the runner script hash when
#      a phase carries a RUNNER_SHA256 file, plus any --note files;
#   3. writes a top-level MANIFEST.sha256 over EVERYTHING under DIR (including the index);
#   4. never opens a network or database connection and never reads environment credentials;
#      it refuses (exit 2) any symlink under DIR that resolves outside DIR, and never hashes
#      through a symlink.
#
# Check id/status: the runner records evidence as <check-id>.<ext>; the id is the file's basename
# minus its extension, the status is STOP/REVIEW when the id is in the phase's .stops/.reviews,
# else PASS. Exit codes: 0 verified · 1 a MANIFEST mismatch or missing phase · 2 usage/refusal.
set -euo pipefail

DIR=""
NOTES=()
ALLOW=()
while [ $# -gt 0 ]; do
  case "$1" in
    --evidence-dir) DIR="${2:?--evidence-dir needs a directory}"; shift ;;
    --note) NOTES+=("${2:?--note needs a file}"); shift ;;
    --allow-missing) ALLOW+=("${2:?--allow-missing needs a phase name}"); shift ;;
    *) echo "usage: $0 --evidence-dir DIR [--note FILE ...] [--allow-missing PHASE ...]" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$DIR" ] && [ -d "$DIR" ] || { echo "REFUSAL: --evidence-dir is not a directory: '${DIR:-<unset>}'" >&2; exit 2; }
DIR="$(cd "$DIR" && pwd -P)"
PHASES=(pre-window pre-train pre-dispatch post-window)

in_allow() { local p; for p in ${ALLOW[@]+"${ALLOW[@]}"}; do [ "$p" = "$1" ] && return 0; done; return 1; }

# No symlink may escape DIR (we never hash through one: only -type f is hashed).
while IFS= read -r link; do
  target="$(cd "$(dirname "$link")" && pwd -P)/$(readlink "$link")"
  target="$(cd "$(dirname "$target")" 2>/dev/null && pwd -P || echo "/nonexistent")/$(basename "$target")"
  case "$target" in
    "$DIR"/*) ;;                                   # stays inside DIR: tolerated, never followed
    *) echo "REFUSAL: symlink escapes --evidence-dir: $link" >&2; exit 2 ;;
  esac
done < <(find "$DIR" -type l)

fails=0
INDEX="$DIR/SITTING_EVIDENCE_INDEX.md"
{
  echo "# Sitting evidence index"
  echo
  echo "Packed: $(date -u +%Y-%m-%dT%H:%M:%SZ) from $DIR"
  for n in ${NOTES[@]+"${NOTES[@]}"}; do
    [ -f "$n" ] || { echo "REFUSAL: --note not found: $n" >&2; exit 2; }
    echo
    echo "## Note: $(basename "$n") (sha256 $(shasum -a 256 "$n" | awk '{print $1}'))"
    echo
    sed 's/^/> /' "$n"
  done
} > "$INDEX"

for phase in "${PHASES[@]}"; do
  pdir="$DIR/$phase"
  {
    echo
    echo "## Phase: $phase"
    echo
  } >> "$INDEX"
  if [ ! -d "$pdir" ]; then
    if in_allow "$phase"; then
      echo "MISSING (allowed by --allow-missing): phase folder absent" >> "$INDEX"
      continue
    fi
    echo "MISSING PHASE: $phase (no folder; use --allow-missing $phase to proceed without it)" >&2
    fails=$((fails + 1))
    continue
  fi
  manifest="$pdir/MANIFEST.sha256"
  if [ ! -f "$manifest" ]; then
    if in_allow "$phase"; then
      echo "MISSING (allowed by --allow-missing): no MANIFEST.sha256" >> "$INDEX"
      continue
    fi
    echo "MISSING PHASE: $phase has no MANIFEST.sha256" >&2
    fails=$((fails + 1))
    continue
  fi
  if [ -f "$pdir/RUNNER_SHA256" ]; then
    echo "runner script sha256: $(head -1 "$pdir/RUNNER_SHA256")" >> "$INDEX"
    echo >> "$INDEX"
  fi
  {
    echo "| check id | status | file | sha256 |"
    echo "|---|---|---|---|"
  } >> "$INDEX"
  # Verify every MANIFEST line against the file present, in emission order; list it in the index.
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    sha="${line%%  *}"; file="${line#*  }"
    fpath="$pdir/$file"
    id="$(basename "$file")"; id="${id%.*}"
    if [ ! -f "$fpath" ]; then
      echo "MANIFEST MISMATCH: $phase/$file is listed but absent" >&2
      fails=$((fails + 1))
      status="MISSING"
      actual="(absent)"
    else
      actual="$(cd "$pdir" && shasum -a 256 "$file" | awk '{print $1}')"
      if [ "$actual" != "$sha" ]; then
        echo "MANIFEST MISMATCH: $phase/$file sha256 $actual != recorded $sha" >&2
        fails=$((fails + 1))
        status="TAMPERED"
      elif grep -qx "$id" "$pdir/.stops" 2>/dev/null; then
        status="STOP"
      elif grep -qx "$id" "$pdir/.reviews" 2>/dev/null; then
        status="REVIEW"
      else
        status="PASS"
      fi
    fi
    echo "| $id | $status | $file | $sha |" >> "$INDEX"
  done < "$manifest"
done

# Top-level manifest over EVERYTHING under DIR (including the index), relative paths, sorted.
( cd "$DIR" && find . -type f ! -path './MANIFEST.sha256' -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 ) > "$DIR/MANIFEST.sha256"

if [ "$fails" -gt 0 ]; then
  echo "RESULT: $fails evidence failure(s) — the index records what was verified" >&2
  exit 1
fi
echo "RESULT: every phase MANIFEST verifies; index at $INDEX; top manifest at $DIR/MANIFEST.sha256"
